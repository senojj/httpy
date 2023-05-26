import unittest

from httpy import _remove_dot_segments


class TestDotSegments(unittest.TestCase):
    def test_standard(self):
        reference = '/../a/b/../c/./d.html'
        target = '/a/c/d.html'

        self.assertEqual(_remove_dot_segments(reference), target)

    def test_rfc_example(self):
        reference = '/a/b/c/./../../g'
        target = '/a/g'

        self.assertEqual(_remove_dot_segments(reference), target)

    def test_single_dot_segment(self):
        reference = '/./a/b/../c/./d.html'
        target = '/a/c/d.html'

        self.assertEqual(_remove_dot_segments(reference), target)

    def test_leading_double_dot(self):
        reference = '../a/b/c/.'
        target = 'a/b/c'

        self.assertEqual(_remove_dot_segments(reference), target)

    def test_leading_single_dot(self):
        reference = './a/b/c/..'
        target = 'a/b'

        self.assertEqual(_remove_dot_segments(reference), target)
