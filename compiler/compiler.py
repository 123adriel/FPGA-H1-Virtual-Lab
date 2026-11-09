"""
H1L Integral Compiler - FPGA-H1 Virtual Lab
Translates H1L hardware description source code directly into:
1. Elaborated typed AST
2. Optimized LUT4 / DFF technology mapping
3. Physical CLB packing
4. Spatial 2D Placement
5. Pathfinder Island-Style Routing
6. Binary H1BS Bitstream with CRC32
7. Executable CircuitEngine simulation model
"""

import math
from typing import Dict, List, Tuple, Set, Optional, Any
from compiler.lexer.lexer import Lexer
from compiler.parser.parser import Parser
from compiler.elaborator.elaborator import Elaborator, ElaboratedDesign
from compiler.ast.nodes import NumberNode, SignalRefNode
from compiler.optimizer.boolean_mapper import BooleanMapper, MappedLUT, MappedDFF
from architecture.blocks.lut4.ble import BLE
from simulator.logic.engine import CircuitEngine
from simulator.routing.grid_circuit import GridCircuit
from simulator.routing.placement import PlacementEngine
from simulator.routing.pathfinder import Net
from compiler.bitstream.bitstream_codec import BitstreamCodec
from compiler.device_profile import get_profile, validate_circuit_against_profile, DeviceProfile


class CompilationResult:
    def __init__(self):
        self.success: bool = False
        self.device_name: str = ""
        self.lut_count: int = 0
        self.dff_count: int = 0
        self.clb_count: int = 0
        self.inputs: List[str] = []
        self.outputs: List[str] = []
        self.clocks: List[str] = []
        self.mapped_luts: List[MappedLUT] = []
        self.mapped_dffs: List[MappedDFF] = []
        self.circuit_engine: Optional[CircuitEngine] = None
        self.grid_circuit: Optional[GridCircuit] = None
        self.bitstream: bytes = b""
        self.routing_report: Dict[str, Any] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.device_profile: str = "FPGA-H1-GW1NR9"
        self.profile_validation: Dict[str, Any] = {}

    def get_summary(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "device": self.device_name,
            "luts_used": self.lut_count,
            "dffs_used": self.dff_count,
            "clbs_used": self.clb_count,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "clocks": self.clocks,
            "bitstream_bytes": len(self.bitstream),
            "profile": self.device_profile,
            "warnings": self.warnings,
            "profile_validation": self.profile_validation,
            "routed": self.routing_report.get("routed_nets_pct", 0.0) if self.routing_report else "N/A"
        }


class H1LCompiler:
    """End-to-end compiler for H1L hardware description language."""

    def __init__(self, run_pnr: bool = True, channel_width: int = 8, device_profile: str = "FPGA-H1-GW1NR9"):
        self.run_pnr = run_pnr
        self.channel_width = channel_width
        self.device_profile = device_profile

    def compile(self, source: str) -> CompilationResult:
        result = CompilationResult()
        result.device_profile = self.device_profile

        try:
            # 1. Lexical Analysis
            lexer = Lexer(source)
            tokens = lexer.tokenize()

            # 2. Syntax Parsing
            parser = Parser(tokens)
            ast_device = parser.parse()
            result.device_name = ast_device.name

            # 3. Semantic Elaboration & Type Checking
            elaborator = Elaborator(ast_device)
            elaborated = elaborator.elaborate()

            # Extract Ports
            for sname, sig in elaborated.signals.items():
                if sig.direction == "INPUT":
                    if sig.width > 1:
                        for i in range(sig.width):
                            result.inputs.append(f"{sname}[{i}]")
                    else:
                        result.inputs.append(sname)
                elif sig.direction == "OUTPUT":
                    if sig.width > 1:
                        for i in range(sig.width):
                            result.outputs.append(f"{sname}[{i}]")
                    else:
                        result.outputs.append(sname)
                elif sig.direction == "CLOCK":
                    result.clocks.append(sname)

            # 4. Technology Mapping to LUT4s and DFFs
            mapper = BooleanMapper()

            # Map direct LUT primitives if any
            for lut_node in elaborated.luts:
                in_names = []
                for inp in lut_node.inputs:
                    if isinstance(inp, NumberNode):
                        in_names.append(str(inp.value & 1))
                    elif isinstance(inp, SignalRefNode):
                        sname = inp.name
                        if inp.subfield:
                            sname = f"{inp.name}.{inp.subfield}"
                        if inp.index is not None:
                            sname = f"{sname}[{inp.index}]"
                        in_names.append(sname)
                    else:
                        in_names.append(str(inp))
                while len(in_names) < 4:
                    in_names.append("0")
                mapper.mapped_luts.append(MappedLUT(lut_node.name, in_names, lut_node.mask, lut_node.name))

            # Map assignments
            for target_ref, expr in elaborated.assignments:
                tgt_sig = elaborated.signals[target_ref.name]
                if target_ref.index is not None:
                    bit_wire = f"{target_ref.name}[{target_ref.index}]"
                    mapper.map_scalar_expression(expr, output_wire=bit_wire)
                elif tgt_sig.width == 1:
                    mapper.map_scalar_expression(expr, output_wire=target_ref.name)
                else:
                    # Bus assignment bit by bit
                    for bit in range(tgt_sig.width):
                        bit_wire = f"{target_ref.name}[{bit}]"
                        mapper.map_scalar_expression(expr, output_wire=bit_wire)

            # Map registers
            for reg in elaborated.registers:
                for bit in range(reg.width):
                    q_wire = f"{reg.name}[{bit}]" if reg.width > 1 else reg.name
                    d_wire = mapper.map_scalar_expression(reg.expr)
                    dff_name = mapper._alloc_dff_name(f"REG_{reg.name}")
                    en_wire = mapper.map_scalar_expression(reg.enable) if reg.enable else None
                    mapped_dff = MappedDFF(dff_name, d_wire=d_wire, q_wire=q_wire, clock=reg.clock, enable=en_wire, reset=reg.reset)
                    mapper.mapped_dffs.append(mapped_dff)

            result.mapped_luts = mapper.mapped_luts
            result.mapped_dffs = mapper.mapped_dffs
            result.lut_count = len(mapper.mapped_luts)
            result.dff_count = len(mapper.mapped_dffs)

            # Profile validation & physical constraints check
            prof = get_profile(self.device_profile)
            issues = validate_circuit_against_profile(
                prof, result.lut_count, result.dff_count, len(result.inputs), len(result.outputs)
            )
            result.profile_validation = {
                "profile": prof.name,
                "category": prof.category,
                "valid": len(issues) == 0,
                "issues": issues,
                "capacity": {
                    "lut_max": prof.lut_count,
                    "dff_max": prof.dff_count,
                    "clb_max": prof.clb_count,
                    "inputs_max": prof.max_inputs,
                    "outputs_max": prof.max_outputs,
                }
            }
            if issues:
                result.warnings.extend(issues)

            # 5. Pack into CircuitEngine for Functional Simulation
            engine = CircuitEngine(name=result.device_name)
            for inp in result.inputs:
                engine.add_input(inp)
            for out in result.outputs:
                engine.add_output(out)

            # Build BLEs in simulation engine
            dff_by_d = {dff.d_wire: dff for dff in mapper.mapped_dffs}
            lut_by_out = {lut.output_wire: lut for lut in mapper.mapped_luts}

            for idx, lut in enumerate(mapper.mapped_luts):
                # Check if this LUT drives a registered DFF
                dff_target = dff_by_d.get(lut.output_wire)
                bypass_ff = (dff_target is None)

                ble = BLE(
                    name=lut.name,
                    ble_id=idx,
                    lut_mask=lut.mask,
                    bypass_ff=bypass_ff
                )
                # Map connections
                conns = []
                for in_sig in lut.inputs:
                    if in_sig in lut_by_out:
                        conns.append(f"{lut_by_out[in_sig].name}.out")
                    elif in_sig in result.inputs or in_sig in ["0", "1"]:
                        conns.append(in_sig)
                    else:
                        conns.append(in_sig)
                while len(conns) < 4:
                    conns.append("0")

                engine.add_ble(ble, conns)

                if lut.output_wire in result.outputs:
                    engine.connect_output(lut.output_wire, f"{ble.name}.out")
                if dff_target and dff_target.q_wire in result.outputs:
                    engine.connect_output(dff_target.q_wire, f"{ble.name}.out")

            engine.compile()
            result.circuit_engine = engine

            # 6. Physical Placement and Routing (Island-Style Grid)
            if self.run_pnr and result.lut_count > 0:
                result.clb_count = max(1, math.ceil(result.lut_count / 4))
                prof = get_profile(self.device_profile)
                if prof.category == "physical" and result.clb_count <= prof.clb_count:
                    grid_side = prof.grid_w
                    chan_w = prof.channel_width
                else:
                    grid_side = max(1, math.ceil(math.sqrt(result.clb_count)))
                    chan_w = self.channel_width
                grid_circuit = GridCircuit(grid_w=grid_side, grid_h=grid_side, channel_width=chan_w)

                # Configure BLEs into CLBs
                for idx, lut in enumerate(mapper.mapped_luts):
                    clb_idx = idx // 4
                    ble_idx = idx % 4
                    gx = clb_idx % grid_side
                    gy = clb_idx // grid_side
                    grid_circuit.configure_ble(gx, gy, ble_idx, lut.mask, bypass_ff=True)

                # Build net connections
                nets = []
                for idx, lut in enumerate(mapper.mapped_luts):
                    src_clb = idx // 4
                    src_ble = idx % 4
                    src_x = src_clb % grid_side
                    src_y = src_clb // grid_side

                    # Find downstream LUTs
                    sink_pins = []
                    for down_idx, down_lut in enumerate(mapper.mapped_luts):
                        if lut.output_wire in down_lut.inputs:
                            down_clb = down_idx // 4
                            down_ble = down_idx % 4
                            dx = down_clb % grid_side
                            dy = down_clb // grid_side
                            pin_in = down_ble * 4 + down_lut.inputs.index(lut.output_wire)
                            sink_pins.append((dx, dy, pin_in))

                    if sink_pins:
                        nets.append(Net(name=f"NET_{lut.name}", source_pin=(src_x, src_y, src_ble), sink_pins=sink_pins))

                if nets:
                    route_res = grid_circuit.route_netlist(nets)
                    result.routing_report = route_res
                    if not route_res.get("success", False):
                        result.success = False
                        failed_reason = route_res.get("reason", f"Routing failed: {route_res.get('nets_failed', 1)} unrouted nets")
                        result.errors.append(failed_reason)
                        return result
                else:
                    result.routing_report = {
                        "success": True,
                        "routed_nets_pct": 100.0,
                        "iterations": 1,
                        "nets_requested": 0,
                        "nets_routed": 0,
                        "nets_failed": 0,
                        "illegal_connections": 0,
                        "max_congestion": 0,
                        "channel_utilization_pct": 0.0,
                        "time_total_sec": 0.0
                    }

                # 7. Generate H1BS Bitstream
                bitstream_bytes = grid_circuit.to_bitstream(metadata={"device": result.device_name})
                result.bitstream = bitstream_bytes
                result.grid_circuit = grid_circuit

            result.success = True

        except Exception as e:
            result.success = False
            result.errors.append(str(e))

        return result
