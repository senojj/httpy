import io
import os
import socket
import unittest
from httpy import RequestWriter, read_request_from, HttpConnection


class TestPath(unittest.TestCase):

    def test_request_streaming(self):
        body = (
            b"Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et "
            b"dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip "
            b"ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore "
            b"eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia "
            b"deserunt mollit anim id est laborum.")

        rd = io.BufferedReader(io.BytesIO(body))
        r, w = os.pipe()
        rw = RequestWriter(io.BufferedWriter(io.FileIO(w, 'wb')))
        rw.chunked()
        rw.add_header("Trailer", "Signature")
        rw.write_header('/hello')

        data = rd.read(1024)
        while len(data) > 0:
            rw.write(data)
            data = rd.read(1024)

        rw.add_header("Signature", "abc123")

        rw.close()
        t = io.BufferedReader(io.FileIO(r, 'rb'))
        req = read_request_from(t)
        b = req.body.read_all()
        req.body.close()
        print(b)
        print(req.trailers)

    def test_socket(self):
        body = (
            b"Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et "
            b"dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip "
            b"ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore "
            b"eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia "
            b"deserunt mollit anim id est laborum.")

        s_client, s_server = socket.socketpair()
        client = HttpConnection(s_client)
        server = HttpConnection(s_server)

        request = client.send_request()
        request.add_header('Host', 'test.com')
        request.sized(len(body))
        request.write_header('/hello-world')
        request.write(body)
        request.close()

        request = client.send_request()
        request.add_header('Host', 'test.com')
        request.sized(5)
        request.write_header('/hello')
        request.write(b'hello')
        request.close()

        recv_request = server.receive_request()
        body = recv_request.body.read_all()
        print(body.decode())
        recv_request.body.close()

        recv_request = server.receive_request()
        body = recv_request.body.read_all()
        print(body.decode())
        recv_request.body.close()

        client.close()
        server.close()

        s_client.close()
        s_server.close()
