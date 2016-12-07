import inspect
import functools
from collections import OrderedDict

from ._base import _Type, DataType

__all__ = ['Structure', 'Const']

class _StructType(_Type):
    def __new__(mcs, name, bases, attrs):
        fields = []
        attrs['_struct_type_fields_'] = []

        for base in bases:
            if isinstance(base, _StructType) and hasattr(base, '_struct_type_fields_'):
                fields.extend(getattr(base, '_struct_type_fields_'))

        if '_fields_' in attrs:
            fields.extend(attrs['_fields_'])
            del attrs['_fields_']

        for field_name, field_type in fields:
            # if inspect.isclass(field_type) and issubclass(field_type, DataType):
            attrs['_struct_type_fields_'].append((field_name, field_type))
            # else:
            #     raise ValueError('Invalid type %r for field %s.' % (field_type, field_name))

        return _Type.__new__(mcs, name, bases, attrs)


class Structure(DataType, metaclass=_StructType):
    """
    A structure. Each element of ``_fields_`` should be a tuple containing the
    name of the field and a type that inherits from :class:`DataType`.
    Example::

        class Test:
            _fields_ = [('foo', int8_t)]

        t = Test()
        t.foo = 99
        print(t.foo)  # 99

        t.foo = 129  # TypeError: can't fit in ``int8_t``

        t.unpack(b'\x0F')

        t.foo == 15  # True
    """
    _fields_ = []

    def __init__(self, *args, **kwargs):

        self.__dict__['_struct_fields'] = OrderedDict()

        for field, field_type in self._cls_iter_fields():
            self.__dict__['_struct_fields'][field] = field_type(parent=self)

        super(Structure, self).__init__(*args, **kwargs)

    def wrap_field(self, field, wrapper):
        try:
            real_field = self._struct_fields[field]
        except KeyError:
            raise AttributeError('%s is not a valid field for %s.' % (field, type(self).__name__)) from None

        else:
            self._struct_fields[field] = wrapper(real_field)

        return real_field

    @classmethod
    def _cls_iter_fields(cls):
        for field, field_type in cls._struct_type_fields_:
            yield field, field_type

    def _iter_fields(self):
        for field_name, field in self.__dict__['_struct_fields'].items():
            yield field_name, field

    def unpack(self, buf, offset=0):
        total_consumed_bytes = 0

        for _, field in self._iter_fields():
            consumed_bytes = field.unpack(buf, offset)
            offset += consumed_bytes
            total_consumed_bytes += consumed_bytes

        return total_consumed_bytes

    def pack(self):
        return bytes(self)

    def __bytes__(self):
        return b''.join(bytes(field) for _, field in self._iter_fields())

    def size(self):
        return sum(field.size() for _, field in self._iter_fields())

    @DataType.value.setter
    def value(self, new_value):
        """
        This will be called by other structures when this structure is assigned
        to a field of that structure.
        """
        if new_value is None:
            self._value = self

        elif not isinstance(new_value, self.__class__):
            raise TypeError('value must be an instance of %s.' % (self.__class__.__name__))

        # When we assign a struct to a struct member, copy the fields. This
        # gives the illusion of the two structs being the same object, as all
        # members shared between them will have the same value. (but if the
        # assigned value is a subclass, the members not defined in this class
        # will not be touched)
        else:
            for field_name, _ in self._iter_fields():
                self._struct_fields[field_name] = new_value._struct_fields[field_name]

    @value.getter
    def value(self):
        return self

    def __setattr__(self, field, value):
        if field in self.__dict__['_struct_fields']:
            try:
                self._struct_fields[field].value = value
            except TypeError as err:
                raise TypeError('%r cannot be assigned to %s.%s: %s' %
                                (value, type(self).__name__, field, err.args[0])) from None
        else:
            return super(Structure, self).__setattr__(field, value)

    def __getattr__(self, attr):
        """
        Get a field. Yeah, for real.
        """
        if attr in self._struct_fields:
            return self._struct_fields[attr].value
        else:
            raise AttributeError('%s is not a valid field for %s.' % (attr, type(self).__name__))

    def __eq__(self, value):
        """
        Test if two structs are equal. Two structs are equal if and only if:
            - Both are instances of Structure.
            - Both have the same number of fields.
            - The structs contain equal values in the same order. (The names and types may differ)
        """
        # NOTE: only checking isinstance(..., Structure) - not requiring it
        # to be the same type - just that fields have the same values.
        if not isinstance(value, Structure):
            return False

        elif len(self.__dict__['_struct_fields']) != len(value.__dict__['_struct_fields']):
            return False

        else:

            for ((field_name, _), (other_field_name, __)) in zip(self._iter_fields(), value._iter_fields()):
                # fields may not have the same name/type, but must have the same value
                if getattr(self, field_name) != getattr(value, other_field_name):
                    return False

            return True


def wrap_type(cls):
    def _wrapper(*wrap_args, **wrap_kwargs):
        # The downside of this is the result is not subscriptable. But why
        # would you need an array of consts? (rather than a Const array)?
        return functools.partial(cls, *wrap_args, **wrap_kwargs)

    return _wrapper


@wrap_type
class Const(DataType):
    def __init__(self, *args, **kwargs):
        """
        Const(type, value) | Const(value)
        """
        if isinstance(args[0], bytes):
            bytes_value = args[0]
            real_value = args[0]

        elif inspect.isclass(args[0]) and issubclass(args[0], DataType):
            type_value = args[0](value=args[1])

            bytes_value = bytes(type_value)
            real_value = type_value.value

        else:
            raise ValueError

        self._value = real_value
        self._bytes_value = bytes_value
        DataType.__init__(self, value=real_value, **kwargs)

    @DataType.value.setter
    def value(self, new_value):
        # TODO: this is horrible.
        if new_value != self._value:
            raise TypeError('Constant')

    def unpack(self, buf, offset=0):
        value = buf[offset:offset + len(self._bytes_value)]

        if value != self._bytes_value:
            raise ValueError('Value does not match expected constant.')

        return len(self._bytes_value)

    def pack(self):
        return self._bytes_value
