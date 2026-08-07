"""
services/pending.py
===================
Pending Action store for Human Approval Mode.

Storage: backend/data/pending_actions.json

Schema of each entry:
{
    "id":          "uuid4 string",
    "timestamp":   "ISO 8601 UTC",
    "expires_at":  "ISO 8601 UTC",
    "agent_id":    "msg-001",
    "agent_name":  "Messenger & Drafter",
    "tool":        "send_email",
    "args":        {"to": "john@example.com", "subject": "Meeting"},
    "description": "Send email to John about tomorrow's meeting",
    "status":      "waiting"   // "waiting" | "approved" | "cancelled" | "expired"
}

Thread-safety: guarded by storage layer.
"""

import uuid
from datetime import datetime, timezone, timedelta
from services.storage import load_json, save_json

# Configurable expiry (minutes)
EXPIRY_MINUTES = 30


# ── Internal helpers ──────────────────────────────────────────────────────────

def _load() -> list[dict]:
    data = load_json("pending_actions.json")
    return data if isinstance(data, list) else []


def _save(actions: list[dict]) -> None:
    save_json("pending_actions.json", actions)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _is_expired(action: dict) -> bool:
    try:
        expires = datetime.fromisoformat(action["expires_at"])
        return _now_utc() > expires
    except (KeyError, ValueError):
        return True


# ── Public API ────────────────────────────────────────────────────────────────

def create_pending_action(
    agent_id:    str,
    agent_name:  str,
    tool:        str,
    args:        dict,
    description: str,
    expiry_minutes: int = EXPIRY_MINUTES,
) -> dict:
    """
    Create a new pending action entry with status "waiting".
    Returns the full action dict (including generated id).
    """
    now     = _now_utc()
    action  = {
        "id":          str(uuid.uuid4()),
        "timestamp":   now.isoformat(),
        "expires_at":  (now + timedelta(minutes=expiry_minutes)).isoformat(),
        "agent_id":    agent_id,
        "agent_name":  agent_name,
        "tool":        tool,
        "args":        args,
        "description": description,
        "status":      "waiting",
    }
    actions = _load()
    # Auto-cancel any other waiting actions for this agent (only one at a time)
    for existing in actions:
        if existing["agent_id"] == agent_id and existing["status"] == "waiting":
            existing["status"] = "cancelled"
    actions.append(action)
    _save(actions)
    return action


def get_waiting_action(agent_id: str) -> dict | None:
    """
    Return the most recent 'waiting' (non-expired) action for this agent.
    Marks expired actions inline and returns None if nothing is waiting.
    """
    actions  = _load()
    modified = False
    result   = None

    for action in reversed(actions):          # most recent first
        if action["agent_id"] != agent_id:
            continue
        if action["status"] != "waiting":
            continue
        if _is_expired(action):
            action["status"] = "expired"
            modified = True
            continue
        result = action
        break

    if modified:
        _save(actions)

    return result


def resolve_action(action_id: str, status: str) -> dict | None:
    """
    Update the status of a pending action to 'approved' or 'cancelled'.
    Returns the updated action, or None if not found.
    """
    if status not in ("approved", "cancelled"):
        raise ValueError(f"Invalid status: {status!r}. Use 'approved' or 'cancelled'.")

    actions = _load()
    target  = None
    for action in actions:
        if action["id"] == action_id:
            action["status"] = status
            action["resolved_at"] = _now_utc().isoformat()
            target = action
            break

    if target:
        _save(actions)
    return target


def cleanup_expired(agent_id: str | None = None) -> int:
    """
    Mark all expired 'waiting' actions as 'expired'.
    Optionally filter by agent_id. Returns count of actions marked.
    """
    actions  = _load()
    count    = 0
    for action in actions:
        if agent_id and action["agent_id"] != agent_id:
            continue
        if action["status"] == "waiting" and _is_expired(action):
            action["status"] = "expired"
            count += 1
    if count:
        _save(actions)
    return count
