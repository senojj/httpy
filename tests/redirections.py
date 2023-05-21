import unittest
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from urllib.parse import urlsplit

from httpy import HttpClient, HttpRequest


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        paths = {
            '/redirect-once': redirect_once,
            '/ok': ok
        }
        url_parts = urlsplit(self.path)
        handler = paths.get(url_parts.path)

        if handler is None:
            self.send_response(404)
            self.end_headers()
        else:
            handler(self)


def redirect_once(handler: RequestHandler):
    handler.send_response(301)
    handler.send_header('location',
                        'https://%s:%s/ok' % (handler.server.server_address[0], handler.server.server_address[1]))
    handler.end_headers()


def ok(handler: RequestHandler):
    handler.send_response(200)
    handler.end_headers()


httpd = HTTPServer(('127.0.0.1', 8585), RequestHandler)
p = Thread(target=httpd.serve_forever)
p.daemon = True
p.start()
client = HttpClient()


def tearDownModule():
    client.close()
    httpd.shutdown()
    httpd.server_close()
    p.join()


class TestRedirects(unittest.TestCase):
    def test_redirect_301_follow(self):
        host, port = httpd.server_address
        request = HttpRequest(url='https://%s:%d/redirect-once' % (host, port))
        response = client.do(request)
        status = response.get_status()
        response.get_body().close()

        self.assertEqual(status, 200)

    def test_redirect_301_nofollow(self):
        host, port = httpd.server_address
        request = HttpRequest(url='https://%s:%d/redirect-once' % (host, port), follow_redirects=False)
        response = client.do(request)
        status = response.get_status()
        location = response.get_headers().get('location')
        response.get_body().close()

        self.assertEqual(status, 301)
        target_location = 'https://%s:%d/ok' % (host, port)
        self.assertEqual(target_location, location)


if __name__ == '__main__':
    unittest.main()
