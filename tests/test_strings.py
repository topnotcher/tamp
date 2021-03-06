import unittest

from tamp import *

class BytesTests(unittest.TestCase):
    def test_unpack_byte(self):
        """
        A ``Byte`` unpacks into a 1-char byte string.
        """
        b = Byte()
        consumed = b.unpack(b'1')

        self.assertEqual(b.value, b'1')
        self.assertEqual(consumed, 1)

    def test_byte_init_empty(self):
        """
        The default value of a byte is b'\\x00'
        """
        self.assertEqual(Byte().value, b'\x00')

    def test_byte_init_byte(self):
        """
        A byte can be initialized with a byte value.
        """
        self.assertEqual(Byte(value=b'\x12').value, b'\x12')

        b = Byte()
        b.value = b'\x12'
        self.assertEqual(b.value, b'\x12')

    def test_byte_init_int(self):
        """
        A byte can be initialized from an integer.
        """
        self.assertEqual(Byte(value=12).value, b'\x0c')

        b = Byte()
        b.value = 12
        self.assertEqual(b.value, b'\x0c')

    def test_byte_invalid_init(self):
        """
        A ``Byte`` raises ``TypeError`` if given too many bytes.
        """
        with self.assertRaises(TypeError):
            b = Byte(value=b'234')

        with self.assertRaises(TypeError):
            b = Byte()
            b.value = b'123'

    def test_pack_byte(self):
        """
        A ``Byte`` packs to the corresponding 1-char byte string.
        """
        self.assertEqual(bytes(Byte(value=b'1')), b'1')

    def test_byte_size(self):
        """
        The size of a ``Byte`` is always 1.
        """
        self.assertEqual(Byte().size(), 1)

    def test_byte_unpack_stream(self):
        """
        ``Bytes`` can unpack from a stream.
        """
        stream = StreamUnpacker(Byte)
        packed = b'12345'

        values = []
        for byte in (packed[i : i + 1] for i in range(len(packed))):
            values.extend(stream.unpack(byte))

        self.assertEqual(values, [b'1', b'2', b'3', b'4', b'5'])

    def test_bytes_init_empty(self):
        """
        The default value a Byte array is an appropriate-length byte
        string.
        """
        self.assertEqual(Byte[5]().value, b'\x00' * 5)
        self.assertEqual(Byte[0]().value, b'')

    def test_bytes_init_value(self):
        """
        Byte[x] can be initialized from a byte string.
        """
        self.assertEqual(Byte[5](value=b'12345').value, b'12345')

        b = Byte[5]()
        b.value = b'12345'

        self.assertEqual(b'12345', b.value)

    def test_unpack_bytes(self):
        """
        Bytes unpack into... bytes.
        """
        packed = b'123456'
        field = Byte[len(packed)]()
        field.unpack(packed)

        self.assertEqual(packed, field.value)

    def test_unpack_bytes_stream(self):
        """
        A byte array can be unpacked from a stream.
        """
        stream = StreamUnpacker(Byte[2])
        packed = b'123456'

        values = []
        for byte in (packed[i : i + 1] for i in range(len(packed))):
            values.extend(stream.unpack(byte))

        self.assertEqual(values, [b'12', b'34', b'56'])

    def test_bytes_init_ints(self):
        """
        A byte array can be initialized from a list of ints - just like
        bytes!
        """
        self.assertEqual(Byte[5](value=[1, 2, 3, 4, 5]).value, b'\x01\x02\x03\x04\x05')

        b = Byte[5]()
        b.value = [1, 2, 3, 4, 5]
        self.assertEqual(b.value, b'\x01\x02\x03\x04\x05')

    def test_bytes_init_invalid(self):
        """
        A Byte array raises ``TypeError`` when given an invalid value.
        """
        with self.assertRaises(TypeError):
            Byte[5](value=1)

    def test_bytes_pack(self):
        """
        Byte arrays pack to ... bytes.
        """
        self.assertEqual(bytes(Byte[5](value=b'12345')), b'12345')

    def test_bytes_size(self):
        """
        The size of a Byte array is the number of bytes.
        """
        # Where applicable: the size is actually a function of the Array length
        # type (LengthField, LengthFixed), etc... but those sometimes defer to
        # ArrayType
        self.assertEqual(Byte[5]().size(), 5)
        self.assertEqual(Byte[0]().size(), 0)
