import unittest

from httpy import HttpRequest


class TestPath(unittest.TestCase):

    def test_url_encoding_3986(self):
        cases = [
            "test.com?t=1%20%2B%201%20%3D%202"
        ]

        for k in cases:
            with self.subTest(i=k):
                self.assertEqual(k, HttpRequest(k).get_url(), 'case=%s' % k)
