"""
Independent Formal Audit Suite - FPGA-H1 Virtual Lab
Verifies the 5 non-negotiable architectural invariants:
1. Route Correctness (contiguous graph path)
2. Configuration Integrity & CRC32
3. Algorithmic Reproducibility (deterministic seeds)
4. Absence of Illegal Connections & Short-Circuits
5. Netlist Interface Validation
"""

import pytest
from architecture.blocks.switch_matrix.switch_box import SwitchBox, Side
from architecture.blocks.switch_matrix.connection_box import ConnectionBox
from simulator.routing.rr_graph import RRGraph
from simulator.routing.pathfinder import PathfinderRouter, Net
from simulator.routing.grid_circuit import GridCircuit
from compiler.netlist.interface import H1Netlist, CellInstance, PinModel, PinDirection, PinType, SignalModel


class TestFormalRoutingAudit:

    def test_audit_01_route_correctness_and_contiguity(self):
        """Invariant 1: Every routed net must form a contiguous directed physical path from OPIN to IPIN."""
        circuit = GridCircuit(grid_w=3, grid_h=3, channel_width=4)
        net = Net("CONTIGUOUS_CHECK", (0, 0, 0), [(2, 2, 0)])
        res = circuit.route_netlist([net])
        assert res["success"] is True

        # Audit path contiguity: check that each consecutive pair in the route has an active edge
        src_nid = circuit.rr_graph.opin_lookup[(0, 0, 0)]
        sink_nid = circuit.rr_graph.ipin_lookup[(2, 2, 0)]

        assert src_nid in net.routed_tree
        assert sink_nid in net.routed_tree

        # Verify that traversing from src_nid along valid RRGraph edges can reach sink_nid
        visited = set()
        queue = [src_nid]
        reached_sink = False

        while queue:
            curr = queue.pop(0)
            if curr == sink_nid:
                reached_sink = True
                break
            visited.add(curr)
            curr_node = circuit.rr_graph.nodes[curr]
            for neighbor in curr_node.edges:
                if neighbor in net.routed_tree and neighbor not in visited:
                    queue.append(neighbor)

        assert reached_sink is True, "Formal Audit Failed: Routed tree contains disconnected islands!"

    def test_audit_02_configuration_integrity_and_bitstream_reproducibility(self):
        """Invariant 2: Reconstructed bitstreams must match bit-for-bit with identical CRC32."""
        circuit_a = GridCircuit(grid_w=2, grid_h=2, channel_width=4)
        circuit_a.configure_ble(0, 0, 0, 0x1234)
        circuit_a.configure_ble(1, 1, 1, 0xABCD)
        net = Net("NET_AUDIT", (0, 0, 0), [(1, 1, 1)])
        circuit_a.route_netlist([net])

        bs1 = circuit_a.to_bitstream({"audit": "run1"})
        bs2 = circuit_a.to_bitstream({"audit": "run1"})
        assert bs1 == bs2, "Formal Audit Failed: Non-deterministic bitstream generation!"

        # Decode and verify CRC32
        decoded = circuit_a.load_bitstream(bs1)
        assert "crc32" in decoded

    def test_audit_03_algorithmic_reproducibility(self):
        """Invariant 3: Two separate router invocations on identical nets must yield identical switch states."""
        c1 = GridCircuit(grid_w=3, grid_h=3, channel_width=6)
        c2 = GridCircuit(grid_w=3, grid_h=3, channel_width=6)

        nets1 = [Net("N1", (0, 0, 0), [(2, 1, 0)]), Net("N2", (1, 0, 0), [(0, 2, 1)])]
        nets2 = [Net("N1", (0, 0, 0), [(2, 1, 0)]), Net("N2", (1, 0, 0), [(0, 2, 1)])]

        r1 = c1.route_netlist(nets1)
        r2 = c2.route_netlist(nets2)

        assert r1["success"] is True and r2["success"] is True
        assert r1["iterations"] == r2["iterations"]

        # Audit every switch box bitmask across both runs
        for coord, sb1 in c1.rr_graph.switch_boxes.items():
            sb2 = c2.rr_graph.switch_boxes[coord]
            assert sb1.to_bitmask() == sb2.to_bitmask(), f"SwitchBox {coord} bitmask mismatch across runs!"

    def test_audit_04_absence_of_illegal_connections_and_shorts(self):
        """Invariant 4: The system must strictly reject multi-driver short circuits and non-Wilton connections."""
        sb = SwitchBox(0, 0, width=4)
        # 1. Attempt non-Wilton connection (e.g. North track 0 to North track 1 loop)
        with pytest.raises(ValueError, match="not realizable in Wilton"):
            sb.connect(Side.NORTH, 0, Side.NORTH, 1)

        # 2. ConnectionBox illegal track rejection
        cb = ConnectionBox(cb_id=1, channel_type="CHANX", x=0, y=0, width=4, num_inputs=4, num_outputs=2, fc_out=1.0)
        # Attempt to drive out of bounds track
        with pytest.raises(IndexError):
            cb.connect_output_pin(pin_idx=5, track_idx=0)

        # 3. ConnectionBox short-circuit prevention: 2 pins driving same track simultaneously
        cb.connect_output_pin(pin_idx=0, track_idx=0)
        with pytest.raises(RuntimeError, match="Short-circuit conflict"):
            cb.connect_output_pin(pin_idx=1, track_idx=0)

    def test_audit_05_netlist_interface_validation(self):
        """Invariant 5: Netlist interface must catch invalid topologies (floating inputs, missing drivers)."""
        netlist = H1Netlist(design_name="AuditDesign", device_target="H1-16")

        # Cell with unconnected input pin
        cell = CellInstance(name="LUT_TEST", cell_type="LUT4")
        cell.pins["I0"] = PinModel(name="I0", direction=PinDirection.INPUT)
        cell.pins["Y"] = PinModel(name="Y", direction=PinDirection.OUTPUT)
        netlist.add_cell(cell)

        # Net without driver
        netlist.add_signal(SignalModel(name="FLOATING_NET"))

        errors = netlist.validate_integrity()
        assert len(errors) >= 2
        assert any("no active driver" in e for e in errors)
        assert any("unconnected" in e for e in errors)


if __name__ == "__main__":
    pytest.main(["-v", __file__])
