"""
Logic Simulation Engine - FPGA-H1 Virtual Lab
Topological & event-driven evaluation of interconnected logic elements.
"""

from typing import Dict, List, Set, Tuple, Any, Optional
from architecture.blocks.lut4.ble import BLE


class CircuitEngine:
    """
    Simulation engine for an arbitrary network of FPGA-H1 BLEs.
    
    Resolves combinational dependencies topologically and steps sequential
    registers on clock edges.
    """

    def __init__(self, name: str = "FPGA_H1_Circuit"):
        self.name = name
        self.inputs: Dict[str, int] = {}
        self.outputs: Dict[str, int] = {}
        self.bles: Dict[str, BLE] = {}
        # Connections: ble_name -> [src_i0, src_i1, src_i2, src_i3]
        # where each src is either an input port name or "BLE_NAME.out" or constant "0"/"1"
        self.ble_connections: Dict[str, List[str]] = {}
        # Output connections: out_port -> src_signal
        self.output_connections: Dict[str, str] = {}
        self.eval_order: List[str] = []
        self._compiled = False

    def add_input(self, name: str, default: int = 0) -> None:
        self.inputs[name] = default & 1
        self._compiled = False

    def add_output(self, name: str) -> None:
        self.outputs[name] = 0
        self._compiled = False

    def add_ble(self, ble: BLE, connections: List[str]) -> None:
        """
        Adds a BLE with 4 connection sources for [I0, I1, I2, I3].
        sources can be:
        - Input port name (e.g. 'A')
        - Another BLE output (e.g. 'L0.out')
        - Constant '0' or '1'
        """
        if len(connections) != 4:
            raise ValueError(f"BLE requires exactly 4 connections, got {len(connections)}")
        self.bles[ble.name] = ble
        self.ble_connections[ble.name] = connections
        self._compiled = False

    def connect_output(self, output_name: str, src_signal: str) -> None:
        self.output_connections[output_name] = src_signal
        self._compiled = False

    def compile(self) -> None:
        """
        Computes topological order for combinational evaluation.
        Detects combinational loops.
        """
        # Build dependency graph among BLEs.
        # Note: If a BLE has bypass_ff=False (registered), its output in the current step
        # depends on its previous register state Q, not combinational paths in the same step.
        adj: Dict[str, Set[str]] = {name: set() for name in self.bles}
        in_degree: Dict[str, int] = {name: 0 for name in self.bles}

        for ble_name, conns in self.ble_connections.items():
            for src in conns:
                if src.endswith(".out"):
                    src_ble = src[:-4]
                    if src_ble in self.bles:
                        # Only purely combinational outputs create same-cycle dependency
                        if self.bles[src_ble].bypass_ff:
                            adj[src_ble].add(ble_name)

        for u in adj:
            for v in adj[u]:
                in_degree[v] = in_degree.get(v, 0) + 1

        # Kahn's algorithm for topological sorting
        queue = [u for u, deg in in_degree.items() if deg == 0]
        order = []

        while queue:
            u = queue.pop(0)
            order.append(u)
            for v in adj[u]:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)

        if len(order) < len(self.bles):
            # Combinational loop detected among combinational BLEs
            unresolved = [u for u, deg in in_degree.items() if deg > 0]
            raise RuntimeError(f"Combinational feedback loop detected in BLEs: {unresolved}")

        self.eval_order = order
        self._compiled = True

    def _resolve_signal(self, src: str) -> int:
        if src == "0":
            return 0
        if src == "1":
            return 1
        if src in self.inputs:
            return self.inputs[src]
        if f"{src}[0]" in self.inputs:
            return self.inputs[f"{src}[0]"]
        if src.endswith(".out"):
            ble_name = src[:-4]
            if ble_name in self.bles:
                return self.bles[ble_name].last_out
        if src in self.bles:
            return self.bles[src].last_out
        if src in self.outputs:
            return self.outputs[src]
        return 0

    def step(self, input_values: Dict[str, int], clk: int = 0, srst: int = 0, arst: int = 0) -> Dict[str, int]:
        """
        Executes one full simulation step with updated inputs and clock.
        Returns the dictionary of all output port values.
        """
        if not self._compiled:
            self.compile()

        # Update inputs
        for k, v in input_values.items():
            if k in self.inputs:
                self.inputs[k] = v & 1

        # Evaluate BLEs in topological order
        for ble_name in self.eval_order:
            ble = self.bles[ble_name]
            conns = self.ble_connections[ble_name]
            i0 = self._resolve_signal(conns[0])
            i1 = self._resolve_signal(conns[1])
            i2 = self._resolve_signal(conns[2])
            i3 = self._resolve_signal(conns[3])

            ble.eval(i0=i0, i1=i1, i2=i2, i3=i3, clk=clk, srst=srst, arst=arst)

        # Update circuit outputs
        for out_name, src in self.output_connections.items():
            self.outputs[out_name] = self._resolve_signal(src)

        return dict(self.outputs)

    def reset(self) -> None:
        """Resets all BLE registers and outputs to 0."""
        for inp in self.inputs:
            self.inputs[inp] = 0
        for out in self.outputs:
            self.outputs[out] = 0
        for ble in self.bles.values():
            ble.last_out = 0
            ble.last_cout = 0
            if ble.dff:
                ble.dff.q = 0
