import inspect
import functools
from collections import OrderedDict

try:
    import enum
except ImportError:
    import enum34 as enum


from ._base import _Type, DataType

__all__ = ['Structure', 'Const', 'Computed']


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

        t.unpack(b'\\x0F')

        t.foo == 15  # True
    """
    _fields_ = []

    def __init__(self, *args, **kwargs):
        self.__dict__['_struct_fields'] = OrderedDict()
        self._unpacked_callbacks = []

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

    def _unpack(self, buf):
        offset = 0
        total_consumed_bytes = 0

        for _, field in self._iter_fields():
            consumed_bytes = field.unpack(buf[offset:])
            offset += consumed_bytes
            total_consumed_bytes += consumed_bytes

        self._unpacked()

        return total_consumed_bytes

    def unpack_stream(self, stream):
        first_field = stream.pop_state(self)
        if first_field is None:
            skip = False
        else:
            skip = True

        for field_name, field in self._iter_fields():
            if skip and field is first_field:
                skip = False

            if not skip:
                result = field.unpack_stream(stream)

                if not result:
                    stream.push_state(self, field)
                    return False

        self._unpacked()
        return True

    def pack(self):
        return bytes(self)

    def _unpacked(self):
        for cb in self._unpacked_callbacks:
            cb(self)

    def add_unpacked_callback(self, cb):
        self._unpacked_callbacks.append(cb)

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
    def __init__(self, *args, mismatch_exc=ValueError, **kwargs):
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
        self.mismatch_exc = mismatch_exc
        DataType.__init__(self, value=real_value, **kwargs)

    @DataType.value.setter
    def value(self, new_value):
        # TODO: this is horrible.
        if new_value != self._value:
            raise TypeError('Constant')

    def _unpack(self, buf):
        value = buf[:len(self._bytes_value)]

        if value != self._bytes_value:
            raise self.mismatch_exc('Value does not match expected constant.')

        return len(self._bytes_value)

    def unpack_stream(self, stream):
        if len(stream) < len(self._bytes_value):
            return False
        else:
            self._unpack(stream.read(len(self._bytes_value)))
            return True

    def pack(self):
        return self._bytes_value

    def size(self):
        return len(self._bytes_value)


@wrap_type
class Computed(DataType):
    """
    Compute the value of a field based on the value of other fields::

        class Foo(Structure):
            _fields_ = [
                ('foo', uint8_t),
                ('bar', uint8_t),
                ('baz', Computed(uint8_t, 'calc_baz')),
            ]

            def calc_baz(self):
                return self.foo + self.bar
    """
    def __init__(self, pack_type, callback, mismatch_exc=ValueError, **kwargs):
        self.pack_field = pack_type(**kwargs)
        DataType.__init__(self, **kwargs)

        self.callback = getattr(self._parent, callback)
        self.mismatch_exc_type = mismatch_exc
        kwargs.get('parent').add_unpacked_callback(self._parent_unpacked)

    def _parent_unpacked(self, _):
        value = self.callback()

        if value != self.pack_field.value:
            raise self.mismatch_exc_type('Unpacked Value %r does not match computed value %r.' %
                                         (self.pack_field.value, value))

    @DataType.value.setter
    def value(self, new_value):
        # TODO: this is horrible.
        if new_value is not None:
            raise TypeError('Computed fields cannot be set.')

    @value.getter
    def value(self):
        self.pack_field.value = self.callback()
        return self.pack_field.value

    def _unpack(self, buf):
        return self.pack_field.unpack(buf)

    def unpack_stream(self, stream):
        return self.pack_field.unpack_stream(stream)

    def pack(self):
        self.pack_field.value = self.callback()
        return self.pack_field.pack()

    def size(self):
        return self.pack_field.size()
