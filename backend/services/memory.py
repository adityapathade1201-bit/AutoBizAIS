"""
services/memory.py
==================
Shared conversation memory and persistent JSON storage for AutoBiz AI.

Storage: backend/data/
Files managed:
- local.json (Conversation history)
- business.json (Structured business information)
- pending_actions.json (Approval workflow)
- agent_logs.json (Logs of every agent execution)
- tasks.json (Future reminders and scheduled tasks)
- users.json (Temporary user profile storage)

All agents read from and write to the SAME files so they share context
across conversations.
"""

from datetime import datetime, timezone
from services.storage import load_json, append_json, update_json

# ── Conversation Memory ───────────────────────────────────────────────────────

def load_all() -> list[dict]:
    """Return the full conversation log (all agents)."""
    return load_json("local.json")

def save_turn(
    agent_id: str,
    agent_name: str,
    user_message: str,
    assistant_reply: str,
) -> None:
    """Append one user/assistant exchange to shared memory."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent_id": agent_id,
        "agent": agent_name,
        "user": user_message,
        "assistant": assistant_reply,
    }
    append_json("local.json", entry)

def build_conversation_messages(max_turns: int = 40) -> list[dict]:
    """
    Convert shared memory into the OpenAI-compatible messages list.
    """
    history = load_all()
    recent = history[-max_turns:]

    messages: list[dict] = []
    for turn in recent:
        agent_label = turn.get("agent", "Agent")
        messages.append({"role": "user", "content": turn.get("user", "")})
        messages.append(
            {
                "role": "assistant",
                "content": f"[{agent_label}]: {turn.get('assistant', '')}",
            }
        )
    return messages

# ── Business Memory ───────────────────────────────────────────────────────────

def load_business_memory() -> dict:
    """Return the structured business information."""
    data = load_json("business.json")
    return data if isinstance(data, dict) else {}

def update_business_memory(updates: dict) -> dict:
    """Merge new business facts into the business JSON file."""
    update_json("business.json", updates)
    return load_business_memory()

# ── Agent Execution Logging ───────────────────────────────────────────────────

def log_agent_execution(
    agent_id: str,
    agent_name: str,
    user_message: str,
    tools_used: list,
    delegations: list,
    execution_time_seconds: float,
    success: bool,
    error_message: str = ""
) -> None:
    """Log an agent's execution to agent_logs.json."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent_id": agent_id,
        "agent_name": agent_name,
        "user_message": user_message,
        "tools_used": tools_used,
        "delegations": delegations,
        "execution_time_seconds": round(execution_time_seconds, 2),
        "success": success,
        "error_message": error_message
    }
    append_json("agent_logs.json", entry)
