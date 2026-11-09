"""
Unit Tests for DFF and BLE - FPGA-H1 Virtual Lab
Verifies sequential state transitions, reset priority, and bypass multiplexer.
"""

import pytest
from architecture.blocks.flipflops.dff import DFF
from architecture.blocks.lut4.ble import BLE
from architecture.blocks.lut4.clb import CLB


class TestSequentialAndBLE:
    def test_dff_edge_triggering(self):
        dff = DFF(init_value=0)
        assert dff.q == 0

        # Clock stays low -> Q stays 0
        dff.step(d=1, clk=0)
        assert dff.q == 0

        # Rising edge (0 -> 1) -> captures D=1
        dff.step(d=1, clk=1)
        assert dff.q == 1

        # Clock stays high (no edge) -> holds Q=1 even if D changes to 0
        dff.step(d=0, clk=1)
        assert dff.q == 1

        # Clock falls (1 -> 0) -> no capture
        dff.step(d=0, clk=0)
        assert dff.q == 1

        # Rising edge with D=0 -> captures 0
        dff.step(d=0, clk=1)
        assert dff.q == 0

    def test_dff_async_reset_priority(self):
        dff = DFF(init_value=0)
        # Capture 1
        dff.step(d=1, clk=1)
        assert dff.q == 1

        # Async reset overrides everything, even on rising edge with D=1
        dff.step(d=1, clk=1, arst=1)
        assert dff.q == 0

    def test_dff_sync_reset(self):
        dff = DFF(init_value=0)
        dff.step(d=1, clk=1)
        assert dff.q == 1

        # Sync reset only takes effect on rising edge
        dff.step(d=1, clk=0, srst=1)
        assert dff.q == 1  # No edge yet!

        dff.step(d=1, clk=1, srst=1)
        assert dff.q == 0  # Cleared on edge

    def test_dff_clock_enable(self):
        dff = DFF(init_value=0)
        # Rising edge but CE=0 -> ignores D=1
        dff.step(d=1, clk=0)
        dff.step(d=1, clk=1, ce=0)
        assert dff.q == 0

        # Rising edge with CE=1 -> captures D=1
        dff.step(d=1, clk=0)
        dff.step(d=1, clk=1, ce=1)
        assert dff.q == 1

    def test_ble_combinational_vs_registered(self):
        # XOR gate mask 0x6666
        ble_comb = BLE(name="BLE_COMB", lut_mask=0x6666, bypass_ff=True)
        ble_reg = BLE(name="BLE_REG", lut_mask=0x6666, bypass_ff=False)

        # 1. Combinational BLE updates immediately without clock
        out_comb = ble_comb.eval(i0=1, i1=0, i2=0, i3=0, clk=0)
        assert out_comb == 1
        out_comb = ble_comb.eval(i0=1, i1=1, i2=0, i3=0, clk=0)
        assert out_comb == 0

        # 2. Registered BLE does not change until clock rising edge
        out_reg = ble_reg.eval(i0=1, i1=0, i2=0, i3=0, clk=0)
        assert out_reg == 0  # Initial DFF state is 0

        # Strobe clock high
        out_reg = ble_reg.eval(i0=1, i1=0, i2=0, i3=0, clk=1)
        assert out_reg == 1  # Captured!

    def test_clb_cluster_evaluation(self):
        clb = CLB(name="CLB_0", clb_id=0)
        # Configure BLE0 as AND (0x8888), BLE1 as OR (0xEEEE), BLE2 as XOR (0x6666), BLE3 as NOT_I0 (0x5555)
        clb.configure_ble(0, 0x8888)
        clb.configure_ble(1, 0xEEEE)
        clb.configure_ble(2, 0x6666)
        clb.configure_ble(3, 0x5555)

        inputs = [
            [1, 1, 0, 0],  # AND -> 1
            [0, 1, 0, 0],  # OR  -> 1
            [1, 1, 0, 0],  # XOR -> 0
            [0, 0, 0, 0]   # NOT -> 1
        ]
        outputs = clb.eval(inputs)
        assert outputs == [1, 1, 0, 1]


if __name__ == "__main__":
    pytest.main(["-v", __file__])
