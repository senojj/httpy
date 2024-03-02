import socket
import unittest
from httpy import HttpConnection


class TestPath(unittest.TestCase):
    def test_sized_socket(self):
        payload = (
            b"Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et "
            b"dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip "
            b"ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore "
            b"eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia "
            b"deserunt mollit anim id est laborum.")

        s_client, s_server = socket.socketpair()
        client = HttpConnection(s_client.makefile('rb'), s_client.makefile('wb'))
        server = HttpConnection(s_server.makefile('rb'), s_server.makefile('wb'))

        request = client.send_request()
        request.add_header('Host', 'test.com')
        request.sized(len(payload))
        request.write_header('/hello-world')
        request.write(payload)
        request.close()

        request = client.send_request()
        request.add_header('Host', 'test.com')
        request.sized(5)
        request.write_header('/hello')
        request.write(b'hello')
        request.close()

        recv_request = server.receive_request()
        body = recv_request.body.read_all()
        recv_request.body.close()

        client.close()
        server.close()

        s_client.close()
        s_server.close()

        self.assertEqual(recv_request.path, '/hello-world')
        self.assertEqual(recv_request.headers, [('Host', 'test.com'), ('Content-Length', '445')])
        self.assertEqual(body, payload)

    def test_stream_socket(self):
        payload = (
            b"Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et "
            b"dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip "
            b"ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore "
            b"eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia "
            b"deserunt mollit anim id est laborum.")

        s_client, s_server = socket.socketpair()
        client = HttpConnection(s_client.makefile('rb'), s_client.makefile('wb'))
        server = HttpConnection(s_server.makefile('rb'), s_server.makefile('wb'))

        request = client.send_request()
        request.add_header('Host', 'test.com')
        request.chunked()
        request.write_header('/hello-world')
        request.write(payload)
        request.close()

        recv_request = server.receive_request()
        body = recv_request.body.read_all()
        recv_request.body.close()

        client.close()
        server.close()

        s_client.close()
        s_server.close()

        self.assertEqual(recv_request.path, '/hello-world')
        self.assertEqual(recv_request.headers, [('Host', 'test.com'), ('Transfer-Encoding', 'chunked')])
        self.assertEqual(body, payload)
