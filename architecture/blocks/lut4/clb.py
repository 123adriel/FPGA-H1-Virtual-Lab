"""
Configurable Logic Block (CLB) - FPGA-H1 Virtual Lab
Cluster of 4 BLEs with fast carry chain and local interconnect.
"""

from typing import List, Dict, Any, Optional
from architecture.blocks.lut4.ble import BLE


class CLB:
    """
    CLB (Configurable Logic Block) containing 4 BLEs.
    
    Architecture:
    - 4x BLE (BLE_0, BLE_1, BLE_2, BLE_3)
    - Cascade carry chain: CIN -> BLE0 -> BLE1 -> BLE2 -> BLE3 -> COUT
    - 16 Inputs: 4 per BLE (can be routed externally or from internal feedback)
    - 4 Outputs: Y0, Y1, Y2, Y3
    """

    def __init__(self, name: str = "CLB", clb_id: int = 0):
        self.name = name
        self.clb_id = clb_id
        self.bles: List[BLE] = [
            BLE(name=f"{name}_BLE{i}", ble_id=clb_id * 4 + i) for i in range(4)
        ]
        self.last_outputs = [0, 0, 0, 0]
        self.last_cout = 0

    def configure_ble(
        self,
        index: int,
        mask: int,
        bypass_ff: bool = True,
        carry_enable: bool = False
    ) -> None:
        """Configures a specific BLE within this CLB."""
        if not (0 <= index < 4):
            raise IndexError(f"BLE index must be 0..3, got {index}")
        self.bles[index].lut.set_mask(mask)
        self.bles[index].bypass_ff = bypass_ff
        self.bles[index].carry_enable = carry_enable

    def eval(
        self,
        inputs: List[List[int]],
        clk: int = 0,
        ce: int = 1,
        srst: int = 0,
        arst: int = 0,
        cin: int = 0
    ) -> List[int]:
        """
        Evaluates the 4 BLEs in the CLB.
        inputs: List of 4 sublists, each containing 4 inputs [I0, I1, I2, I3] for that BLE.
        """
        if len(inputs) != 4:
            raise ValueError(f"CLB requires input list of length 4, got {len(inputs)}")

        carry = cin
        outputs = []
        for i in range(4):
            inp = inputs[i]
            y = self.bles[i].eval(
                i0=inp[0],
                i1=inp[1],
                i2=inp[2],
                i3=inp[3],
                clk=clk,
                ce=ce,
                srst=srst,
                arst=arst,
                cin=carry
            )
            outputs.append(y)
            if self.bles[i].carry_enable:
                carry = self.bles[i].last_cout

        self.last_outputs = outputs
        self.last_cout = carry
        return outputs

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "clb_id": self.clb_id,
            "bles": [b.to_dict() for b in self.bles],
            "outputs": self.last_outputs,
            "cout": self.last_cout
        }

    def __repr__(self) -> str:
        return f"CLB(id={self.clb_id}, name='{self.name}', bles=4)"
