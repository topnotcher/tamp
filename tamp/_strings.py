from ._arrays import _ArrayType
from ._base import DataType


__all__ = ['Byte', 'String']


class String(_ArrayType):
    def __init__(self, string_type, *args, **kwargs):
        self.string_type = string_type
        super(String, self).__init__(*args, **kwargs)

    def init(self, length, value):
        if value is not None:
            if not isinstance(value, self.string_type):
                raise TypeError('value %d must be instance of %s, not %s: %r' %
                                (id(self), self.string_type.__name__, type(value).__name__, value))
            else:
                self._value = value

        elif length is not None:
            # TODO: this is kind of fucked up, eh?
            self._value = self.string_type(self.elem_type().value) * length

        else:
            self._value = self.string_type()

    def unpack(self, buf):
        elem = self.elem_type()
        consumed = elem.unpack(buf)
        self._value += elem.value

        return consumed

    def unpack_stream(self, stream):
        elem = stream.pop_state(self) or self.elem_type()

        result = elem.unpack_stream(stream)
        if result:
            self._value += elem.value
        else:
            stream.push_state(self, elem)

        return result

    def __bytes__(self):
        return self._string_type().join(bytes(self.elem_type(value=value)) for value in self._value)

    def size(self):
        return len(bytes(self))


class Byte(DataType):
    _array_type_ = lambda *args, **kwargs: String(bytes, *args, **kwargs)

    def _unpack(self, buf):
        self._value = buf[0:1]
        return 1

    @DataType.value.setter
    def value(self, value):
        if value is None:
            self._value = b'\x00'

        elif isinstance(value, int):
            self._value = bytes([value])

        elif len(value) == 1:
            self._value = value

        else:
            raise TypeError('Value must be a 1-char byte string.')

    def unpack_stream(self, stream):
        if len(stream) < self.size():
            return False

        else:
            self._unpack(stream.read(self.size()))
            return True

    def size(self):
        return 1

    def pack(self):
        return self._value
