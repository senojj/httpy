import httpy
import io


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


'''
class HttpClient:
    def __init__(self,
                 context: Optional[ssl.SSLContext] = None):
        self._connections = {}
        self._context = context

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

        target_url = url.transform_reference(str(urlunsplit(url_parts)), location)

        method = request.get_method()

        if status == 303:
            method = method.GET

        redirect_request = HttpRequest(target_url,
                                       method=method,
                                       headers=request.get_headers(),
                                       body=request.get_body())

        return self._do(redirect_request, redirect_count + 1)
'''
