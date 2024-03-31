import io
from httpy import method
from httpy import version
from httpy import status
from httpy import header
from typing import List, Tuple, Optional

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


class Header:
    def __init__(self):
        self._fields = []

    def get_first(self, key: str) -> Optional[str]:
        for k, v in self._fields:
            if k.lower() == key.lower():
                return v
        return None

    def add_field(self, key: str, value: str):
        self._fields.append((key, value))

    def set_field(self, key: str, value: Optional[str]):
        self._fields = [(k, v) for k, v in self._fields if k.lower() != key.lower()]
        if value is not None:
            self.add_field(key, value)

    def as_list(self) -> List[Tuple[str, str]]:
        return self._fields


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
    def __init__(self, w: io.IOBase, chunk_size: int, trailers: Header):
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
        self._header = Header()
        self._body_writer = NoBodyWriter()

    def sized(self, value: int):
        self._header.set_field('Content-Length', str(value))
        self._header.set_field('Transfer-Encoding', None)

    def chunked(self, value: bool = True):
        if value:
            self._header.set_field('Transfer-Encoding', 'chunked')
            self._header.set_field('Content-Length', None)
        else:
            self._header.set_field('Transfer-Encoding', None)

    def header(self) -> Header:
        return self._header

    def _initial_data(self) -> bytes:
        pass

    def write_header(self):
        if self._header_written:
            return
        h = bytearray(self._initial_data())
        transfer_encoding = self._header.get_first('Transfer-Encoding')
        content_length = self._header.get_first('Content-Length') or '0'
        _write_fields(h, self._header.as_list())
        # clear the header fields to make room for trailer fields.
        self._header = Header()
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
        self.method = method.GET
        self.path = '/'
        self.version = version.HTTP_1_1
        super().__init__(w)

    def _initial_data(self) -> bytes:
        return str.encode(f'{self.method} {self.path} {self.version}\r\n')


class ResponseWriter(MessageWriter):
    def __init__(self, w: io.IOBase):
        self._status = status.OK
        self._version = version.HTTP_1_1
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
    req = HttpRequest(method, path, fields, NoBodyReader(), [], version)
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
