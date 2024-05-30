import io

import httpy
from httpy import header
from typing import List, Tuple, Optional

VERSION_HTTP_1_0 = "HTTP/1.0"
VERSION_HTTP_1_1 = "HTTP/1.1"

METHOD_GET = 'GET'
METHOD_POST = 'POST'
METHOD_PUT = 'PUT'
METHOD_PATCH = 'PATCH'
METHOD_HEAD = 'HEAD'
METHOD_OPTION = 'OPTION'

STATUS_CONTINUE = (100, 'Continue')
STATUS_SWITCHING_PROTOCOLS = (101, 'Switching Protocols')
STATUS_OK = (200, 'OK')
STATUS_CREATED = (201, 'Created')
STATUS_ACCEPTED = (202, 'Accepted')
STATUS_NON_AUTHORITATIVE_INFORMATION = (203, 'Non-Authoritative Information')
STATUS_NO_CONTENT = (204, 'No Content')
STATUS_RESET_CONTENT = (205, 'Reset Content')
STATUS_PARTIAL_CONTENT = (206, 'Partial content')
STATUS_MULTIPLE_CHOICES = (300, 'Multiple Choices')
STATUS_MOVED_PERMANENTLY = (301, 'Moved Permanently')
STATUS_FOUND = (302, 'Found')
STATUS_SEE_OTHER = (303, 'See Other')
STATUS_NOT_MODIFIED = (304, 'Not Modified')
STATUS_TEMPORARY_REDIRECT = (307, 'Temporary Redirect')
STATUS_PERMANENT_REDIRECT = (308, 'Permanent Redirect')
STATUS_BAD_REQUEST = (400, 'Bad Request')
STATUS_UNAUTHORIZED = (401, 'Unauthorized')
STATUS_PAYMENT_REQUIRED = (402, 'Payment Required')
STATUS_FORBIDDEN = (403, 'Forbidden')
STATUS_NOT_FOUND = (404, 'Not Found')
STATUS_METHOD_NOT_ALLOWED = (405, 'Method Not Allowed')
STATUS_NOT_ACCEPTABLE = (406, 'Not Acceptable')
STATUS_PROXY_AUTHENTICATION_REQUIRED = (407, 'Proxy Authentication Required')
STATUS_REQUEST_TIMEOUT = (408, 'Request Timeout')
STATUS_CONFLICT = (409, 'Conflict')
STATUS_GONE = (410, 'Gone')
STATUS_LENGTH_REQUIRED = (411, 'Length Required')
STATUS_PRECONDITION_FAILED = (412, 'Precondition Failed')
STATUS_CONTENT_TOO_LARGE = (413, 'Content Too Large')
STATUS_URI_TOO_LONG = (414, 'URI Too Long')
STATUS_UNSUPPORTED_MEDIA_TYPE = (415, 'Unsupported Media Type')
STATUS_RANGE_NOT_SATISFIABLE = (416, 'Range not Satisfiable')
STATUS_EXPECTATION_FAILED = (417, 'Expectation Failed')
STATUS_MISDIRECTED_REQUEST = (421, 'Misdirected Request')
STATUS_UNPROCESSABLE_CONTENT = (422, 'Unprocessable Content')
STATUS_UPGRADE_REQUIRED = (426, 'Upgrade Required')
STATUS_INTERNAL_SERVER_ERROR = (500, 'Internal Server Error')
STATUS_NOT_IMPLEMENTED = (501, 'Not Implemented')
STATUS_BAD_GATEWAY = (502, 'Bad Gateway')
STATUS_SERVICE_UNAVAILABLE = (503, 'Service Unavailable')
STATUS_GATEWAY_TIMEOUT = (504, 'Gateway Timeout')
STATUS_HTTP_VERSION_NOT_SUPPORTED = (505, 'HTTP Version Not Supported')

SCHEME_HTTP = 'http'
SCHEME_HTTPS = 'https'
_DEFAULT_SCHEME = SCHEME_HTTP

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
    def __init__(self, r: io.IOBase, size: int):
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
    def __init__(self, r: io.IOBase, trailers: List[Tuple[str, str]]):
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
            name = header.parse_field_name(str.rstrip(field_parts[0])).decode()
            value = header.parse_field_value(str.lstrip(field_parts[1])).decode()
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

    def flush(self):
        pass


class NoBodyWriter(BodyWriter):
    pass


class SizedBodyWriter(BodyWriter):
    def __init__(self, w: io.IOBase, size: int):
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

    def flush(self):
        self._writer.flush()


class StreamBodyWriter(BodyWriter):
    def __init__(self, w: io.IOBase, chunk_size: int, trailers: header.FieldList):
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
            self._writer.write(f'{len(chunk)}\r\n'.encode() + chunk + b'\r\n')
            self._buffer[0:] = self._buffer[self._chunk_size:]
            self._pos = remainder
        return length

    def close(self):
        chunk = self._buffer[0:self._pos]
        size = len(chunk)
        self._writer.write(f'{size}\r\n'.encode())
        self._writer.write(chunk)
        self._writer.write(b'\r\n0\r\n')
        buffer = bytearray()
        _write_fields(buffer, self._trailers.as_list())
        self._writer.write(buffer)
        self._writer.write(b'\r\n')
        self._writer.flush()

    def flush(self):
        self._writer.flush()


class HttpRequest:
    def __init__(self,
                 path: str = '/',
                 http_method: str = METHOD_GET,
                 headers: header.FieldList = header.FieldList(),
                 body: BodyReader = NoBodyReader(),
                 trailers: header.FieldList = header.FieldList(),
                 http_version: str = VERSION_HTTP_1_1):
        self.method = http_method
        self.path = path
        self.headers = headers
        self.body = body
        self.trailers = trailers
        self.version = http_version

    def host(self, value: str):
        self.headers.set_field(header.HOST, value)


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
        name = header.parse_field_name(k)
        buffer.extend(name)
        buffer.extend(b': ')
        value = header.parse_field_value(v)
        buffer.extend(value)
        buffer.extend(b'\r\n')


class MessageWriter:
    def __init__(self, w: io.IOBase):
        self._writer = w
        self._header_written = False
        self._header = header.FieldList()
        self._body_writer = NoBodyWriter()

    def sized(self, value: int):
        self._header.set_field('Content-Length', str(value))
        self._header.set_field('Transfer-Encoding', None)

    def chunked(self, value: bool = True):
        if value:
            self._header.set_field(header.TRANSFER_ENCODING, 'chunked')
            self._header.set_field(header.CONTENT_LENGTH, None)
        else:
            self._header.set_field(header.TRANSFER_ENCODING, None)

    def header(self) -> header.FieldList:
        return self._header

    def _initial_data(self) -> bytes:
        pass

    def write_header(self):
        if self._header_written:
            return
        h = bytearray(self._initial_data())
        transfer_encoding = self._header.get_first(header.TRANSFER_ENCODING)
        content_length = self._header.get_first(header.CONTENT_LENGTH) or '0'
        _write_fields(h, self._header.as_list())
        # clear the header fields to make room for trailer fields.
        self._header = header.FieldList()
        h.extend(b'\r\n')
        b_written = self._writer.write(h)
        self._header_written = True
        if b_written < len(h):
            raise BlockingIOError()
        if not transfer_encoding == 'chunked':
            self._body_writer = SizedBodyWriter(self._writer, int(content_length))
        else:
            self._body_writer = StreamBodyWriter(self._writer, 64, self._header)

    def write(self, data: bytes) -> int:
        if not self._header_written:
            self.write_header()
        b_written = self._body_writer.write(data)
        return b_written

    def close(self):
        if not self._header_written:
            return
        self._body_writer.close()


class RequestWriter(MessageWriter):
    def __init__(self, w: io.IOBase):
        self.method = METHOD_GET
        self.path = '/'
        self.version = VERSION_HTTP_1_1
        super().__init__(w)

    def _initial_data(self) -> bytes:
        return str.encode(f'{self.method} {self.path} {self.version}\r\n')


class ResponseWriter(MessageWriter):
    def __init__(self, w: io.IOBase):
        self._status = STATUS_OK
        self._version = VERSION_HTTP_1_1
        super().__init__(w)

    def _initial_data(self) -> bytes:
        return str.encode(f'{self._version} {self._status[0]} {self._status[1]}\r\n')


def _read_line_from(b: io.IOBase, max_line_sz: int = _MAX_READ_SZ) -> bytes:
    buf = b.readline(max_line_sz)
    if buf[-2:] != b'\r\n':
        raise BlockingIOError(f"Unexpected end: {buf[-2:]}")
    return buf[:-2]


def _parse_field(line: str) -> Tuple[str, str]:
    field_parts = line.split(':', 1)
    if len(field_parts) != 2:
        raise BlockingIOError(f"illegal header field")
    name = header.parse_field_name(str.rstrip(field_parts[0])).decode()
    value = header.parse_field_value(str.lstrip(field_parts[1])).decode()
    return name, value


def _read_header_fields(b: io.IOBase,
                        fields: List[Tuple[str, str]],
                        max_line_sz: int = _MAX_READ_SZ,
                        max_field_cnt: int = _MAX_HEADER_FIELD_CNT) -> (int, bool):
    field_cnt = 0
    content_length = 0
    chunked = False
    line = _read_line_from(b, max_line_sz).decode()
    while line != '':
        if field_cnt > max_field_cnt:
            raise BlockingIOError("Invalid header field count")
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
    return content_length, chunked


def _read_request_line(b: io.IOBase, max_line_sz: _MAX_READ_SZ) -> (str, str, str):
    rl = _read_line_from(b, max_line_sz)
    rl_parts = rl.decode('utf-8').split(' ', 2)
    return rl_parts[0], rl_parts[1], rl_parts[2]


def read_request_from(b: io.IOBase,
                      max_line_sz: int = _MAX_READ_SZ,
                      max_field_cnt: int = _MAX_HEADER_FIELD_CNT) -> HttpRequest:
    method, path, version = _read_request_line(b, max_line_sz)
    fields = []
    content_length, chunked = _read_header_fields(b, fields, max_line_sz, max_field_cnt)
    req = HttpRequest(path, method, header.FieldList(fields), NoBodyReader(), header.FieldList(), version)
    if not chunked:
        body = SizedBodyReader(b, content_length)
    else:
        body = StreamBodyReader(b, req.trailers)
    req.body = body
    return req


def _read_status_line(b: io.IOBase, max_line_sz: int = _MAX_READ_SZ) -> (str, str, str):
    sl = _read_line_from(b, max_line_sz)
    sl_parts = sl.decode('utf-8').split(' ', 2)
    return sl_parts[0], sl_parts[1], sl_parts[2]


def read_response_from(b: io.IOBase,
                       max_line_sz: int = _MAX_READ_SZ,
                       max_field_cnt: int = _MAX_HEADER_FIELD_CNT) -> HttpResponse:
    version, status_code, status_text = _read_status_line(b, max_line_sz)
    status = (int(status_code), status_text)
    fields = []
    content_length, chunked = _read_header_fields(b, fields, max_line_sz, max_field_cnt)
    res = HttpResponse(version, status, fields, NoBodyReader(), [])
    if not chunked:
        body = SizedBodyReader(b, content_length)
    else:
        body = StreamBodyReader(b, res.trailers)
    res.body = body
    return res


class HeaderMap:
    pass