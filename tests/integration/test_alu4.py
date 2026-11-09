"""
Integration Tests for ALU4 - FPGA-H1 Virtual Lab
Verifies all 4-bit ALU operations across input spaces.
"""

import pytest
from examples.alu4.alu4_circuit import ALU4Circuit


class TestALU4Integration:
    @classmethod
    def setup_class(cls):
        cls.alu = ALU4Circuit()

    def test_addition_exhaustive(self):
        """Tests A + B for all 256 combinations (0..15 + 0..15)."""
        for a in range(16):
            for b in range(16):
                res = self.alu.execute(a_val=a, b_val=b, opcode=ALU4Circuit.OP_ADD)
                expected_sum = (a + b) & 0x0F
                expected_carry = 1 if (a + b) > 15 else 0
                expected_zero = 1 if expected_sum == 0 else 0
                expected_neg = (expected_sum >> 3) & 1

                assert res["RES"] == expected_sum, f"ADD failed for {a} + {b}: got {res['RES']}, expected {expected_sum}"
                assert res["CARRY"] == expected_carry, f"ADD Carry failed for {a} + {b}"
                assert res["ZERO"] == expected_zero, f"ADD Zero failed for {a} + {b}"
                assert res["NEG"] == expected_neg, f"ADD Neg failed for {a} + {b}"

    def test_subtraction_exhaustive(self):
        """Tests A - B for all 256 combinations."""
        for a in range(16):
            for b in range(16):
                res = self.alu.execute(a_val=a, b_val=b, opcode=ALU4Circuit.OP_SUB)
                expected_diff = (a - b) & 0x0F
                expected_zero = 1 if expected_diff == 0 else 0

                assert res["RES"] == expected_diff, f"SUB failed for {a} - {b}: got {res['RES']}, expected {expected_diff}"
                assert res["ZERO"] == expected_zero, f"SUB Zero flag failed for {a} - {b}"

    def test_bitwise_logic_exhaustive(self):
        """Tests AND, OR, XOR, NOT operations."""
        for a in range(16):
            for b in range(16):
                # AND (010)
                res_and = self.alu.execute(a_val=a, b_val=b, opcode=ALU4Circuit.OP_AND)
                assert res_and["RES"] == (a & b)

                # OR (011)
                res_or = self.alu.execute(a_val=a, b_val=b, opcode=ALU4Circuit.OP_OR)
                assert res_or["RES"] == (a | b)

                # XOR (100)
                res_xor = self.alu.execute(a_val=a, b_val=b, opcode=ALU4Circuit.OP_XOR)
                assert res_xor["RES"] == (a ^ b)

                # NOT (101)
                res_not = self.alu.execute(a_val=a, b_val=b, opcode=ALU4Circuit.OP_NOT)
                assert res_not["RES"] == ((~a) & 0x0F)


if __name__ == "__main__":
    pytest.main(["-v", __file__])
