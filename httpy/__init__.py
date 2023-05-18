from typing import Optional, Dict, List
from http.client import HTTPConnection, HTTPResponse, HTTPSConnection
from urllib.parse import urlsplit, urlunsplit, urlencode, parse_qs
from email.message import Message

_SCHEME_PORT = {
    'http': 80,
    'https': 443
}

_REDIRECT_STATUS = [
    301,
    302,
    303,
    307,
    308
]

METHOD_GET = 'GET'
METHOD_POST = 'POST'
METHOD_PUT = 'PUT'
METHOD_PATCH = 'PATCH'
METHOD_HEAD = 'HEAD'
METHOD_OPTION = 'OPTION'


class Header:
    def __init__(self, message: Message):
        self._message = message

    def get(self, name: str) -> Optional[str]:
        return self._message.get(name)


class Body:
    def __init__(self, response: HTTPResponse):
        self._response = response

    def read(self, amt: int) -> bytes:
        return self._response.read(amt)

    def read_into(self, b: bytearray) -> int:
        return self._response.readinto(b)

    def close(self):
        return self._response.close()

    def __del__(self):
        self.close()


class HttpRequest:
    def __init__(self,
                 url: str,
                 method: Optional[str] = None,
                 headers: Optional[Dict[str, str]] = None,
                 parameters: Optional[Dict[str, List[str]]] = None,
                 body: Optional[bytes] = None,
                 tls: Optional[bool] = None,
                 follow_redirects: bool = True,
                 max_redirects: Optional[int] = 10):
        parts = urlsplit(url)
        qs = parse_qs(parts.query)

        if parameters is not None:
            qs.update(parameters)

        parts._replace(query=urlencode(qs, doseq=True))
        self._url = urlunsplit(parts)
        self._method = method
        self._headers = headers
        self._parameters = parameters
        self._body = body
        self._tls = tls
        self._follow_redirects = follow_redirects
        self._max_redirects = max_redirects

    def get_url(self) -> str:
        return self._url

    def get_method(self) -> Optional[str]:
        return self._method

    def get_headers(self) -> Optional[Dict[str, str]]:
        return self._headers

    def get_parameters(self) -> Optional[Dict[str, List[str]]]:
        return self._parameters

    def get_body(self) -> Optional[bytes]:
        return self._body

    def use_tls(self) -> Optional[bool]:
        return self._tls

    def should_follow_redirects(self) -> bool:
        return self._follow_redirects

    def get_max_redirects(self) -> Optional[int]:
        return self._max_redirects


class HttpResponse:
    def __init__(self,
                 status: int,
                 version: int,
                 headers: Header,
                 body: Body):
        self._status = status
        self._version = version
        self._headers = headers
        self._body = body

    def get_status(self) -> int:
        return self._status

    def get_version(self) -> int:
        return self._version

    def get_headers(self) -> Header:
        return self._headers

    def get_body(self) -> Body:
        return self._body


class HttpClient:
    def __init__(self):
        self.connections = {}

    def do(self, request: HttpRequest) -> HttpResponse:
        return self._do(request, 1)

    def _do(self, request: HttpRequest, redirect_count: int) -> HttpResponse:
        max_redirects = request.get_max_redirects()

        if max_redirects is not None and redirect_count > max_redirects:
            raise ValueError('exceeded maximum redirections')

        url_parts = urlsplit(request.get_url())
        port = url_parts.port

        if port is None:
            port = _SCHEME_PORT.get(url_parts.scheme)

        host = url_parts.hostname
        connection = self.connections.get((host, port))

        use_tls = port == 443

        if request.use_tls() is not None:
            use_tls = request.use_tls()

        if connection is None:
            if use_tls:
                connection = HTTPSConnection(host, port)
            else:
                connection = HTTPConnection(host, port)
            self.connections[(host, port)] = connection

        headers = request.get_headers()

        if headers is None:
            headers = {}

        method = request.get_method()

        if method is None:
            method = METHOD_GET

        connection.request(method,
                           request.get_url(),
                           body=request.get_body(),
                           headers=headers)

        response = connection.getresponse()

        response = HttpResponse(response.status,
                                response.version,
                                Header(response.headers),
                                Body(response))

        status = response.get_status()

        if status not in _REDIRECT_STATUS or not request.should_follow_redirects():
            return response

        location = response.get_headers().get('location')

        if location is None:
            raise ValueError('redirect specified but no location provided')

        new_url_parts = urlsplit(location)

        if new_url_parts.netloc != '':
            new_url_parts._replace(scheme=url_parts.scheme,
                                   netloc=url_parts.netloc)

        method = request.get_method()

        if status == 303:
            method = METHOD_GET

        redirect_request = HttpRequest(urlunsplit(new_url_parts),
                                       method=method,
                                       headers=request.get_headers(),
                                       body=request.get_body())

        return self._do(redirect_request, ++redirect_count)
