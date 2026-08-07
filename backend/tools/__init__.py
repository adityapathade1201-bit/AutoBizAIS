"""
tools/__init__.py
=================
Tool registry for AutoBiz AI.

Every tool file in this package must expose:
    NAME        : str   — unique identifier used by the planner
    DESCRIPTION : str   — one-line description for the planner prompt
    PARAMETERS  : str   — brief description of expected args (for planner)
    execute(args: dict) -> dict  — async function returning structured result

Adding a new tool (Task 6+):
    1. Create tools/my_tool.py  with NAME, DESCRIPTION, PARAMETERS, execute()
    2. Import it below and add to _TOOL_MODULES
    That's it — the planner automatically discovers it.
"""

from tools import calculator, datetime_tool, memory_lookup, delegate_to_agent, update_business_memory, analyze_spreadsheet, draft_email, schedule_task

# ── Registry ─────────────────────────────────────────────────────────────────
_TOOL_MODULES = [
    calculator,
    datetime_tool,
    memory_lookup,
    delegate_to_agent,
    update_business_memory,
    analyze_spreadsheet,
    draft_email,
    schedule_task
]

# name → module mapping for tool executor
TOOL_REGISTRY: dict = {m.NAME: m for m in _TOOL_MODULES}


def get_tool_descriptions() -> str:
    """
    Return a formatted string listing all available tools.
    Injected into the planner's system prompt so it knows what exists.
    """
    lines = []
    for m in _TOOL_MODULES:
        lines.append(f"- {m.NAME}: {m.DESCRIPTION}")
        lines.append(f"  Parameters: {m.PARAMETERS}")
    return "\n".join(lines)
