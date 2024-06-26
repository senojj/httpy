import socket
import io
import unittest
import gzip
import httpy

from httpy import client
from httpy import server
from httpy import header

from typing import Generator

payload = (b"Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et "
           b"dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip "
           b"ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore "
           b"eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia "
           b"deserunt mollit anim id est laborum.")


def _chunk(size: int, data: bytes) -> Generator[bytes, None, None]:
    for i in range(0, len(data), size):
        yield data[i:i + size]


class TestPath(unittest.TestCase):
    def test_sized_body_writer(self):
        buf = io.BytesIO()
        body_writer = httpy.SizedBodyWriter(buf, 10)
        b_written = body_writer.write(b'aaaaa')
        self.assertEqual(b_written, 5)
        b_written = body_writer.write(b'bbbbb')
        self.assertEqual(b_written, 5)
        b_written = body_writer.write(b'ccccc')
        self.assertEqual(b_written, 0)
        body_writer.close()
        buf.seek(0)
        self.assertEqual(buf.read(), b'aaaaabbbbb')
        buf.close()

    def test_stream_body_writer(self):
        buf = io.BytesIO()
        trailers = header.FieldList()
        trailers.append_field('Test', '123')
        body_writer = httpy.StreamBodyWriter(buf, 6, trailers)
        b_written = body_writer.write(b'aaaaa')
        self.assertEqual(b_written, 5)
        body_writer.flush()
        self.assertEqual(buf.getvalue(), b'')
        b_written = body_writer.write(b'bbbbb')
        self.assertEqual(b_written, 5)
        body_writer.flush()
        self.assertEqual(buf.getvalue(), b'6\r\n'
                                         b'aaaaab\r\n')
        b_written = body_writer.write(b'ccccc')
        self.assertEqual(b_written, 5)
        body_writer.flush()
        self.assertEqual(buf.getvalue(), b'6\r\n'
                                         b'aaaaab\r\n'
                                         b'6\r\n'
                                         b'bbbbcc\r\n')
        b_written = body_writer.write(b'ddd')
        self.assertEqual(b_written, 3)
        body_writer.flush()
        self.assertEqual(buf.getvalue(), b'6\r\n'
                                         b'aaaaab\r\n'
                                         b'6\r\n'
                                         b'bbbbcc\r\n'
                                         b'6\r\n'
                                         b'cccddd\r\n')
        b_written = body_writer.write(b'eee')
        self.assertEqual(b_written, 3)
        body_writer.flush()
        self.assertEqual(buf.getvalue(), b'6\r\n'
                                         b'aaaaab\r\n'
                                         b'6\r\n'
                                         b'bbbbcc\r\n'
                                         b'6\r\n'
                                         b'cccddd\r\n')
        body_writer.close()
        buf.seek(0)
        self.assertEqual(buf.read(), b'6\r\n'
                                     b'aaaaab\r\n'
                                     b'6\r\n'
                                     b'bbbbcc\r\n'
                                     b'6\r\n'
                                     b'cccddd\r\n'
                                     b'3\r\n'
                                     b'eee'
                                     b'\r\n'
                                     b'0\r\n'
                                     b'Test: 123\r\n'
                                     b'\r\n')
        buf.close()

    def test_sized_socket(self):
        s_client, s_server = socket.socketpair()
        c = client.ClientConnection(s_client.makefile('rb'), s_client.makefile('wb'))
        s = server.ServerConnection(s_server.makefile('rb'), s_server.makefile('wb'))

        request = c.send_request()
        request.path = '/hello-world'
        request.method = httpy.METHOD_POST
        request.header().append_field('Host', 'test.com')
        request.sized(len(payload))
        request.write(payload)
        request.close()

        recv_request = s.receive_request()
        body = recv_request.body.read_all()
        recv_request.body.close()

        c.close()
        s.close()

        s_client.close()
        s_server.close()

        self.assertEqual(recv_request.method, httpy.METHOD_POST)
        self.assertEqual(recv_request.version, httpy.VERSION_HTTP_1_1)
        self.assertEqual(recv_request.path, '/hello-world')
        self.assertEqual(recv_request.headers, [('Host', 'test.com'), ('Content-Length', str(len(payload)))])
        self.assertEqual(body, payload)

    def test_stream_socket(self):
        s_client, s_server = socket.socketpair()
        c = client.ClientConnection(s_client.makefile('rb'), s_client.makefile('wb'))
        s = server.ServerConnection(s_server.makefile('rb'), s_server.makefile('wb'))

        request = c.send_request()
        request.path = '/hello-world'
        request.header().append_field('Host', 'test.com')
        request.chunked()
        request.write(payload)
        request.header().append_field('Test', '123')
        request.close()

        recv_request = s.receive_request()
        body = recv_request.body.read_all()
        recv_request.body.close()

        c.close()
        s.close()

        s_client.close()
        s_server.close()

        self.assertEqual(recv_request.method, httpy.METHOD_GET)
        self.assertEqual(recv_request.version, httpy.VERSION_HTTP_1_1)
        self.assertEqual(recv_request.path, '/hello-world')
        self.assertEqual(recv_request.headers, [('Host', 'test.com'), ('Transfer-Encoding', 'chunked')])
        self.assertEqual(body, payload)
        self.assertEqual(recv_request.trailers, [('Test', '123')])

    def test_gzip_streaming(self):
        s_client = io.BytesIO()
        b_writer = httpy.StreamBodyWriter(s_client, 6, httpy.HeaderMap())
        g_client = gzip.GzipFile(filename=None, fileobj=b_writer, mode='wb')

        for data in _chunk(6, payload):
            g_client.write(data)

        g_client.close()
        b_writer.close()
        s_client.seek(0)
        b_reader = httpy.StreamBodyReader(s_client, [])
        value = b_reader.read_all()
        body = gzip.decompress(value)
        self.assertEqual(payload, body)
