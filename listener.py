import re
import struct
import pymem
import pymem.pattern

PYASCII_OBJECT_SIZE    = 48
PYCOMPACT_UNICODE_SIZE = 72
KIND_SHIFT = 2
KIND_MASK  = 0b111 << KIND_SHIFT
KIND_1BYTE = 1
KIND_2BYTE = 2
KIND_4BYTE = 4

class RenpyMemoryListener:
    def __init__(self, process_name: str):
        self.pm = pymem.Pymem(process_name)
        self.store_dict_addr = self.find_say_dict_entry()
        self.tag_re = re.compile(r'\{[^}]*\}')

    def find_say_dict_entry(self):
        target = b"renpy.store"
        result = pymem.pattern.pattern_scan_all(self.pm.process_handle, target)
        store_key_addr = result - PYASCII_OBJECT_SIZE
        return self._find_store_dict_via_modules(store_key_addr)

    def _find_store_dict_via_modules(self, renpy_store_key_addr: int) -> int:
        key_bytes = struct.pack("<Q", renpy_store_key_addr)
        hits = pymem.pattern.pattern_scan_all(
            self.pm.process_handle, key_bytes, return_multiple=True
        )
        for hit in hits:
            val_ptr = self.read_u64(hit + 8)
            md_dict = self.read_u64(val_ptr + 16)
            if md_dict < 0x10000:
                continue
            return md_dict
        raise RuntimeError("无法找到 renpy.store.__dict__")

    def read_u64(self, addr: int) -> int:
        return struct.unpack_from("<Q", self.pm.read_bytes(addr, 8))[0]

    def read_i64(self, addr: int) -> int:
        return struct.unpack_from("<q", self.pm.read_bytes(addr, 8))[0]

    def read_u32(self, addr: int) -> int:
        return struct.unpack_from("<I", self.pm.read_bytes(addr, 4))[0]

    def read_pyunicode(self, obj_addr: int) -> str:
        length = self.read_i64(obj_addr + 16)
        state  = self.read_u32(obj_addr + 32)
        kind   = (state & KIND_MASK) >> KIND_SHIFT
        ascii_ = (state >> 6) & 1

        data_addr = obj_addr + (PYASCII_OBJECT_SIZE if ascii_ else PYCOMPACT_UNICODE_SIZE)

        if kind == KIND_1BYTE:
            raw = self.pm.read_bytes(data_addr, length)
            return raw.decode("latin-1")
        elif kind == KIND_2BYTE:
            raw = self.pm.read_bytes(data_addr, length * 2)
            return raw.decode("utf-16-le")
        elif kind == KIND_4BYTE:
            raw = self.pm.read_bytes(data_addr, length * 4)
            chars = struct.unpack_from(f"<{length}I", raw)
            return "".join(chr(c) for c in chars)
        return ""

    def _dict_lookup(self, dict_addr: int, key_str: str) -> int:
        ma_keys_ptr = self.read_u64(dict_addr + 32)
        dk_size     = self.read_i64(ma_keys_ptr + 8)
        dk_nentries = self.read_i64(ma_keys_ptr + 32)

        if dk_size <= 0xFF:
            index_size = 1
        elif dk_size <= 0xFFFF:
            index_size = 2
        elif dk_size <= 0xFFFFFFFF:
            index_size = 4
        else:
            index_size = 8

        indices_bytes = (dk_size * index_size + 7) & ~7
        entries_start = ma_keys_ptr + 40 + indices_bytes

        for i in range(dk_nentries):
            entry_addr = entries_start + i * 24
            key_ptr = self.read_u64(entry_addr + 8)
            key_val = self.read_pyunicode(key_ptr)
            if key_val == key_str:
                return self.read_u64(entry_addr + 16)

        return 0

    def run_once(self):
        what_ptr = self._dict_lookup(self.store_dict_addr, "_last_say_what")
        what = self.read_pyunicode(what_ptr)
        what = self.tag_re.sub('', what)

        return what