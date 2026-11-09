"""
Unit Tests for Bitstream Codec - FPGA-H1 Virtual Lab
Verifies binary encoding, serialization, CRC32 validation, and error detection.
"""

import pytest
from compiler.bitstream.bitstream_codec import BitstreamCodec


class TestBitstreamCodec:
    def test_encode_and_decode_cycle(self):
        ble_configs = [
            {"id": 0, "mask": 0x8888, "bypass_ff": True, "carry_enable": False, "invert_clk": False},
            {"id": 1, "mask": 0xEEEE, "bypass_ff": True, "carry_enable": False, "invert_clk": False},
            {"id": 2, "mask": 0x6666, "bypass_ff": False, "carry_enable": True, "invert_clk": False},
            {"id": 3, "mask": 0x5555, "bypass_ff": False, "carry_enable": False, "invert_clk": True},
        ]
        meta = {"author": "FPGA-H1 Team", "circuit": "Test4LUT"}

        raw_bytes = BitstreamCodec.encode(
            num_luts=4,
            ble_configs=ble_configs,
            metadata=meta
        )

        assert raw_bytes.startswith(b"H1BS")
        assert len(raw_bytes) > 20

        decoded = BitstreamCodec.decode(raw_bytes)
        assert decoded["version"] == 1
        assert decoded["arch_id"] == 0x0004
        assert decoded["metadata"]["circuit"] == "Test4LUT"
        assert len(decoded["bles"]) == 4

        # Verify BLE 0
        assert decoded["bles"][0]["id"] == 0
        assert decoded["bles"][0]["mask"] == 0x8888
        assert decoded["bles"][0]["bypass_ff"] is True

        # Verify BLE 2
        assert decoded["bles"][2]["id"] == 2
        assert decoded["bles"][2]["mask"] == 0x6666
        assert decoded["bles"][2]["bypass_ff"] is False
        assert decoded["bles"][2]["carry_enable"] is True

    def test_crc32_corruption_rejection(self):
        ble_configs = [{"id": 0, "mask": 0xFFFF, "bypass_ff": True}]
        raw_bytes = BitstreamCodec.encode(num_luts=4, ble_configs=ble_configs)

        # Corrupt 1 byte in the middle of the payload
        corrupted = bytearray(raw_bytes)
        corrupted[15] ^= 0xFF

        with pytest.raises(ValueError, match="CRC32 mismatch"):
            BitstreamCodec.decode(bytes(corrupted))


if __name__ == "__main__":
    pytest.main(["-v", __file__])
