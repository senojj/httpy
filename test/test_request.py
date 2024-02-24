import io
import unittest
from httpy import HttpRequest, Body


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
            body=Body(io.BufferedReader(io.BytesIO(body)), len(body)),
            trailer=[('Signature', 'arolighroaeigfhjarlkseiklgfhaoli')]
        )
        buf = io.BytesIO()
        writer = io.BufferedWriter(buf)
        r.write_to(writer, 64)
        writer.flush()
        buf.seek(0)
        print(buf.read().decode())
        return
