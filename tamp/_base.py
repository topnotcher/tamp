import inspect


class _Type(type): # yo dawg, I heard you like types.types

    def __iter__(cls):
        yield NotImplemented

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

        # TODO This is a tad janky and probably overcomplicated now.
        def __init__(self, *args, **kwargs):
            new_args = list(size.args)
            new_args.extend(args)
            new_args.append(lambda value=None, length=None: cls._array_type_(cls, value=value, length=length))
            kwargs.update(size.kwargs)
            size.cls.__init__(self, *new_args, **kwargs)

        new_name = cls.__name__ + '_array_' + str(size.cls)
        new_type = type(size.cls)(new_name, (size.cls,), {'__init__': __init__})

        return new_type


class _ArrayType(object):
    def __init__(self, elem_type, value=None, length=None):
        self.elem_type = elem_type
        self._value = None
        self.init(length, value)

    def init(self, length, value):
        raise NotImplementedError

    def unpack(self, value):
        raise NotImplementedError

    def unpack_stream(self, stream):
        raise NotImplementedError

    def __bytes__(self):
        raise NotImplementedError

    @property
    def value(self):
        return self._value

    def __len__(self):
        return len(self._value)

    def __eq__(self, other):
        if isinstance(other, _ArrayType):
            return self._value == other._value

        elif isinstance(other, type(self._value)):
            return self._value == other

        else:
            return False

    def size(self):
        return NotImplementedError


class ListArray(_ArrayType):
    def init(self, length, value):
        if isinstance(value, _ArrayType):
            raise Exception

        if value is not None:
            # This will raise a TypeError if any of the elements is invalid
            self._value = [self.elem_type(value=elem).value for elem in value]

        elif length is not None:
            self._value = [self.elem_type().value] * length

        else:
            self._value = []

    def unpack(self, buf):
        elem = self.elem_type()
        consuemd = elem.unpack(buf)
        self._value.append(elem.value)

        return consuemd

    def unpack_stream(self, stream):
        elem = stream.pop_state(self) or self.elem_type()

        result = elem.unpack_stream(stream)
        if result:
            self._value.append(elem.value)
        else:
            stream.push_state(self, elem)

        return result

    def __bytes__(self):
        return b''.join(bytes(self.elem_type(value=value)) for value in self._value)

    def size(self):
        return len(self) * self.elem_type().size()


class DataType(metaclass=_Type):
    _array_type_ = ListArray

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

    def unpack(self, buf):
        """
        unpack bytes from the given ``buf`` into ``self.value``. ``ValueError``
        should be raised if too few bytes are given.
        """
        return self._unpack(buf)

    def _unpack(self, buf):
        raise NotImplementedError

    def unpack_stream(self, stream):
        raise NotImplementedError

    def pack(self):
        """
        :param value: value to pack
        :return: bytes
        """
        raise NotImplementedError

    def from_bytes(self, buf):
        """
        Like unpack, but raises ``ValueError`` if fewer than ``len(buf)`` bytes are consumed.
        """
        consumed_bytes = self.unpack(buf)

        if consumed_bytes != len(buf):
            raise ValueError('Must consume exactly %d bytes; consumed %d.' % (len(buf), consumed_bytes))

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


class _Array(DataType):
    def __init__(self, array_type, *args, **kwargs):
        self.array_type = array_type
        super(_Array, self).__init__(*args, **kwargs)

    @DataType.value.getter
    def value(self):
        return self._value.value

    def unpack_more(self, values):
        raise NotImplementedError

    def _unpack(self, buf):
        array = self.array_type()

        offset = 0
        total_consumed_bytes = 0
        while self.unpack_more(array) and offset < len(buf):
            consumed_bytes = array.unpack(buf[offset:])
            offset += consumed_bytes
            total_consumed_bytes += consumed_bytes

        self._check_length(array)
        self._value = array

        return total_consumed_bytes

    def unpack_stream(self, stream):
        array = stream.pop_state(self) or self.array_type()

        unpack_more = True
        result = True
        while unpack_more and result:
            result = array.unpack_stream(stream)

            if result:
                unpack_more = self.unpack_more(array)
            else:
                unpack_more = True

        if unpack_more:
            stream.push_state(self, array)
            return False
        else:
            self._check_length(array)
            self._value = array

            return True

    def _check_length(self, value):
        raise NotImplementedError

    def pack(self):
        return bytes(self._value)

    def size(self):
        raise NotImplementedError


@array_type
class LengthFixed(_Array):
    def __init__(self, length, *args, **kwargs):
        self._length = length
        _Array.__init__(self, *args, **kwargs)  # TODO

    def unpack_more(self, values):
        # 0 => variable length member: consume all the bytes.
        return (len(values) < self._length) or (self._length == 0)

    def size(self):
        return 0 if self._length == 0 else self._value.size()

    def _check_length(self, value, exc=ValueError):
        if self._length not in (0, len(value)):
            raise exc('Expected %d elements, but got %d.' % (self._length, len(value)))

    @_Array.value.setter
    def value(self, new_value):
        value = self.array_type(value=new_value, length=self._length)
        self._check_length(value, exc=TypeError)

        self._value = value
