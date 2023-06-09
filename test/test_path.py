import unittest

from httpy import url_remove_dot_segments, url_transform_reference


class TestPath(unittest.TestCase):
    def test_dot_segments_standard(self):
        reference = '/a/b/c/./../../g'
        target = '/a/g'

        self.assertEqual(target, url_remove_dot_segments(reference))

    def test_dot_segments_leading_character(self):
        reference = 'mid/content=5/../6'
        target = 'mid/6'

        self.assertEqual(target, url_remove_dot_segments(reference))

    def test_process_rfc_3986(self):
        base = 'http://a/b/c/d;p?q'
        cases = {
            'g:h': 'g:h',
            'g': 'http://a/b/c/g',
            './g': 'http://a/b/c/g',
            'g/': 'http://a/b/c/g/',
            '/g': 'http://a/g',
            '//g': 'http://g',
            '?y': 'http://a/b/c/d;p?y',
            'g?y': 'http://a/b/c/g?y',
            '#s': 'http://a/b/c/d;p?q#s',
            'g#s': 'http://a/b/c/g#s',
            'g?y#s': 'http://a/b/c/g?y#s',
            ';x': 'http://a/b/c/;x',
            'g;x': 'http://a/b/c/g;x',
            'g;x?y#s': 'http://a/b/c/g;x?y#s',
            '': 'http://a/b/c/d;p?q',
            '.': 'http://a/b/c/',
            './': 'http://a/b/c/',
            '..': 'http://a/b/',
            '../': 'http://a/b/',
            '../g': 'http://a/b/g',
            '../..': 'http://a/',
            '../../': 'http://a/',
            '../../g': 'http://a/g',
            '../../../g': 'http://a/g',
            '../../../../g': 'http://a/g',
            '/./g': 'http://a/g',
            '/../g': 'http://a/g',
            'g.': 'http://a/b/c/g.',
            '.g': 'http://a/b/c/.g',
            'g..': 'http://a/b/c/g..',
            '..g': 'http://a/b/c/..g',
            './../g': 'http://a/b/g',
            './g/.': 'http://a/b/c/g/',
            'g/./h': 'http://a/b/c/g/h',
            'g/../h': 'http://a/b/c/h',
            'g;x=1/./y': 'http://a/b/c/g;x=1/y',
            'g;x=1/../y': 'http://a/b/c/y',
            'g?y/./x': 'http://a/b/c/g?y/./x',
            'g?y/../x': 'http://a/b/c/g?y/../x',
            'g#s/./x': 'http://a/b/c/g#s/./x',
            'g#s/../x': 'http://a/b/c/g#s/../x'
        }

        for k in cases:
            with self.subTest(i=k):
                self.assertEqual(cases[k], url_transform_reference(base, k), 'case=%s' % k)
