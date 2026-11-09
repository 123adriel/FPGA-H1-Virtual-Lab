"""
Compiler Backend API - FPGA-H1 Virtual Lab
Provides structured JSON interfaces for Frontend integration:
AST visualization, Netlist graph, Placement layout, Routing vectors, and Simulation engine.
"""

from typing import Dict, Any, List, Optional
from compiler.compiler import H1LCompiler, CompilationResult
from compiler.ast.nodes import (
    DeviceNode, ModuleNode, SignalDeclNode, RegisterDeclNode,
    AssignNode, LutNode, InstanceNode, ConnectNode
)


class H1LCompilerAPI:
    """High-level service interface for Web UI / Frontend."""

    def __init__(self, default_channel_width: int = 8):
        self.compiler = H1LCompiler(run_pnr=True, channel_width=default_channel_width)

    def compile_project(self, h1l_code: str) -> Dict[str, Any]:
        """
        Compiles H1L code and produces complete structured data for UI rendering.
        """
        res = self.compiler.compile(h1l_code)

        if not res.success:
            return {
                "success": False,
                "errors": res.errors,
                "device": None,
                "ast": None,
                "resources": None,
                "placement": None,
                "routing": None,
                "bitstream_hex": None
            }

        # 1. AST Summary
        ast_summary = {
            "device": res.device_name,
            "inputs": res.inputs,
            "outputs": res.outputs,
            "clocks": res.clocks,
            "luts": [
                {"name": lut.name, "inputs": lut.inputs, "mask_hex": hex(lut.mask), "out": lut.output_wire}
                for lut in res.mapped_luts
            ],
            "dffs": [
                {"name": dff.name, "d": dff.d_wire, "q": dff.q_wire, "clk": dff.clock}
                for dff in res.mapped_dffs
            ]
        }

        # 2. Resources Summary
        resources = {
            "luts_used": res.lut_count,
            "dffs_used": res.dff_count,
            "clbs_used": res.clb_count,
            "io_pins": len(res.inputs) + len(res.outputs) + len(res.clocks),
            "bitstream_bytes": len(res.bitstream)
        }

        # 3. Placement Layout
        placement_data = {}
        if res.grid_circuit:
            placement_data = {
                "grid_w": res.grid_circuit.grid_w,
                "grid_h": res.grid_circuit.grid_h,
                "channel_width": res.grid_circuit.channel_width,
                "clbs": [
                    {
                        "x": x,
                        "y": y,
                        "clb_id": clb.clb_id,
                        "active_bles": sum(1 for b in clb.bles if b.lut.mask != 0)
                    }
                    for (x, y), clb in res.grid_circuit.clbs.items()
                ]
            }

        # 4. Routing Data
        routing_data = {
            "success": res.routing_report.get("success", False),
            "routed_pct": res.routing_report.get("routed_nets_pct", 0.0),
            "iterations": res.routing_report.get("iterations", 0),
            "total_segments": res.routing_report.get("total_segments_used", 0)
        }

        return {
            "success": True,
            "device": res.device_name,
            "ast": ast_summary,
            "resources": resources,
            "placement": placement_data,
            "routing": routing_data,
            "bitstream_hex": res.bitstream.hex().upper(),
            "bitstream_size_bytes": len(res.bitstream)
        }

    def simulate(self, res: CompilationResult, inputs: Dict[str, int], clk: int = 0) -> Dict[str, int]:
        """Executes a single simulation clock step."""
        if not res.circuit_engine:
            raise RuntimeError("CircuitEngine not initialized for this compilation")
        return res.circuit_engine.step(inputs, clk=clk)
