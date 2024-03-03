import socket
import io
import unittest
import gzip
from httpy import HttpConnection, VERSION_HTTP_1_1, METHOD_GET, StreamBodyWriter, StreamBodyReader


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

        self.assertEqual(recv_request.method, METHOD_GET)
        self.assertEqual(recv_request.version, VERSION_HTTP_1_1)
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
        request.add_header('Test', '123')
        request.close()

        recv_request = server.receive_request()
        body = recv_request.body.read_all()
        recv_request.body.close()

        client.close()
        server.close()

        s_client.close()
        s_server.close()

        self.assertEqual(recv_request.method, METHOD_GET)
        self.assertEqual(recv_request.version, VERSION_HTTP_1_1)
        self.assertEqual(recv_request.path, '/hello-world')
        self.assertEqual(recv_request.headers, [('Host', 'test.com'), ('Transfer-Encoding', 'chunked')])
        self.assertEqual(body, payload)
        self.assertEqual(recv_request.trailers, [('Test', '123')])

    def test_gzip_streaming(self):
        s_client = io.BytesIO()
        w_client = io.BufferedWriter(s_client)
        b_writer = StreamBodyWriter(w_client, 64, [])
        g_client = gzip.GzipFile(filename=None, fileobj=b_writer, mode='wb')
        g_client.write(b'hello')
        g_client.close()
        b_writer.close()
        s_client.seek(0)
        b_reader = StreamBodyReader(s_client, [])
        value = b_reader.read_all()
        print(value)
        print(gzip.decompress(value).decode('utf-8'))
