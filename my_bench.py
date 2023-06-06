from httpy import _process_reference_url

base = 'http://a/b/c/d;p?q'
reference = '../../g'

def test():
    _process_reference_url(base, reference)

if __name__ == '__main__':
    import timeit
    print(timeit.timeit("test()", setup="from __main__ import test", number=1000000))