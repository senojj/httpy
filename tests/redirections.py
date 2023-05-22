import unittest
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from urllib.parse import urlsplit

import httpy


class RequestHandler(BaseHTTPRequestHandler):
    def handle_any(self):
        paths = {
            '/redirect-permanent-once': redirect_permanent_once,
            '/ok': ok,
            '/redirect-see-other': redirect_see_other,
            '/get-other': get_other
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


def redirect_permanent_once(handler: RequestHandler):
    handler.send_response(httpy.STATUS_MOVED_PERMANENTLY)
    handler.send_header('location', '/ok')
    handler.end_headers()


def ok(handler: RequestHandler):
    handler.send_response(httpy.STATUS_OK)
    handler.end_headers()


def redirect_see_other(handler: RequestHandler):
    handler.send_response(httpy.STATUS_SEE_OTHER)
    handler.send_header('location', '/get-other')
    handler.end_headers()


def get_other(handler: RequestHandler):
    if handler.command != httpy.METHOD_GET:
        handler.send_response(httpy.STATUS_NOT_FOUND)
    else:
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
        request = httpy.HttpRequest(url='https://%s:%d/redirect-permanent-once' % httpd.server_address)
        response = client.do(request)
        status = response.get_status()
        response.get_body().close()

        self.assertEqual(status, httpy.STATUS_OK)

    def test_redirect_301_nofollow(self):
        request = httpy.HttpRequest(url='https://%s:%d/redirect-permanent-once' % httpd.server_address,
                                    follow_redirects=False)
        response = client.do(request)
        status = response.get_status()
        location = response.get_headers().get('location')
        response.get_body().close()

        self.assertEqual(status, httpy.STATUS_MOVED_PERMANENTLY)
        target_location = '/ok'
        self.assertEqual(target_location, location)

    def test_redirect_303_follow(self):
        request = httpy.HttpRequest(url='https://%s:%d/redirect-see-other' % httpd.server_address)
        response = client.do(request)
        status = response.get_status()
        response.get_body().close()

        self.assertEqual(status, httpy.STATUS_OK)

    def test_redirect_303_nofollow(self):
        request = httpy.HttpRequest(url='https://%s:%d/redirect-see-other' % httpd.server_address,
                                    follow_redirects=False)
        response = client.do(request)
        status = response.get_status()
        location = response.get_headers().get('location')
        response.get_body().close()

        self.assertEqual(status, httpy.STATUS_SEE_OTHER)
        target_location = '/get-other'
        self.assertEqual(target_location, location)


if __name__ == '__main__':
    unittest.main()
