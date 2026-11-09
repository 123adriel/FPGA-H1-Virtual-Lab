"""
Integrated Routed Grid Circuit - FPGA-H1 Virtual Lab
Simulates logic evaluation across physical Switch Boxes, Connection Boxes, and CLBs.
Supports full roundtrip serialization to H1BS bitstream.
"""

from typing import Dict, List, Tuple, Set, Any, Optional
from architecture.blocks.lut4.clb import CLB
from architecture.blocks.switch_matrix.switch_box import SwitchBox, Side
from architecture.blocks.switch_matrix.connection_box import ConnectionBox
from simulator.routing.rr_graph import RRGraph, NodeType
from simulator.routing.pathfinder import PathfinderRouter, Net
from simulator.routing.placement import PlacementEngine
from compiler.bitstream.bitstream_codec import BitstreamCodec


class GridCircuit:
    """
    Physical Island-Style FPGA Circuit Fabric.
    Integrates CLBs, SwitchBoxes, ConnectionBoxes, and signal evaluation across routed tracks.
    """

    def __init__(self, grid_w: int, grid_h: int, channel_width: int = 8):
        self.grid_w = grid_w
        self.grid_h = grid_h
        self.channel_width = channel_width
        self.clb_count = grid_w * grid_h

        # Instantiate CLBs at each (x, y)
        self.clbs: Dict[Tuple[int, int], CLB] = {}
        for y in range(grid_h):
            for x in range(grid_w):
                cid = y * grid_w + x
                self.clbs[(x, y)] = CLB(name=f"CLB_{x}_{y}", clb_id=cid)

        # Build physical RRGraph (contains all SwitchBoxes and ConnectionBoxes)
        self.rr_graph = RRGraph(grid_w, grid_h, channel_width)
        self.placed_nets: List[Net] = []

    def get_clb(self, x: int, y: int) -> CLB:
        return self.clbs[(x, y)]

    def configure_ble(
        self,
        x: int,
        y: int,
        ble_idx: int,
        mask: int,
        bypass_ff: bool = True,
        carry_enable: bool = False
    ) -> None:
        self.clbs[(x, y)].configure_ble(ble_idx, mask, bypass_ff, carry_enable)

    def route_netlist(self, nets: List[Net], max_iterations: int = 50) -> Dict[str, Any]:
        """Runs Pathfinder to route all nets on this physical grid."""
        router = PathfinderRouter(self.rr_graph, max_iterations=max_iterations)
        result = router.route(nets)
        if result["success"]:
            self.placed_nets = nets
        return result

    def to_bitstream(self, metadata: Optional[Dict[str, Any]] = None) -> bytes:
        """
        Serializes the entire state (all LUT4s, DFFs, SwitchBoxes, and ConnectionBoxes)
        into an official H1BS binary bitstream.
        """
        # 1. BLE configurations
        ble_configs = []
        for (x, y), clb in self.clbs.items():
            for i, ble in enumerate(clb.bles):
                ble_configs.append({
                    "id": ble.ble_id,
                    "mask": ble.lut.mask,
                    "bypass_ff": ble.bypass_ff,
                    "carry_enable": ble.carry_enable,
                    "invert_clk": ble.dff.invert_clk
                })

        # 2. Switch Box configurations
        sb_configs = []
        for (x, y), sb in self.rr_graph.switch_boxes.items():
            mask = sb.to_bitmask()
            if mask != 0:
                sb_configs.append({
                    "id": sb.sb_id,
                    "mask": mask
                })

        # 3. Connection Box configurations
        cb_configs = []
        for (x, y), cb in self.rr_graph.cb_x.items():
            mask = cb.to_bitmask()
            if mask != 0:
                cb_configs.append({"id": cb.cb_id, "mask": mask})

        for (x, y), cb in self.rr_graph.cb_y.items():
            mask = cb.to_bitmask()
            if mask != 0:
                cb_configs.append({"id": cb.cb_id, "mask": mask})

        total_luts = self.clb_count * 4
        meta = metadata or {
            "grid_w": self.grid_w,
            "grid_h": self.grid_h,
            "channel_width": self.channel_width,
            "active_nets": len(self.placed_nets)
        }

        return BitstreamCodec.encode(
            num_luts=total_luts,
            ble_configs=ble_configs,
            metadata=meta,
            sb_configs=sb_configs,
            cb_configs=cb_configs
        )

    def load_bitstream(self, data: bytes) -> Dict[str, Any]:
        """
        Reconstructs all LUTs, DFFs, SwitchBoxes, and ConnectionBoxes from a binary bitstream.
        Verifies CRC32 integrity.
        """
        decoded = BitstreamCodec.decode(data)

        # Restore BLEs
        for bcfg in decoded["bles"]:
            ble_id = bcfg["id"]
            # Map ble_id back to clb (x, y) and ble_idx
            clb_id = ble_id // 4
            ble_idx = ble_id % 4
            x = clb_id % self.grid_w
            y = clb_id // self.grid_w
            if (x, y) in self.clbs:
                self.configure_ble(
                    x=x,
                    y=y,
                    ble_idx=ble_idx,
                    mask=bcfg["mask"],
                    bypass_ff=bcfg["bypass_ff"],
                    carry_enable=bcfg["carry_enable"]
                )

        # Restore Switch Boxes
        sb_by_id = {sb.sb_id: sb for sb in self.rr_graph.switch_boxes.values()}
        for sb_cfg in decoded.get("switch_boxes", []):
            sbid = sb_cfg["id"]
            if sbid in sb_by_id:
                sb_by_id[sbid].from_bitmask(sb_cfg["mask"])

        # Restore Connection Boxes
        cb_by_id = {cb.cb_id: cb for cb in self.rr_graph.cb_x.values()}
        cb_by_id.update({cb.cb_id: cb for cb in self.rr_graph.cb_y.values()})
        for cb_cfg in decoded.get("connection_boxes", []):
            cbid = cb_cfg["id"]
            if cbid in cb_by_id:
                cb_by_id[cbid].from_bitmask(cb_cfg["mask"])

        return decoded
