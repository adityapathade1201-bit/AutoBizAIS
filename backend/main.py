"""
AutoBiz AI — FastAPI Backend
==============================
Exposes POST /api/chat which routes to the correct per-agent Python module.
Also implements endpoints expected by the React frontend for business metrics, agents, and onboarding.
Includes WebSocket real-time broadcast support for multi-device live sync.

Run locally:
    cd backend
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

import importlib
import json
import uuid
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services import llm

app = FastAPI(title="AutoBiz AI Backend", version="0.2.0")

# ── Paths ────────────────────────────────────────────────────────────────────
BACKEND_DIR = Path(__file__).parent
ROOT_DIR = BACKEND_DIR.parent
PUBLIC_DATA_DIR = ROOT_DIR / "public" / "data"
BACKEND_DATA_DIR = BACKEND_DIR / "data"

# ── Helpers for loading data ─────────────────────────────────────────────────
def load_json(path: Path) -> Any:
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_json(path: Path, data: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def _get_agents_from_public():
    public_agents = load_json(PUBLIC_DATA_DIR / "agents.json")
    if public_agents and "agents" in public_agents:
        return public_agents["agents"]
    return []

def get_agents():
    # Load from backend, fallback to public
    agents_file = BACKEND_DATA_DIR / "agents.json"
    if not agents_file.exists():
        # Initialize
        public_agents = _get_agents_from_public()
        save_json(agents_file, public_agents)
        return public_agents
    return load_json(agents_file)

def save_agents(agents: List[Dict]):
    agents_file = BACKEND_DATA_DIR / "agents.json"
    save_json(agents_file, agents)


# ── CORS ────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow requests from Ngrok, Localhost, and Mobile Devices
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── WebSocket Manager for Live Multi-Device Sync ─────────────────────────────
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"⚡ WebSocket client connected. Active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"🔌 WebSocket client disconnected. Remaining: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error broadcasting message: {e}")

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # Broadcast any message received over WS to all other connected devices
            await manager.broadcast({
                "event": "NEW_RECORD",
                "data": data
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket connection error: {e}")
        manager.disconnect(websocket)


# ── Request / Response schemas ───────────────────────────────────────────────

class ChatRequest(BaseModel):
    agent_id: str   # e.g. "msg-001", "data-001"
    message: str


class ChatResponse(BaseModel):
    reply: str
    toolExecution: Optional[Dict] = None

class OnboardingData(BaseModel):
    businessName: str
    industry: str
    customerSize: str
    revenueRange: str
    goals: List[str]
    challenges: List[str]
    teamSize: str
    freeText: Optional[str] = None


# ── Helper ───────────────────────────────────────────────────────────────────

def _agent_module_name(agent_id: str) -> str:
    """Turn 'msg-001' into 'agents.msg_001'."""
    return f"agents.{agent_id.replace('-', '_')}"


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "AutoBiz AI backend is running 🚀", "version": "0.2.0"}

# ── Agent Endpoints ──────────────────────────────────────────────────────────

@app.get("/api/agents")
async def api_get_agents():
    return get_agents()

@app.post("/api/agents/create")
async def api_create_agent(agent_data: Request):
    data = await agent_data.json()
    agents = get_agents()
    
    new_agent = {
        "id": f"custom-{uuid.uuid4().hex[:8]}",
        "status": "online",
        "avatar": "🤖",
        "color": "#6366f1",
        **data
    }
    agents.append(new_agent)
    save_agents(agents)

    # Broadcast new agent creation to mobile app
    await manager.broadcast({"event": "AGENT_CREATED", "agent": new_agent})
    return new_agent

@app.put("/api/agents/{agent_id}")
async def api_update_agent(agent_id: str, agent_data: Request):
    data = await agent_data.json()
    agents = get_agents()
    
    updated_agent = None
    for a in agents:
        if a["id"] == agent_id:
            a.update(data)
            updated_agent = a
            break
            
    if not updated_agent:
        raise HTTPException(status_code=404, detail="Agent not found")
        
    save_agents(agents)
    return updated_agent

# ── Dashboard API ─────────────────────────────────────────────────────────────
@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    from services.storage import load_json, get_all_business_facts
    
    logs = load_json("agent_logs.json")
    if not isinstance(logs, list): logs = []
    
    local = load_json("local.json")
    if not isinstance(local, list): local = []
    
    pending = load_json("pending_actions.json")
    if not isinstance(pending, dict): pending = {}
    
    tasks = load_json("tasks.json")
    if not isinstance(tasks, list): tasks = []
    
    # Calculate simple stats using a single efficient loop
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_activity = 0
    agent_usage = {}
    delegation_count = 0
    
    for log in logs:
        # Check today's activity
        if log.get("timestamp", "").startswith(today_str):
            today_activity += 1
            
        # Agent usage
        agent = log.get("agent", log.get("agent_id", "unknown"))
        agent_usage[agent] = agent_usage.get(agent, 0) + 1
        
        # Delegation count
        if "delegate_to_agent" in log.get("tools_used", []):
            delegation_count += 1
    
    return {
        "today_activity": today_activity,
        "total_messages": len(local),
        "agent_usage": agent_usage,
        "delegation_count": delegation_count,
        "pending_approvals": len(pending),
        "active_tasks": len(tasks),
        "business_facts_count": len(get_all_business_facts().keys())
    }

# ── File Upload API ───────────────────────────────────────────────────────────
from services.document_parser import parse_document, ocr_invoice

@app.post("/api/upload")
async def upload_document(request: Request):
    """
    Handle document upload, optionally trigger OCR for invoices.
    Saves extracted data to memory for the agents to process.
    """
    try:
        form = await request.form()
        files = form.getlist("files")
        
        file_ids = []
        for f in files:
            file_ids.append(f"file-{uuid.uuid4().hex[:8]}")
            # If we want to extract OCR or parse documents:
            if isinstance(f, UploadFile):
                if f.filename.lower().endswith(('png', 'jpg', 'jpeg', 'pdf')):
                    await ocr_invoice(f)
                else:
                    await parse_document(f)
            
        return {"success": True, "fileIds": file_ids}
    except Exception as e:
        print("Upload parsing failed", e)
        return {"success": False, "fileIds": []}

@app.delete("/api/reset")
async def reset_data():
    """
    Reset all backend JSON data for demo purposes.
    """
    from services.storage import save_json
    save_json("local.json", [])
    save_json("agent_logs.json", [])
    save_json("business.json", {})
    save_json("pending_actions.json", {})
    save_json("tasks.json", [])
    return {"success": True, "message": "All data reset successfully."}

# ── Chat Endpoints ───────────────────────────────────────────────────────────

@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    Route a message to the appropriate agent module and return its reply.
    Agent modules expose an async process(message) function.
    Broadcasts the user message and agent reply live to all connected WebSocket clients!
    """
    module_name = _agent_module_name(req.agent_id)

    try:
        agent_module = importlib.import_module(module_name)
    except ModuleNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{req.agent_id}' not found. Expected module: {module_name}",
        )

    if not hasattr(agent_module, "process"):
        raise HTTPException(
            status_code=500,
            detail=f"Module '{module_name}' does not expose a 'process' function.",
        )

    # Automatically extract structured business facts from the user's message
    try:
        from services.business_extractor import process_message_for_business_facts
        await process_message_for_business_facts(req.message, req.agent_id)
    except Exception as e:
        print(f"Business extraction skipped: {e}")

    reply: str = await agent_module.process(req.message)

    # ⚡ REAL-TIME BROADCAST to Mobile App & Web Clients
    timestamp = datetime.now(timezone.utc).strftime("%I:%M %p")
    
    # 1. Broadcast specifically for AgentsTab chat screen
    await manager.broadcast({
        "event": "NEW_AGENT_MESSAGE",
        "agentId": req.agent_id,
        "userMessage": req.message,
        "aiReply": reply,
        "timestamp": timestamp
    })

    # 2. Broadcast for general ChatbotTab feed stream
    await manager.broadcast({
        "event": "NEW_RECORD",
        "data": {
            "message": req.message,
            "reply": reply,
            "agent_id": req.agent_id,
            "time": timestamp,
            "source": "Web Browser"
        }
    })

    return ChatResponse(reply=reply)

@app.get("/api/chat/{agent_id}")
async def api_get_chat_history(agent_id: str):
    # Load from local memory
    local_memory_file = BACKEND_DATA_DIR / "local.json"
    messages = []
    
    if local_memory_file.exists():
        history = load_json(local_memory_file) or []
        for turn in history:
            if turn.get("agent_id") == agent_id:
                # Add user message
                messages.append({
                    "id": f"u_{turn.get('timestamp')}",
                    "type": "user",
                    "content": turn.get("user"),
                    "timestamp": turn.get("timestamp")
                })
                # Add agent message
                messages.append({
                    "id": f"a_{turn.get('timestamp')}",
                    "type": "agent",
                    "content": turn.get("assistant"),
                    "timestamp": turn.get("timestamp")
                })
                
    if not messages:
        # Fallback to mock data if empty
        mock_data = load_json(PUBLIC_DATA_DIR / "chat-history.json")
        if mock_data and "conversations" in mock_data and agent_id in mock_data["conversations"]:
            messages = mock_data["conversations"][agent_id]["messages"]
            
    return {"messages": messages}

# ── Business Endpoints ───────────────────────────────────────────────────────

@app.get("/api/business/metrics")
async def api_get_metrics():
    metrics_data = load_json(PUBLIC_DATA_DIR / "business-metrics.json")
    if metrics_data and "metrics" in metrics_data:
        return metrics_data["metrics"]
    raise HTTPException(status_code=404, detail="Metrics data not found")

@app.get("/api/business/charts")
async def api_get_chart_data():
    metrics_data = load_json(PUBLIC_DATA_DIR / "business-metrics.json")
    if metrics_data and "chartData" in metrics_data:
        return metrics_data["chartData"]
    raise HTTPException(status_code=404, detail="Chart data not found")

@app.get("/api/business/recommendations")
async def api_get_recommendations():
    metrics_data = load_json(PUBLIC_DATA_DIR / "business-metrics.json")
    if metrics_data and "ai_recommendations" in metrics_data:
        return metrics_data["ai_recommendations"]
    raise HTTPException(status_code=404, detail="Recommendations not found")

# ── Marketplace Endpoints ────────────────────────────────────────────────────

@app.get("/api/marketplace")
async def api_get_marketplace():
    mp_data = load_json(PUBLIC_DATA_DIR / "marketplace-agents.json")
    if mp_data and "featured_agents" in mp_data:
        return mp_data["featured_agents"]
    raise HTTPException(status_code=404, detail="Marketplace data not found")

@app.get("/api/marketplace/categories")
async def api_get_categories():
    mp_data = load_json(PUBLIC_DATA_DIR / "marketplace-agents.json")
    if mp_data and "categories" in mp_data:
        return mp_data["categories"]
    raise HTTPException(status_code=404, detail="Marketplace categories not found")

# ── Onboarding & Upload Endpoints ─────────────────────────────────────────────

@app.post("/api/onboarding/analyze")
async def api_onboarding_analyze(data: OnboardingData):
    # We will try to call the LLM first.
    prompt = f"""You are a professional business analyst. Analyze the following business information and return a JSON object with:
1) "summary": A comprehensive business summary (3-4 paragraphs with markdown formatting).
2) "recommended_agents": A list of recommended agents from the available list: msg-001, data-001, mkt-001, sales-001, ledger-001, alarm-001, fin-001, mgr-001, legal-001. Each recommended agent must have the "agent_id" and a "reason" string explaining why they are recommended.

Business Info:
Name: {data.businessName}
Industry: {data.industry}
Customer Size: {data.customerSize}
Revenue Range: {data.revenueRange}
Team Size: {data.teamSize}
Goals: {', '.join(data.goals)}
Challenges: {', '.join(data.challenges)}
Free text: {data.freeText or 'None'}

Return ONLY a valid JSON object matching this schema:
{{
  "summary": "...",
  "recommended_agents": [
    {{"agent_id": "...", "reason": "..."}}
  ]
}}
Do not include any markdown fences or extra text, just the raw JSON.
"""
    
    try:
        reply = await llm.generate_response(
            system_prompt="You are a professional business analyst. Return only JSON.",
            history=[],
            user_message=prompt
        )
        
        # Clean up possible markdown fences
        clean_reply = reply.strip()
        if clean_reply.startswith("```json"):
            clean_reply = clean_reply[7:]
        elif clean_reply.startswith("```"):
            clean_reply = clean_reply[3:]
        if clean_reply.endswith("```"):
            clean_reply = clean_reply[:-3]
            
        parsed_reply = json.loads(clean_reply.strip())
        if "summary" in parsed_reply and "recommended_agents" in parsed_reply:
            return parsed_reply
            
    except Exception as e:
        print("LLM analyze failed, falling back to mock data.", e)

    # Fallback to mock response
    config = load_json(PUBLIC_DATA_DIR / "onboarding-config.json")
    if config and "mock_response" in config:
        return config["mock_response"]
        
    raise HTTPException(status_code=500, detail="Failed to analyze business")