import unittest
from http.server import HTTPServer, BaseHTTPRequestHandler
from httpy import HttpClient, HttpRequest
from threading import Thread


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(301)
        self.send_header('location', 'https://dynata.com')
        self.end_headers()


class TestRedirects(unittest.TestCase):
    def test_redirect_301(self):
        httpd = HTTPServer(('127.0.0.1', 8585), RequestHandler)
        p = Thread(target=httpd.serve_forever)
        p.daemon = True
        p.start()

        try:
            client = HttpClient()
            request = HttpRequest(url='http://127.0.0.1:%d' % 8585)
            response = client.do(request)
            status = response.get_status()
            response.get_body().close()
            client.close()
        finally:
            httpd.shutdown()
            httpd.server_close()
            p.join()

        self.assertEqual(status, 200)


if __name__ == '__main__':
    unittest.main()
