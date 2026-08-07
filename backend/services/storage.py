"""
services/storage.py
===================
Centralized JSON storage layer for AutoBiz AI.

This module handles all read/write operations for the JSON storage files,
ensuring thread safety and consistent behavior across the application.
"""

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# ── Storage paths ─────────────────────────────────────────────────────────────
_DATA_DIR = Path(__file__).parent.parent / "data"

_FILES = {
    "local.json": "[]",
    "business.json": "{}",
    "pending_actions.json": "[]",
    "agent_logs.json": "[]",
    "tasks.json": "[]",
    "users.json": "{}"
}

# Thread-safe write lock
_LOCK = threading.Lock()


def _ensure_files() -> None:
    """Create the data directory and all JSON files with default structure if they do not exist."""
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    for file_name, default_content in _FILES.items():
        file_path = _DATA_DIR / file_name
        if not file_path.exists():
            file_path.write_text(default_content, encoding="utf-8")

# Initialize files on module import
_ensure_files()


# ── Core Storage Functions ────────────────────────────────────────────────────

def load_json(file_name: str) -> Union[List[Any], Dict[str, Any]]:
    """Load JSON data from a file."""
    file_path = _DATA_DIR / file_name
    
    if not file_path.exists():
        _ensure_files()
        
    with _LOCK:
        raw = file_path.read_text(encoding="utf-8")
        
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Return default structure if file is corrupted
        default_content = _FILES.get(file_name, "[]")
        return [] if default_content == "[]" else {}


def save_json(file_name: str, data: Any) -> None:
    """Save data to a JSON file."""
    file_path = _DATA_DIR / file_name
    
    if not file_path.exists():
        _ensure_files()
        
    with _LOCK:
        file_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def append_json(file_name: str, item: Any) -> None:
    """Append an item to a JSON file containing a list."""
    file_path = _DATA_DIR / file_name
    if not file_path.exists():
        _ensure_files()
        
    with _LOCK:
        try:
            raw = file_path.read_text(encoding="utf-8")
            data = json.loads(raw)
        except (json.JSONDecodeError, FileNotFoundError):
            data = []
            
        if not isinstance(data, list):
            data = []
        data.append(item)
        file_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def update_json(file_name: str, updates: Dict[str, Any]) -> None:
    """Update a JSON file containing an object with new keys/values."""
    file_path = _DATA_DIR / file_name
    if not file_path.exists():
        _ensure_files()
        
    with _LOCK:
        try:
            raw = file_path.read_text(encoding="utf-8")
            data = json.loads(raw)
        except (json.JSONDecodeError, FileNotFoundError):
            data = {}
            
        if not isinstance(data, dict):
            data = {}
        data.update(updates)
        file_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def delete_json(file_name: str) -> None:
    """Delete a JSON file."""
    file_path = _DATA_DIR / file_name
    if file_path.exists():
        with _LOCK:
            if file_path.exists():
                file_path.unlink()


# ── Business Memory Helpers ───────────────────────────────────────────────────

def save_business_fact(key: str, value: Any) -> None:
    """Save a specific business fact."""
    update_json("business.json", {key: value})


def get_business_fact(key: str) -> Any:
    """Retrieve a specific business fact."""
    data = load_json("business.json")
    if isinstance(data, dict):
        return data.get(key)
    return None


def get_all_business_facts() -> Dict[str, Any]:
    """Retrieve all business facts."""
    data = load_json("business.json")
    return data if isinstance(data, dict) else {}


# ── Agent Logs Helpers ────────────────────────────────────────────────────────

def log_agent_execution(
    agent: str,
    user_message: str,
    tools_used: list,
    delegated_agents: list,
    execution_time: float,
    status: str,
    timestamp: Optional[str] = None
) -> None:
    """Log an agent's execution to agent_logs.json."""
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat()
        
    entry = {
        "timestamp": timestamp,
        "agent": agent,
        "user_message": user_message,
        "tools_used": tools_used,
        "delegated_agents": delegated_agents,
        "execution_time": execution_time,
        "status": status
    }
    append_json("agent_logs.json", entry)


# ── Tasks Helpers ─────────────────────────────────────────────────────────────

def create_task(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new task."""
    if "id" not in task_data:
        task_data["id"] = str(uuid.uuid4())
    append_json("tasks.json", task_data)
    return task_data


def update_task(task_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update an existing task."""
    tasks = load_json("tasks.json")
    if isinstance(tasks, list):
        for task in tasks:
            if isinstance(task, dict) and task.get("id") == task_id:
                task.update(updates)
                save_json("tasks.json", tasks)
                return task
    return None


def delete_task(task_id: str) -> None:
    """Delete a task by ID."""
    tasks = load_json("tasks.json")
    if isinstance(tasks, list):
        filtered_tasks = [t for t in tasks if isinstance(t, dict) and t.get("id") != task_id]
        save_json("tasks.json", filtered_tasks)


def get_tasks() -> List[Any]:
    """Retrieve all tasks."""
    data = load_json("tasks.json")
    return data if isinstance(data, list) else []


# ── Users Helpers ─────────────────────────────────────────────────────────────

def create_user(user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create or overwrite a user profile."""
    update_json("users.json", {user_id: user_data})
    return user_data


def update_user(user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update an existing user profile."""
    users = load_json("users.json")
    if isinstance(users, dict) and user_id in users:
        if isinstance(users[user_id], dict):
            users[user_id].update(updates)
            save_json("users.json", users)
            return users[user_id]
    return None


def get_user(user_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a user profile."""
    users = load_json("users.json")
    if isinstance(users, dict):
        return users.get(user_id)
    return None
