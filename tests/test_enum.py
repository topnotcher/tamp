import unittest
import enum

from tamp import *


class TestEnumWrap(unittest.TestCase):
    class _TestEnum(enum.IntEnum):
        foo = 1
        bar = 2

    def _test_struct(self, pack_type=uint32_t.le):
        return _test_field_struct(EnumWrap(self._TestEnum, pack_type))

    def test_enum_unpack(self):
        """
        A wrapped enum field unpacks to the wrapped enum value.
        """
        s = self._test_struct()()

        s.from_bytes(b'\x01\x00\x00\x00')
        unpacked = s.test

        self.assertEqual(self._TestEnum.foo, unpacked)
        self.assertIsInstance(unpacked, self._TestEnum)

    def test_enum_unpack_invalid(self):
        """
        A wrapped enum field cannot be unpacked from an invalid value.
        """
        s = self._test_struct()

        with self.assertRaises(ValueError):
            s.from_bytes(b'\x03\x00\x00\x00')

    def test_assign_valid_enum_value(self):
        """
        A wrapped enum field can be assgigned to an enum instance.
        """
        s = self._test_struct()

        s.test = self._TestEnum.foo

        self.assertEqual(s.test, self._TestEnum.foo)
        self.assertIsInstance(s.test, self._TestEnum)

    def test_assign_valid_value(self):
        """
        A wrapped enum field can be assgigned to a valid enum value that is not
        an enum instance.
        """
        s = self._test_struct()

        s.test = 1

        self.assertEqual(s.test, self._TestEnum.foo)
        self.assertIsInstance(s.test, self._TestEnum)

    def test_assign_invalid(self):
        """
        A wrapped enum field cannot be assigned to an invalid value.
        """
        s = self._test_struct()

        with self.assertRaises(TypeError):
            s.test = 3

    def test_enum_pack(self):
        """
        A wrapped enum packs to the associated pack type.
        """
        l = self._test_struct()
        b = self._test_struct(pack_type=uint32_t.be)

        l.test = self._TestEnum.foo
        b.test = self._TestEnum.foo

        self.assertEqual(bytes(l), bytes(uint32_t.le(self._TestEnum.foo)))
        self.assertEqual(bytes(b), bytes(uint32_t.be(self._TestEnum.foo)))

    def test_enum_wrap(self):
        """
        enum_wrap creates an instance of enum_type.
        """
        class _enum_type(Enum):
            _type_ = uint32_t.le
            _enum_ = self._TestEnum

        e = EnumWrap(self._TestEnum, uint32_t.le)

        # e and _enum_type should be identical types.
        self.assertIs(e, _enum_type)

    def test_enum_unpack(self):
        """
        A wrapped enum field can be an array.
        """
        class _test(Structure):
            _fields_ = [
                ('test', EnumWrap(self._TestEnum, uint32_t)[2]),
            ]

        s = _test()

        s.from_bytes(b'\x01\x00\x00\x00\x02\x00\x00\x00')
        unpacked = s.test

        self.assertEqual([self._TestEnum.foo, self._TestEnum.bar], unpacked)

        for val in unpacked:
            self.assertIsInstance(val, self._TestEnum)

    def test_enum_unpack_stream(self):
        """
        An enum can unpack from a stream.
        """
        packed = b'\x01\x00\x00\x00\x02\x00\x00\x00'
        # stream = StreamUnpacker(self._test_struct(EnumWrap(self._TestEnum, uint32_t)))
        stream = StreamUnpacker(EnumWrap(self._TestEnum, uint32_t))

        values = []
        for byte in (packed[i : i + 1] for i in range(len(packed))):
            values.extend(e.value for e in stream.unpack(byte))

        self.assertEqual(values, [self._TestEnum.foo, self._TestEnum.bar])

    def test_enum_wrap_reverse_args(self):
        """
        One does not simply reverse enum args.
        """
        with self.assertRaises(ValueError):
            EnumWrap(uint8_t, self._TestEnum)()


def _test_field_struct(field_type):
    class _test(Structure):
        _fields_ = [
            ('test', field_type)
        ]

    return _test()


if __name__ == '__main__':
    unittest.main()
