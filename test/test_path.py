import unittest
from urllib.parse import urlsplit

from httpy import _remove_dot_segments, _merge_path


class TestPath(unittest.TestCase):
    def test_dot_segments_standard(self):
        reference = '/../a/b/../c/./d.html'
        target = '/a/c/d.html'

        self.assertEqual(_remove_dot_segments(reference), target)

    def test_dot_segments_rfc_example(self):
        reference = '/a/b/c/./../../g'
        target = '/a/g'

        self.assertEqual(_remove_dot_segments(reference), target)

    def test_dot_segments_leading_character(self):
        reference = 'a/b/c/'
        target = 'a/b/c/'

        self.assertEqual(_remove_dot_segments(reference), target)

    def test_dot_segments_single_dot(self):
        reference = '/./a/b/../c/./d.html'
        target = '/a/c/d.html'

        self.assertEqual(_remove_dot_segments(reference), target)

    def test_dot_segments_leading_double_dot(self):
        reference = '../a/b/c/.'
        target = 'a/b/c'

        self.assertEqual(_remove_dot_segments(reference), target)

    def test_dot_segments_leading_single_dot(self):
        reference = './a/b/c/..'
        target = 'a/b'

        self.assertEqual(_remove_dot_segments(reference), target)

    def test_merge_standard(self):
        base = 'https://somplace.org/test1/test2/'
        reference = '/test3/test4'
        target = '/test1/test2/test3/test4'

        base_parts = urlsplit(base)
        reference_parts = urlsplit(reference)

        self.assertEqual(_merge_path(base_parts, reference_parts), target)

    def test_merge_missing_trailing_slash(self):
        base = 'https://somplace.org/test1/test2'
        reference = '/test3/test4'
        target = '/test1/test3/test4'

        base_parts = urlsplit(base)
        reference_parts = urlsplit(reference)

        self.assertEqual(_merge_path(base_parts, reference_parts), target)