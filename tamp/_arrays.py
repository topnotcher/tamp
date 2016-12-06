from ._base import DataType, array_type, _Array, LengthFixed


__all__ = ['LengthField', 'LengthFixed']


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
