from httpy import url_transform_reference

base = 'http://a/b/c/d;p?q'
reference = '../../g'

def test():
    url_transform_reference(base, reference)

if __name__ == '__main__':
    import timeit
    print(timeit.timeit("test()", setup="from __main__ import test", number=1000000))