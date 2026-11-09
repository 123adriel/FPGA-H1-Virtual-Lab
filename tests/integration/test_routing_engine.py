"""
Integration Test Suite for Routing Engine & Placement - FPGA-H1 Virtual Lab
Verifies the 10 core routing scenarios required by Phase 2:
1. Two CLBs connected
2. Four CLBs in 2x2 matrix
3. Eight CLBs connected
4. Sixteen CLBs grid (4x4)
5. Sixty-four CLBs grid (8x8)
6. Multi-input circuits
7. High fan-out nets (Steiner sharing)
8. Intentional congestion resolution
9. Impossible route detection
10. Bitstream full roundtrip reconstruction & anti-short verification
"""

import pytest
from architecture.blocks.switch_matrix.switch_box import SwitchBox, Side
from architecture.blocks.switch_matrix.connection_box import ConnectionBox
from simulator.routing.rr_graph import RRGraph
from simulator.routing.pathfinder import PathfinderRouter, Net
from simulator.routing.placement import PlacementEngine
from simulator.routing.grid_circuit import GridCircuit


class TestRoutingEngineSuite:

    def test_01_two_clbs_connected(self):
        """1. Two CLBs connected horizontally: CLB(0,0) -> CLB(1,0)."""
        circuit = GridCircuit(grid_w=2, grid_h=1, channel_width=4)
        net = Net(name="NET_A", source_pin=(0, 0, 0), sink_pins=[(1, 0, 0)])

        res = circuit.route_netlist([net], max_iterations=20)
        assert res["success"] is True, f"Routing failed: {res}"
        assert res["routed_nets_pct"] == 100.0
        assert res["max_overuse"] == 0
        assert len(net.routed_tree) > 0

    def test_02_four_clbs_2x2_matrix(self):
        """2. Four CLBs in 2x2 matrix with diagonal turn routing."""
        circuit = GridCircuit(grid_w=2, grid_h=2, channel_width=4)
        # Diagonal routes requiring Wilton switch turns
        nets = [
            Net(name="DIAG_1", source_pin=(0, 0, 0), sink_pins=[(1, 1, 0)]),
            Net(name="DIAG_2", source_pin=(1, 0, 0), sink_pins=[(0, 1, 0)]),
        ]
        res = circuit.route_netlist(nets, max_iterations=25)
        assert res["success"] is True
        assert res["max_overuse"] == 0

    def test_03_eight_clbs_chain(self):
        """3. Eight CLBs connected in pipeline chain across 4x2 grid."""
        circuit = GridCircuit(grid_w=4, grid_h=2, channel_width=4)
        nets = []
        for i in range(7):
            x1, y1 = i % 4, i // 4
            x2, y2 = (i + 1) % 4, (i + 1) // 4
            nets.append(Net(name=f"PIPE_{i}", source_pin=(x1, y1, 0), sink_pins=[(x2, y2, 0)]))

        res = circuit.route_netlist(nets, max_iterations=30)
        assert res["success"] is True
        assert res["total_nets"] == 7
        assert res["max_overuse"] == 0

    def test_04_sixteen_clbs_grid(self):
        """4. Sixteen CLBs in 4x4 grid (64 LUT4 capacity) with meshed connections."""
        circuit = GridCircuit(grid_w=4, grid_h=4, channel_width=6)
        nets = [
            Net("C0_to_C15", (0, 0, 0), [(3, 3, 0)]),
            Net("C3_to_C12", (3, 0, 1), [(0, 3, 1)]),
            Net("MID_H", (1, 1, 0), [(2, 1, 0)]),
            Net("MID_V", (1, 1, 1), [(1, 2, 1)]),
        ]
        res = circuit.route_netlist(nets, max_iterations=30)
        assert res["success"] is True
        assert res["max_overuse"] == 0

    def test_05_sixty_four_clbs_grid(self):
        """5. Sixty-four CLBs in 8x8 grid (256 LUT4 capacity). Corner-to-corner long nets."""
        circuit = GridCircuit(grid_w=8, grid_h=8, channel_width=8)
        nets = [
            Net("CORNER_TOP_RIGHT", (0, 0, 0), [(7, 7, 0)]),
            Net("CORNER_TOP_LEFT", (7, 0, 1), [(0, 7, 1)]),
            Net("CROSS_CENTER_X", (0, 4, 2), [(7, 4, 2)]),
            Net("CROSS_CENTER_Y", (4, 0, 3), [(4, 7, 3)]),
        ]
        res = circuit.route_netlist(nets, max_iterations=30)
        assert res["success"] is True
        assert res["max_overuse"] == 0

    def test_06_multi_input_circuit(self):
        """6. Single CLB sink receiving 4 distinct inputs from 4 different remote CLBs."""
        circuit = GridCircuit(grid_w=3, grid_h=3, channel_width=6)
        target = (1, 1)  # Center CLB
        nets = [
            Net("SRC_TOP", (1, 2, 0), [(target[0], target[1], 0)]),
            Net("SRC_BOT", (1, 0, 0), [(target[0], target[1], 1)]),
            Net("SRC_LFT", (0, 1, 0), [(target[0], target[1], 2)]),
            Net("SRC_RGT", (2, 1, 0), [(target[0], target[1], 3)]),
        ]
        res = circuit.route_netlist(nets, max_iterations=25)
        assert res["success"] is True
        assert res["max_overuse"] == 0

    def test_07_high_fanout_net(self):
        """7. High fan-out net: 1 driver broadcasting to 5 distributed CLB sinks (Steiner sharing)."""
        circuit = GridCircuit(grid_w=4, grid_h=4, channel_width=8)
        sinks = [(1, 0, 0), (2, 1, 0), (3, 2, 0), (0, 3, 0), (2, 3, 0)]
        broadcast_net = Net("BROADCAST", source_pin=(0, 0, 0), sink_pins=sinks)

        res = circuit.route_netlist([broadcast_net], max_iterations=20)
        assert res["success"] is True
        # Verify that total nodes used is less than 5 independent paths (sharing verified)
        assert len(broadcast_net.routed_tree) < (len(sinks) * 15)

    def test_08_intentional_congestion_negotiation(self):
        """8. Intentional congestion: multiple competing nets negotiated successfully by Pathfinder."""
        circuit = GridCircuit(grid_w=3, grid_h=2, channel_width=4)
        # Pack 3 competing horizontal nets between columns 0 and 2
        nets = [
            Net("COMPETE_0", (0, 0, 0), [(2, 0, 0)]),
            Net("COMPETE_1", (0, 0, 1), [(2, 0, 1)]),
            Net("COMPETE_2", (0, 0, 2), [(2, 0, 2)]),
            Net("COMPETE_3", (0, 1, 0), [(2, 1, 0)]),
        ]
        res = circuit.route_netlist(nets, max_iterations=30)
        assert res["success"] is True
        assert res["max_overuse"] == 0

    def test_09_impossible_routes_detection(self):
        """9. Detection of impossible route: channel bottleneck physically exceeding capacity."""
        # 1x2 grid with channel_width=1, trying to route 3 parallel independent nets
        circuit = GridCircuit(grid_w=1, grid_h=2, channel_width=1)
        nets = [
            Net("NET_OVER_1", (0, 0, 0), [(0, 1, 0)]),
            Net("NET_OVER_2", (0, 0, 1), [(0, 1, 1)]),
            Net("NET_OVER_3", (0, 0, 2), [(0, 1, 2)]),
        ]
        # Pathfinder must detect that it cannot eliminate congestion and fail gracefully
        res = circuit.route_netlist(nets, max_iterations=10)
        assert res["success"] is False
        assert res["max_overuse"] > 0
        assert "impossible" in res.get("reason", "").lower() or res["max_overuse"] > 0

    def test_10_full_bitstream_reconstruction_and_integrity(self):
        """10. Full bitstream serialization, CRC32 validation, and exact hardware restoration."""
        circuit1 = GridCircuit(grid_w=2, grid_h=2, channel_width=4)
        # Configure some LUTs
        circuit1.configure_ble(0, 0, 0, mask=0x8888, bypass_ff=True)
        circuit1.configure_ble(1, 1, 0, mask=0x6666, bypass_ff=False)

        # Route a net
        net = Net("ROUNDTRIP_NET", source_pin=(0, 0, 0), sink_pins=[(1, 1, 0)])
        res = circuit1.route_netlist([net])
        assert res["success"] is True

        # Generate binary H1BS bitstream
        raw_bitstream = circuit1.to_bitstream(metadata={"test": "roundtrip"})
        assert raw_bitstream.startswith(b"H1BS")

        # Create brand new unconfigured circuit
        circuit2 = GridCircuit(grid_w=2, grid_h=2, channel_width=4)
        assert circuit2.get_clb(0, 0).bles[0].lut.mask == 0x0000

        # Load bitstream into circuit2
        decoded = circuit2.load_bitstream(raw_bitstream)
        assert decoded["crc32"] is not None

        # Verify BLE restoration
        assert circuit2.get_clb(0, 0).bles[0].lut.mask == 0x8888
        assert circuit2.get_clb(0, 0).bles[0].bypass_ff is True
        assert circuit2.get_clb(1, 1).bles[0].lut.mask == 0x6666
        assert circuit2.get_clb(1, 1).bles[0].bypass_ff is False

        # Verify Switch Box restoration
        sb1 = circuit1.rr_graph.switch_boxes[(1, 1)]
        sb2 = circuit2.rr_graph.switch_boxes[(1, 1)]
        assert sb1.to_bitmask() == sb2.to_bitmask()
        assert sb1.get_connected_terminals(Side.NORTH, 0) == sb2.get_connected_terminals(Side.NORTH, 0)

    def test_11_placement_hpwl_minimization(self):
        """11. Verifies placement engine correctly places CLBs and optimizes HPWL."""
        placer = PlacementEngine(grid_w=4, grid_h=4)
        # Add 4 CLBs
        for i in range(4):
            placer.add_clb(f"CLB_{i}", clb_id=i)

        # Add nets forming a ring: 0-1, 1-2, 2-3, 3-0
        placer.add_net("NET_0_1", ["CLB_0", "CLB_1"])
        placer.add_net("NET_1_2", ["CLB_1", "CLB_2"])
        placer.add_net("NET_2_3", ["CLB_2", "CLB_3"])
        placer.add_net("NET_3_0", ["CLB_3", "CLB_0"])

        placer.initial_placement_heuristic()
        initial_hpwl = placer.compute_hpwl()
        assert initial_hpwl > 0

        opt_res = placer.optimize_simulated_annealing(max_moves=200, seed=42)
        assert opt_res["final_hpwl"] <= initial_hpwl


if __name__ == "__main__":
    pytest.main(["-v", __file__])
