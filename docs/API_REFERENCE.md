# FPGA-H1 Virtual Lab — API Reference

## 1. Overview

The FPGA-H1 Virtual Lab backend exposes a comprehensive REST and WebSocket interface for compilation, physical design inspection, hardware simulation, dynamic logic modification, and benchmark telemetry.

- **Base URL**: `http://localhost:8000/api`
- **WebSocket URL**: `ws://localhost:8000/ws/simulate`

---

## 2. REST Endpoints

### 2.1 System Health
- **Endpoint**: `GET /api/health`
- **Description**: Returns server status, architecture details, and target specifications.
- **Response**:
```json
{
  "status": "online",
  "engine": "FPGA-H1 Virtual Lab",
  "version": "1.0.0",
  "architecture": {
    "lut_type": "LUT4",
    "clb_size": 4,
    "switch_box": "Wilton Fs=3",
    "bitstream": "H1BS v1 with CRC32",
    "reference_target": "Gowin GW1NR-9 (8,640 LUT4)"
  }
}
```

### 2.2 Projects Management
- **`GET /api/projects`**: List all saved projects and seeded examples.
- **`GET /api/projects/{project_id}`**: Retrieve project details including H1L source code.
- **`POST /api/projects`**: Create or update a project.
  - Payload:
    ```json
    {
      "name": "alu4",
      "source_code": "DEVICE ALU4\n...",
      "description": "4-bit ALU",
      "category": "alu4",
      "project_id": null
    }
    ```
- **`DELETE /api/projects/{project_id}`**: Delete project from SQLite database.

### 2.3 Compilation & Synthesis Pipeline
- **Endpoint**: `POST /api/compile`
- **Description**: Runs full 8-stage compilation pipeline, generates bitstream, and loads engine into the simulation coordinator.
- **Request Body**:
  ```json
  {
    "source_code": "DEVICE ALU4\n...",
    "project_id": "optional-uuid",
    "channel_width": 8
  }
  ```
- **Response Body**:
  ```json
  {
    "success": true,
    "total_duration_ms": 12.45,
    "device": "ALU4",
    "inputs": ["A[0]", "A[1]", "B[0]", ...],
    "outputs": ["RES[0]", "RES[1]", "ZERO", ...],
    "clocks": ["CLK"],
    "resources": {
      "luts_used": 18,
      "dffs_used": 4,
      "clbs_used": 5,
      "io_pins": 18,
      "bitstream_bytes": 324
    },
    "stages": {
      "lexer": { "name": "Lexical Analysis", "duration_ms": 0.28, "status": "success", "token_count": 134 },
      "parser": { "name": "Syntax Parsing", "duration_ms": 0.35, "status": "success", "items_count": 14 },
      "elaborator": { "name": "Semantic Elaboration & Typing", "duration_ms": 0.12, "status": "success" },
      "optimizer": { "name": "Technology Mapping", "duration_ms": 1.25, "status": "success", "lut4_count": 18 },
      "netlist": { "name": "Netlist Generation", "duration_ms": 0.42, "status": "success" },
      "placement": { "name": "Spatial 2D Placement", "duration_ms": 1.85, "status": "success", "grid_w": 3, "grid_h": 3 },
      "routing": { "name": "Pathfinder Routing", "duration_ms": 7.15, "status": "success", "routed_nets_pct": 100.0 },
      "bitstream": { "name": "H1BS Synthesis", "duration_ms": 0.88, "status": "success", "crc32_hex": "0x34C81A02" }
    },
    "placement": { ... },
    "routing": { ... },
    "bitstream_hex": "48314253...",
    "bitstream_size_bytes": 324,
    "compilation_id": "uuid"
  }
  ```

### 2.4 Simulation Stepping & Controls
- **`POST /api/simulate/step`**: Advance clock cycle.
  - Body: `{"inputs": {"A[0]": 1, "B[0]": 1}}`
  - Response: `{ "cycle": 1, "clk": 1, "inputs": {...}, "outputs": {...}, "ble_states": [...] }`
- **`POST /api/simulate/reset`**: Resets all BLE registers to 0 and clears cycle counter.
- **`POST /api/simulate/inputs`**: Injects new input vector without clock stepping.

### 2.5 Dynamic LUT Modification
- **Endpoint**: `POST /api/lut/update`
- **Description**: Dynamically modifies the 16-bit truth table mask of an active BLE in real-time.
- **Request Body**:
  ```json
  {
    "ble_name": "FA0",
    "mask": 34952
  }
  ```
- **Response**:
  ```json
  {
    "status": "updated",
    "ble_name": "FA0",
    "new_mask": "0x8888",
    "state": { "cycle": 1, "outputs": {...} }
  }
  ```

### 2.6 Bitstream Download
- **Endpoint**: `GET /api/bitstream/download/{compilation_id}`
- **Response**: Raw binary `application/octet-stream` containing valid H1BS bitstream with header, frames, and CRC-32 checksum.

### 2.7 Benchmarks
- **`GET /api/benchmarks`**: Retrieve historical and latest scalability benchmarks.
- **`POST /api/benchmarks/run`**: Trigger execution of the full scalability benchmark suite across all 6 tiers.

---

## 3. WebSocket Simulation Protocol

- **Endpoint**: `/ws/simulate`

### 3.1 Client to Server Commands
- **Step Clock**:
  ```json
  { "type": "STEP", "inputs": { "A[0]": 1, "B[0]": 1 } }
  ```
- **Run Auto Clock**:
  ```json
  { "type": "RUN", "speed_hz": 5.0 }
  ```
- **Pause Auto Clock**:
  ```json
  { "type": "PAUSE" }
  ```
- **Reset Circuit**:
  ```json
  { "type": "RESET" }
  ```
- **Update Stimulus**:
  ```json
  { "type": "SET_INPUTS", "inputs": { "A[0]": 1 } }
  ```
- **Dynamic Mask Override**:
  ```json
  { "type": "SET_LUT_MASK", "ble_name": "FA0", "mask": 27030 }
  ```

### 3.2 Server to Client Frames
- **State Snapshot**:
  ```json
  {
    "type": "STATE",
    "data": {
      "cycle": 4,
      "clk": 1,
      "inputs": { "A[0]": 1, "B[0]": 1, "OP[0]": 0 },
      "outputs": { "RES[0]": 0, "ZERO": 1, "NEG": 0 },
      "ble_states": [
        {
          "name": "FA0",
          "ble_id": 0,
          "lut_mask": "0x6996",
          "inputs": [1, 1, 0, 0],
          "lut_out": 0,
          "dff_q": 0,
          "out": 0,
          "bypass_ff": true
        }
      ],
      "timestamp": 1731189400.123
    }
  }
  ```
- **Status Update**:
  ```json
  { "type": "STATUS", "status": "running", "speed_hz": 5.0 }
  ```
- **Error**:
  ```json
  { "type": "ERROR", "message": "No active circuit compiled." }
  ```
