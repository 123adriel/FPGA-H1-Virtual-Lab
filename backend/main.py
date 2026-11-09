"""
FastAPI Server & WebSocket Hub - FPGA-H1 Virtual Lab
Provides comprehensive REST API for projects, stage-by-stage compilation,
dynamic LUT inspection/modification, bitstream export, benchmarks, and real-time WebSocket simulation.
"""

import json
import asyncio
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.database import (
    init_db, list_projects, get_project, create_or_update_project,
    save_compilation, get_latest_benchmarks, get_db_connection
)
from backend.pipeline import PipelineExecution
from compiler.device_profile import PROFILES, get_profile
from backend.simulation_manager import simulation_manager
from backend.benchmark_runner import run_all_scalability_benchmarks, run_benchmark_for_scale
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# Initialize DB on start
init_db()

app = FastAPI(
    title="FPGA-H1 Virtual Lab API",
    description="Professional Engineering Environment for FPGA-H1 Architecture",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"


# Request Models
class ProjectPayload(BaseModel):
    name: str
    source_code: str
    description: Optional[str] = ""
    category: Optional[str] = "custom"
    project_id: Optional[str] = None


class CompileRequest(BaseModel):
    source_code: str
    project_id: Optional[str] = None
    channel_width: Optional[int] = 8
    device_profile: Optional[str] = "FPGA-H1-GW1NR9"


class StepRequest(BaseModel):
    inputs: Optional[Dict[str, int]] = None


class InputUpdateRequest(BaseModel):
    inputs: Dict[str, int]


class LutUpdateRequest(BaseModel):
    ble_name: str
    mask: int


# REST Endpoints
@app.get("/api/profiles")
def get_device_profiles():
    return {k: v.__dict__ for k, v in PROFILES.items()}


@app.get("/api/health")
def get_health():
    return {
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


@app.get("/api/projects")
def get_projects_list():
    return list_projects()


@app.get("/api/projects/{project_id}")
def get_single_project(project_id: str):
    proj = get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    return proj


@app.post("/api/projects")
def save_project_endpoint(payload: ProjectPayload):
    proj = create_or_update_project(
        name=payload.name,
        source_code=payload.source_code,
        description=payload.description or "",
        category=payload.category or "custom",
        project_id=payload.project_id
    )
    return proj


@app.delete("/api/projects/{project_id}")
def delete_project_endpoint(project_id: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()
    return {"status": "deleted", "id": project_id}


@app.post("/api/compile")
def compile_circuit_endpoint(req: CompileRequest):
    pipeline = PipelineExecution(channel_width=req.channel_width or 8, device_profile=req.device_profile or "FPGA-H1-GW1NR9")
    res = pipeline.run(req.source_code)

    comp_id = None
    if res.get("success"):
        # Load compiled circuit into simulation manager automatically
        simulation_manager.load_engine(res["_engine"], res["_grid_circuit"])
        comp_id = save_compilation(req.project_id, res)

    # Strip non-serializable internal objects before returning JSON
    res.pop("_engine", None)
    res.pop("_grid_circuit", None)
    res["compilation_id"] = comp_id
    return res


@app.post("/api/simulate/step")
def simulate_step(req: StepRequest):
    session = simulation_manager.current_session
    if not session:
        raise HTTPException(status_code=400, detail="No active simulation circuit loaded. Compile first.")

    if req.inputs:
        session.set_inputs(req.inputs)

    state = session.step()
    return state


@app.post("/api/simulate/reset")
def simulate_reset():
    session = simulation_manager.current_session
    if not session:
        raise HTTPException(status_code=400, detail="No active simulation circuit loaded.")
    return session.reset()


@app.post("/api/simulate/inputs")
def simulate_update_inputs(req: InputUpdateRequest):
    session = simulation_manager.current_session
    if not session:
        raise HTTPException(status_code=400, detail="No active simulation circuit loaded.")
    session.set_inputs(req.inputs)
    # Trigger logic refresh without advancing clock
    session.outputs = session.engine.step(session.inputs, clk=session.clk_state)
    session.internal_nodes = dict(session.engine.nodes)
    return session._record_history()


@app.post("/api/lut/update")
def update_lut_mask_endpoint(req: LutUpdateRequest):
    session = simulation_manager.current_session
    if not session:
        raise HTTPException(status_code=400, detail="No active simulation circuit loaded.")

    success = session.set_lut_mask(req.ble_name, req.mask)
    if not success:
        raise HTTPException(status_code=404, detail=f"BLE {req.ble_name} not found in active circuit")

    return {
        "status": "updated",
        "ble_name": req.ble_name,
        "new_mask": f"0x{req.mask:04X}",
        "state": session.history[-1]
    }


@app.get("/api/bitstream/download/{compilation_id}")
def download_bitstream(compilation_id: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT device_name, bitstream_hex FROM compilations WHERE id = ?", (compilation_id,))
    row = cur.fetchone()
    conn.close()

    if not row or not row["bitstream_hex"]:
        raise HTTPException(status_code=404, detail="Bitstream not found")

    raw_bytes = bytes.fromhex(row["bitstream_hex"])
    filename = f"{row['device_name'] or 'circuit'}.h1bs"

    return Response(
        content=raw_bytes,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.get("/api/benchmarks")
def get_benchmarks_endpoint():
    benchmarks = get_latest_benchmarks()
    if not benchmarks:
        # Run default benchmarks if none exist yet
        benchmarks = run_all_scalability_benchmarks()
    return benchmarks


@app.post("/api/benchmarks/run")
def trigger_benchmarks():
    return run_all_scalability_benchmarks()


# WebSocket Real-Time Telemetry & Simulation Hub
@app.websocket("/ws/simulate")
async def websocket_simulation_hub(websocket: WebSocket):
    await websocket.accept()
    running_task: Optional[asyncio.Task] = None

    async def simulation_loop(speed_hz: float):
        interval = max(0.01, 1.0 / max(0.1, speed_hz))
        try:
            while True:
                session = simulation_manager.current_session
                if session and session.is_running:
                    state = session.step()
                    await websocket.send_json({"type": "STATE", "data": state})
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            await websocket.send_json({"type": "ERROR", "message": str(e)})

    try:
        # Send current state if available
        if simulation_manager.current_session:
            await websocket.send_json({
                "type": "STATE",
                "data": simulation_manager.current_session.history[-1]
            })

        while True:
            msg_text = await websocket.receive_text()
            msg = json.loads(msg_text)
            action = msg.get("type", "").upper()
            session = simulation_manager.current_session

            if action == "STEP":
                if session:
                    if "inputs" in msg:
                        session.set_inputs(msg["inputs"])
                    state = session.step()
                    await websocket.send_json({"type": "STATE", "data": state})
                else:
                    await websocket.send_json({"type": "ERROR", "message": "No active circuit compiled."})

            elif action == "RUN":
                if session:
                    speed_hz = float(msg.get("speed_hz", 2.0))
                    session.is_running = True
                    session.speed_hz = speed_hz
                    if running_task and not running_task.done():
                        running_task.cancel()
                    running_task = asyncio.create_task(simulation_loop(speed_hz))
                    await websocket.send_json({"type": "STATUS", "status": "running", "speed_hz": speed_hz})
                else:
                    await websocket.send_json({"type": "ERROR", "message": "No active circuit compiled."})

            elif action == "PAUSE":
                if session:
                    session.is_running = False
                if running_task and not running_task.done():
                    running_task.cancel()
                    running_task = None
                await websocket.send_json({"type": "STATUS", "status": "paused"})

            elif action == "RESET":
                if session:
                    session.is_running = False
                    if running_task and not running_task.done():
                        running_task.cancel()
                        running_task = None
                    state = session.reset()
                    await websocket.send_json({"type": "STATE", "data": state})
                else:
                    await websocket.send_json({"type": "ERROR", "message": "No active circuit compiled."})

            elif action == "SET_INPUTS":
                if session and "inputs" in msg:
                    session.set_inputs(msg["inputs"])
                    session.outputs = session.engine.step(session.inputs, clk=session.clk_state)
                    session.internal_nodes = {f"{b.name}.out": b.last_out for b in session.engine.bles.values()}
                    state = session._record_history()
                    await websocket.send_json({"type": "STATE", "data": state})

            elif action == "SET_LUT_MASK":
                if session and "ble_name" in msg and "mask" in msg:
                    success = session.set_lut_mask(msg["ble_name"], int(msg["mask"]))
                    if success:
                        await websocket.send_json({"type": "STATE", "data": session.history[-1]})
                    else:
                        await websocket.send_json({"type": "ERROR", "message": f"BLE {msg['ble_name']} not found."})

    except WebSocketDisconnect:
        if running_task and not running_task.done():
            running_task.cancel()
    except Exception as e:
        if running_task and not running_task.done():
            running_task.cancel()


# Mount compiled frontend if available
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
