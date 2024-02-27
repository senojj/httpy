import io
import os
import unittest
from httpy import RequestWriter, read_request_from


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

    def test_request_sized(self):
        body = (
            b"Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et "
            b"dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip "
            b"ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore "
            b"eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia "
            b"deserunt mollit anim id est laborum.")

        r = io.BufferedReader(io.BytesIO(body))
        output = io.BytesIO()
        w = io.BufferedWriter(output)
        rw = RequestWriter(w)
        rw.sized(len(body))

        rw.write_header('/hello')

        data = r.read(1024)
        while len(data) > 0:
            rw.write(data)
            data = r.read(1024)

        rw.close()
        w.flush()
        output.seek(0)
        print(output.read().decode('utf-8'))
