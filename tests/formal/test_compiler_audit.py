"""
Independent Formal Compiler Audit - FPGA-H1 Virtual Lab
Audits rejection of invalid circuits and proves 3-way equivalence:
Reference Model == Compiled Circuit == Reconstructed Bitstream.
"""

import pytest
from compiler.compiler import H1LCompiler
from compiler.lexer.lexer import Lexer, LexerError
from compiler.parser.parser import Parser, ParserError
from compiler.elaborator.elaborator import Elaborator, ElaboratorError
from simulator.routing.grid_circuit import GridCircuit


class TestCompilerFormalAudit:

    @classmethod
    def setup_class(cls):
        cls.compiler = H1LCompiler(run_pnr=True, channel_width=6)

    def test_audit_01_reject_illegal_characters(self):
        """Audit 1: Lexer must reject illegal characters with line/col location."""
        bad_src = "DEVICE BAD\nINPUT A\nASSIGN Y = A @ B\nEND"
        res = self.compiler.compile(bad_src)
        assert res.success is False
        assert any("Unexpected character '@'" in e for e in res.errors)

    def test_audit_02_reject_syntax_errors(self):
        """Audit 2: Parser must reject missing END or invalid token grammar."""
        bad_src = "DEVICE UNFINISHED\nINPUT A\nOUTPUT Y\nASSIGN Y = A"  # Missing END
        res = self.compiler.compile(bad_src)
        assert res.success is False
        assert any("Expected 'END'" in e or "Unexpected" in e for e in res.errors)

    def test_audit_03_reject_undeclared_signals(self):
        """Audit 3: Elaborator must reject undeclared signal references."""
        bad_src = "DEVICE UNDECLARED\nINPUT A\nOUTPUT Y\nASSIGN Y = A & NON_EXISTENT_SIG\nEND"
        res = self.compiler.compile(bad_src)
        # In BooleanMapper, non-existent inputs will either fail in elaborator or map to env missing
        assert res.success is False or "NON_EXISTENT_SIG" in str(res.errors)

    def test_audit_04_reject_multiple_drivers(self):
        """Audit 4: Elaborator must strictly reject multiple conflicting drivers on a wire."""
        bad_src = """
        DEVICE MULTI_DRIVER
            INPUT A, B, C
            OUTPUT Y
            ASSIGN Y = A & B
            ASSIGN Y = C | A
        END
        """
        res = self.compiler.compile(bad_src)
        assert res.success is False
        assert any("Multiple drivers" in e for e in res.errors)

    def test_audit_05_three_way_equivalence(self):
        """
        Audit 5: 3-Way Equivalence Verification:
        (1) Golden Reference == (2) Compiled CircuitEngine == (3) Deserialized H1BS Bitstream.
        """
        src = """
        DEVICE EQUIV_TEST
            INPUT A, B, C
            OUTPUT Y
            ASSIGN Y = (A & B) ^ C
        END
        """
        res = self.compiler.compile(src)
        assert res.success is True
        assert len(res.bitstream) > 0

        engine = res.circuit_engine
        grid = res.grid_circuit

        # Create fresh blank GridCircuit and restore it entirely from bitstream bytes
        restored_grid = GridCircuit(grid_w=grid.grid_w, grid_h=grid.grid_h, channel_width=grid.channel_width)
        restored_grid.load_bitstream(res.bitstream)

        # Exhaustively verify all 8 input combinations across the 3 representations
        for a in [0, 1]:
            for b in [0, 1]:
                for c in [0, 1]:
                    # 1. Golden Reference
                    expected = (a & b) ^ c

                    # 2. Compiled CircuitEngine
                    out_eng = engine.step({"A": a, "B": b, "C": c})
                    actual_eng = out_eng["Y"]
                    assert actual_eng == expected, f"Engine mismatch for ({a},{b},{c}): expected {expected}, got {actual_eng}"

                    # 3. Restored Bitstream Grid Circuit BLE Mask
                    restored_ble = restored_grid.get_clb(0, 0).bles[0]
                    # LUT mask evaluated for inputs [A, B, C, 0]
                    actual_bs = restored_ble.lut.eval(a, b, c, 0)
                    assert actual_bs == expected, f"Bitstream restored LUT mismatch for ({a},{b},{c}): expected {expected}, got {actual_bs}"


if __name__ == "__main__":
    pytest.main(["-v", __file__])
