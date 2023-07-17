from urllib.parse import urljoin

base = 'http://a/b/c/d;p?q'
reference = '../../g'

def test():
    r = urljoin(base, reference)

if __name__ == '__main__':
    import timeit
    print(timeit.timeit("test()", setup="from __main__ import test", number=1000000))