"""
Switch Box Architecture - FPGA-H1 Virtual Lab
Wilton Topology Switch Box (Fs = 3) for Island-Style FPGA routing.
"""

from enum import Enum
from typing import Dict, List, Tuple, Set, Any, Optional


class Side(str, Enum):
    NORTH = "NORTH"
    SOUTH = "SOUTH"
    EAST = "EAST"
    WEST = "WEST"

    @classmethod
    def opposite(cls, side: "Side") -> "Side":
        mapping = {
            cls.NORTH: cls.SOUTH,
            cls.SOUTH: cls.NORTH,
            cls.EAST: cls.WEST,
            cls.WEST: cls.EAST
        }
        return mapping[side]


class SwitchBox:
    """
    Switch Box with Wilton topology (Fs = 3).
    Located at grid intersection (x, y).
    
    Channels:
    - NORTH: connects to vertical channel track t
    - SOUTH: connects to vertical channel track t
    - EAST:  connects to horizontal channel track t
    - WEST:  connects to horizontal channel track t
    
    Wilton Topology:
    For track t in 0..W-1:
      1. Straight:
         - N(t) <-> S(t)
         - E(t) <-> W(t)
      2. Diagonal / Turns:
         - N(t) <-> W((t + 1) % W)
         - N(t) <-> E((t + W - 1) % W)
         - S(t) <-> W((t + W - 1) % W)
         - S(t) <-> E((t + 1) % W)
    """

    __slots__ = ('x', 'y', 'width', 'sb_id', '_active_switches', '_allowed_switches', '_switch_to_idx')

    def __init__(self, x: int, y: int, width: int = 8, sb_id: Optional[int] = None):
        self.x = x
        self.y = y
        self.width = width
        self.sb_id = sb_id if sb_id is not None else ((x << 8) | y)

        # Precompute allowed Wilton connections
        self._allowed_switches: Set[Tuple[Side, int, Side, int]] = set()
        self._switch_to_idx: Dict[Tuple[Side, int, Side, int], int] = {}
        self._build_wilton_topology()

        # Active switches: set of canonical tuples (side1, track1, side2, track2)
        self._active_switches: Set[Tuple[Side, int, Side, int]] = set()

    def _canonical(self, s1: Side, t1: int, s2: Side, t2: int) -> Tuple[Side, int, Side, int]:
        """Ensures consistent ordering for switch pairs so (A, B) == (B, A)."""
        if (s1.value, t1) <= (s2.value, t2):
            return (s1, t1, s2, t2)
        return (s2, t2, s1, t1)

    def _build_wilton_topology(self) -> None:
        """Precomputes all valid Wilton switch connections and assigns them a deterministic bit index."""
        W = self.width
        switches = []

        for t in range(W):
            # 1. Straight
            switches.append(self._canonical(Side.NORTH, t, Side.SOUTH, t))
            switches.append(self._canonical(Side.EAST, t, Side.WEST, t))

            # 2. Turns
            switches.append(self._canonical(Side.NORTH, t, Side.WEST, (t + 1) % W))
            switches.append(self._canonical(Side.NORTH, t, Side.EAST, (t + W - 1) % W))
            switches.append(self._canonical(Side.SOUTH, t, Side.WEST, (t + W - 1) % W))
            switches.append(self._canonical(Side.SOUTH, t, Side.EAST, (t + 1) % W))

        # Deduplicate while preserving order
        seen = set()
        idx = 0
        for sw in switches:
            if sw not in seen:
                seen.add(sw)
                self._allowed_switches.add(sw)
                self._switch_to_idx[sw] = idx
                idx += 1

    @property
    def total_switches(self) -> int:
        """Total number of programmable switch points in this Wilton box."""
        return len(self._allowed_switches)

    def is_allowed(self, s1: Side, t1: int, s2: Side, t2: int) -> bool:
        """Checks if a connection is physically realizable under the Wilton topology."""
        return self._canonical(s1, t1, s2, t2) in self._allowed_switches

    def connect(self, s1: Side, t1: int, s2: Side, t2: int) -> None:
        """Activates a switch connection between two terminal tracks."""
        if not (0 <= t1 < self.width and 0 <= t2 < self.width):
            raise IndexError(f"Track out of bounds: t1={t1}, t2={t2}, width={self.width}")
        pair = self._canonical(s1, t1, s2, t2)
        if pair not in self._allowed_switches:
            raise ValueError(
                f"Connection {s1.value}[{t1}] <-> {s2.value}[{t2}] is not realizable in Wilton topology (width={self.width})"
            )
        self._active_switches.add(pair)

    def disconnect(self, s1: Side, t1: int, s2: Side, t2: int) -> None:
        """Deactivates a switch connection."""
        pair = self._canonical(s1, t1, s2, t2)
        self._active_switches.discard(pair)

    def is_connected(self, s1: Side, t1: int, s2: Side, t2: int) -> bool:
        """Checks whether a specific connection is active."""
        return self._canonical(s1, t1, s2, t2) in self._active_switches

    def get_connected_terminals(self, side: Side, track: int) -> List[Tuple[Side, int]]:
        """Returns all terminals connected to a given (side, track)."""
        terminals = []
        for s1, t1, s2, t2 in self._active_switches:
            if s1 == side and t1 == track:
                terminals.append((s2, t2))
            elif s2 == side and t2 == track:
                terminals.append((s1, t1))
        return terminals

    def clear(self) -> None:
        """Opens all switches."""
        self._active_switches.clear()

    def to_bitmask(self) -> int:
        """Encodes active switches into an exact integer bitmask for H1BS bitstream serialization."""
        mask = 0
        for sw in self._active_switches:
            idx = self._switch_to_idx[sw]
            mask |= (1 << idx)
        return mask

    def from_bitmask(self, mask: int) -> None:
        """Restores active switches from a bitmask."""
        self.clear()
        for sw, idx in self._switch_to_idx.items():
            if (mask >> idx) & 1:
                self._active_switches.add(sw)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "x": self.x,
            "y": self.y,
            "sb_id": self.sb_id,
            "width": self.width,
            "total_switches": self.total_switches,
            "active_switches_count": len(self._active_switches),
            "bitmask_hex": hex(self.to_bitmask()),
            "connections": [
                {"s1": s1.value, "t1": t1, "s2": s2.value, "t2": t2}
                for s1, t1, s2, t2 in self._active_switches
            ]
        }

    def __repr__(self) -> str:
        return f"SwitchBox({self.x}, {self.y}, W={self.width}, active={len(self._active_switches)}/{self.total_switches})"
