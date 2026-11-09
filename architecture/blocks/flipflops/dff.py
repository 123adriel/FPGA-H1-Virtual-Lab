"""
D-Flip-Flop Architecture - FPGA-H1 Virtual Lab
Sequential storage element with async/sync reset and clock enable.
"""

from typing import Dict, Any


class DFF:
    """
    D-Type Flip-Flop with edge trigger, synchronous & asynchronous reset,
    and clock enable.
    
    Truth table on edge:
    - If ARST=1 -> Q = 0 (Async, independent of clock)
    - On CLK rising edge:
        - If SRST=1 -> Q = 0
        - Else If CE=1 -> Q = D
        - Else -> Q = Q (Hold)
    """

    __slots__ = ('name', 'dff_id', 'q', 'last_clk', 'invert_clk', 'init_value')

    def __init__(self, name: str = "DFF", dff_id: int = 0, init_value: int = 0, invert_clk: bool = False):
        self.name = name
        self.dff_id = dff_id
        self.init_value = init_value & 1
        self.q = self.init_value
        self.last_clk = 0
        self.invert_clk = invert_clk

    def reset_async(self) -> None:
        """Forces asynchronous reset immediately."""
        self.q = 0

    def step(self, d: int, clk: int, ce: int = 1, srst: int = 0, arst: int = 0) -> int:
        """
        Simulates one time step.
        Returns the current state Q.
        """
        d = d & 1
        clk = clk & 1
        ce = ce & 1
        srst = srst & 1
        arst = arst & 1

        # 1. Asynchronous reset has absolute priority
        if arst:
            self.q = 0
            self.last_clk = clk
            return self.q

        # 2. Clock edge detection
        effective_clk = (1 - clk) if self.invert_clk else clk
        rising_edge = (effective_clk == 1 and self.last_clk == 0)
        self.last_clk = effective_clk

        if rising_edge:
            if srst:
                self.q = 0
            elif ce:
                self.q = d

        return self.q

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "dff_id": self.dff_id,
            "q": self.q,
            "invert_clk": self.invert_clk,
            "init_value": self.init_value
        }

    def __repr__(self) -> str:
        return f"DFF(id={self.dff_id}, name='{self.name}', q={self.q})"
