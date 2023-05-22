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


def ok_only(handler: RequestHandler):
    handler.send_response(httpy.STATUS_OK)
    handler.end_headers()


httpd = HTTPServer(('127.0.0.1', 8585), RequestHandler)
p = Thread(target=httpd.serve_forever)
p.daemon = True
p.start()
client = httpy.HttpClient()


def tearDownModule():
    client.close()
    httpd.shutdown()
    httpd.server_close()
    p.join()


class TestRedirects(unittest.TestCase):
    def test_redirect_301_follow(self):
        request = httpy.HttpRequest(url='https://%s:%d/generic' % httpd.server_address,
                                    headers={'status': '301', 'to': '/ok-only'})
        response = client.do(request)
        status = response.get_status()
        response.get_body().close()

        self.assertEqual(status, httpy.STATUS_OK)

    def test_redirect_301_nofollow(self):
        request = httpy.HttpRequest(url='https://%s:%d/generic' % httpd.server_address,
                                    headers={'status': '301', 'to': '/ok-only'},
                                    follow_redirects=False)
        response = client.do(request)
        status = response.get_status()
        location = response.get_headers().get('location')
        response.get_body().close()

        self.assertEqual(status, httpy.STATUS_MOVED_PERMANENTLY)
        target_location = '/ok-only'
        self.assertEqual(target_location, location)

    def test_redirect_303_follow(self):
        request = httpy.HttpRequest(url='https://%s:%d/generic' % httpd.server_address,
                                    headers={'status': '303', 'to': '/get-only'})
        response = client.do(request)
        status = response.get_status()
        response.get_body().close()

        self.assertEqual(status, httpy.STATUS_OK)

    def test_redirect_303_nofollow(self):
        request = httpy.HttpRequest(url='https://%s:%d/generic' % httpd.server_address,
                                    headers={'status': '303', 'to': '/get-only'},
                                    follow_redirects=False)
        response = client.do(request)
        status = response.get_status()
        location = response.get_headers().get('location')
        response.get_body().close()

        self.assertEqual(status, httpy.STATUS_SEE_OTHER)
        target_location = '/get-only'
        self.assertEqual(target_location, location)


if __name__ == '__main__':
    unittest.main()