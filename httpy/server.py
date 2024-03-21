import httpy
import io


class HttpConnection:
    def __init__(self, receiver: io.IOBase, sender: io.IOBase):
        self._receiver = receiver
        self._sender = sender
        self._closed = False

    def receive_request(self) -> httpy.HttpRequest:
        if self._closed:
            raise ConnectionError("Connection is closed")
        return httpy.read_request_from(self._receiver)

    def send_response(self) -> httpy.ResponseWriter:
        if self._closed:
            raise ConnectionError("Connection is closed")
        return httpy.ResponseWriter(self._sender)

    def close(self):
        if not self._closed:
            self._sender.close()
            self._receiver.close()
