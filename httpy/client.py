import httpy
import io
import ssl
import socket

from typing import Optional, Tuple, List
from httpy import url
from urllib.parse import urlunsplit, urlsplit


class HttpConnection:
    def __init__(self, receiver: io.IOBase, sender: io.IOBase):
        self._receiver = receiver
        self._sender = sender
        self._closed = False

    def send_request(self) -> httpy.RequestWriter:
        if self._closed:
            raise ConnectionError("Connection is closed")
        return httpy.RequestWriter(self._sender)

    def receive_response(self) -> httpy.HttpResponse:
        if self._closed:
            raise ConnectionError("Connection is closed")
        return httpy.read_response_from(self._receiver)

    def close(self):
        if not self._closed:
            self._sender.close()
            self._receiver.close()


def connect(host: Tuple[str, int], context: Optional[ssl.SSLContext] = None) -> Tuple[HttpConnection, socket.socket]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if context is not None:
        sock = context.wrap_socket(sock)
    sock.connect(host)
    return HttpConnection(sock.makefile('rb'), sock.makefile('wb')), sock

'''
class HttpClient:
    def __init__(self,
                 max_redirects: Optional[int] = 10,
                 context: Optional[ssl.SSLContext] = None):
        self._connections = {}
        self._max_redirects = max_redirects
        self._context = context

    def close(self):
        self._connections.clear()

    def do(self,
           host: Tuple[str, int],
           request: httpy.HttpRequest = httpy.HttpRequest(),
           context: Optional[ssl.SSLContext] = None) -> httpy.HttpResponse:
        sock = self.connections.get(host)
        if sock is None:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(host)
            self._connections[host] = sock
        

        redirect_count = -1
        while self._max_redirects is None or redirect_count < self._max_redirects:
            url_parts = urlsplit(request.get_url())

            if url_parts.scheme.strip() == '':
                url_parts = url_parts._replace(scheme=httpy.SCHEME_HTTPS)

            port = url_parts.port

            if port is None:
                port = _SCHEME_PORT.get(url_parts.scheme)

            scheme = url_parts.scheme
            host = url_parts.hostname
            connection = self._connections.get(host, port)

            use_tls = url_parts.scheme == SCHEME_HTTPS

            if connection is None:
                if use_tls:
                    connection = HTTPSConnection(host, port, context=self._context)
                else:
                    connection = HTTPConnection(host, port)
                self._connections[(scheme, host, port)] = connection

            headers = request.get_headers()

            if headers is None:
                headers = {}

            method = request.get_method()

            if method is None:
                method = httpy.METHOD_GET

            request_url = str(urlunsplit(url_parts))

            connection.request(method,
                               request_url,
                               body=request.get_body(),
                               headers=headers)

            response = connection.getresponse()

            response = HttpResponse(request_url,
                                    response.status,
                                    response.version,
                                    Header(response.headers),
                                    Body(response))

            status = response.get_status()

            if status not in _REDIRECT_STATUS or not request.should_follow_redirects():
                return response

            location = response.get_headers().get('location')

            if location is None:
                raise ValueError('redirect specified but no location provided')

            target_url = url.transform_reference(str(urlunsplit(url_parts)), location)
            t_scheme, t_netloc, t_path, t_query, t_fragment = urlsplit(target_url)

            http_method = request.method

            if status == 303:
                http_method = method.GET

            redirect_request = httpy.HttpRequest(http_method=http_method,
                                                 path=
                                                 headers = request.get_headers(),
            body = request.get_body())

            request = redirect_request
            redirect_count += 1
        raise ValueError('exceeded maximum redirections')
'''
