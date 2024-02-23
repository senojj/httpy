import io
import unittest
from httpy import HttpRequest


class TestPath(unittest.TestCase):

    def test_request(self):
        body = io.BytesIO(b'hello')

        r = HttpRequest(
            method='GET',
            path='/hello',
            header=[('Transfer-Encoding', 'chunked')],
            body=body
        )
        buf = io.BytesIO()
        r.write_to(buf)
        buf.seek(0)
        print(buf.read().decode())
        return
