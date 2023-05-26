import ssl
import unittest
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from urllib.parse import urlsplit

import httpy


class RequestHandler(BaseHTTPRequestHandler):
    def handle_any(self):
        paths = {
            '/generic': generic,
            '/get-only': get_only,
            '/post-only': post_only,
            '/ok-only': ok_only
        }
        url_parts = urlsplit(self.path)
        handler = paths.get(url_parts.path)

        if handler is None:
            self.send_response(httpy.STATUS_NOT_FOUND)
            self.end_headers()
        else:
            handler(self)

    def do_GET(self):
        self.handle_any()

    def do_POST(self):
        self.handle_any()


def generic(handler: RequestHandler):
    status = handler.headers.get('status')

    if status is None:
        status = httpy.STATUS_OK

    handler.send_response(int(status))

    to = handler.headers.get('to')

    if to is None:
        to = '/generic'

    handler.send_header('location', to)
    handler.end_headers()


def get_only(handler: RequestHandler):
    if handler.command != httpy.METHOD_GET:
        handler.send_response(httpy.STATUS_METHOD_NOT_ALLOWED)
    else:
        handler.send_response(httpy.STATUS_OK)
    handler.end_headers()


def post_only(handler: RequestHandler):
    if handler.command != httpy.METHOD_POST:
        handler.send_response(httpy.STATUS_METHOD_NOT_ALLOWED)
    else:
        handler.send_response(httpy.STATUS_OK)
    handler.end_headers()


def ok_only(handler: RequestHandler):
    handler.send_response(httpy.STATUS_OK)
    handler.end_headers()


httpd = HTTPServer(('127.0.0.1', 8080), RequestHandler)
httpsd = HTTPServer(('127.0.0.1', 4443), RequestHandler)

httpsd.socket = ssl.wrap_socket(httpsd.socket,
                                keyfile='./localhost.key',
                                certfile='./localhost.crt',
                                server_side=True)

ctx_no_check = ssl.create_default_context()
ctx_no_check.check_hostname = False
ctx_no_check.verify_mode = ssl.CERT_NONE

p1 = Thread(target=httpd.serve_forever)
p2 = Thread(target=httpsd.serve_forever)
p1.daemon = True
p2.daemon = True
p1.start()
p2.start()
client = httpy.HttpClient()


def tearDownModule():
    client.close()
    httpd.shutdown()
    httpsd.shutdown()
    httpd.server_close()
    httpsd.server_close()
    p1.join()
    p2.join()


class TestRedirects(unittest.TestCase):
    def test_redirect_301_follow(self):
        request = httpy.HttpRequest(url='https://%s:%d/generic' % httpsd.server_address,
                                    headers={'status': str(httpy.STATUS_MOVED_PERMANENTLY),
                                             'to': 'http://%s:%d/ok-only' % httpd.server_address},
                                    context=ctx_no_check)
        response = client.do(request)
        status = response.get_status()
        response.get_body().close()

        self.assertEqual(status, httpy.STATUS_OK)

    def test_redirect_301_nofollow(self):
        request = httpy.HttpRequest(url='https://%s:%d/generic' % httpsd.server_address,
                                    headers={'status': str(httpy.STATUS_MOVED_PERMANENTLY), 'to': '/ok-only'},
                                    follow_redirects=False,
                                    context=ctx_no_check)
        response = client.do(request)
        status = response.get_status()
        location = response.get_headers().get('location')
        response.get_body().close()

        self.assertEqual(status, httpy.STATUS_MOVED_PERMANENTLY)
        target_location = '/ok-only'
        self.assertEqual(target_location, location)

    def test_redirect_http_to_https(self):
        request = httpy.HttpRequest(url='http://%s:%d/generic' % httpd.server_address,
                                    headers={'status': str(httpy.STATUS_MOVED_PERMANENTLY),
                                             'to': 'https://%s:%d/ok-only' % httpsd.server_address},
                                    context=ctx_no_check)
        response = client.do(request)
        status = response.get_status()
        url = response.get_url()
        response.get_body().close()

        self.assertEqual(status, httpy.STATUS_OK)
        self.assertEqual(url, 'https://%s:%d/ok-only' % httpsd.server_address)

    def test_redirect_exceed_maximum(self):
        request = httpy.HttpRequest(url='https://%s:%d/generic' % httpsd.server_address,
                                    headers={'status': str(httpy.STATUS_MOVED_PERMANENTLY),
                                             'to': 'https://%s:%d/generic' % httpsd.server_address},
                                    max_redirects=3,
                                    context=ctx_no_check)

        def subject():
            client.do(request)

        self.assertRaises(ValueError, subject)

    def test_redirect_302_follow(self):
        request = httpy.HttpRequest(url='https://%s:%d/generic' % httpsd.server_address,
                                    headers={'status': str(httpy.STATUS_FOUND), 'to': '/ok-only'},
                                    context=ctx_no_check)
        response = client.do(request)
        status = response.get_status()
        response.get_body().close()

        self.assertEqual(status, httpy.STATUS_OK)

    def test_redirect_302_nofollow(self):
        request = httpy.HttpRequest(url='https://%s:%d/generic' % httpsd.server_address,
                                    headers={'status': str(httpy.STATUS_FOUND), 'to': '/ok-only'},
                                    follow_redirects=False,
                                    context=ctx_no_check)
        response = client.do(request)
        status = response.get_status()
        location = response.get_headers().get('location')
        response.get_body().close()

        self.assertEqual(status, httpy.STATUS_FOUND)
        target_location = '/ok-only'
        self.assertEqual(target_location, location)

    def test_redirect_303_follow(self):
        request = httpy.HttpRequest(url='https://%s:%d/generic' % httpsd.server_address,
                                    method=httpy.METHOD_POST,
                                    headers={'status': str(httpy.STATUS_SEE_OTHER), 'to': '/get-only'},
                                    context=ctx_no_check)
        response = client.do(request)
        status = response.get_status()
        response.get_body().close()

        self.assertEqual(status, httpy.STATUS_OK)

    def test_redirect_303_nofollow(self):
        request = httpy.HttpRequest(url='https://%s:%d/generic' % httpsd.server_address,
                                    method=httpy.METHOD_POST,
                                    headers={'status': str(httpy.STATUS_SEE_OTHER), 'to': '/get-only'},
                                    follow_redirects=False,
                                    context=ctx_no_check)
        response = client.do(request)
        status = response.get_status()
        location = response.get_headers().get('location')
        response.get_body().close()

        self.assertEqual(status, httpy.STATUS_SEE_OTHER)
        target_location = '/get-only'
        self.assertEqual(target_location, location)

    def test_redirect_304_follow(self):
        request = httpy.HttpRequest(url='https://%s:%d/generic' % httpsd.server_address,
                                    headers={'status': str(httpy.STATUS_NOT_MODIFIED)},
                                    context=ctx_no_check)
        response = client.do(request)
        status = response.get_status()
        response.get_body().close()

        self.assertEqual(status, httpy.STATUS_NOT_MODIFIED)

    def test_redirect_304_nofollow(self):
        request = httpy.HttpRequest(url='https://%s:%d/generic' % httpsd.server_address,
                                    headers={'status': str(httpy.STATUS_NOT_MODIFIED)},
                                    follow_redirects=False,
                                    context=ctx_no_check)
        response = client.do(request)
        status = response.get_status()
        response.get_body().close()

        self.assertEqual(status, httpy.STATUS_NOT_MODIFIED)

    def test_redirect_307_follow(self):
        request = httpy.HttpRequest(url='https://%s:%d/generic' % httpsd.server_address,
                                    method=httpy.METHOD_POST,
                                    headers={'status': str(httpy.STATUS_TEMPORARY_REDIRECT), 'to': '/post-only'},
                                    context=ctx_no_check)
        response = client.do(request)
        status = response.get_status()
        response.get_body().close()

        self.assertEqual(status, httpy.STATUS_OK)

    def test_redirect_307_nofollow(self):
        request = httpy.HttpRequest(url='https://%s:%d/generic' % httpsd.server_address,
                                    method=httpy.METHOD_POST,
                                    headers={'status': str(httpy.STATUS_TEMPORARY_REDIRECT), 'to': '/post-only'},
                                    follow_redirects=False,
                                    context=ctx_no_check)
        response = client.do(request)
        status = response.get_status()
        location = response.get_headers().get('location')
        response.get_body().close()

        self.assertEqual(status, httpy.STATUS_TEMPORARY_REDIRECT)
        target_location = '/post-only'
        self.assertEqual(target_location, location)

    def test_redirect_308_follow(self):
        request = httpy.HttpRequest(url='https://%s:%d/generic' % httpsd.server_address,
                                    method=httpy.METHOD_POST,
                                    headers={'status': str(httpy.STATUS_PERMANENT_REDIRECT), 'to': '/post-only'},
                                    context=ctx_no_check)
        response = client.do(request)
        status = response.get_status()
        response.get_body().close()

        self.assertEqual(status, httpy.STATUS_OK)

    def test_redirect_308_nofollow(self):
        request = httpy.HttpRequest(url='https://%s:%d/generic' % httpsd.server_address,
                                    method=httpy.METHOD_POST,
                                    headers={'status': str(httpy.STATUS_PERMANENT_REDIRECT), 'to': '/post-only'},
                                    follow_redirects=False,
                                    context=ctx_no_check)
        response = client.do(request)
        status = response.get_status()
        location = response.get_headers().get('location')
        response.get_body().close()

        self.assertEqual(status, httpy.STATUS_PERMANENT_REDIRECT)
        target_location = '/post-only'
        self.assertEqual(target_location, location)


if __name__ == '__main__':
    unittest.main()
