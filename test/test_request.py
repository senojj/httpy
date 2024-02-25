import io
import unittest
from httpy import HttpRequest, SizedBodyReader, StreamBodyReader, read_request_from


class TestPath(unittest.TestCase):

    def test_request_streaming(self):
        body = (
            b"Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et "
            b"dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip "
            b"ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore "
            b"eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia "
            b"deserunt mollit anim id est laborum.")

        r = HttpRequest(
            method='GET',
            path='/hello',
            header=[('Transfer-Encoding', 'chunked')],
            body=io.BufferedReader(io.BytesIO(body)),
            trailer=[('Signature', 'arolighroaeigfhjarlkseiklgfhaoli')]
        )
        buf = io.BytesIO()
        writer = io.BufferedWriter(buf)
        r.write_to(writer)
        writer.flush()
        buf.seek(0)
        print(buf.read().decode('utf-8'))

    def test_request_sized(self):
        body = (
            b"Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et "
            b"dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip "
            b"ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore "
            b"eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia "
            b"deserunt mollit anim id est laborum.")

        r = HttpRequest(
            method='GET',
            path='/hello',
            header=[('Content-Length', f'{len(body)}')],
            body=io.BufferedReader(io.BytesIO(body)),
            trailer=[]
        )
        buf = io.BytesIO()
        writer = io.BufferedWriter(buf)
        r.write_to(writer)
        writer.flush()
        buf.seek(0)
        print(buf.read().decode('utf-8'))
