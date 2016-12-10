tamp: Python structure packing/unpacking
========================================
![test status](https://travis-ci.org/topnotcher/tamp.svg?branch=master)

`tamp` is a Python library for packing and unpacking binary structures. It aims
to do so by specifying the structure declaratively as a Python class:

```python
class Foo(Structure):
	_fields_ = [
		('bar', uint8_t),
		('baz', int16_t[13]),
	]
```

`tamp` does not aim to replace similar Python libraries, or even to be better,
but hopes to be different. It exists primiarly as a for-fun personal project for
use in other personal projects.

Examples
========
A packet structure I use for inter processor communication in a project using
8-bit AVRs:
```python
class mpc_pkt(Structure):
    _fields_ = [
        ('len', uint8_t),
        ('cmd', EnumWrap(MPC_CMD, uint8_t)),
        ('saddr', uint8_t),
        ('chksum', Computed(uint8_t, '_compute_chksum', mismatch_exc=ChecksumMismatchError)),
        ('data', uint8_t[LengthField('len')]),
    ]

    def _compute_chksum(self):
		return self.len ^ self.cmd ^ self.saddr  # just an example
```

* `len` is the number of elments to unpack into the `data` array. The
  relationship is indicated by `LengthField('len')`, which also makes the `len`
  field read-only.
* `cmd` is an enum field specified with an `enum.IntEnum` type (`MPC_CMD`) and a
  pack type `uint8_t`. When the value is assigned or unpacked, the `MPC_CMD`
  enum is consulted to check the validity of the value. The value is always an
  instance of the enum type.
* `chksum` is a `Computed` field: its value cannot be assigned directly, but
  rather is computed based on other structure fields. When unpacking,
  `mismatch_exc` is raised if the unpacked value does not match the computed
  value.


This structure can be read from a stream:
```python
stream = StreamUnpacker(mpc_pkt)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(...)

while True:
	for pkt in stream.unpack(sock.recv(4096)):
		print('received cmd', pkt.cmd, 'from', pkt.saddr)
```

And written:

```python
pkt = mpc_pkt()
pkt.cmd = MPC_CMD.FOO
pkt.saddr = 1
pkt.data = [0x11, 0x22, 0x33]

sock.send(bytes(pkt))
```
