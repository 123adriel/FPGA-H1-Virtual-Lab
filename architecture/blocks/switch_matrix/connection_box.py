"""
Connection Box Architecture - FPGA-H1 Virtual Lab
Connects CLB input/output pins to routing channel tracks.
"""

from typing import Dict, List, Set, Tuple, Any, Optional


class ConnectionBox:
    """
    Connection Box (CB) interface between CLB pins and channel tracks.
    
    Parameters:
    - cb_id: unique ID
    - channel_type: 'CHANX' (horizontal) or 'CHANY' (vertical)
    - x, y: grid coordinate of adjacent CLB
    - width: channel track count W
    - num_inputs: count of CLB input pins accessible (e.g. 8 or 16)
    - num_outputs: count of CLB output pins accessible (e.g. 2 or 4)
    - fc_in: fraction of tracks connected to each input pin (default 0.5)
    - fc_out: fraction of tracks each output pin can drive (default 0.25)
    """

    def __init__(
        self,
        cb_id: int,
        channel_type: str,
        x: int,
        y: int,
        width: int = 8,
        num_inputs: int = 8,
        num_outputs: int = 2,
        fc_in: float = 0.5,
        fc_out: float = 0.5
    ):
        self.cb_id = cb_id
        self.channel_type = channel_type  # 'CHANX' or 'CHANY'
        self.x = x
        self.y = y
        self.width = width
        self.num_inputs = num_inputs
        self.num_outputs = num_outputs
        self.fc_in = fc_in
        self.fc_out = fc_out

        # Allowed connections
        # input_pin_idx -> List[track_idx]
        self.allowed_input_tracks: Dict[int, List[int]] = {}
        # output_pin_idx -> List[track_idx]
        self.allowed_output_tracks: Dict[int, List[int]] = {}
        self._build_connectivity_pattern()

        # Configured state:
        # input_pin_idx -> selected track_idx (via MUX, max 1 track selected)
        self.input_mux_selection: Dict[int, Optional[int]] = {i: None for i in range(num_inputs)}
        # track_idx -> driving output_pin_idx (max 1 driver per track)
        self.track_driver: Dict[int, Optional[int]] = {t: None for t in range(width)}

    def _build_connectivity_pattern(self) -> None:
        """Determines the fixed switch distribution using standard island-style interleaving."""
        w = self.width
        # For inputs: spread tracks evenly
        num_in_tracks = max(1, int(round(self.fc_in * w)))
        for pin in range(self.num_inputs):
            # Interleaved track selection
            tracks = [(pin + i) % w for i in range(num_in_tracks)]
            self.allowed_input_tracks[pin] = sorted(list(set(tracks)))

        # For outputs: spread tracks evenly
        num_out_tracks = max(1, int(round(self.fc_out * w)))
        for pin in range(self.num_outputs):
            tracks = [(pin * 2 + i) % w for i in range(num_out_tracks)]
            self.allowed_output_tracks[pin] = sorted(list(set(tracks)))

    def connect_input_pin(self, pin_idx: int, track_idx: int) -> None:
        """Configures input pin multiplexer to listen to track_idx."""
        if pin_idx not in self.allowed_input_tracks:
            raise IndexError(f"Input pin {pin_idx} out of range (0..{self.num_inputs - 1})")
        if track_idx not in self.allowed_input_tracks[pin_idx]:
            raise ValueError(
                f"Track {track_idx} not reachable from pin {pin_idx}. Allowed: {self.allowed_input_tracks[pin_idx]}"
            )
        self.input_mux_selection[pin_idx] = track_idx

    def disconnect_input_pin(self, pin_idx: int) -> None:
        """Disconnects input pin (float / open MUX)."""
        if pin_idx in self.input_mux_selection:
            self.input_mux_selection[pin_idx] = None

    def connect_output_pin(self, pin_idx: int, track_idx: int) -> None:
        """Enables output driver from pin_idx to track_idx."""
        if pin_idx not in self.allowed_output_tracks:
            raise IndexError(f"Output pin {pin_idx} out of range (0..{self.num_outputs - 1})")
        if track_idx not in self.allowed_output_tracks[pin_idx]:
            raise ValueError(
                f"Pin {pin_idx} cannot drive track {track_idx}. Allowed: {self.allowed_output_tracks[pin_idx]}"
            )
        # Check for multiple drivers conflict (short circuit)
        current_driver = self.track_driver.get(track_idx)
        if current_driver is not None and current_driver != pin_idx:
            raise RuntimeError(
                f"Short-circuit conflict: Track {track_idx} already driven by pin {current_driver}, cannot also drive with pin {pin_idx}"
            )
        self.track_driver[track_idx] = pin_idx

    def disconnect_output_pin(self, pin_idx: int, track_idx: int) -> None:
        """Disables output driver."""
        if self.track_driver.get(track_idx) == pin_idx:
            self.track_driver[track_idx] = None

    def clear(self) -> None:
        """Resets all connections."""
        for p in self.input_mux_selection:
            self.input_mux_selection[p] = None
        for t in self.track_driver:
            self.track_driver[t] = None

    def to_bitmask(self) -> int:
        """
        Serializes CB configuration to an integer bitmask.
        Encodes input multiplexer selections and active output driver switches.
        """
        mask = 0
        bit_offset = 0
        # 1. Inputs: 1 bit per allowed track connection
        for pin in range(self.num_inputs):
            selected = self.input_mux_selection.get(pin)
            for track in self.allowed_input_tracks[pin]:
                if selected == track:
                    mask |= (1 << bit_offset)
                bit_offset += 1

        # 2. Outputs: 1 bit per allowed track connection
        for pin in range(self.num_outputs):
            for track in self.allowed_output_tracks[pin]:
                if self.track_driver.get(track) == pin:
                    mask |= (1 << bit_offset)
                bit_offset += 1

        return mask

    def from_bitmask(self, mask: int) -> None:
        """Restores CB configuration from bitmask."""
        self.clear()
        bit_offset = 0
        for pin in range(self.num_inputs):
            for track in self.allowed_input_tracks[pin]:
                if (mask >> bit_offset) & 1:
                    self.connect_input_pin(pin, track)
                bit_offset += 1

        for pin in range(self.num_outputs):
            for track in self.allowed_output_tracks[pin]:
                if (mask >> bit_offset) & 1:
                    self.connect_output_pin(pin, track)
                bit_offset += 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cb_id": self.cb_id,
            "type": self.channel_type,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "input_mux": {k: v for k, v in self.input_mux_selection.items() if v is not None},
            "output_drivers": {k: v for k, v in self.track_driver.items() if v is not None},
            "bitmask_hex": hex(self.to_bitmask())
        }

    def __repr__(self) -> str:
        return f"ConnectionBox({self.channel_type}, at=({self.x}, {self.y}), W={self.width})"
