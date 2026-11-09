"""
Stage-by-Stage Compilation Pipeline Engine - FPGA-H1 Virtual Lab
Executes each compilation stage independently, capturing precise execution times (ms),
diagnostic outputs, and intermediate data models for UI rendering:
Lexer -> Parser -> AST -> Elaborator -> Optimizer -> Netlist -> Placement -> Routing -> H1BS.
"""

import time
import math
from typing import Dict, Any, List, Optional
from compiler.lexer.lexer import Lexer
from compiler.parser.parser import Parser
from compiler.elaborator.elaborator import Elaborator
from compiler.optimizer.boolean_mapper import BooleanMapper, MappedLUT, MappedDFF
from compiler.ast.nodes import NumberNode, SignalRefNode
from architecture.blocks.lut4.ble import BLE
from simulator.logic.engine import CircuitEngine
from simulator.routing.grid_circuit import GridCircuit
from simulator.routing.pathfinder import Net
from compiler.bitstream.bitstream_codec import BitstreamCodec


class PipelineExecution:
    """Executes H1L compilation while capturing rich stage metrics."""

    def __init__(self, channel_width: int = 8):
        self.channel_width = channel_width

    def run(self, source_code: str) -> Dict[str, Any]:
        stages = {}
        t_total_start = time.perf_counter()
        overall_success = True
        error_msg = None

        lexer_tokens = []
        ast_device = None
        elaborated = None
        mapper = None
        circuit_engine = None
        grid_circuit = None
        routing_report = {}
        bitstream_bytes = b""
        inputs_list = []
        outputs_list = []
        clocks_list = []

        # Stage 1: Lexer
        t0 = time.perf_counter()
        try:
            lexer = Lexer(source_code)
            tokens = lexer.tokenize()
            lexer_tokens = tokens
            t1 = time.perf_counter()
            stages["lexer"] = {
                "name": "Lexical Analysis",
                "duration_ms": round((t1 - t0) * 1000, 3),
                "status": "success",
                "token_count": len(tokens),
                "tokens_sample": [
                    {"type": tok.type.name, "value": str(tok.value), "line": tok.line, "col": tok.column}
                    for tok in tokens[:200]
                ]
            }
        except Exception as e:
            t1 = time.perf_counter()
            stages["lexer"] = {"name": "Lexical Analysis", "duration_ms": round((t1 - t0) * 1000, 3), "status": "error", "error": str(e)}
            return self._build_failure_response(stages, str(e), (time.perf_counter() - t_total_start) * 1000)

        # Stage 2: Parser
        t0 = time.perf_counter()
        try:
            parser = Parser(lexer_tokens)
            ast_device = parser.parse()
            t1 = time.perf_counter()
            stages["parser"] = {
                "name": "Syntax Parsing",
                "duration_ms": round((t1 - t0) * 1000, 3),
                "status": "success",
                "device_name": ast_device.name,
                "items_count": len(ast_device.items),
                "modules_count": len(ast_device.modules)
            }
        except Exception as e:
            t1 = time.perf_counter()
            stages["parser"] = {"name": "Syntax Parsing", "duration_ms": round((t1 - t0) * 1000, 3), "status": "error", "error": str(e)}
            return self._build_failure_response(stages, str(e), (time.perf_counter() - t_total_start) * 1000)

        # Stage 3: Elaborator
        t0 = time.perf_counter()
        try:
            elaborator = Elaborator(ast_device)
            elaborated = elaborator.elaborate()
            t1 = time.perf_counter()

            # Collect port lists
            for sname, sig in elaborated.signals.items():
                if sig.direction == "INPUT":
                    if sig.width > 1:
                        for i in range(sig.width):
                            inputs_list.append(f"{sname}[{i}]")
                    else:
                        inputs_list.append(sname)
                elif sig.direction == "OUTPUT":
                    if sig.width > 1:
                        for i in range(sig.width):
                            outputs_list.append(f"{sname}[{i}]")
                    else:
                        outputs_list.append(sname)
                elif sig.direction == "CLOCK":
                    clocks_list.append(sname)

            stages["elaborator"] = {
                "name": "Semantic Elaboration & Typing",
                "duration_ms": round((t1 - t0) * 1000, 3),
                "status": "success",
                "signals": {
                    sname: {"direction": sig.direction, "width": sig.width, "drivers": len(sig.drivers)}
                    for sname, sig in elaborated.signals.items()
                },
                "registers_count": len(elaborated.registers),
                "assignments_count": len(elaborated.assignments),
                "luts_count": len(elaborated.luts)
            }
        except Exception as e:
            t1 = time.perf_counter()
            stages["elaborator"] = {"name": "Semantic Elaboration & Typing", "duration_ms": round((t1 - t0) * 1000, 3), "status": "error", "error": str(e)}
            return self._build_failure_response(stages, str(e), (time.perf_counter() - t_total_start) * 1000)

        # Stage 4: Boolean Mapper & Technology Optimization
        t0 = time.perf_counter()
        try:
            mapper = BooleanMapper()
            # 4.1 Direct LUT primitives
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

            # 4.2 Assignments
            for target_ref, expr in elaborated.assignments:
                tgt_sig = elaborated.signals[target_ref.name]
                if target_ref.index is not None:
                    bit_wire = f"{target_ref.name}[{target_ref.index}]"
                    mapper.map_scalar_expression(expr, output_wire=bit_wire)
                elif tgt_sig.width == 1:
                    mapper.map_scalar_expression(expr, output_wire=target_ref.name)
                else:
                    for bit in range(tgt_sig.width):
                        bit_wire = f"{target_ref.name}[{bit}]"
                        mapper.map_scalar_expression(expr, output_wire=bit_wire)

            # 4.3 Registers
            for reg in elaborated.registers:
                for bit in range(reg.width):
                    q_wire = f"{reg.name}[{bit}]" if reg.width > 1 else reg.name
                    d_wire = mapper.map_scalar_expression(reg.expr)
                    dff_name = mapper._alloc_dff_name(f"REG_{reg.name}")
                    en_wire = mapper.map_scalar_expression(reg.enable) if reg.enable else None
                    mapped_dff = MappedDFF(dff_name, d_wire=d_wire, q_wire=q_wire, clock=reg.clock, enable=en_wire, reset=reg.reset)
                    mapper.mapped_dffs.append(mapped_dff)

            t1 = time.perf_counter()
            stages["optimizer"] = {
                "name": "Technology Mapping & Boolean Optimization",
                "duration_ms": round((t1 - t0) * 1000, 3),
                "status": "success",
                "lut4_count": len(mapper.mapped_luts),
                "dff_count": len(mapper.mapped_dffs),
                "luts": [
                    {
                        "name": l.name,
                        "inputs": l.inputs,
                        "mask_hex": f"0x{l.mask:04X}",
                        "out": l.output_wire
                    }
                    for l in mapper.mapped_luts
                ],
                "dffs": [
                    {
                        "name": d.name,
                        "d": d.d_wire,
                        "q": d.q_wire,
                        "clock": d.clock,
                        "enable": d.enable,
                        "reset": d.reset
                    }
                    for d in mapper.mapped_dffs
                ]
            }
        except Exception as e:
            t1 = time.perf_counter()
            stages["optimizer"] = {"name": "Technology Mapping & Boolean Optimization", "duration_ms": round((t1 - t0) * 1000, 3), "status": "error", "error": str(e)}
            return self._build_failure_response(stages, str(e), (time.perf_counter() - t_total_start) * 1000)

        # Stage 5: Netlist & CircuitEngine
        t0 = time.perf_counter()
        try:
            circuit_engine = CircuitEngine(name=ast_device.name)
            for inp in inputs_list:
                circuit_engine.add_input(inp)
            for out in outputs_list:
                circuit_engine.add_output(out)

            dff_by_d = {dff.d_wire: dff for dff in mapper.mapped_dffs}
            lut_by_out = {lut.output_wire: lut for lut in mapper.mapped_luts}

            for idx, lut in enumerate(mapper.mapped_luts):
                dff_target = dff_by_d.get(lut.output_wire)
                bypass_ff = (dff_target is None)

                ble = BLE(
                    name=lut.name,
                    ble_id=idx,
                    lut_mask=lut.mask,
                    bypass_ff=bypass_ff
                )
                conns = []
                for in_sig in lut.inputs:
                    if in_sig in lut_by_out:
                        conns.append(f"{lut_by_out[in_sig].name}.out")
                    elif in_sig in inputs_list or in_sig in ["0", "1"]:
                        conns.append(in_sig)
                    else:
                        conns.append(in_sig)
                while len(conns) < 4:
                    conns.append("0")

                circuit_engine.add_ble(ble, conns)
                if lut.output_wire in outputs_list:
                    circuit_engine.connect_output(lut.output_wire, f"{ble.name}.out")

            circuit_engine.compile()
            t1 = time.perf_counter()
            stages["netlist"] = {
                "name": "Netlist Generation & Circuit Graph",
                "duration_ms": round((t1 - t0) * 1000, 3),
                "status": "success",
                "nodes_count": len(circuit_engine.bles) + len(inputs_list) + len(outputs_list),
                "inputs_count": len(inputs_list),
                "outputs_count": len(outputs_list),
                "bles_count": len(circuit_engine.bles)
            }
        except Exception as e:
            t1 = time.perf_counter()
            stages["netlist"] = {"name": "Netlist Generation & Circuit Graph", "duration_ms": round((t1 - t0) * 1000, 3), "status": "error", "error": str(e)}
            return self._build_failure_response(stages, str(e), (time.perf_counter() - t_total_start) * 1000)

        # Stage 6: Placement (Island-Style 2D Grid)
        t0 = time.perf_counter()
        lut_count = len(mapper.mapped_luts)
        clb_count = max(1, math.ceil(lut_count / 4)) if lut_count > 0 else 1
        grid_side = max(1, math.ceil(math.sqrt(clb_count)))
        clb_matrix_info = []

        try:
            grid_circuit = GridCircuit(grid_w=grid_side, grid_h=grid_side, channel_width=self.channel_width)
            for idx, lut in enumerate(mapper.mapped_luts):
                clb_idx = idx // 4
                ble_idx = idx % 4
                gx = clb_idx % grid_side
                gy = clb_idx // grid_side
                dff_target = dff_by_d.get(lut.output_wire)
                bypass_ff = (dff_target is None)
                grid_circuit.configure_ble(gx, gy, ble_idx, lut.mask, bypass_ff=bypass_ff)

            # Build matrix summary for UI
            for gy in range(grid_side):
                for gx in range(grid_side):
                    clb = grid_circuit.clbs.get((gx, gy))
                    bles_info = []
                    if clb:
                        for b in clb.bles:
                            bles_info.append({
                                "ble_id": b.ble_id,
                                "name": b.name,
                                "lut_mask": f"0x{b.lut.mask:04X}",
                                "bypass_ff": b.bypass_ff,
                                "active": (b.lut.mask != 0 or not b.bypass_ff)
                            })
                    clb_matrix_info.append({
                        "x": gx,
                        "y": gy,
                        "clb_id": f"CLB_{gx}_{gy}",
                        "active_bles": sum(1 for b in bles_info if b["active"]),
                        "bles": bles_info
                    })

            t1 = time.perf_counter()
            stages["placement"] = {
                "name": "Spatial 2D Placement",
                "duration_ms": round((t1 - t0) * 1000, 3),
                "status": "success",
                "grid_w": grid_side,
                "grid_h": grid_side,
                "clb_count": clb_count,
                "clbs": clb_matrix_info
            }
        except Exception as e:
            t1 = time.perf_counter()
            stages["placement"] = {"name": "Spatial 2D Placement", "duration_ms": round((t1 - t0) * 1000, 3), "status": "error", "error": str(e)}
            return self._build_failure_response(stages, str(e), (time.perf_counter() - t_total_start) * 1000)

        # Stage 7: Pathfinder Wilton Routing
        t0 = time.perf_counter()
        try:
            nets = []
            for idx, lut in enumerate(mapper.mapped_luts):
                src_clb = idx // 4
                src_ble = idx % 4
                src_x = src_clb % grid_side
                src_y = src_clb // grid_side

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
                routing_report = grid_circuit.route_netlist(nets)
            else:
                routing_report = {"success": True, "routed_nets_pct": 100.0, "iterations": 1, "total_segments_used": 0}

            t1 = time.perf_counter()
            stages["routing"] = {
                "name": "Pathfinder Routing (Wilton Fs=3)",
                "duration_ms": round((t1 - t0) * 1000, 3),
                "status": "success" if routing_report.get("success", False) else "warning",
                "channel_width": self.channel_width,
                "routed_nets_pct": routing_report.get("routed_nets_pct", 100.0),
                "iterations": routing_report.get("iterations", 1),
                "total_segments_used": routing_report.get("total_segments_used", 0),
                "nets": [
                    {
                        "name": net.name,
                        "source": {"x": net.source_pin[0], "y": net.source_pin[1], "ble_pin": net.source_pin[2]},
                        "sinks": [{"x": s[0], "y": s[1], "input_pin": s[2]} for s in net.sink_pins],
                        "routed_segments": routing_report.get("routes", {}).get(net.name, [])
                    }
                    for net in nets
                ]
            }
        except Exception as e:
            t1 = time.perf_counter()
            stages["routing"] = {"name": "Pathfinder Routing (Wilton Fs=3)", "duration_ms": round((t1 - t0) * 1000, 3), "status": "error", "error": str(e)}
            return self._build_failure_response(stages, str(e), (time.perf_counter() - t_total_start) * 1000)

        # Stage 8: Bitstream Generation
        t0 = time.perf_counter()
        try:
            bitstream_bytes = grid_circuit.to_bitstream(metadata={"device": ast_device.name})
            codec = BitstreamCodec()
            decoded = codec.decode(bitstream_bytes)
            t1 = time.perf_counter()
            stages["bitstream"] = {
                "name": "H1BS Bitstream Synthesis",
                "duration_ms": round((t1 - t0) * 1000, 3),
                "status": "success",
                "magic": "H1BS",
                "crc32_hex": decoded["crc32"],
                "size_bytes": len(bitstream_bytes),
                "grid_dims": f"{grid_side}x{grid_side}",
                "channels": self.channel_width,
                "frames_count": len(decoded["bles"]) + len(decoded["switch_boxes"]) + len(decoded["connection_boxes"])
            }
        except Exception as e:
            t1 = time.perf_counter()
            stages["bitstream"] = {"name": "H1BS Bitstream Synthesis", "duration_ms": round((t1 - t0) * 1000, 3), "status": "error", "error": str(e)}
            return self._build_failure_response(stages, str(e), (time.perf_counter() - t_total_start) * 1000)

        t_total_end = time.perf_counter()

        return {
            "success": True,
            "total_duration_ms": round((t_total_end - t_total_start) * 1000, 3),
            "device": ast_device.name if ast_device else "UNKNOWN",
            "inputs": inputs_list,
            "outputs": outputs_list,
            "clocks": clocks_list,
            "resources": {
                "luts_used": len(mapper.mapped_luts),
                "dffs_used": len(mapper.mapped_dffs),
                "clbs_used": clb_count,
                "io_pins": len(inputs_list) + len(outputs_list) + len(clocks_list),
                "bitstream_bytes": len(bitstream_bytes)
            },
            "stages": stages,
            "placement": {
                "grid_w": grid_side,
                "grid_h": grid_side,
                "channel_width": self.channel_width,
                "clbs": clb_matrix_info
            },
            "routing": stages["routing"],
            "bitstream_hex": bitstream_bytes.hex().upper(),
            "bitstream_size_bytes": len(bitstream_bytes),
            "_engine": circuit_engine,
            "_grid_circuit": grid_circuit
        }

    def _build_failure_response(self, stages: Dict[str, Any], error: str, total_duration_ms: float) -> Dict[str, Any]:
        return {
            "success": False,
            "total_duration_ms": round(total_duration_ms, 3),
            "errors": [error],
            "stages": stages,
            "device": None,
            "inputs": [],
            "outputs": [],
            "clocks": [],
            "resources": {},
            "placement": None,
            "routing": None,
            "bitstream_hex": None,
            "bitstream_size_bytes": 0
        }
