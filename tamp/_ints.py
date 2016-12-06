import struct
import sys

from ._base import _Type, DataType

class _IntType(_Type):
    def __new__(mcs, name, bases, attrs):

        if '_fmt_' in attrs and attrs['_fmt_'] is not None:
            be_attrs = attrs.copy()
            be_attrs['_endian_'] = '>'
            attrs['be'] = super(_IntType, mcs).__new__(mcs, name + '.be', bases, be_attrs)
            attrs['network'] = attrs['be']
            attrs['le'] = None

            new_type = super(_IntType, mcs).__new__(mcs, name + '.le', bases, attrs)
            new_type.le = new_type

            return new_type

        else:
            return super(_IntType, mcs).__new__(mcs, name, bases, attrs)


class _Int(DataType, metaclass=_IntType):
    _fmt_ = None

    # Default little endian
    _endian_ = '<'
    _bounds_ = (0, -1)

    @DataType.value.setter
    def value(self, new_value):
        if new_value is None:
            new_value = 0

        min_val, max_val = self._bounds_
        if not min_val <= new_value <= max_val:
            raise TypeError('%s must be %d <= x <= %d.' % (self.__class__.__name__, min_val, max_val))
        else:
            self._value = new_value

    @classmethod
    def _fmt(cls):
        return cls._endian_ + cls._fmt_

    def unpack(self, buf, offset=0):
        if len(buf) - offset < self.size():
            raise ValueError('Not enough bytes to unpack.')

        self._value = struct.unpack_from(self._fmt(), buf, offset)[0]

        return self.size()

    def pack(self):
        return struct.pack(self._fmt(), self._value)

    def size(self):
        return struct.calcsize(self._fmt())


_int_types = [
    ('uint8_t', 'B', (0, 255)),
    ('int8_t', 'b', (-128, 127)),
    ('uint16_t', 'H', (0, 65535)),
    ('int16_t', 'h', (-32768, 32767)),
    ('uint32_t', 'I', (0, 4294967295)),
    ('int32_t', 'i', (-2147483648, 2147483647)),
    ('uint64_t', 'Q', (0, 18446744073709551615)),
    ('int64_t', 'q', (-9223372036854775808, 9223372036854775807)),
]

__all__ = []

for _name, _fmt, _bounds in _int_types:
    _new_type = _IntType(_name, (_Int,), {'_bounds_': _bounds, '_fmt_': _fmt})
    sys.modules[__name__].__dict__[_name] = _new_type
    __all__.append(_name)
