import ssl
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

STATUS_CONTINUE = 100
STATUS_SWITCHING_PROTOCOLS = 101
STATUS_OK = 200
STATUS_CREATED = 201
STATUS_ACCEPTED = 202
STATUS_NON_AUTHORITATIVE_INFORMATION = 203
STATUS_NO_CONTENT = 204
STATUS_RESET_CONTENT = 205
STATUS_PARTIAL_CONTENT = 206
STATUS_MULTIPLE_CHOICES = 300
STATUS_MOVED_PERMANENTLY = 301
STATUS_FOUND = 302
STATUS_SEE_OTHER = 303
STATUS_NOT_MODIFIED = 304
STATUS_USE_PROXY = 305
STATUS_TEMPORARY_REDIRECT = 307
STATUS_PERMANENT_REDIRECT = 308
STATUS_BAD_REQUEST = 400
STATUS_UNAUTHORIZED = 401
STATUS_PAYMENT_REQUIRED = 402
STATUS_FORBIDDEN = 403
STATUS_NOT_FOUND = 404
STATUS_METHOD_NOT_ALLOWED = 405
STATUS_NOT_ACCEPTABLE = 406
STATUS_PROXY_AUTHENTICATION_REQUIRED = 407
STATUS_REQUEST_TIMEOUT = 408
STATUS_CONFLICT = 409
STATUS_GONE = 410
STATUS_LENGTH_REQUIRED = 411
STATUS_PRECONDITION_FAILED = 412
STATUS_CONTENT_TOO_LARGE = 413
STATUS_URI_TOO_LONG = 414
STATUS_UNSUPPORTED_MEDIA_TYPE = 415
STATUS_RANGE_NOT_SATISFIABLE = 416
STATUS_EXPECTATION_FAILED = 417
STATUS_MISDIRECTED_REQUEST = 421
STATUS_UNPROCESSABLE_CONTENT = 422
STATUS_UPGRADE_REQUIRED = 426
STATUS_INTERNAL_SERVER_ERROR = 500
STATUS_NOT_IMPLEMENTED = 501
STATUS_BAD_GATEWAY = 502
STATUS_SERVICE_UNAVAILABLE = 503
STATUS_GATEWAY_TIMEOUT = 504
STATUS_HTTP_VERSION_NOT_SUPPORTED = 505

SCHEME_HTTP = 'http'
SCHEME_HTTPS = 'https'
DEFAULT_SCHEME = SCHEME_HTTP


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


class HttpRequest:
    def __init__(self,
                 url: str,
                 method: Optional[str] = None,
                 headers: Optional[Dict[str, str]] = None,
                 parameters: Optional[Dict[str, List[str]]] = None,
                 body: Optional[bytes] = None,
                 follow_redirects: bool = True,
                 max_redirects: Optional[int] = 10,
                 context: Optional[ssl.SSLContext] = None):
        parts = urlsplit(url)
        qs = parse_qs(parts.query)

        if parameters is not None:
            qs.update(parameters)

        parts = parts._replace(query=urlencode(qs, doseq=True))
        self._url = urlunsplit(parts)
        self._method = method
        self._headers = headers
        self._parameters = parameters
        self._body = body
        self._follow_redirects = follow_redirects
        self._max_redirects = max_redirects
        self._context = context

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

    def should_follow_redirects(self) -> bool:
        return self._follow_redirects

    def get_max_redirects(self) -> Optional[int]:
        return self._max_redirects

    def get_context(self) -> Optional[ssl.SSLContext]:
        return self._context


class HttpResponse:
    def __init__(self,
                 url: str,
                 status: int,
                 version: int,
                 headers: Header,
                 body: Body):
        self._url = url
        self._status = status
        self._version = version
        self._headers = headers
        self._body = body

    def get_url(self) -> str:
        return self._url

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

    def close(self):
        for _, connection in self.connections.items():
            connection.close()

    def do(self, request: HttpRequest) -> HttpResponse:
        return self._do(request, 1)

    def _do(self, request: HttpRequest, redirect_count: int) -> HttpResponse:
        print(request.get_url())
        max_redirects = request.get_max_redirects()

        if max_redirects is not None and redirect_count > max_redirects:
            raise ValueError('exceeded maximum redirections')

        url_parts = urlsplit(request.get_url())

        if url_parts.scheme.strip() == '':
            url_parts = url_parts._replace(scheme=DEFAULT_SCHEME)

        port = url_parts.port

        if port is None:
            port = _SCHEME_PORT.get(url_parts.scheme)

        scheme = url_parts.scheme
        host = url_parts.hostname
        connection = self.connections.get((scheme, host, port))

        use_tls = url_parts.scheme == SCHEME_HTTPS

        if connection is None:
            if use_tls:
                connection = HTTPSConnection(host, port, context=request.get_context())
            else:
                connection = HTTPConnection(host, port)
            self.connections[(scheme, host, port)] = connection

        headers = request.get_headers()

        if headers is None:
            headers = {}

        method = request.get_method()

        if method is None:
            method = METHOD_GET

        request_url = urlunsplit(url_parts)

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

        new_url_parts = urlsplit(location)

        host = new_url_parts.hostname

        if host is None:
            host = url_parts.hostname

        port = new_url_parts.port

        if port is None:
            port = url_parts.port

        if port is None:
            netloc = host
        else:
            netloc = '%s:%d' % (host, port)

        new_url_parts = new_url_parts._replace(netloc=netloc)

        if new_url_parts.scheme.strip() == '':
            new_url_parts = new_url_parts._replace(scheme=url_parts.scheme)

        method = request.get_method()

        if status == 303:
            method = METHOD_GET

        redirect_request = HttpRequest(urlunsplit(new_url_parts),
                                       method=method,
                                       headers=request.get_headers(),
                                       body=request.get_body(),
                                       context=request.get_context())

        return self._do(redirect_request, redirect_count + 1)
