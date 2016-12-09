import enum
import inspect

from ._base import _Type, DataType

__all__ = ['Enum', 'EnumWrap']


class _EnumFactory(dict):
    def __missing__(self, key):
        enum_type, pack_type = key

        name = '_enum_' + '_' + enum_type.__name__ + '_' + pack_type.__name__
        value = _Type.__new__(_EnumMeta, name, (Enum,), {'_enum_': enum_type, '_type_': pack_type})

        self[key] = value

        return value


class _EnumMeta(_Type):
    _enum_pack_types = _EnumFactory()

    def __new__(mcs, name, bases, attrs):
        if '_type_' not in attrs or '_enum_' not in attrs:
            raise ValueError('Enum subclasses must define _type_ and _enum_.')

        if DataType in bases:
            base_type = super(_EnumMeta, mcs).__new__(mcs, name, bases, attrs)
            mcs._enum_pack_types[(None, None)] = base_type

            return base_type

        else:
            return mcs.enum_type(attrs['_enum_'], attrs['_type_'])

    @classmethod
    def enum_type(mcs, enum_type, pack_type):
        if not inspect.isclass(enum_type) or not issubclass(enum_type, enum.Enum):
            raise ValueError('enum_type must be subclass of enum.Enum.')

        return mcs._enum_pack_types[(enum_type, pack_type)]


class Enum(DataType, metaclass=_EnumMeta):
    """
    Create an enumerated type based on an Python ``enum.IntEnum`` and some
    other type (e.g.  ``uint8_t``)::

        class PizzaToppings(enum.IntEnum):
            Pepperoni = 1
            Olives = 2
            Sausage = 3

        class PizzaToppingField(Enum):
            _type_ = uint8_t
            _enum_ = PizzaToppings

        ``PizzaToppingsField().value`` is always an instance of
        ``PizzaToppings``. Unpacking or assigning an invalid value raises a
        ``TypeError``.
    """
    _type_ = None
    _enum_ = None

    @DataType.value.setter
    def value(self, new_value):
        try:
            if new_value is None:
                new_value = list(self._enum_).pop(0)
            else:
                new_value = self._enum_(new_value)

        # TODO: some hella inconsistent exception types: ``unpack`` always
        # raises ValueError \o/.
        except ValueError as err:
            raise TypeError(err) from None

        self._value = new_value

    def _unpack(self, buf):
        unpack_type = self._type_()
        consumed = unpack_type.unpack(buf)
        self._value = self._enum_(unpack_type.value)

        return consumed

    def pack(self):
        return bytes(self._type_(self._value))

    def size(self):
        return self._type_().size()


def EnumWrap(enum_type, pack_type):
    return _EnumMeta.enum_type(enum_type, pack_type)
