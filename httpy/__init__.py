from collections import deque
from socket import socket, AF_INET, SOCK_STREAM

from httpy import header

VERSION_HTTP_1_0 = "HTTP/1.0"
VERSION_HTTP_1_1 = "HTTP/1.1"

METHOD_GET = 'GET'
METHOD_POST = 'POST'
METHOD_PUT = 'PUT'
METHOD_PATCH = 'PATCH'
METHOD_HEAD = 'HEAD'
METHOD_OPTION = 'OPTION'

STATUS_CONTINUE = ("100", 'Continue')
STATUS_SWITCHING_PROTOCOLS = ("101", 'Switching Protocols')
STATUS_OK = ("200", 'OK')
STATUS_CREATED = ("201", 'Created')
STATUS_ACCEPTED = ("202", 'Accepted')
STATUS_NON_AUTHORITATIVE_INFORMATION = ("203", 'Non-Authoritative Information')
STATUS_NO_CONTENT = ("204", 'No Content')
STATUS_RESET_CONTENT = ("205", 'Reset Content')
STATUS_PARTIAL_CONTENT = ("206", 'Partial content')
STATUS_MULTIPLE_CHOICES = ("300", 'Multiple Choices')
STATUS_MOVED_PERMANENTLY = ("301", 'Moved Permanently')
STATUS_FOUND = ("302", 'Found')
STATUS_SEE_OTHER = ("303", 'See Other')
STATUS_NOT_MODIFIED = ("304", 'Not Modified')
STATUS_TEMPORARY_REDIRECT = ("307", 'Temporary Redirect')
STATUS_PERMANENT_REDIRECT = ("308", 'Permanent Redirect')
STATUS_BAD_REQUEST = ("400", 'Bad Request')
STATUS_UNAUTHORIZED = ("401", 'Unauthorized')
STATUS_PAYMENT_REQUIRED = ("402", 'Payment Required')
STATUS_FORBIDDEN = ("403", 'Forbidden')
STATUS_NOT_FOUND = ("404", 'Not Found')
STATUS_METHOD_NOT_ALLOWED = ("405", 'Method Not Allowed')
STATUS_NOT_ACCEPTABLE = ("406", 'Not Acceptable')
STATUS_PROXY_AUTHENTICATION_REQUIRED = ("407", 'Proxy Authentication Required')
STATUS_REQUEST_TIMEOUT = ("408", 'Request Timeout')
STATUS_CONFLICT = ("409", 'Conflict')
STATUS_GONE = ("410", 'Gone')
STATUS_LENGTH_REQUIRED = ("411", 'Length Required')
STATUS_PRECONDITION_FAILED = ("412", 'Precondition Failed')
STATUS_CONTENT_TOO_LARGE = ("413", 'Content Too Large')
STATUS_URI_TOO_LONG = ("414", 'URI Too Long')
STATUS_UNSUPPORTED_MEDIA_TYPE = ("415", 'Unsupported Media Type')
STATUS_RANGE_NOT_SATISFIABLE = ("416", 'Range not Satisfiable')
STATUS_EXPECTATION_FAILED = ("417", 'Expectation Failed')
STATUS_MISDIRECTED_REQUEST = ("421", 'Misdirected Request')
STATUS_UNPROCESSABLE_CONTENT = ("422", 'Unprocessable Content')
STATUS_UPGRADE_REQUIRED = ("426", 'Upgrade Required')
STATUS_INTERNAL_SERVER_ERROR = ("500", 'Internal Server Error')
STATUS_NOT_IMPLEMENTED = ("501", 'Not Implemented')
STATUS_BAD_GATEWAY = ("502", 'Bad Gateway')
STATUS_SERVICE_UNAVAILABLE = ("503", 'Service Unavailable')
STATUS_GATEWAY_TIMEOUT = ("504", 'Gateway Timeout')
STATUS_HTTP_VERSION_NOT_SUPPORTED = ("505", 'HTTP Version Not Supported')

SCHEME_HTTP = 'http'
SCHEME_HTTPS = 'https'
_DEFAULT_SCHEME = SCHEME_HTTP

_DEFAULT_METHOD = 'GET'

_MAX_HEADER_FIELD_CNT = 100

OPT_METHOD = 1
OPT_URL = 2

__HND_POOL = []
__FREE_HND = deque()
__SOCK_POOL: dict[str, deque[socket]] = {}


def cleanup():
    __HND_POOL.clear()
    __FREE_HND.clear()


def init() -> int:
    opts = {}
    try:
        hnd = __FREE_HND.popleft()
        __HND_POOL[hnd - 1] = opts
    except IndexError:
        __HND_POOL.append(opts)
        hnd = len(__HND_POOL)
    return hnd


def free(hnd: int):
    try:
        opts = __HND_POOL[hnd - 1]
        opts.clear()
        __HND_POOL.insert(hnd - 1, 0x00)
        __FREE_HND.append(hnd)
    except IndexError:
        raise ValueError("invalid handle")


def __get(hnd: int) -> dict[str, any] | None:
    try:
        opts = __HND_POOL[hnd - 1]
        if opts == 0x00:
            raise IndexError
    except IndexError:
        opts = None
    return opts


def set_opt(hnd: int, opt: int, value: any):
    opts = __get(hnd)

    if opts is None:
        raise ValueError("invalid handle")

    match opt:
        case 1:
            opts["method"] = str(value)
        case 2:
            opts["url"] = str(value)
        case _:
            raise ValueError("invalid option")


def perform(hnd: int):
    opts = __get(hnd)
    if opts is None:
        raise ValueError("invalid handle")

    url = opts.get("url")
    if url is None:
        raise ValueError("OPT_URL is a required option")

    method = opts.get("method") or _DEFAULT_METHOD
    url = opts.get("url") or "/"
    print(method + " " + url)
