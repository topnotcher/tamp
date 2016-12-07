import unittest
import struct

from tamp import *


class TestArray(unittest.TestCase):
    expected_packed = b'\x01\x02\x03\x04\x05'
    expected_unpacked = [1, 2, 3, 4, 5]
    array_type = uint8_t[len(expected_unpacked)]

    def test_fixed_array_pack_unpack_value(self):
        """
        Test that a fixed length array packs and unpacks properly.
        """
        array = self.array_type(value=self.expected_unpacked)
        self.assertEqual(bytes(array), self.expected_packed)

        array.from_bytes(self.expected_packed)

        self.assertEqual(array.value, self.expected_unpacked)

    def test_fixed_array_unpack_too_few(self):
        """
        A fixed length array raises exc:`ValueError` when unpacking too few
        bytes.
        """
        array = self.array_type()

        # try to unpack too little data - must fail.
        with self.assertRaises(ValueError):
            array.from_bytes(self.expected_packed[:-1])

    def test_fixed_array_unpack_too_many(self):
        """
        A fixed length array raises exc:`ValueError` when unpacking too many
        bytes.
        """
        array = self.array_type()
        # try to unpack too little data - must fail.
        with self.assertRaises(ValueError):
            array.from_bytes(self.expected_packed + b'\x13')

    def test_fixed_array_unpack_size(self):
        """
        A fixed length array consumes the correct number of bytes.
        """
        array = self.array_type()

        # try to unpack too little data - must fail.
        # unpack() should consume exactly the amount required
        consumed = array.unpack(self.expected_packed + b'\x13')
        self.assertEqual(consumed, len(self.expected_unpacked))

    def test_fixed_array_pack_size(self):
        """
        A fixed length array should accept only the exact number of bytes for
        packing.
        """
        with self.assertRaises(TypeError):
            self.array_type(self.expected_unpacked[:-1])

        with self.assertRaises(TypeError):
            self.array_type(self.expected_unpacked + [0])

    def test_array_pack_invalid_value(self):
        """
        An array type raise TypeError when packing a value that is not a valid
        instance of its element type.
        """
        test_type = uint8_t[2][2]

        test_type(value=[[1, 2], [1, 2]])

        with self.assertRaises(TypeError):
            test_type(value=[[1, -1], [1, 2]])

        with self.assertRaises(TypeError):
            test_type(value=[[1, 2], [1, 2], [1, 2]])

    def test_variable_array_unpack(self):
        """
        Verify that a variable length array unpacks correctly and consumes all
        bytes.
        """
        # argh. There's a design flaw here: variable length arrays can't be in
        # an array or nested because they'll consume everything. - They should
        # be able to read the amount to consume from other fields in a struct.
        buf = b'\x01\x02\x03\x04\x05'
        unpacked = uint8_t[0]()
        unpacked.unpack(buf)

        self.assertEqual(unpacked.value, list(buf))

    def test_array_unpack_offset(self):
        """
        An array can unpack at an offset.
        """
        field = uint8_t[0]()


    def test_variable_length_array_pack(self):
        """
        Variable length array members should pack all  the things.
        """
        data = list(range(5))
        packed = bytes(uint8_t[0](value=data))

        self.assertEqual(packed, bytes(data))

    def test_assign_invalid_length(self):
        """
        A :exc:`TypeError` is raised when assigning a field of the wrong length.
        """
        s = _test_field_struct(uint8_t[1])

        s.test = [1]

        with self.assertRaises(TypeError):
            s.test = [1, 2]

    def test_assign_invalid_values(self):
        """
        A :exc:`TypeError` is raised when assigning a field containing invalid values.
        """
        s = _test_field_struct(uint8_t[1])

        s.test = [1]

        with self.assertRaises(TypeError):
            s.test = [-1]

    def test_array_default(self):
        """
        An array defaults to a list of default element values.
        """
        elem_type = uint8_t
        array_length = 3
        elem_default = elem_type().value

        array_type = elem_type[array_length]()
        array_default = array_type.value

        self.assertEqual(array_default, [elem_default] * array_length)

    def test_fixed_length_size(self):
        """
        A fixed length array is the size of ``elements  *sizeof(element)``.
        """
        self.assertEqual(uint32_t[3]().size(), 3 * uint32_t().size())

    def test_variable_length_size(self):
        """
        A variable length array has a size of 0.
        """
        self.assertEqual(uint32_t[0]().size(), 0)

    def test_array_length_field_unpack(self):
        """
        An array's length can be determined from a struct field.
        """
        class _test(Structure):
            _fields_ = [
                ('len', uint8_t),
                ('data', uint8_t[LengthField('len')])
            ]

        packed = struct.pack('BBBBBB', 5, 0, 1, 2, 3, 4)

        s = _test()
        s.unpack(packed + b'abcdefg')
        self.assertEqual(s.len, 5)
        self.assertEqual(s.data, [0, 1, 2, 3, 4])

    def test_array_length_field_autoset(self):
        """
        Setting the value of an array field with a length field sets the length field.
        """
        class _test(Structure):
            _fields_ = [
                ('len', uint8_t),
                ('data', uint8_t[LengthField('len')])
            ]

        s = _test()
        s.data = [1, 2, 3]

        self.assertEqual(s.len, len(s.data))

    def test_array_length_field_readonly(self):
        """
        Setting a length field directly fails.
        """
        class _test(Structure):
            _fields_ = [
                ('len', uint8_t),
                ('data', uint8_t[LengthField('len')])
            ]

        s = _test()
        with self.assertRaises(TypeError):  # TODO
            s.len = 5

    def test_field_length_array_unpack_too_few(self):
        """
        A ``LengthField`` array raises ``ValueError`` when too few bytes are
        unpacked.
        """
        class _test(Structure):
            _fields_ = [
                ('len', uint8_t),
                ('data', uint8_t[LengthField('len')])
            ]

        packed = struct.pack('BBBBB', 5, 0, 1, 2, 3)

        s = _test()
        with self.assertRaises(ValueError):
            s.unpack(packed)

    def test_field_length_array_size(self):
        """
        A ``LengthField`` type array always returns a size of 0.
        """
        class _test(Structure):
            _fields_ = [
                ('len', uint8_t),
                ('data', uint8_t[LengthField('len')])
            ]

        s = _test()
        s.data = list(range(5))

        self.assertEqual(s.size(), uint8_t().size())

    def test_multi_dimensional(self):
        """
        An array can be multidimensional
        """
        test_type = uint8_t[2][2]
        t = test_type(value=[[1, 2], [3, 4]])

        self.assertEqual(bytes(t), b'\x01\x02\x03\x04')

        t.unpack(b'\x04\x03\x02\x01')
        self.assertEqual(t.value, [[4, 3], [2, 1]])

    @unittest.expectedFailure
    def test_length_field_multidimensional(self):
        """
        A LengthField can be the second dimension in an array.
        """

        # This seems like an insane case, but really isn't: you might want a
        # variable number of uint8_t[2] in your struct. This doesn't work
        # currently because array's don't pass parents down to their members
        # (and in fact do not even instantiate members like structs do...)
        class _test(Structure):
            _fields_ = [
                ('len1', uint8_t),
                ('len2', uint8_t),
                ('data', uint8_t[LengthField('len1')][LengthField('len2')])
            ]

        s = _test()
        s.unpack(b'\x02\x03\x09\x07\x12\x34\xff\x00')

        self.assertEqual(s.data, [[0x09, 0x07], [0x12, 0x34], [0xff, 0x00]])

    # def test_array_length_field_pack(self):
    #     """
    #     An array's length can be determined from a struct field.
    #     """
    #     class _test(Structure):
    #         _fields_ = [
    #             ('len', uint8_t),
    #             ('data', uint8_t[LengthField('len', poop=1234)])
    #         ]
    #
    #
    #     #packed = struct.pack('BBBBBB', 5, 0, 1, 2, 3, 4)
    #
    #     s = _test()
    #     s.data = [1,2,3,34,5,6]
    #     print(s.len)
        #s.unpack(packed + b'abcdefg')
        #self.assertEqual(s.len, 5)
        #self.assertEqual(s.data, [0, 1, 2, 3, 4])


class PackedLengthTests(unittest.TestCase):
    def setUp(self):
        self.end = 77
        self.data = [1, 2, 3, 4]
        self.data_packed = bytes(uint32_t[len(self.data)](value=self.data))
        self.dsize = len(self.data_packed)
        self.dsize_packed = bytes(uint8_t(value=self.dsize))
        self.end_packed = bytes(uint32_t(value=self.end))

        # TODO: Implicitly testing using a structure as the packed length field.
        # Should be a separate case

        class _inner(Structure):
            # Variable length array will normally consume all the bytes
            _fields_ = [
                ('data', uint32_t[0]),
            ]


        class _struct(Structure):
            _fields_ = [
                ('dsize', uint8_t),

                ('inner', PackedLength(_inner, 'dsize')),
                ('end', Const(uint32_t, self.end)),
            ]

        self.s = _struct()

    def test_packed_length_unpack(self):
        """
        A PackedLength field determines how many bytes the target field unpacks.
        """
        s = self.s
        s.unpack(self.dsize_packed + self.data_packed + self.end_packed)

        self.assertEqual(s.dsize, self.dsize)
        self.assertEqual(s.inner.data, self.data)
        self.assertEqual(s.end, self.end)

    def test_packed_length_updates(self):
        """
        The length field for a PackedLength field updates based on the ...
        other field.
        """
        # This is an interesting case: "inner" is updated; "s" is not...
        self.s.inner.data = [1, 2, 3, 4, 5, 6]

        self.assertEqual(self.s.dsize, len(bytes(uint32_t[len(self.s.inner.data)](value=self.s.inner.data))))

    def test_packed_length_pack(self):
        """
        A PackedLength field packs correctly.
        """
        self.s.inner.data = self.data
        self.s.end = self.end

        self.assertEqual(bytes(self.s), self.dsize_packed + self.data_packed + self.end_packed)

    def test_packed_length_read_only(self):
        """
        The length field for a PackedLength is read only.
        """
        with self.assertRaises(TypeError):
            self.s.dsize = 1


def _test_field_struct(field_type):
    class _test(Structure):
        _fields_ = [
            ('test', field_type)
        ]

    return _test()


if __name__ == '__main__':
    unittest.main()
