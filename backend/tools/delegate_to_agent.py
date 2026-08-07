"""
tools/delegate_to_agent.py
===========================
Multi-agent delegation tool for AutoBiz AI.

Allows any agent to delegate a sub-task to another specialist agent.
The delegated agent runs with full shared memory context but bypasses
the planner to prevent infinite recursion.

Delegation chain is automatically logged to local.json because every
delegated agent saves its turn via memory.save_turn().

Circular import prevention
--------------------------
Agent modules are loaded with importlib.import_module() INSIDE execute(),
not at module level. This means: tools/__init__.py → delegate_to_agent.py
is safe — no module-level import of agents/* happens here.

Recursion prevention
--------------------
Uses a Python contextvars.ContextVar (_DELEGATION_DEPTH) to track nesting.
Delegated agents are limited to depth=1 — they cannot delegate further.
This prevents A → B → A → ... infinite loops.
"""

import importlib
from contextvars import ContextVar

from agents.registry import AGENT_REGISTRY
from services import llm, memory as mem

NAME        = "delegate_to_agent"
DESCRIPTION = (
    "Delegates a specific sub-task to another specialist AI agent and returns their response. "
    "Use when the current question requires deep expertise from a different domain "
    "(e.g. finance analysis, legal review, draft writing, sales strategy)."
)
PARAMETERS  = (
    '{"agent": "<agent key: manager|finance|marketing|sales|messenger|legal|data|ledger|alarmy>", '
    '"task": "<precise task description for the delegated agent>"}'
)

# ── Recursion guard ───────────────────────────────────────────────────────────
# Tracks delegation nesting depth in the current async call chain.
# When an agent is delegated to (depth >= 1) it should not delegate further.
_DELEGATION_DEPTH: ContextVar[int] = ContextVar("_delegation_depth", default=0)

_MAX_DEPTH = 1  # Primary agent can delegate; delegated agent cannot re-delegate


def _agent_list_for_description() -> str:
    """Return a compact listing of available agents (used in PARAMETERS above)."""
    return " | ".join(AGENT_REGISTRY.keys())


async def execute(args: dict) -> dict:
    """
    Delegate a task to a specialist agent and return its response.

    Args
    ----
    args["agent"] : str — agent key from AGENT_REGISTRY
                          (manager, finance, marketing, sales, messenger,
                           legal, data, ledger, alarmy)
    args["task"]  : str — the specific task or question for that agent

    Returns
    -------
    {
        "name":             "delegate_to_agent",
        "success":          True,
        "result":           "<agent's response text>",
        "delegated_agent":  "Finance Expert"
    }

    Recursion guard
    ---------------
    If called from within a delegated context (depth >= _MAX_DEPTH),
    returns an error to prevent infinite loops.
    """
    current_depth = _DELEGATION_DEPTH.get()

    # ── Recursion guard ───────────────────────────────────────────────────
    if current_depth >= _MAX_DEPTH:
        return {
            "name":    NAME,
            "success": False,
            "error":   "Delegation depth limit reached — cannot delegate further from within a delegated call.",
        }

    agent_key = args.get("agent", "").strip().lower()
    task      = args.get("task", "").strip()

    if not agent_key:
        return {"name": NAME, "success": False, "error": "No 'agent' key provided."}
    if not task:
        return {"name": NAME, "success": False, "error": "No 'task' provided for delegation."}

    # ── Look up agent ─────────────────────────────────────────────────────
    agent_info = AGENT_REGISTRY.get(agent_key)
    if not agent_info:
        available = ", ".join(AGENT_REGISTRY.keys())
        return {
            "name":    NAME,
            "success": False,
            "error":   f"Unknown agent '{agent_key}'. Available: {available}",
        }

    # ── Load agent module (runtime import — no circular dependency) ───────
    module_path = f"agents.{agent_info['module']}"
    try:
        agent_module = importlib.import_module(module_path)
    except ModuleNotFoundError as exc:
        return {"name": NAME, "success": False, "error": f"Agent module not found: {exc}"}

    agent_id   = agent_info["id"]
    agent_name = agent_info["name"]

    # ── Run delegated agent (bypasses planner to prevent recursion) ───────
    # We call the LLM directly with the agent's system prompt + shared memory.
    # This is intentional: delegated sub-tasks should not trigger further
    # delegation — they should just answer with their specialist knowledge.
    system_prompt = getattr(agent_module, "SYSTEM_PROMPT", "You are a helpful business assistant.")
    history       = mem.build_conversation_messages()

    # Set recursion depth for this async context
    token = _DELEGATION_DEPTH.set(current_depth + 1)
    try:
        reply = await llm.generate_response(
            system_prompt=system_prompt,
            history=history,
            user_message=task,
        )
    finally:
        _DELEGATION_DEPTH.reset(token)

    # ── Log the delegated interaction to shared memory ────────────────────
    # This makes the delegation chain visible in local.json and available
    # to future agents via shared memory.
    mem.save_turn(
        agent_id=agent_id,
        agent_name=f"{agent_name} [delegated]",
        user_message=task,
        assistant_reply=reply,
    )

    return {
        "name":            NAME,
        "success":         True,
        "result":          reply,
        "delegated_agent": agent_name,
    }
