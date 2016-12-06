import unittest
import struct

from tamp import *


class TestIntTypes(unittest.TestCase):

    def _test_int_type(self, field_type, bits, signed):
        """
        Apparently the units being tested are now classes.
        """
        bits_to_char = {
            8: 'b',
            16: 'h',
            32: 'i',
            64: 'q',
        }

        fmt_char = bits_to_char[bits]
        if not signed:
            fmt_char = fmt_char.upper()

        for endian, test_type in (('<', field_type), ('>', getattr(field_type, 'be'))):
            fmt = endian + fmt_char

            self._test_int_bounds(test_type, bits, signed)
            self._test_int_pack_unpack(test_type, bits, fmt)
            self._test_int_size(test_type, bits)
            self._test_int_offset(test_type, bits, fmt)

        self.assertEqual(getattr(field_type, 'le'), field_type)

    def test_uint8_t(self):
        """
        Verify functionality of ``uint8_t`` type.
        """
        self._test_int_type(uint8_t, 8, False)

    def test_int8_t(self):
        """
        Verify functionality of ``int8_t`` type.
        """
        self._test_int_type(int8_t, 8, True)

    def test_uint16_t(self):
        """
        Verify functionality of ``uint16_t`` type.
        """
        self._test_int_type(uint16_t, 16, False)

    def test_int16_t(self):
        """
        Verify functionality of ``int16_t`` type.
        """
        self._test_int_type(int16_t, 16, True)

    def test_uint32_t(self):
        """
        Verify functionality of ``uint32_t`` type.
        """
        self._test_int_type(uint32_t, 32, False)

    def test_int32_t(self):
        """
        Verify functionality of ``int32_t`` type.
        """
        self._test_int_type(int32_t, 32, True)

    def test_uint64_t(self):
        """
        Verify functionality of ``uint64_t`` type.
        """
        self._test_int_type(uint64_t, 64, False)

    def test_int64_t(self):
        """
        Verify functionality of ``int64_t`` type.
        """
        self._test_int_type(int64_t, 64, True)

    def _test_int_pack_unpack(self, field_type, bits, fmt):
        """
        Really this is multiple tests... really this should be data-driven somehow.
        """
        # pack some value that just happens to be valid for all types.
        value = 10
        #expected_pack = b'\x0A' + b'\x00' * (bits // 8 - 1)
        expected_pack = struct.pack(fmt, value)

        field = field_type(value)
        packed = bytes(field)

        self.assertEqual(packed, expected_pack, '%s did not pack to the correct value.' % (field_type.__name__))

        field.from_bytes(packed)
        self.assertEqual(field.value, value, '%s did not unpack to the correct value.' % (field_type.__name__))

        # from_bytes should insist on consuming all that it is given
        with self.assertRaises(ValueError, msg='%s did not raise ValueError when given too many bytes to unpack.'):
            field.from_bytes(expected_pack + b'\x13')

    def _test_int_size(self, field_type, bits):
        """
        Verify that ``size`` agrees with reality.
        """
        field = field_type()
        size = field.size()

        self.assertEqual(size, bits // 8, "%s is the wrong size :'(." % (field_type.__name__))

        zero = b'\x00' * size + b'\x01'

        consumed_bytes = field.unpack(zero)

        self.assertEqual(consumed_bytes, size, "%s consumed wrong number of bytes." % (field_type.__name__))

    def _test_int_bounds(self, field_type, bits, signed):
        """
        Verify that ``field_type`` can hold ``min_val`` and ``max_val``, but
        not values outside of that range.
        """
        struct = _test_field_struct(field_type)

        min_val = -2 ** (bits - 1) if signed else 0
        max_val = 2 ** (bits - 1) - 1 if signed else 2 ** bits - 1

        # these should work
        struct.test = min_val
        struct.test = max_val

        with self.assertRaises(TypeError):
            struct.test = min_val - 1

        with self.assertRaises(TypeError):
            struct.test = max_val + 1

        with self.assertRaises(TypeError):
            f = field_type(min_val - 1)

    def _test_int_offset(self, field_type, bits, fmt):
        """
        This sort of tests unpacking at an offset.
        """
        size = bits // 8
        value = 13
        offset = 12
        packed = b'\x99' * offset + struct.pack(fmt, value)

        field = field_type()
        field.unpack(packed, offset=offset)
        self.assertEqual(value, field.value)


def _test_field_struct(field_type):
    class _test(Structure):
        _fields_ = [
            ('test', field_type)
        ]

    return _test()


if __name__ == '__main__':
    unittest.main()
