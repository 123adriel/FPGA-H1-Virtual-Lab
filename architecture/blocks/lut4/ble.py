"""
Basic Logic Element (BLE) - FPGA-H1 Virtual Lab
Combines 1x LUT4, 1x DFF, Bypass Multiplexer, and Fast Carry logic.
"""

from typing import Dict, Any, List
from architecture.blocks.lut4.lut4_core import LUT4
from architecture.blocks.flipflops.dff import DFF


class BLE:
    """
    Basic Logic Element (BLE):
    - 4 Inputs: I0, I1, I2, I3
    - Carry In: CIN
    - Carry Out: COUT
    - 1x LUT4
    - 1x DFF
    - Output Y: Either combinational (bypass_ff=True) or registered (bypass_ff=False)
    """

    def __init__(
        self,
        name: str = "BLE",
        ble_id: int = 0,
        lut_mask: int = 0x0000,
        bypass_ff: bool = True,
        carry_enable: bool = False,
        invert_clk: bool = False
    ):
        self.name = name
        self.ble_id = ble_id
        self.lut = LUT4(name=f"{name}_LUT4", lut_id=ble_id, initial_mask=lut_mask)
        self.dff = DFF(name=f"{name}_DFF", dff_id=ble_id, invert_clk=invert_clk)
        self.bypass_ff = bypass_ff
        self.carry_enable = carry_enable
        self.last_out = 0
        self.last_cout = 0

    def eval(
        self,
        i0: int,
        i1: int,
        i2: int,
        i3: int,
        clk: int = 0,
        ce: int = 1,
        srst: int = 0,
        arst: int = 0,
        cin: int = 0
    ) -> int:
        """
        Evaluates the BLE for the given inputs and clock signals.
        Returns the output Y (combinational or registered).
        """
        # 1. Combinational LUT evaluation
        lut_out = self.lut.eval(i0, i1, i2, i3)

        # 2. Fast carry generation if enabled
        # In arithmetic mode, I0 is A, I1 is B, cin is carry-in.
        # Cout = (A & B) | (A & cin) | (B & cin)
        if self.carry_enable:
            a = i0 & 1
            b = i1 & 1
            c = cin & 1
            self.last_cout = (a & b) | (a & c) | (b & c)
        else:
            self.last_cout = 0

        # 3. Sequential evaluation (DFF clocked by lut_out)
        dff_out = self.dff.step(d=lut_out, clk=clk, ce=ce, srst=srst, arst=arst)

        # 4. Output multiplexer
        self.last_out = lut_out if self.bypass_ff else dff_out
        return self.last_out

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "ble_id": self.ble_id,
            "lut": self.lut.to_dict(),
            "dff": self.dff.to_dict(),
            "bypass_ff": self.bypass_ff,
            "carry_enable": self.carry_enable,
            "last_out": self.last_out,
            "last_cout": self.last_cout
        }

    def __repr__(self) -> str:
        mode = "COMB" if self.bypass_ff else "REG"
        return f"BLE(id={self.ble_id}, name='{self.name}', mode={mode}, mask=0x{self.lut.mask:04X})"
