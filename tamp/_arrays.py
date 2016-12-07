import functools

from ._base import DataType, array_type, _Array, LengthFixed
from ._struct import wrap_type


__all__ = ['LengthField', 'LengthFixed', 'PackedLength']


class _LengthFieldWrapper(DataType):
    def __init__(self, field):
        self.field = field

    @DataType.value.getter
    def value(self):
        return self.field.value

    @value.setter
    def value(self, _):
        raise TypeError('Cannot manually set length on legnth field.')

    def unpack(self, buf, offset=0):
        return self.field.unpack(buf, offset=offset)

    def pack(self):
        return self.field.pack()

    def size(self):
        return self.field.size()


@array_type
class LengthField(_Array):
    # TODO: validate that length field is defined before array field.

    def __init__(self, field, *args, **kwargs):
        self.field = kwargs.get('parent').wrap_field(field, _LengthFieldWrapper)
        _Array.__init__(self, *args, **kwargs)  # TODO
        # TODO: validate the length field, hijack the field and make it read only

    def unpack_more(self, values, consumed, buf, offset):
        return len(values) < self.field.value

    @DataType.value.setter
    def value(self, new_value):
        if new_value is None:
            new_value = []

        self._value = new_value
        self.field.value = len(self._value)

    def size(self):
        return 0  # always like a variable length member.

    def _check_length(self, value):
        if len(value) != self.field.value:
            raise ValueError('Expected %d elements, but got %d.' % (self.field.value, len(value)))


class _PackedLengthFieldWrapper(DataType):
    def __init__(self, wrapped_field, length_field):
        self.wrapped_field = wrapped_field
        self.length_field = length_field

    def _update_length(self):
        # This is definitely ghetto. It's mainly here because in the case the
        # field whose length is represented by the length field is a struct,
        # the parent struct doesn't know that the field changes.
        self.length_field.value = len(bytes(self.wrapped_field))

    @DataType.value.getter
    def value(self):
        self._update_length()

        return self.length_field.value

    @value.setter
    def value(self, _):
        raise TypeError('Cannot manually set length on legnth field.')

    def unpack(self, buf, offset=0):
        return self.length_field.unpack(buf, offset=offset)

    def pack(self):
        self._update_length()
        return self.length_field.pack()

    def size(self):
        return self.length_field.size()


@wrap_type
class PackedLength(DataType):
    """
    Allow storing the number of bytes one field should unpack in another field::

        class Foo(Structure):
            _fields_ = [
                # Indicates how many bytes to unpack in the data field
                ('dsize', uint8_t),

                # Variable length array will normally consume all the bytes
                # PackedLength will ensure it consumes exactly as many as
                # indicated by dsize.
                ('data', PackedLength(uint32_t[0], 'dsize')),
                ('end', Const(uint8_t, 0xFF)),
            ]
    """
    def __init__(self, wrapped_field_type, size_field_name, **kwargs):
        self.wrapped_field = wrapped_field_type(**kwargs)

        wrapper = functools.partial(_PackedLengthFieldWrapper, self.wrapped_field)
        self.length_field = kwargs['parent'].wrap_field(size_field_name, wrapper)

        DataType.__init__(self, **kwargs)

    def unpack(self, buf, offset=0):
        unpack_size = self.length_field.value
        consumed = self.wrapped_field.unpack(buf[offset : offset + unpack_size])

        if consumed != unpack_size:
            raise ValueError('Expected to unpack %d bytes; unpacked %d.' % (unpack_size, consumed))

        return unpack_size

    def pack(self):
        return self.wrapped_field.pack()

    @DataType.value.getter
    def value(self):
        return self.wrapped_field.value

    @value.setter
    def value(self, new_value):
        self.wrapped_field.value = new_value
