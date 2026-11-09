"""
Routing Resource Graph (RR-Graph) - FPGA-H1 Virtual Lab
Represents physical routing tracks, CLB pins, switch boxes, and connection boxes as a directed graph.
"""

from enum import IntEnum
from typing import Dict, List, Set, Tuple, Optional, Any
from architecture.blocks.switch_matrix.switch_box import SwitchBox, Side
from architecture.blocks.switch_matrix.connection_box import ConnectionBox


class NodeType(IntEnum):
    SOURCE = 0
    SINK = 1
    OPIN = 2
    IPIN = 3
    CHANX = 4
    CHANY = 5


class RRNode:
    """A physical routing node (track, pin, or virtual source/sink)."""

    __slots__ = (
        'node_id', 'node_type', 'x', 'y', 'track_or_pin',
        'capacity', 'occ', 'historical_cost', 'base_cost',
        'edges', 'edge_switches'
    )

    def __init__(
        self,
        node_id: int,
        node_type: NodeType,
        x: int,
        y: int,
        track_or_pin: int,
        capacity: int = 1,
        base_cost: float = 1.0
    ):
        self.node_id = node_id
        self.node_type = node_type
        self.x = x
        self.y = y
        self.track_or_pin = track_or_pin
        self.capacity = capacity
        self.occ = 0
        self.historical_cost = 0.0
        self.base_cost = base_cost
        # Outgoing edges: target_node_id -> edge_cost
        self.edges: Dict[int, float] = {}
        # Associated physical switch info if any
        self.edge_switches: Dict[int, Any] = {}

    def add_edge(self, target_id: int, cost: float = 1.0, switch_info: Any = None) -> None:
        self.edges[target_id] = cost
        if switch_info is not None:
            self.edge_switches[target_id] = switch_info

    def get_cost(self, pres_fac: float) -> float:
        """
        Calculates total cost of this node in Pathfinder:
        cost = (base_cost + historical_cost) * present_congestion_factor
        """
        overuse = max(0, self.occ - self.capacity)
        pres_penalty = 1.0 + (overuse * pres_fac)
        return (self.base_cost + self.historical_cost) * pres_penalty

    def __repr__(self) -> str:
        return f"RRNode({self.node_id}, {self.node_type.name}, at=({self.x},{self.y}), tp={self.track_or_pin})"


class RRGraph:
    """
    Routing Resource Graph generator for Island-Style FPGA grid.
    Grid size: grid_w x grid_h CLBs.
    Channel track width: W.
    """

    def __init__(self, grid_w: int, grid_h: int, channel_width: int = 8):
        self.grid_w = grid_w
        self.grid_h = grid_h
        self.channel_width = channel_width

        self.nodes: Dict[int, RRNode] = {}
        self._next_node_id = 0

        # Fast lookup tables:
        # (x, y, pin) -> node_id
        self.opin_lookup: Dict[Tuple[int, int, int], int] = {}
        self.ipin_lookup: Dict[Tuple[int, int, int], int] = {}
        # (x, y, track) -> node_id
        self.chanx_lookup: Dict[Tuple[int, int, int], int] = {}
        self.chany_lookup: Dict[Tuple[int, int, int], int] = {}

        # Physical switch boxes and connection boxes
        self.switch_boxes: Dict[Tuple[int, int], SwitchBox] = {}
        self.cb_x: Dict[Tuple[int, int], ConnectionBox] = {}
        self.cb_y: Dict[Tuple[int, int], ConnectionBox] = {}

        self._build_graph()

    def _alloc_node(
        self,
        node_type: NodeType,
        x: int,
        y: int,
        track_or_pin: int,
        capacity: int = 1,
        base_cost: float = 1.0
    ) -> RRNode:
        nid = self._next_node_id
        self._next_node_id += 1
        node = RRNode(nid, node_type, x, y, track_or_pin, capacity, base_cost)
        self.nodes[nid] = node
        return node

    def _build_graph(self) -> None:
        """Constructs the full island-style routing graph."""
        W = self.channel_width

        # 1. Allocate Pins for each CLB: 16 inputs (4 BLEs * 4 inputs), 4 outputs (4 BLEs * 1 output)
        for x in range(self.grid_w):
            for y in range(self.grid_h):
                for p in range(4):
                    # OPIN base_cost slightly lower to encourage direct starts
                    node = self._alloc_node(NodeType.OPIN, x, y, p, capacity=1, base_cost=0.5)
                    self.opin_lookup[(x, y, p)] = node.node_id
                for p in range(16):
                    node = self._alloc_node(NodeType.IPIN, x, y, p, capacity=1, base_cost=0.5)
                    self.ipin_lookup[(x, y, p)] = node.node_id

        # 2. Allocate Channel Segments
        # Horizontal channels CHANX: grid_w segments x (grid_h + 1) rows
        for y in range(self.grid_h + 1):
            for x in range(self.grid_w):
                for t in range(W):
                    node = self._alloc_node(NodeType.CHANX, x, y, t, capacity=1, base_cost=1.0)
                    self.chanx_lookup[(x, y, t)] = node.node_id

        # Vertical channels CHANY: (grid_w + 1) columns x grid_h segments
        for x in range(self.grid_w + 1):
            for y in range(self.grid_h):
                for t in range(W):
                    node = self._alloc_node(NodeType.CHANY, x, y, t, capacity=1, base_cost=1.0)
                    self.chany_lookup[(x, y, t)] = node.node_id

        # 3. Instantiate Switch Boxes at grid intersections: (grid_w + 1) x (grid_h + 1)
        for x in range(self.grid_w + 1):
            for y in range(self.grid_h + 1):
                sb = SwitchBox(x, y, width=W)
                self.switch_boxes[(x, y)] = sb

                # Connect Wilton switches inside Switch Box
                # Terminal mapping:
                # NORTH track t -> CHANY(x, y, t) if y < grid_h
                # SOUTH track t -> CHANY(x, y - 1, t) if y > 0
                # EAST track t  -> CHANX(x, y, t) if x < grid_w
                # WEST track t  -> CHANX(x - 1, y, t) if x > 0

                term_to_node = {}
                for t in range(W):
                    if y < self.grid_h and (x, y, t) in self.chany_lookup:
                        term_to_node[(Side.NORTH, t)] = self.chany_lookup[(x, y, t)]
                    if y > 0 and (x, y - 1, t) in self.chany_lookup:
                        term_to_node[(Side.SOUTH, t)] = self.chany_lookup[(x, y - 1, t)]
                    if x < self.grid_w and (x, y, t) in self.chanx_lookup:
                        term_to_node[(Side.EAST, t)] = self.chanx_lookup[(x, y, t)]
                    if x > 0 and (x - 1, y, t) in self.chanx_lookup:
                        term_to_node[(Side.WEST, t)] = self.chanx_lookup[(x - 1, y, t)]

                # Add bidirectional edges for each allowed Wilton switch
                for s1, t1, s2, t2 in sb._allowed_switches:
                    n1 = term_to_node.get((s1, t1))
                    n2 = term_to_node.get((s2, t2))
                    if n1 is not None and n2 is not None and n1 != n2:
                        sw_meta = {"type": "SB", "sb": sb, "s1": s1, "t1": t1, "s2": s2, "t2": t2}
                        self.nodes[n1].add_edge(n2, cost=1.0, switch_info=sw_meta)
                        self.nodes[n2].add_edge(n1, cost=1.0, switch_info=sw_meta)

        # 4. Connection Boxes (CB)
        # Connect CLB pins to adjacent CHANX and CHANY
        for x in range(self.grid_w):
            for y in range(self.grid_h):
                # Horizontal Connection Box (CLB (x, y) with CHANX(x, y) and CHANX(x, y+1))
                cbx = ConnectionBox(
                    cb_id=((x << 8) | y),
                    channel_type="CHANX",
                    x=x,
                    y=y,
                    width=W,
                    num_inputs=16,
                    num_outputs=4,
                    fc_in=0.5,
                    fc_out=0.5
                )
                self.cb_x[(x, y)] = cbx

                # Wire OPINs to adjacent CHANX
                for opin_idx, tracks in cbx.allowed_output_tracks.items():
                    opin_node_id = self.opin_lookup[(x, y, opin_idx)]
                    for t in tracks:
                        if (x, y, t) in self.chanx_lookup:
                            target_nid = self.chanx_lookup[(x, y, t)]
                            meta = {"type": "CB_OUT", "cb": cbx, "pin": opin_idx, "track": t}
                            self.nodes[opin_node_id].add_edge(target_nid, cost=0.8, switch_info=meta)

                # Wire CHANX to IPINs
                for ipin_idx, tracks in cbx.allowed_input_tracks.items():
                    ipin_node_id = self.ipin_lookup[(x, y, ipin_idx)]
                    for t in tracks:
                        if (x, y, t) in self.chanx_lookup:
                            src_nid = self.chanx_lookup[(x, y, t)]
                            meta = {"type": "CB_IN", "cb": cbx, "pin": ipin_idx, "track": t}
                            self.nodes[src_nid].add_edge(ipin_node_id, cost=0.8, switch_info=meta)

                # Vertical Connection Box
                cby = ConnectionBox(
                    cb_id=((x << 8) | (y + 128)),
                    channel_type="CHANY",
                    x=x,
                    y=y,
                    width=W,
                    num_inputs=16,
                    num_outputs=4,
                    fc_in=0.5,
                    fc_out=0.5
                )
                self.cb_y[(x, y)] = cby

                # Wire OPINs to adjacent CHANY
                for opin_idx, tracks in cby.allowed_output_tracks.items():
                    opin_node_id = self.opin_lookup[(x, y, opin_idx)]
                    for t in tracks:
                        if (x, y, t) in self.chany_lookup:
                            target_nid = self.chany_lookup[(x, y, t)]
                            meta = {"type": "CB_OUT", "cb": cby, "pin": opin_idx, "track": t}
                            self.nodes[opin_node_id].add_edge(target_nid, cost=0.8, switch_info=meta)

                # Wire CHANY to IPINs
                for ipin_idx, tracks in cby.allowed_input_tracks.items():
                    ipin_node_id = self.ipin_lookup[(x, y, ipin_idx)]
                    for t in tracks:
                        if (x, y, t) in self.chany_lookup:
                            src_nid = self.chany_lookup[(x, y, t)]
                            meta = {"type": "CB_IN", "cb": cby, "pin": ipin_idx, "track": t}
                            self.nodes[src_nid].add_edge(ipin_node_id, cost=0.8, switch_info=meta)

    def reset_occupancies(self) -> None:
        """Clears usage for all nodes."""
        for n in self.nodes.values():
            n.occ = 0
            n.historical_cost = 0.0

    def get_summary(self) -> Dict[str, Any]:
        return {
            "grid_w": self.grid_w,
            "grid_h": self.grid_h,
            "channel_width": self.channel_width,
            "total_nodes": len(self.nodes),
            "total_switch_boxes": len(self.switch_boxes),
            "total_connection_boxes": len(self.cb_x) + len(self.cb_y),
            "clb_count": self.grid_w * self.grid_h,
            "lut4_capacity": self.grid_w * self.grid_h * 4
        }
