import io
import socket
from typing import Optional, List, Tuple, Union
from urllib.parse import urlsplit, urlunsplit
from email.message import Message

VERSION_HTTP_1_0 = "HTTP/1.0"
VERSION_HTTP_1_1 = "HTTP/1.1"

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
_DEFAULT_SCHEME = SCHEME_HTTP

_HEADER_FIELD_NAME_CHARACTER_MAP = [
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, b'-', 0, 0, b'0', b'1', b'2', b'3', b'4', b'5', b'6',
    b'7', b'8', b'9', 0, 0, 0, 0, 0, 0, 0, b'A', b'B', b'C', b'D', b'E', b'F', b'G', b'H', b'I',
    b'J', b'K', b'L', b'M', b'N', b'O', b'P', b'Q', b'R', b'S', b'T', b'U', b'V', b'W', b'X', b'Y',
    b'Z', 0, 0, 0, 0, b'_', 0, b'a', b'b', b'c', b'd', b'e', b'f', b'g', b'h', b'i', b'j', b'k',
    b'l', b'm', b'n', b'o', b'p', b'q', b'r', b's', b't', b'u', b'v', b'w', b'x', b'y', b'z', 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0,
]


def parse_header_field_name(name: str) -> bytes:
    ba = str.encode(name)
    for b in ba:
        if _HEADER_FIELD_NAME_CHARACTER_MAP[b] == 0:
            raise ValueError(f'Invalid header field name: {name}')
    return ba


_HEADER_FIELD_VALUE_CHARACTER_MAP = [
    0, 0, 0, 0, 0, 0, 0, 0, 0, b'\t', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, b' ', b'!', b'"', b'#', b'$', b'%', b'&', b'\'', b'(', b')', b'*', b'+', b',', b'-',
    b'.', b'/', b'0', b'1', b'2', b'3', b'4', b'5', b'6', b'7', b'8', b'9', b':', b';', b'<', b'=',
    b'>', b'?', b'@', b'A', b'B', b'C', b'D', b'E', b'F', b'G', b'H', b'I', b'J', b'K', b'L', b'M',
    b'N', b'O', b'P', b'Q', b'R', b'S', b'T', b'U', b'V', b'W', b'X', b'Y', b'Z', b'[', b'\\',
    b']', b'^', b'_', b'`', b'a', b'b', b'c', b'd', b'e', b'f', b'g', b'h', b'i', b'j', b'k', b'l',
    b'm', b'n', b'o', b'p', b'q', b'r', b's', b't', b'u', b'v', b'w', b'x', b'y', b'z', b'{', b'|',
    b'}', b'~', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0,
]


def parse_header_field_value(value: str) -> bytes:
    ba = str.encode(value)
    for b in ba:
        if _HEADER_FIELD_VALUE_CHARACTER_MAP[b] == 0:
            raise ValueError(f'Invalid header field value: {value}')
    return ba


def url_remove_dot_segments(path: str) -> str:
    tokens, output, buf, pos = list(path), [], [], len(path) - 1
    tokens.reverse()

    while pos >= 0:
        ctr = 0
        buf.clear()
        while pos >= 0:
            buf.append(tokens[pos])
            if tokens[pos] == '/' and ctr > 0:
                break
            pos = pos - 1
            ctr = ctr + 1
        segment = ''.join(buf)
        if segment == '../' or segment == './':
            pass
        elif segment == '/./' or segment == '/.':
            pos = max(pos, 0)
            tokens[pos] = '/'
        elif segment == '/../' or segment == '/..':
            pos = max(pos, 0)
            tokens[pos] = '/'
            output = output[0:-1]
        elif segment == '..' or segment == '.':
            pass
        else:
            output.append(''.join(buf[:ctr]))

    return ''.join(output)


def url_transform_reference(base: str, reference: str) -> str:
    b_scheme, b_netloc, b_path, b_query, b_fragment = urlsplit(base)
    scheme, netloc, path, query, fragment = urlsplit(reference)

    if scheme != '':
        path = url_remove_dot_segments(path)
    else:
        if netloc != '':
            path = url_remove_dot_segments(path)
        else:
            if path == '':
                path = b_path
                if query == '':
                    query = b_query
            else:
                if path[0] == '/':
                    path = url_remove_dot_segments(path)
                else:
                    if b_netloc != '' and b_path == '':
                        path = '/' + path
                    else:
                        path = b_path[:b_path.rfind('/') + 1] + path
                    path = url_remove_dot_segments(path)
            netloc = b_netloc
        scheme = b_scheme

    return str(urlunsplit((scheme, netloc, path, query, fragment)))


class Header:
    def __init__(self, message: Message):
        self._message = message

    def get(self, name: str) -> Optional[str]:
        return self._message.get(name)


_MAX_READ_SZ = 1024


class Body:
    def __init__(self, r: io.BufferedReader = io.BufferedReader(io.BytesIO()), size: int = 0):
        self._reader = r
        self._pos = 0
        self._size = size

    def __len__(self):
        return self._size

    def read(self, buffer: bytearray) -> int:
        amt = min(len(buffer), self._size - self._pos)
        if amt == 0:
            return 0
        b = self._reader.read(amt)
        b_read = len(b)
        self._pos += b_read
        buffer[0:b_read] = b
        return b_read

    def read_all(self) -> bytes:
        result = bytearray(self._size)
        buffer = bytearray(_MAX_READ_SZ)
        b_read = self.read(buffer)
        while b_read > 0:
            result.extend(buffer[0:b_read])
        return result


class HttpRequest:
    def __init__(self,
                 method: str,
                 path: str,
                 header: List[Tuple[str, str]],
                 body: Body,
                 trailer: List[Tuple[str, str]],
                 version: str = VERSION_HTTP_1_1):
        self.method = method
        self.path = path
        self.header = header
        self.body = body
        self.trailer = trailer
        self.version = version

    def write_to(self, b: io.BufferedWriter, read_sz: int = _MAX_READ_SZ):
        chunked = False
        content_length = 0
        request_line = str.encode(f'{self.method} {self.path} HTTP/1.1\r\n')
        header = bytearray(request_line)
        header.extend(f'Content-Length: {len(self.body)}\r\n'.encode())
        for k, v in self.header:
            match k.lower():
                case 'transfer-encoding':
                    if v.lower() == 'chunked':
                        chunked = True
            name = parse_header_field_name(k)
            header.extend(name)
            header.extend(b': ')
            value = parse_header_field_value(v)
            header.extend(value)
            header.extend(b'\r\n')
        for k, v in self.trailer:
            header.extend(b'Trailer: ')
            header.extend(parse_header_field_name(k))
            header.extend(b'\r\n')
        header.extend(b'\r\n')
        b_written = b.write(header)
        if b_written < len(header):
            raise BlockingIOError()

        buffer = bytearray(read_sz)
        b_read = self.body.read(buffer)
        if not chunked:
            while b_read > 0:
                b_written = b.write(buffer[0:b_read])
                if b_written < b_read:
                    raise BlockingIOError()
                b_read = self.body.read(buffer)
        else:
            while b_read > 0:
                ba = bytearray(str(b_read).encode())
                ba.extend(b'\r\n')
                b_written = b.write(ba)
                if b_written < len(ba):
                    raise BlockingIOError()
                ba = bytearray(buffer[0:b_read])
                ba.extend(b'\r\n')
                b_written = b.write(ba)
                if b_written < len(ba):
                    raise BlockingIOError()
                b_read = self.body.read(buffer)
            ba = bytearray(b'0\r\n')
            for k, v in self.trailer:
                ba.extend(parse_header_field_name(k))
                ba.extend(b': ')
                ba.extend(parse_header_field_value(v))
                ba.extend(b'\r\n')
            ba.extend(b'\r\n')
            b_written = b.write(ba)
            if b_written < len(ba):
                raise BlockingIOError()


def _read_line_from(b: io.BufferedReader, max_line_sz: int = 1024) -> bytes:
    buf = b.readline(max_line_sz)
    if buf[-2:] != b'\r\n':
        raise BlockingIOError()
    return buf[:-2]


def read_request_from(b: io.BufferedReader, max_line_sz: int = 1024, max_field_cnt: int = 100) -> HttpRequest:
    request_line = _read_line_from(b, max_line_sz)
    request_line_parts = request_line.decode().split(' ', 2)
    method = request_line_parts[0]
    path = request_line_parts[1]
    version = request_line_parts[2]
    field_cnt = 0
    line = _read_line_from(b, max_line_sz).decode()
    while line != '/r/n':
        if field_cnt > max_field_cnt:
            raise BlockingIOError()
        line = _read_line_from(b, max_line_sz).decode()
        field_cnt += 1
    return HttpRequest(method, path, [], Body(b, 0), [], version)


_CS_AWAIT_REQUEST = 1


class HttpConnection:
    def __init__(self, sock: socket.socket):
        self._socket = sock

    def send_request(self, request: HttpRequest):
        return


'''
class HttpClient:
    def __init__(self,
                 context: Optional[ssl.SSLContext] = None,
                 default_tls: bool = False,
                 pool: Optional[Pool] = None):
        if pool is None:
            self._connections = Pool()
        else:
            self._connections = pool
        self._context = context
        self._default_scheme = _DEFAULT_SCHEME
        if default_tls:
            self._default_scheme = SCHEME_HTTPS

    def close(self):
        self._connections.clear()

    def do(self, request: HttpRequest) -> HttpResponse:
        return self._do(request, 0)

    def _do(self, request: HttpRequest, redirect_count: int) -> HttpResponse:
        max_redirects = request.get_max_redirects()

        if max_redirects is not None and redirect_count > max_redirects:
            raise ValueError('exceeded maximum redirections')

        url_parts = urlsplit(request.get_url())

        if url_parts.scheme.strip() == '':
            url_parts = url_parts._replace(scheme=self._default_scheme)

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
            method = METHOD_GET

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

        target_url = url_transform_reference(str(urlunsplit(url_parts)), location)

        method = request.get_method()

        if status == 303:
            method = METHOD_GET

        redirect_request = HttpRequest(target_url,
                                       method=method,
                                       headers=request.get_headers(),
                                       body=request.get_body())

        return self._do(redirect_request, redirect_count + 1)
'''
