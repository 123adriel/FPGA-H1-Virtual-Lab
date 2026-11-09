"""
Unit Tests for LUT4 Core - FPGA-H1 Virtual Lab
Exhaustive verification of truth tables, minterms, and canonical gates.
"""

import pytest
import random
from architecture.blocks.lut4.lut4_core import LUT4


class TestLUT4Core:
    def test_zero_and_one_constants(self):
        lut_zero = LUT4(initial_mask=0x0000)
        lut_one = LUT4(initial_mask=0xFFFF)
        for i in range(16):
            i0, i1, i2, i3 = (i & 1), (i >> 1) & 1, (i >> 2) & 1, (i >> 3) & 1
            assert lut_zero.eval(i0, i1, i2, i3) == 0
            assert lut_one.eval(i0, i1, i2, i3) == 1

    def test_buffers(self):
        lut_i0 = LUT4(initial_mask=0xAAAA)
        lut_i1 = LUT4(initial_mask=0xCCCC)
        lut_i2 = LUT4(initial_mask=0xF0F0)
        lut_i3 = LUT4(initial_mask=0xFF00)
        for i in range(16):
            i0, i1, i2, i3 = (i & 1), (i >> 1) & 1, (i >> 2) & 1, (i >> 3) & 1
            assert lut_i0.eval(i0, i1, i2, i3) == i0
            assert lut_i1.eval(i0, i1, i2, i3) == i1
            assert lut_i2.eval(i0, i1, i2, i3) == i2
            assert lut_i3.eval(i0, i1, i2, i3) == i3

    def test_standard_gates_i0_i1(self):
        and_lut = LUT4(initial_mask=0x8888)
        or_lut = LUT4(initial_mask=0xEEEE)
        xor_lut = LUT4(initial_mask=0x6666)
        nand_lut = LUT4(initial_mask=0x7777)
        nor_lut = LUT4(initial_mask=0x1111)
        xnor_lut = LUT4(initial_mask=0x9999)

        for i in range(16):
            i0, i1, i2, i3 = (i & 1), (i >> 1) & 1, (i >> 2) & 1, (i >> 3) & 1
            assert and_lut.eval(i0, i1, i2, i3) == (i0 & i1)
            assert or_lut.eval(i0, i1, i2, i3) == (i0 | i1)
            assert xor_lut.eval(i0, i1, i2, i3) == (i0 ^ i1)
            assert nand_lut.eval(i0, i1, i2, i3) == (1 - (i0 & i1))
            assert nor_lut.eval(i0, i1, i2, i3) == (1 - (i0 | i1))
            assert xnor_lut.eval(i0, i1, i2, i3) == (1 - (i0 ^ i1))

    def test_full_adder_sum_and_carry(self):
        # Full adder with I0=A, I1=B, I2=Cin
        # SUM = A ^ B ^ Cin -> mask 0x9696
        # CARRY = (A & B) | (Cin & (A ^ B)) -> mask 0xE8E8
        sum_lut = LUT4(initial_mask=0x9696)
        carry_lut = LUT4(initial_mask=0xE8E8)

        for a in [0, 1]:
            for b in [0, 1]:
                for cin in [0, 1]:
                    for dummy_i3 in [0, 1]:
                        s = sum_lut.eval(a, b, cin, dummy_i3)
                        c = carry_lut.eval(a, b, cin, dummy_i3)
                        expected_sum = (a + b + cin) & 1
                        expected_carry = (a + b + cin) >> 1
                        assert s == expected_sum, f"SUM mismatch for a={a}, b={b}, cin={cin}"
                        assert c == expected_carry, f"CARRY mismatch for a={a}, b={b}, cin={cin}"

    def test_mux2_logic(self):
        # MUX 2:1 with I0=D0, I1=D1, I2=SEL
        # Y = D1 if SEL else D0 -> mask 0xCACA
        mux_lut = LUT4(initial_mask=0xCACA)
        for d0 in [0, 1]:
            for d1 in [0, 1]:
                for sel in [0, 1]:
                    for i3 in [0, 1]:
                        out = mux_lut.eval(d0, d1, sel, i3)
                        expected = d1 if sel else d0
                        assert out == expected

    def test_exhaustive_minterm_isolation(self):
        """
        Verify that for every minterm k in 0..15,
        a mask with only bit k set produces 1 IF AND ONLY IF inputs equal minterm k.
        """
        for k in range(16):
            single_bit_mask = 1 << k
            lut = LUT4(initial_mask=single_bit_mask)
            for idx in range(16):
                i0, i1, i2, i3 = (idx & 1), (idx >> 1) & 1, (idx >> 2) & 1, (idx >> 3) & 1
                out = lut.eval(i0, i1, i2, i3)
                if idx == k:
                    assert out == 1, f"Minterm {k} failed to activate on matching inputs"
                else:
                    assert out == 0, f"Minterm {k} falsely activated on input {idx}"

    def test_configure_from_arbitrary_lambda(self):
        # Majority function: at least two of (I0, I1, I2) are 1
        lut = LUT4()
        lut.configure_from_truth_table(lambda i0, i1, i2, i3: int((i0 + i1 + i2) >= 2))
        for idx in range(16):
            i0, i1, i2, i3 = (idx & 1), (idx >> 1) & 1, (idx >> 2) & 1, (idx >> 3) & 1
            expected = 1 if (i0 + i1 + i2) >= 2 else 0
            assert lut.eval(i0, i1, i2, i3) == expected

    def test_random_masks_verification(self):
        """Test 1000 randomly generated 16-bit masks against reference software simulation."""
        random.seed(42)
        for _ in range(1000):
            mask = random.randint(0, 0xFFFF)
            lut = LUT4(initial_mask=mask)
            for idx in range(16):
                i0, i1, i2, i3 = (idx & 1), (idx >> 1) & 1, (idx >> 2) & 1, (idx >> 3) & 1
                expected = (mask >> idx) & 1
                assert lut.eval(i0, i1, i2, i3) == expected


if __name__ == "__main__":
    pytest.main(["-v", __file__])
