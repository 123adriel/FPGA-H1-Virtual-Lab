"""
LUT4 Core Architecture - FPGA-H1 Virtual Lab
Mathematical model of 4-input Look-Up Table.

A 4-input LUT can implement any boolean function f: {0, 1}^4 -> {0, 1}.
Configured by a 16-bit unsigned integer (SRAM table).
"""

from typing import Union, List, Callable, Dict, Any


class LUT4:
    """
    Look-Up Table with 4 inputs and a 16-bit configuration mask.
    
    Inputs:
        I0: Input 0 (LSB, weight 1)
        I1: Input 1 (weight 2)
        I2: Input 2 (weight 4)
        I3: Input 3 (MSB, weight 8)
    
    Address index: idx = I0 + 2*I1 + 4*I2 + 8*I3 (range 0..15)
    Output: bit 'idx' of the 16-bit configuration mask.
    """
    
    __slots__ = ('name', 'lut_id', '_mask', '_cached_output')

    def __init__(self, name: str = "LUT4", lut_id: int = 0, initial_mask: int = 0x0000):
        self.name = name
        self.lut_id = lut_id
        self._mask = 0
        self._cached_output = 0
        self.set_mask(initial_mask)

    @property
    def mask(self) -> int:
        """Returns the current 16-bit configuration mask."""
        return self._mask

    def set_mask(self, mask: int) -> None:
        """Sets the 16-bit configuration mask. Validates range [0x0000, 0xFFFF]."""
        if not isinstance(mask, int):
            raise TypeError(f"Mask must be an integer, got {type(mask)}")
        if not (0 <= mask <= 0xFFFF):
            raise ValueError(f"Mask must be a 16-bit unsigned integer (0x0000..0xFFFF), got {hex(mask)}")
        self._mask = mask

    def configure_from_truth_table(self, func: Callable[[int, int, int, int], int]) -> int:
        """
        Computes and sets the 16-bit mask from a boolean function f(I0, I1, I2, I3).
        Iterates over all 16 minterms (idx = 0..15).
        """
        computed_mask = 0
        for idx in range(16):
            i0 = idx & 1
            i1 = (idx >> 1) & 1
            i2 = (idx >> 2) & 1
            i3 = (idx >> 3) & 1
            out_bit = int(bool(func(i0, i1, i2, i3)))
            computed_mask |= (out_bit << idx)
        self.set_mask(computed_mask)
        return computed_mask

    def eval(self, i0: int, i1: int, i2: int, i3: int) -> int:
        """
        Evaluates the LUT output deterministically in O(1) time.
        Index: idx = (i0 & 1) | ((i1 & 1) << 1) | ((i2 & 1) << 2) | ((i3 & 1) << 3)
        Output: (mask >> idx) & 1
        """
        idx = (i0 & 1) | ((i1 & 1) << 1) | ((i2 & 1) << 2) | ((i3 & 1) << 3)
        out = (self._mask >> idx) & 1
        self._cached_output = out
        return out

    def eval_vector(self, inputs: List[int]) -> int:
        """Evaluates LUT given a list or tuple of 4 binary inputs [I0, I1, I2, I3]."""
        if len(inputs) < 4:
            raise ValueError(f"LUT4 requires exactly 4 inputs, got {len(inputs)}")
        return self.eval(inputs[0], inputs[1], inputs[2], inputs[3])

    def get_truth_table(self) -> List[Dict[str, int]]:
        """Generates the full 16-row truth table for inspection and debugging."""
        rows = []
        for idx in range(16):
            i0 = idx & 1
            i1 = (idx >> 1) & 1
            i2 = (idx >> 2) & 1
            i3 = (idx >> 3) & 1
            rows.append({
                "idx": idx,
                "I3": i3,
                "I2": i2,
                "I1": i1,
                "I0": i0,
                "Y": (self._mask >> idx) & 1
            })
        return rows

    def to_dict(self) -> Dict[str, Any]:
        """Serializes LUT configuration to dictionary."""
        return {
            "name": self.name,
            "lut_id": self.lut_id,
            "mask_hex": f"0x{self._mask:04X}",
            "mask_dec": self._mask
        }

    def __repr__(self) -> str:
        return f"LUT4(id={self.lut_id}, name='{self.name}', mask=0x{self._mask:04X})"
