class _Type(type): # yo dawg, I heard you like types.types

    def __getitem__(cls, key):
        """
        Allow defining array types: ``uint32_t[5]`` creates a new type.
        """
        # TODO
        if isinstance(key, int):
            size = LengthFixed(key)

        elif not isinstance(key, _ArrayLengthWrapper):  # TODO
            raise ValueError('Invalid length: %r.' % key)

        else:
            size = key

        def __init__(self, *args, **kwargs):
            new_args = list(size.args)
            new_args.extend(args)
            new_args.append(cls)
            kwargs.update(size.kwargs)
            size.cls.__init__(self, *new_args, **kwargs)

        new_name = cls.__name__ + '_array_' + str(size.cls)
        new_type = type(size.cls)(new_name, (size.cls,), {'__init__': __init__})

        return new_type


class DataType(metaclass=_Type):
    def __init__(self, value=None, parent=None):
        super(DataType, self).__init__()
        self._parent = parent
        self.value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = new_value  # TODO: this allows defaults.

    def unpack(self, buf, offset=0):
        """
        unpack bytes from the given ``buf`` starting at ``offset`` into
        ``self.value``. ``ValueError`` should be raised if too few bytes are
        given.
        """
        raise NotImplementedError

    def pack(self):
        """
        :param value: value to pack
        :return: bytes
        """
        raise NotImplementedError

    def from_bytes(self, buf, offset=0):
        """
        Like unpack, but raises ``ValueError`` if fewer than ``len(buf)`` bytes are consumed.
        """
        consumed_bytes = self.unpack(buf, offset)
        rest_length = len(buf) - offset

        if consumed_bytes != rest_length:
            raise ValueError('Must consume exactly %d bytes; consumed %d.' % (rest_length, consumed_bytes))

    def __bytes__(self):
        return self.pack()

    def size(self):
        """
        The size of the type. This should behave like ``sizeof()`` and may be 0
        (e.g. for  variable length arrays).
        """
        raise NotImplementedError


def array_type(cls):
    def _wrapper(*args, **kwargs):
        return _ArrayLengthWrapper(cls, *args, **kwargs)

    return _wrapper


class _ArrayLengthWrapper:
    def __init__(self, cls, *args, **kwargs):
        self.cls = cls
        self.args = args
        self.kwargs = kwargs

    def __call__(self, parent, elem_type):
        args = [parent, elem_type]
        args.extend(self.args)

        return self.cls(*args, **self.kwargs)


class _Array(DataType):
    def __init__(self, elem_type, *args, **kwargs):
        self.elem_type = elem_type
        super(_Array, self).__init__(*args, **kwargs)

    def unpack_more(self, values, consumed, buf, offset):
        raise NotImplementedError

    def _unpack(self, buf, offset=0):
        elem = self.elem_type()

        unpack_more = (len(buf) - offset) > 0
        total_consumed_bytes = 0
        values = []

        while self.unpack_more(values, total_consumed_bytes, buf, offset) and offset < len(buf):
            consumed_bytes = elem.unpack(buf, offset)
            offset += consumed_bytes
            total_consumed_bytes += consumed_bytes

            values.append(elem.value)

        return total_consumed_bytes, values

    def unpack(self, buf, offset=0):
        total_consumed_bytes, values = self._unpack(buf, offset=offset)
        self._check_length(values)

        self._value = values

        return total_consumed_bytes

    def _check_length(self, value):
        raise NotImplementedError

    def pack(self):
        return b''.join(bytes(self.elem_type(value=value)) for value in self._value)

    def size(self):
        raise NotImplementedError


@array_type
class LengthFixed(_Array):
    def __init__(self, length, *args, **kwargs):
        self._length = length
        _Array.__init__(self, *args, **kwargs)  # TODO

    def unpack_more(self, values, consumed, buf, offset):
        # 0 => variable length member: consume all the bytes.
        return (len(values) < self._length) or (self._length == 0)

    def size(self):
        return self._length * self.elem_type().size()

    def _check_length(self, value, exc=ValueError):
        if self._length not in (0, len(value)):
            raise exc('Expected %d elements, but got %d.' % (self._length, len(value)))

    @DataType.value.setter
    def value(self, new_value):
        if new_value is None:
            self._value = [self.elem_type().value] * self._length
        else:
            self._check_length(new_value, exc=TypeError)

            # This will raise a TypeError if any of the elements is invalid
            self._value = [self.elem_type(value=elem).value for elem in new_value]
