import io
import unittest
from httpy import HttpRequest, _MAX_READ_SZ


class TestPath(unittest.TestCase):

    def test_request(self):
        body = io.BytesIO(
            b"Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et "
            b"dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip "
            b"ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore "
            b"eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia "
            b"deserunt mollit anim id est laborum.")

        r = HttpRequest(
            method='GET',
            path='/hello',
            header=[('Transfer-Encoding', 'chunked')],
            body=body,
            trailer=[('Signature', 'arolighroaeigfhjarlkseiklgfhaoli')]
        )
        buf = io.BytesIO()
        r.write_to(buf, 64)
        buf.seek(0)
        print(buf.read().decode())
        return
