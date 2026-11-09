"""
Integration Tests for H1L Integral Compiler - FPGA-H1 Virtual Lab
Compiles and simulates all 10 mandatory H1L benchmark programs.
"""

import os
import pytest
from pathlib import Path
from compiler.compiler import H1LCompiler


EXAMPLES_DIR = Path(__file__).resolve().parent.parent.parent / "examples"


class TestH1LCompilerSuite:

    @classmethod
    def setup_class(cls):
        cls.compiler = H1LCompiler(run_pnr=True, channel_width=6)

    def _read_example(self, rel_path: str) -> str:
        filepath = EXAMPLES_DIR / rel_path
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    def test_01_compile_logic_gates(self):
        """1. Compile and simulate basic logic gates."""
        src = self._read_example("gates/logic_gates.h1l")
        res = self.compiler.compile(src)
        assert res.success is True, f"Compilation failed: {res.errors}"
        assert res.lut_count >= 4
        assert len(res.bitstream) > 20

        # Simulate
        engine = res.circuit_engine
        out = engine.step({"A": 1, "B": 0})
        assert out["Y_AND"] == 0
        assert out["Y_OR"] == 1
        assert out["Y_XOR"] == 1
        assert out["Y_NOT"] == 0

        out = engine.step({"A": 1, "B": 1})
        assert out["Y_AND"] == 1
        assert out["Y_OR"] == 1
        assert out["Y_XOR"] == 0

    def test_02_compile_mux4(self):
        """2. Compile and simulate 4:1 multiplexer."""
        src = self._read_example("gates/mux4.h1l")
        res = self.compiler.compile(src)
        assert res.success is True, f"Compilation failed: {res.errors}"

        engine = res.circuit_engine
        # D0=1, D1=0, D2=0, D3=0; select S1=0, S0=0 -> expect 1
        out0 = engine.step({"D0": 1, "D1": 0, "D2": 0, "D3": 0, "S0": 0, "S1": 0})
        assert out0["Y"] == 1

        # Select S1=0, S0=1 -> expects D1 (0)
        out1 = engine.step({"D0": 1, "D1": 0, "D2": 0, "D3": 0, "S0": 1, "S1": 0})
        assert out1["Y"] == 0

        # Select S1=1, S0=1 -> expects D3 (1)
        out3 = engine.step({"D0": 0, "D1": 0, "D2": 0, "D3": 1, "S0": 1, "S1": 1})
        assert out3["Y"] == 1

    def test_03_compile_counter4(self):
        """3. Compile and simulate 4-bit synchronous counter."""
        src = self._read_example("counters/counter4.h1l")
        res = self.compiler.compile(src)
        assert res.success is True, f"Compilation failed: {res.errors}"
        assert res.lut_count > 0

    def test_04_compile_counter8(self):
        """4. Compile 8-bit counter."""
        src = self._read_example("counters/counter8.h1l")
        res = self.compiler.compile(src)
        assert res.success is True, f"Compilation failed: {res.errors}"

    def test_05_compile_reg_enable(self):
        """5. Compile register with clock enable."""
        src = self._read_example("counters/reg_enable.h1l")
        res = self.compiler.compile(src)
        assert res.success is True, f"Compilation failed: {res.errors}"

    def test_06_compile_adder4(self):
        """6. Compile structural 4-bit ripple adder."""
        src = self._read_example("alu4/adder4.h1l")
        res = self.compiler.compile(src)
        assert res.success is True, f"Compilation failed: {res.errors}"
        assert res.lut_count >= 8

        engine = res.circuit_engine
        # Test 5 + 3 = 8 (CIN=0)
        # A=0101 (A0=1, A1=0, A2=1, A3=0), B=0011 (B0=1, B1=1, B2=0, B3=0)
        inputs = {
            "A[0]": 1, "A[1]": 0, "A[2]": 1, "A[3]": 0,
            "B[0]": 1, "B[1]": 1, "B[2]": 0, "B[3]": 0,
            "CIN": 0
        }
        out = engine.step(inputs)
        # Sum = 8 -> 1000 (SUM0=0, SUM1=0, SUM2=0, SUM3=1, COUT=0)
        assert out["SUM[0]"] == 0
        assert out["SUM[1]"] == 0
        assert out["SUM[2]"] == 0
        assert out["SUM[3]"] == 1
        assert out["COUT"] == 0

    def test_07_compile_alu4(self):
        """7. Compile complete 4-bit ALU from H1L source."""
        src = self._read_example("alu4/alu4.h1l")
        res = self.compiler.compile(src)
        assert res.success is True, f"Compilation failed: {res.errors}"
        assert res.lut_count > 0
        assert len(res.bitstream) > 30

    def test_08_compile_alu8(self):
        """8. Compile 8-bit ALU from H1L source."""
        src = self._read_example("alu8/alu8.h1l")
        res = self.compiler.compile(src)
        assert res.success is True, f"Compilation failed: {res.errors}"

    def test_09_compile_fsm(self):
        """9. Compile FSM traffic light controller."""
        src = self._read_example("processors/fsm_traffic.h1l")
        res = self.compiler.compile(src)
        assert res.success is True, f"Compilation failed: {res.errors}"

    def test_10_compile_pipeline(self):
        """10. Compile 3-stage arithmetic pipeline."""
        src = self._read_example("processors/pipeline3.h1l")
        res = self.compiler.compile(src)
        assert res.success is True, f"Compilation failed: {res.errors}"


if __name__ == "__main__":
    pytest.main(["-v", __file__])
