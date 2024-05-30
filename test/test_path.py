import unittest

from httpy.url import remove_dot_segments, transform_reference


class TestPath(unittest.TestCase):
    def test_dot_segments_standard(self):
        reference = '/a/b/c/./../../g'
        target = '/a/g'

        self.assertEqual(target, remove_dot_segments(reference))

    def test_dot_segments_leading_character(self):
        reference = 'mid/content=5/../6'
        target = 'mid/6'

        self.assertEqual(target, remove_dot_segments(reference))

    def test_process_rfc_3986(self):
        base = '/b/c/d;p?q'
        cases = {
            'g:h': 'g:h',
            'g': '/b/c/g',
            './g': '/b/c/g',
            'g/': '/b/c/g/',
            '/g': '/g',
            '//g': '//g',
            '?y': '/b/c/d;p?y',
            'g?y': '/b/c/g?y',
            '#s': '/b/c/d;p?q#s',
            'g#s': '/b/c/g#s',
            'g?y#s': '/b/c/g?y#s',
            ';x': '/b/c/;x',
            'g;x': '/b/c/g;x',
            'g;x?y#s': '/b/c/g;x?y#s',
            '': '/b/c/d;p?q',
            '.': '/b/c/',
            './': '/b/c/',
            '..': '/b/',
            '../': '/b/',
            '../g': '/b/g',
            '../..': '/',
            '../../': '/',
            '../../g': '/g',
            '../../../g': '/g',
            '../../../../g': '/g',
            '/./g': '/g',
            '/../g': '/g',
            'g.': '/b/c/g.',
            '.g': '/b/c/.g',
            'g..': '/b/c/g..',
            '..g': '/b/c/..g',
            './../g': '/b/g',
            './g/.': '/b/c/g/',
            'g/./h': '/b/c/g/h',
            'g/../h': '/b/c/h',
            'g;x=1/./y': '/b/c/g;x=1/y',
            'g;x=1/../y': '/b/c/y',
            'g?y/./x': '/b/c/g?y/./x',
            'g?y/../x': '/b/c/g?y/../x',
            'g#s/./x': '/b/c/g#s/./x',
            'g#s/../x': '/b/c/g#s/../x'
        }

        for k in cases:
            with self.subTest(i=k):
                self.assertEqual(cases[k], transform_reference(base, k), 'case=%s' % k)
