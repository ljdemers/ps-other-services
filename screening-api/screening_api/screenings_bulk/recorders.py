"""Screening API screenings bulk recorders module"""
from io import BytesIO


class RecorderError(Exception):
    pass


class BaseRecorder:
    """
    Base recorder. Iterator that reads an encoded data
    and decodes the input to specified encoding.
    """

    def __init__(self, encoding: str = 'utf-8'):
        self.encoding = encoding

    def __iter__(self):
        return self

    def __next__(self) -> str:
        line = self.get_line()

        if not line:
            raise StopIteration

        return self.decode(line)

    def get_line(self) -> bytes:
        raise NotADirectoryError

    def decode(self, line):
        try:
            return line.decode(self.encoding)
        except UnicodeDecodeError:
            raise RecorderError("Decoding error")


class ListRecorder(BaseRecorder):
    """
    List recorder.
    """
    def __init__(self, data: list, encoding: str = 'utf-8'):
        super(ListRecorder, self).__init__(encoding)
        self.data = iter(data)

    def get_line(self) -> bytes:
        line = next(self.data)
        return bytes(str(line), self.encoding)

    @classmethod
    def from_request(cls, request):
        data = request.openapi.body['imo_ids']
        return cls(data)


class BytesRecoder(BaseRecorder):
    """
    Bytes recorder.
    """
    def __init__(self, data: bytes, encoding: str = 'utf-8'):
        super(BytesRecoder, self).__init__(encoding)
        self.lines = iter(data.split(b'\n'))

    def get_line(self) -> bytes:
        return next(self.lines)

    @classmethod
    def from_request(cls, request):
        data = request.get_data()
        return cls(data)


class StreamRecoder(BaseRecorder):
    """
    Stream recorder.
    """
    def __init__(self, stream: BytesIO, encoding: str = 'utf-8'):
        super(StreamRecoder, self).__init__(encoding)
        self.stream = stream

    def get_line(self) -> bytes:
        return self.stream.readline()

    @classmethod
    def from_request(cls, request):
        request_file = request.files['file']
        return cls(request_file.stream)
