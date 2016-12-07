import unittest
import enum

from tamp import *


class TestStruct(unittest.TestCase):
    def test_struct_inheritence(self):
        class _struct1(Structure):
            _fields_ = [
                ('test1', uint8_t.le)
            ]

        class _struct2(_struct1):
            _fields_ = [
                ('test2', uint32_t.be)
            ]

        s = _struct2()
        s.test1 = 13
        s.test2 = 1337

        self.assertTrue(hasattr(_struct2(), 'test1'))
        self.assertTrue(hasattr(_struct2(), 'test2'))
        self.assertEqual(bytes(s), b'\x0D\x00\x00\x059')

    def test_struct_pack(self):
        """
        """

    def test_struct_bytes_extend(self):
        """
        Packing a structure calls __bytes__().
        """
        class _test(Structure):
            _fields_ = [('test', uint8_t)]

            def __init__(self, *args, **kwargs):
                super(_test, self).__init__(*args, **kwargs)
                self.__dict__['called'] = False

            def __bytes__(self):
                self.__dict__['called'] = True
                return super(_test, self).__bytes__()

        t = _test()
        t.pack()

        self.assertTrue(t.__dict__['called'])

    @unittest.expectedFailure  # intentionally broke this.
    def test_set_invalid_field(self):
        """
        Setting an invalid field raises :exc:`AttributeError`.
        """
        s = _test_field_struct(uint8_t)

        with self.assertRaises(AttributeError):
            s.foo = 1

    def test_get_invalid_field(self):
        """
        Getting an invalid field raises :exc:`AttributeError`.
        """
        s = _test_field_struct(uint8_t)

        with self.assertRaises(AttributeError):
            t = s.bar

    def test_value_inequality(self):
        """
        Two structs are not equal when the values are different.
        """
        class _test(Structure):
            _fields_ = [
                ('test', uint8_t)
            ]

        s = _test()
        t = _test()

        s.test = 1
        t.test = 2

        self.assertNotEqual(s, t)

    def test_values_equal(self):
        """
        Two structs are equal when their values (even of different types and
        names) are equal.
        """
        s = _test_field_struct(uint8_t, field_name='test1')
        t = _test_field_struct(int16_t, field_name='test2')

        s.test1 = 2
        t.test2 = 2

        self.assertEqual(s, t)

    def test_fields_number_inequality(self):
        """
        Two structs are not equal if they have a different number of fields.
        """
        class _test(Structure):
            _fields_ = [
                ('test', uint8_t),
                ('test2', uint8_t)
            ]

        s = _test_field_struct(uint8_t, field_name='test')
        s.test = 1

        t = _test()
        t.test = 1

        self.assertNotEqual(s, t)

    def test_struct_in_a_struct(self):
        """
        A struct can be a struct member.
        """
        class _test1(Structure):
            _fields_ = [
                ('test', uint32_t.le),
            ]

        class _test2(Structure):
            _fields_ = [
                ('test2', _test1),
                ('test3', uint8_t)
            ]

        t = _test2()
        t.test2.test = 5
        t.test3 = 1

        self.assertEqual(b'\x05\x00\x00\x00\x01', bytes(t))

        t.unpack(b'\xff\x00\x00\x00\x02')
        self.assertEqual(t.test2.test, 0xFF)
        self.assertEqual(t.test3, 2)

        # Assigning a struct field - TODO: test this way better
        # TODO: test that the fields copy!
        t.test2 = _test1()

    def test_const_bytes_unpack(self):
        """
        Const bytes can unpack properly.
        """
        s = _test_field_struct(Const(b'12345'))
        s.from_bytes(b'12345')

        self.assertEqual(s.test, b'12345')

    def test_const_field_type_unpack(self):
        """
        Const field/type can unpack properly
        """
        s = _test_field_struct(Const(int8_t, -5))
        s.from_bytes(bytes(int8_t(value=-5)))

        self.assertEqual(s.test, -5)

    def test_const_bytes_pack(self):
        """
        Const bytes can pack properly.
        """
        s = _test_field_struct(Const(b'12345'))

        self.assertEqual(bytes(s), b'12345')

    def test_const_field_type_pack(self):
        """
        Const field/type can pack properly
        """
        s = _test_field_struct(Const(int8_t, -5))

        self.assertEqual(bytes(s), bytes(int8_t(value=-5)))

    def test_const_bytes_unpack_value_error(self):
        """
        A const bytes field raises ValueError if the unpacked value does not match.
        """
        s = _test_field_struct(Const(b'12345'))

        with self.assertRaises(ValueError):
            s.from_bytes(b'12340')

    def test_const_field_type_unpack_value_error(self):
        """
        A const field/type field raises ValueError if the unpacked value does not match.
        """
        s = _test_field_struct(Const(int8_t, -5))

        with self.assertRaises(ValueError):
            s.from_bytes(bytes(int8_t(value=-4)))


def _test_field_struct(field_type, field_name='test'):
    class _test(Structure):
        _fields_ = [
            (field_name, field_type)
        ]

    return _test()


if __name__ == '__main__':
    unittest.main()
