"""Universal Decoder: Seven Generations knowledge preservation.
Modular codec architecture for Cherokee AI Federation data formats.
Each codec is self-describing — headers contain format version + schema."""

import json
import zlib
import hashlib
from datetime import datetime

FORMAT_VERSION = "1.0.0"
MAGIC_HEADER = b"CHRKEE7G"

class Codec:
    """Base codec with self-describing header."""
    codec_type = "base"

    def encode(self, data):
        raise NotImplementedError

    def decode(self, blob):
        raise NotImplementedError

    def _make_header(self, payload_len):
        header = {
            "magic": MAGIC_HEADER.hex(),
            "version": FORMAT_VERSION,
            "codec": self.codec_type,
            "created": datetime.now().isoformat(),
            "payload_bytes": payload_len,
        }
        return json.dumps(header).encode("utf-8")

class MarkdownCodec(Codec):
    """Codec for Markdown knowledge documents."""
    codec_type = "markdown"

    def encode(self, text):
        payload = zlib.compress(text.encode("utf-8"), level=9)
        header = self._make_header(len(payload))
        header_len = len(header).to_bytes(4, "big")
        return MAGIC_HEADER + header_len + header + payload

    def decode(self, blob):
        assert blob[:8] == MAGIC_HEADER, "Invalid magic header"
        header_len = int.from_bytes(blob[8:12], "big")
        header = json.loads(blob[12:12+header_len])
        payload = blob[12+header_len:]
        return zlib.decompress(payload).decode("utf-8")

class ThermalCodec(Codec):
    """Codec for thermal memory JSONB archives."""
    codec_type = "thermal"

    def encode(self, records):
        payload = zlib.compress(json.dumps(records, default=str).encode("utf-8"), level=9)
        header = self._make_header(len(payload))
        header_len = len(header).to_bytes(4, "big")
        return MAGIC_HEADER + header_len + header + payload

    def decode(self, blob):
        assert blob[:8] == MAGIC_HEADER, "Invalid magic header"
        header_len = int.from_bytes(blob[8:12], "big")
        payload = blob[12+header_len:]
        return json.loads(zlib.decompress(payload).decode("utf-8"))

CODECS = {
    "markdown": MarkdownCodec(),
    "thermal": ThermalCodec(),
}

def encode(data, codec_type="markdown"):
    return CODECS[codec_type].encode(data)

def decode(blob):
    assert blob[:8] == MAGIC_HEADER, "Not a Cherokee 7G archive"
    header_len = int.from_bytes(blob[8:12], "big")
    header = json.loads(blob[12:12+header_len])
    codec_type = header["codec"]
    return CODECS[codec_type].decode(blob)

if __name__ == "__main__":
    test = "# Sacred Knowledge\n\nThis is a test of the seven generations codec."
    blob = encode(test, "markdown")
    restored = decode(blob)
    assert restored == test
    ratio = len(blob) / len(test.encode())
    print(f"Encoded {len(test)} chars -> {len(blob)} bytes ({ratio:.1%})")
    print(f"Round-trip: {'PASS' if restored == test else 'FAIL'}")

    thermal_test = [{"content": "Memory 1", "temp": 80}, {"content": "Memory 2", "temp": 50}]
    blob2 = encode(thermal_test, "thermal")
    restored2 = decode(blob2)
    print(f"Thermal round-trip: {'PASS' if restored2 == thermal_test else 'FAIL'}")