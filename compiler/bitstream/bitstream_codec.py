"""
Bitstream Codec - FPGA-H1 Virtual Lab
Encodes and decodes the official H1BS binary bitstream with CRC32 integrity check.
"""

import struct
import json
import zlib
from typing import Dict, List, Any, Optional

MAGIC_HEADER = b"H1BS"
FORMAT_VERSION = 1

# Frame Types
FRAME_LUT_BLE = 0x01
FRAME_DFF_SEQ = 0x02
FRAME_SWITCH_BOX = 0x03
FRAME_CONN_BOX = 0x04
FRAME_IOB = 0x05
FRAME_END_OF_STREAM = 0xFF

# Architecture Families
ARCH_FAMILY_MAP = {
    4: 0x0004,
    16: 0x0010,
    64: 0x0040,
    256: 0x0100,
    1024: 0x0400,
    4096: 0x1000,
    8640: 0x21C0
}


class BitstreamCodec:
    """Encodes and decodes binary bitstreams for FPGA-H1."""

    @staticmethod
    def encode(
        num_luts: int,
        ble_configs: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
        sb_configs: Optional[List[Dict[str, Any]]] = None
    ) -> bytes:
        """
        Generates binary bitstream bytes.
        
        ble_configs format:
        [
            {"id": 0, "mask": 0x8888, "bypass_ff": True, "carry_enable": False, "invert_clk": False},
            ...
        ]
        """
        arch_id = ARCH_FAMILY_MAP.get(num_luts, 0x0000)
        meta_dict = metadata or {"project": "FPGA-H1", "device_luts": num_luts}
        meta_bytes = json.dumps(meta_dict).encode("utf-8")
        if len(meta_bytes) > 65535:
            raise ValueError("Metadata size exceeds uint16 limit")

        # 1. Header: Magic(4), Version(1), ArchFamily(2), Flags(1), MetadataLen(2)
        flags = 0
        header = struct.pack(
            ">4sBHBH",
            MAGIC_HEADER,
            FORMAT_VERSION,
            arch_id,
            flags,
            len(meta_bytes)
        )

        body = bytearray()
        body.extend(header)
        body.extend(meta_bytes)

        # 2. Frames: BLE configurations
        for cfg in ble_configs:
            target_id = cfg.get("id", 0)
            mask = cfg.get("mask", 0) & 0xFFFF
            bypass = 1 if cfg.get("bypass_ff", True) else 0
            carry = 1 if cfg.get("carry_enable", False) else 0
            inv_clk = 1 if cfg.get("invert_clk", False) else 0
            flag_byte = (bypass & 1) | ((carry & 1) << 1) | ((inv_clk & 1) << 2)

            payload = struct.pack("<HBB", mask, flag_byte, 0x00)
            frame_header = struct.pack(">HBB", target_id, FRAME_LUT_BLE, len(payload))
            body.extend(frame_header)
            body.extend(payload)

        # 3. Frames: Switch Box configurations if present
        if sb_configs:
            for sb in sb_configs:
                sb_id = sb.get("id", 0)
                matrix_mask = sb.get("mask", 0) & 0xFFFFFFFF
                payload = struct.pack("<I", matrix_mask)
                frame_header = struct.pack(">HBB", sb_id, FRAME_SWITCH_BOX, len(payload))
                body.extend(frame_header)
                body.extend(payload)

        # 4. End-of-Stream frame
        body.extend(struct.pack(">HBB", 0xFFFF, FRAME_END_OF_STREAM, 0))

        # 5. Calculate CRC32 across all bytes up to this point
        crc = zlib.crc32(body) & 0xFFFFFFFF
        body.extend(struct.pack("<I", crc))

        return bytes(body)

    @staticmethod
    def decode(data: bytes) -> Dict[str, Any]:
        """
        Decodes and verifies a binary bitstream.
        Raises ValueError if integrity check fails or format is invalid.
        """
        if len(data) < 14:
            raise ValueError(f"Bitstream is too short ({len(data)} bytes)")

        # Verify CRC32
        data_without_crc = data[:-4]
        stored_crc = struct.unpack("<I", data[-4:])[0]
        calc_crc = zlib.crc32(data_without_crc) & 0xFFFFFFFF

        if stored_crc != calc_crc:
            raise ValueError(f"Bitstream CRC32 mismatch: stored 0x{stored_crc:08X} != calculated 0x{calc_crc:08X}")

        # Parse Header
        magic, version, arch_id, flags, meta_len = struct.unpack(">4sBHBH", data_without_crc[:10])
        if magic != MAGIC_HEADER:
            raise ValueError(f"Invalid magic header: {magic}")
        if version != FORMAT_VERSION:
            raise ValueError(f"Unsupported bitstream version: {version}")

        offset = 10
        meta_bytes = data_without_crc[offset:offset + meta_len]
        offset += meta_len
        metadata = json.loads(meta_bytes.decode("utf-8"))

        bles = []
        switch_boxes = []

        # Parse frames
        while offset < len(data_without_crc):
            if offset + 4 > len(data_without_crc):
                break
            target_id, frame_type, payload_len = struct.unpack(">HBB", data_without_crc[offset:offset + 4])
            offset += 4

            payload = data_without_crc[offset:offset + payload_len]
            offset += payload_len

            if frame_type == FRAME_END_OF_STREAM:
                break
            elif frame_type == FRAME_LUT_BLE:
                mask, flag_byte, _ = struct.unpack("<HBB", payload)
                bles.append({
                    "id": target_id,
                    "mask": mask,
                    "mask_hex": f"0x{mask:04X}",
                    "bypass_ff": bool(flag_byte & 1),
                    "carry_enable": bool((flag_byte >> 1) & 1),
                    "invert_clk": bool((flag_byte >> 2) & 1)
                })
            elif frame_type == FRAME_SWITCH_BOX:
                matrix_mask = struct.unpack("<I", payload)[0]
                switch_boxes.append({
                    "id": target_id,
                    "mask": matrix_mask
                })

        return {
            "version": version,
            "arch_id": arch_id,
            "flags": flags,
            "metadata": metadata,
            "bles": bles,
            "switch_boxes": switch_boxes,
            "crc32": f"0x{stored_crc:08X}",
            "byte_count": len(data)
        }
