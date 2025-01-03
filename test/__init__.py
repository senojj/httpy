import httpy
from unittest import TestCase

class TestSystem(TestCase):
    def test_init(self):
        hnd = httpy.init()
        httpy.set_opt(hnd, httpy.OPT_METHOD, httpy.METHOD_POST)
        httpy.set_opt(hnd, httpy.OPT_URL, "http://example.com")
        httpy.perform(hnd)
        httpy.free(hnd)
        httpy.cleanup()