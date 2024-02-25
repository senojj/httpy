import io
import unittest
from httpy import HttpRequest, SizedBodyReader, StreamBodyReader


class TestPath(unittest.TestCase):

    def test_request(self):
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
            body=SizedBodyReader(io.BufferedReader(io.BytesIO(body)), len(body)),
            trailer=[('Signature', 'arolighroaeigfhjarlkseiklgfhaoli')]
        )
        buf = io.BytesIO()
        writer = io.BufferedWriter(buf)
        r.write_to(writer, 64)
        writer.flush()
        buf.seek(0)
        print(buf.read().decode())
        return

    def test_body_reader(self):
        body = (
            b'64\r\n'
            b'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do \r\n'
            b'64\r\n'
            b'eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut e\r\n'
            b'64\r\n'
            b'nim ad minim veniam, quis nostrud exercitation ullamco laboris n\r\n'
            b'64\r\n'
            b'isi ut aliquip ex ea commodo consequat. Duis aute irure dolor in\r\n'
            b'64\r\n'
            b' reprehenderit in voluptate velit esse cillum dolore eu fugiat n\r\n'
            b'64\r\n'
            b'ulla pariatur. Excepteur sint occaecat cupidatat non proident, s\r\n'
            b'61\r\n'
            b'unt in culpa qui officia deserunt mollit anim id est laborum.\r\n'
            b'0\r\n')
        buffer = io.BufferedReader(io.BytesIO(body))
        reader = StreamBodyReader(buffer)
        result = reader.read_all().decode()
        print(result)
