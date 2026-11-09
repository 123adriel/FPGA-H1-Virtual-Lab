"""
Simulation Manager & WebSocket Telemetry Engine - FPGA-H1 Virtual Lab
Manages active CircuitEngine instances, cycle-by-cycle logic execution,
signal waveform history, dynamic LUT modification, and real-time streaming.
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from simulator.logic.engine import CircuitEngine
from simulator.routing.grid_circuit import GridCircuit


class SimulationSession:
    """Represents a stateful interactive simulation session."""

    def __init__(self, engine: CircuitEngine, grid_circuit: Optional[GridCircuit] = None, max_history: int = 500):
        self.engine = engine
        self.grid_circuit = grid_circuit
        self.cycle: int = 0
        self.clk_state: int = 0
        self.inputs: Dict[str, int] = {inp: 0 for inp in engine.inputs}
        self.outputs: Dict[str, int] = {out: 0 for out in engine.outputs}
        self.internal_nodes: Dict[str, int] = {}
        self.max_history = max_history
        self.history: List[Dict[str, Any]] = []
        self.is_running: bool = False
        self.speed_hz: float = 2.0  # default 2 cycles per second
        self._record_history()

    def set_inputs(self, new_inputs: Dict[str, int]):
        for k, v in new_inputs.items():
            if k in self.inputs:
                self.inputs[k] = 1 if v else 0

    def step(self) -> Dict[str, Any]:
        """Advances clock: toggles clock or completes half-cycle/full-cycle."""
        self.cycle += 1
        self.clk_state = 1 - self.clk_state

        out = self.engine.step(self.inputs, clk=self.clk_state)
        self.outputs = out
        self.internal_nodes = {f"{b.name}.out": b.last_out for b in self.engine.bles.values()}

        state = self._record_history()
        return state

    def set_lut_mask(self, ble_name: str, new_mask: int) -> bool:
        """Dynamically overrides a LUT mask in the live engine."""
        ble = self.engine.bles.get(ble_name)
        if ble:
            ble.lut.mask = new_mask & 0xFFFF
            self.outputs = self.engine.step(self.inputs, clk=self.clk_state)
            self.internal_nodes = {f"{b.name}.out": b.last_out for b in self.engine.bles.values()}
            self._record_history()
            return True
        return False

    def reset(self) -> Dict[str, Any]:
        self.cycle = 0
        self.clk_state = 0
        self.engine.reset()
        self.outputs = {out: 0 for out in self.engine.outputs}
        self.internal_nodes = {f"{b.name}.out": 0 for b in self.engine.bles.values()}
        self.history.clear()
        return self._record_history()

    def get_ble_states(self) -> List[Dict[str, Any]]:
        ble_states = []
        for ble in self.engine.bles.values():
            conns = self.engine.ble_connections.get(ble.name, ["0", "0", "0", "0"])
            in_vals = []
            for src in conns:
                try:
                    in_vals.append(self.engine._resolve_signal(src))
                except Exception:
                    in_vals.append(0)

            while len(in_vals) < 4:
                in_vals.append(0)

            # Reconstruct truth table index
            idx = in_vals[0] | (in_vals[1] << 1) | (in_vals[2] << 2) | (in_vals[3] << 3)
            lut_out = (ble.lut.mask >> idx) & 1

            ble_states.append({
                "name": ble.name,
                "ble_id": ble.ble_id,
                "lut_mask": f"0x{ble.lut.mask:04X}",
                "inputs": in_vals,
                "lut_out": lut_out,
                "dff_q": ble.dff.q if ble.dff else 0,
                "out": ble.last_out,
                "bypass_ff": ble.bypass_ff
            })
        return ble_states

    def _record_history(self) -> Dict[str, Any]:
        state = {
            "cycle": self.cycle,
            "clk": self.clk_state,
            "inputs": dict(self.inputs),
            "outputs": dict(self.outputs),
            "ble_states": self.get_ble_states(),
            "timestamp": time.time()
        }
        self.history.append(state)
        if len(self.history) > self.max_history:
            self.history.pop(0)
        return state


class SimulationManager:
    """Singleton session coordinator."""

    def __init__(self):
        self.current_session: Optional[SimulationSession] = None
        self._runner_task: Optional[asyncio.Task] = None

    def load_engine(self, engine: CircuitEngine, grid_circuit: Optional[GridCircuit] = None) -> SimulationSession:
        self.stop_runner()
        self.current_session = SimulationSession(engine, grid_circuit)
        return self.current_session

    def stop_runner(self):
        if self.current_session:
            self.current_session.is_running = False
        if self._runner_task and not self._runner_task.done():
            self._runner_task.cancel()
            self._runner_task = None


simulation_manager = SimulationManager()
