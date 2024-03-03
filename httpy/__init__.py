import io
import socket
from typing import List, Tuple
from urllib.parse import urlsplit, urlunsplit

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
STATUS_OK = (200, 'OK')
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


_MAX_READ_SZ = 1024
_MAX_HEADER_FIELD_CNT = 100


class BodyReader:
    def read_into(self, buffer: bytearray) -> int:
        return 0

    def read(self, size: int = -1) -> bytes:
        return b''

    def __len__(self):
        return 0

    def read_all(self) -> bytes:
        result = bytearray()
        buffer = bytearray(_MAX_READ_SZ)
        b_read = self.read_into(buffer)
        while b_read > 0:
            result.extend(buffer[0:b_read])
            b_read = self.read_into(buffer)
        return result

    def close(self):
        buffer = bytearray(_MAX_READ_SZ)
        b_read = self.read_into(buffer)
        while b_read > 0:
            b_read = self.read_into(buffer)


class NoBodyReader(BodyReader):
    pass


class SizedBodyReader(BodyReader):
    def __init__(self, r: io.BufferedReader, size: int):
        self._reader = r
        self._pos = 0
        self._size = size

    def __len__(self):
        return self._size

    def read_into(self, buffer: bytearray) -> int:
        amt = min(len(buffer), self._size - self._pos)
        if amt == 0:
            return 0
        b = self._reader.read(amt)
        b_read = len(b)
        self._pos += b_read
        buffer[0:b_read] = b
        return b_read

    def read(self, size: int = -1) -> bytes:
        return self._reader.read(size)


class StreamBodyReader(BodyReader):
    def __init__(self, r: io.BufferedReader, trailers: List[Tuple[str, str]]):
        self._reader = r
        self._trailers = trailers
        self._buffer = bytearray()
        self._chunk = NoBodyReader()

    def _next_chunk(self):
        line = _read_line_from(self._reader, _MAX_READ_SZ)
        while len(line) == 0:
            line = _read_line_from(self._reader, _MAX_READ_SZ)
        value = line.decode()
        if not value.isnumeric():
            raise BlockingIOError(f"Invalid size: {line}")
        amt = int(value)
        if amt == 0:
            self._chunk = None
        else:
            self._chunk = SizedBodyReader(self._reader, amt)

    def read_into(self, buffer: bytearray) -> int:
        if self._chunk is None:
            return 0
        b_read = self._chunk.read_into(buffer)
        if b_read > 0:
            return b_read
        self._next_chunk()
        return self.read_into(buffer)

    def read(self, size: int = -1) -> bytes:
        return self._reader.read(size)

    def close(self):
        line = _read_line_from(self._reader, _MAX_READ_SZ).decode()
        count = 0
        while line != '' and count < _MAX_READ_SZ:
            field_parts = line.split(':', 1)
            name = parse_header_field_name(str.rstrip(field_parts[0])).decode()
            value = parse_header_field_value(str.lstrip(field_parts[1])).decode()
            self._trailers.append((name, value))
            count += 1
            line = _read_line_from(self._reader, _MAX_READ_SZ).decode()


class BodyWriter:
    def write(self, data: bytes) -> int:
        return 0

    def __len__(self):
        return 0

    def close(self):
        pass


class NoBodyWriter(BodyWriter):
    pass


class SizedBodyWriter(BodyWriter):
    def __init__(self, w: io.BufferedWriter, size: int):
        self._writer = w
        self._size = size
        self._pos = 0

    def __len__(self):
        return self._pos

    def write(self, data: bytes) -> int:
        if self._pos == self._size:
            return 0
        amt = min(len(data), self._size - self._pos)
        b_written = self._writer.write(data[0:amt])
        self._pos += b_written
        return b_written

    def close(self):
        self._writer.flush()


class StreamBodyWriter(BodyWriter):
    def __init__(self, w: io.BufferedWriter, chunk_size: int, trailers: List[Tuple[str, str]]):
        self._writer = w
        self._buffer = bytearray()
        self._chunk_size = chunk_size
        self._trailers = trailers
        self._pos = 0

    def __len__(self):
        return self._pos

    def write(self, data: bytes) -> int:
        length = len(data)
        self._buffer[self._pos:length] = data[0:]
        self._pos += length
        while self._pos >= self._chunk_size:
            remainder = self._pos - self._chunk_size
            chunk = self._buffer[0:self._chunk_size]
            self._writer.write(f'{len(chunk)}\r\n'.encode())
            self._writer.write(chunk)
            self._writer.write(b'\r\n')
            self._buffer[0:remainder] = self._buffer[self._chunk_size:]
            self._pos = remainder
        return length

    def close(self):
        chunk = self._buffer[0:self._pos]
        size = len(chunk)
        self._writer.write(f'{size}\r\n'.encode())
        self._writer.write(chunk)
        self._writer.write(b'\r\n0\r\n')
        buffer = bytearray()
        _write_fields(buffer, self._trailers)
        self._writer.write(buffer)
        self._writer.write(b'\r\n')
        self._writer.flush()


class HttpRequest:
    def __init__(self,
                 method: str,
                 path: str,
                 headers: List[Tuple[str, str]],
                 body: BodyReader,
                 trailers: List[Tuple[str, str]],
                 version: str):
        self.method = method
        self.path = path
        self.headers = headers
        self.body = body
        self.trailers = trailers
        self.version = version


class HttpResponse:
    def __init__(self,
                 version: str,
                 status: Tuple[int, str],
                 headers: List[Tuple[str, str]],
                 body: BodyReader,
                 trailers: List[Tuple[str, str]]):
        self.version = version
        self.status = status
        self.headers = headers
        self.body = body
        self.trailers = trailers


def _write_fields(buffer: bytearray, fields: List[Tuple[str, str]]):
    for k, v in fields:
        name = parse_header_field_name(k)
        buffer.extend(name)
        buffer.extend(b': ')
        value = parse_header_field_value(v)
        buffer.extend(value)
        buffer.extend(b'\r\n')


class RequestWriter:
    def __init__(self, w: io.BufferedWriter):
        self._chunked = False
        self._content_length = 0
        self._header_written = False
        self._writer = w
        self._header = []
        self._body_writer = NoBodyWriter()

    def sized(self, value: int):
        self._content_length = value

    def chunked(self, value: bool = True):
        self._chunked = value

    def add_header(self, key: str, value: str):
        self._header.append((key, value))

    def set_header(self, key: str, value: str):
        self.unset_header(key)
        self.add_header(key, value)

    def unset_header(self, key: str):
        self._header = [(k, v) for k, v in self._header if k.lower() != key.lower()]

    def write_header(self, path: str, method: str = METHOD_GET, version: str = VERSION_HTTP_1_1):
        request_line = str.encode(f'{method} {path} {version}\r\n')
        if self._content_length > 0:
            self.set_header("Content-Length", str(self._content_length))
        if self._chunked:
            self.set_header("Transfer-Encoding", "chunked")
            self.unset_header("Content-Length")
        header = bytearray(request_line)
        _write_fields(header, self._header)
        self._header = []
        header.extend(b'\r\n')
        b_written = self._writer.write(header)
        self._header_written = True
        if b_written < len(header):
            raise BlockingIOError()
        if not self._chunked:
            self._body_writer = SizedBodyWriter(self._writer, self._content_length)
        else:
            self._body_writer = StreamBodyWriter(self._writer, 64, self._header)

    def write(self, data: bytes) -> int:
        if not self._header_written:
            self.write_header('/')
        b_written = self._body_writer.write(data)
        return b_written

    def close(self):
        if not self._header_written:
            return
        self._body_writer.close()


class ResponseWriter:
    def __init__(self, w: io.BufferedWriter):
        self._chunked = False
        self._content_length = 0
        self._header_written = False
        self._writer = w
        self._header = []
        self._body_writer = NoBodyWriter()

    def sized(self, value: int):
        self._content_length = value

    def chunked(self, value: bool = True):
        self._chunked = value

    def add_header(self, key: str, value: str):
        self._header.append((key, value))

    def set_header(self, key: str, value: str):
        self.unset_header(key)
        self.add_header(key, value)

    def unset_header(self, key: str):
        self._header = [(k, v) for k, v in self._header if k.lower() != key.lower()]

    def write_header(self, status: Tuple[int, str], version: str = VERSION_HTTP_1_1):
        status_line = str.encode(f'{version} {status[0]} {status[1]}\r\n')
        if self._content_length > 0:
            self.set_header("Content-Length", str(self._content_length))
        if self._chunked:
            self.set_header("Transfer-Encoding", "chunked")
            self.unset_header("Content-Length")
        header = bytearray(status_line)
        _write_fields(header, self._header)
        self._header = []
        header.extend(b'\r\n')
        b_written = self._writer.write(header)
        self._header_written = True
        if b_written < len(header):
            raise BlockingIOError()
        if not self._chunked:
            self._body_writer = SizedBodyWriter(self._writer, self._content_length)
        else:
            self._body_writer = StreamBodyWriter(self._writer, 64, self._header)

    def write(self, data: bytes) -> int:
        if not self._header_written:
            self.write_header(STATUS_OK)
        b_written = self._body_writer.write(data)
        return b_written

    def close(self):
        if not self._header_written:
            return
        self._body_writer.close()


def _read_line_from(b: io.BufferedReader, max_line_sz: int = 1024) -> bytes:
    buf = b.readline(max_line_sz)
    if buf[-2:] != b'\r\n':
        raise BlockingIOError(f"Unexpected end: {buf[-2:]}")
    return buf[:-2]


def _parse_field(line: str) -> Tuple[str, str]:
    field_parts = line.split(':', 1)
    if len(field_parts) != 2:
        raise BlockingIOError(f"illegal header field")
    name = parse_header_field_name(str.rstrip(field_parts[0])).decode()
    value = parse_header_field_value(str.lstrip(field_parts[1])).decode()
    return name, value


def read_request_from(b: io.BufferedReader, max_line_sz: int = 1024, max_field_cnt: int = 100) -> HttpRequest:
    request_line = _read_line_from(b, max_line_sz)
    request_line_parts = request_line.decode().split(' ', 2)
    method = request_line_parts[0]
    path = request_line_parts[1]
    version = request_line_parts[2]
    field_cnt = 0
    fields = []
    content_length = 0
    chunked = False
    line = _read_line_from(b, max_line_sz).decode()
    while line != '':
        if field_cnt > max_field_cnt:
            raise BlockingIOError()
        name, value = _parse_field(line)
        match name.lower():
            case 'content-length':
                if not value.isnumeric():
                    raise BlockingIOError("Invalid content length value")
                content_length = int(value)
            case 'transfer-encoding':
                chunked = value.lower() == 'chunked'
        fields.append((name, value))
        line = _read_line_from(b, max_line_sz).decode()
        field_cnt += 1
    req = HttpRequest(method, path, fields, NoBodyReader(), [], version)
    if not chunked:
        body = SizedBodyReader(b, content_length)
    else:
        body = StreamBodyReader(b, req.trailers)
    req.body = body
    return req


def read_response_from(b: io.BufferedReader, max_line_sz: int = 1024, max_field_cnt: int = 100) -> HttpResponse:
    status_line = _read_line_from(b, max_line_sz)
    status_line_parts = status_line.decode().split(' ', 2)
    version = status_line_parts[0]
    status_code = status_line_parts[1]
    if not status_code.isnumeric():
        raise BlockingIOError("Invalid")
    status_text = status_line_parts[2]
    status = (int(status_code), status_text)
    field_cnt = 0
    fields = []
    content_length = 0
    chunked = False
    line = _read_line_from(b, max_line_sz).decode()
    while line != '':
        if field_cnt > max_field_cnt:
            raise BlockingIOError()
        name, value = _parse_field(line)
        match name.lower():
            case 'content-length':
                if not value.isnumeric():
                    raise BlockingIOError("Invalid content length value")
                content_length = int(value)
            case 'transfer-encoding':
                chunked = value.lower() == 'chunked'
        fields.append((name, value))
        line = _read_line_from(b, max_line_sz).decode()
        field_cnt += 1
    res = HttpResponse(version, status, fields, NoBodyReader(), [])
    if not chunked:
        body = SizedBodyReader(b, content_length)
    else:
        body = StreamBodyReader(b, res.trailers)
    res.body = body
    return res


_CS_AWAIT_REQUEST = 1


class HttpConnection:
    def __init__(self, reader: io.BufferedReader, writer: io.BufferedWriter):
        self._writer = writer
        self._reader = reader

    def send_request(self) -> RequestWriter:
        return RequestWriter(self._writer)

    def receive_request(self) -> HttpRequest:
        return read_request_from(self._reader)

    def send_response(self) -> ResponseWriter:
        return ResponseWriter(self._writer)

    def receive_response(self) -> HttpResponse:
        return read_response_from(self._reader)

    def close(self):
        self._writer.close()
        self._reader.close()


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
