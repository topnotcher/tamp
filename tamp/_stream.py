class StreamUnpacker:
    def __init__(self, unpack_type):
        self.unpack_type = unpack_type
        self._buf = b''
        self._obj = None
        self._stack = []

    def unpack(self, buf=None):
        result = self.unpack_one(buf=buf)
        while result is not None:
            yield result

            result = self.unpack_one(buf=None)

    def unpack_one(self, buf=None):
        if buf:
            self._buf += buf

        if self._obj is None:
            self._obj = self.unpack_type()

        result = self._obj.unpack_stream(self)
        if result:
            obj = self._obj
            self._obj = None

            return obj.value

        else:
            return None

    def __len__(self):
        return len(self._buf)

    def read(self, size):
        buf = self._buf[:size]
        self._buf = self._buf[size:]

        if len(buf) != size:
            raise IndexError

        return buf

    def push_state(self, obj, state):
        self._stack.append((obj, state))

    def pop_state(self, obj, default=None):
        if len(self._stack) > 0 and self._stack[-1][0] is obj:
            return self._stack.pop()[1]
        else:
            return default
