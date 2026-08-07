"""
workflow/graph.py
=================
Reusable LangGraph graph builder for all AutoBiz AI agents.

Current graph shape (Task 6 — Human Approval Mode):

    START
      ↓
    [node_load_memory]        — reads local.json → history
      ↓
    [node_planner]            — LLM routing + approval-response detection
      ↓
    <conditional: _route_after_planner>
      ├── is_approval_response  → [node_approval_handler] → [node_call_llm] → END
      ├── awaiting_human        → [node_create_pending]   → [node_call_llm] → END
      ├── needs_tools           → [node_tool_executor]    → [node_call_llm] → END
      └── default               →                           [node_call_llm] → END

High-risk tools (require human approval before execution):
    send_email, send_whatsapp, create_invoice, schedule_meeting,
    delete_file, delete_data, transfer_money, publish_post, book_appointment

Low-risk tools (execute immediately):
    calculator, datetime_tool, memory_lookup, delegate_to_agent

Future node (Task 7 — MCP):
    [node_mcp_bridge] — replace node_tool_executor with real MCP server calls

Agent files NEVER change — they only call build_agent_graph().
"""

from __future__ import annotations

import json
import re
from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from services import llm, memory as mem
from services import pending as pending_svc


# ═══════════════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════════════

# Tools whose execution MUST be approved by the user before running.
# Any tool_name returned by the planner that is in this set will create
# a pending action instead of executing immediately.
# When MCP tools are added (Task 7), add them here if they are destructive.
HIGH_RISK_TOOLS: frozenset[str] = frozenset({
    "send_email", "email", "gmail",
    "send_whatsapp", "whatsapp", "send_message",
    "create_invoice", "invoice", "send_invoice",
    "schedule_meeting", "meeting", "book_meeting",
    "delete_file", "delete_data", "delete",
    "transfer_money", "payment", "pay",
    "publish_post", "post_content",
    "book_appointment", "submit_form",
})

# Keywords that indicate user is approving a pending action
_APPROVAL_KEYWORDS: frozenset[str] = frozenset({
    "approve", "yes", "confirm", "ok", "okay", "proceed",
    "go ahead", "send it", "do it", "execute", "go", "sure",
    "accept", "agreed", "done", "yep", "yup",
})

# Keywords that indicate user is cancelling a pending action
_CANCEL_KEYWORDS: frozenset[str] = frozenset({
    "cancel", "no", "stop", "discard", "don't", "do not",
    "abort", "reject", "decline", "nope", "nah", "skip",
    "nevermind", "never mind", "hold on", "wait",
})


def _classify_approval_response(message: str) -> str | None:
    """
    Check if the user message is an approval/cancellation response.

    Returns "approve", "cancel", or None (not an approval response).
    """
    lower = message.lower().strip().rstrip("!.,")
    words = set(lower.split())

    if words & _APPROVAL_KEYWORDS or lower in _APPROVAL_KEYWORDS:
        return "approve"
    if words & _CANCEL_KEYWORDS or lower in _CANCEL_KEYWORDS:
        return "cancel"
    return None


# ═══════════════════════════════════════════════════════════════════════════
# State definition
# ═══════════════════════════════════════════════════════════════════════════

class AgentState(TypedDict):
    """
    Shared state flowing through every node of the graph.

    Core fields
    -----------
    agent_id          : str   — e.g. "msg-001"
    agent_name        : str   — e.g. "Messenger & Drafter"
    system_prompt     : str   — agent's personality
    user_message      : str   — current user input
    history           : list  — OpenAI-format chat history from shared memory
    reply             : str   — final response text

    Planner / Tool fields (Task 4+)
    --------------------------------
    plan              : str   — planner's raw JSON decision
    needs_tools       : bool  — router flag: low-risk tool ready to run
    tool_calls        : list  — [{"name": "calculator", "args": {}}]
    tool_results      : list  — [{"name": "calculator", "success": True, "result": "25"}]

    Human Approval fields (Task 6)
    --------------------------------
    awaiting_human    : bool  — True when a high-risk action needs approval
    is_approval_response: bool  — True when user is responding to a pending action
    approval_decision : str   — "approve" | "cancel" | ""
    pending_action    : dict  — the pending action dict from pending_actions.json
    """

    # ── Core ──────────────────────────────────────────────────────────────
    agent_id:              str
    agent_name:            str
    system_prompt:         str
    user_message:          str
    history:               list
    business_context:      dict
    reply:                 str

    # ── Planner ───────────────────────────────────────────────────────────
    plan:                  str
    needs_tools:           bool
    tool_calls:            list
    tool_results:          list

    # ── Human Approval (Task 6) ────────────────────────────────────────────
    awaiting_human:        bool
    is_approval_response:  bool
    approval_decision:     str
    pending_action:        dict


# ═══════════════════════════════════════════════════════════════════════════
# Planner system prompt
# ═══════════════════════════════════════════════════════════════════════════

_PLANNER_SYSTEM = """\
You are a routing planner for an AI business assistant.
Your ONLY job is to decide what action is needed for the user's message.

Available low-risk tools (execute immediately, no approval needed):
{tool_descriptions}

ROUTING RULES — follow strictly:

1. CALCULATOR
   Use when: user asks for arithmetic (×, ÷, +, -, %, powers, percentages, totals).
   Example: "What is 245 times 88?" → calculator, expression "245*88"

2. DATETIME_TOOL
   Use when: user asks what the current date or time is.

3. MEMORY_LOOKUP
   Use when: user asks about facts mentioned earlier (company name, owner, location, business type, products, revenue, team size).

4. DELEGATE_TO_AGENT
   Use when: task requires deep specialist expertise from another domain.
   agents: manager | finance | marketing | sales | messenger | legal | data | ledger | alarmy

5. HIGH-RISK ACTIONS (require human approval — set requires_approval: true)
   These are real-world actions that cannot be undone easily:
   - send_email     → user wants to send an actual email
   - send_whatsapp  → user wants to send a WhatsApp message
   - create_invoice → user wants to create and send an invoice
   - schedule_meeting → user wants to schedule/book a real meeting
   - delete_data    → user wants to delete records or files
   - transfer_money → any payment or money transfer
   - publish_post   → publish content to social media
   For these, return: {{"needs_tool": true, "tool_name": "<action>", "tool_args": {{...}}, "requires_approval": true}}

7. NO TOOL — for general advice, strategy, writing help, explanations.

Respond ONLY with a single valid JSON object. No markdown, no explanation.

Standard tool:
{{"needs_tool": true, "tool_name": "<name>", "tool_args": {{"<key>": "<value>"}}, "requires_approval": false}}

High-risk action:
{{"needs_tool": true, "tool_name": "send_email", "tool_args": {{"to": "...", "subject": "...", "body": "..."}}, "requires_approval": true}}

No tool:
{{"needs_tool": false}}
"""


def _build_planner_prompt(tool_descriptions: str) -> str:
    return _PLANNER_SYSTEM.format(tool_descriptions=tool_descriptions)


def _parse_planner_response(raw: str) -> dict:
    """
    Robustly parse the planner's JSON output.
    Strips markdown fences, extracts first JSON block, falls back to no-tool.
    """
    text = raw.strip()
    text = re.sub(r"^```[a-z]*\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        text = match.group(0)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"needs_tool": False}


# ═══════════════════════════════════════════════════════════════════════════
# Graph Nodes
# ═══════════════════════════════════════════════════════════════════════════

async def node_load_memory(state: AgentState) -> dict:
    """
    NODE: load_memory
    -----------------
    Reads backend/data/local.json → converts to OpenAI message list.
    Also reads business.json into business_context.
    Also runs cleanup of expired pending actions for this agent.
    """
    history = mem.build_conversation_messages()
    business = mem.load_business_memory()
    pending_svc.cleanup_expired(state["agent_id"])  # housekeeping
    return {"history": history, "business_context": business}


async def node_planner(state: AgentState) -> dict:
    """
    NODE: planner
    -------------
    Phase 1: Check if the user is responding to a pending approval action.
             (Fast, server-side keyword matching — no LLM call needed.)

    Phase 2: LLM routing call to decide: tool / high-risk action / delegation / direct reply.

    Sets: needs_tools, tool_calls, awaiting_human, is_approval_response,
          approval_decision, pending_action, plan.
    """
    from tools import get_tool_descriptions  # lazy import — avoids circular refs

    agent_id     = state["agent_id"]
    user_message = state["user_message"]

    # ── Phase 1: Approval response detection (server-side, fast) ─────────
    pending = pending_svc.get_waiting_action(agent_id)
    if pending:
        decision = _classify_approval_response(user_message)
        if decision:
            return {
                "is_approval_response": True,
                "approval_decision":    decision,
                "pending_action":       pending,
                "needs_tools":          False,
                "awaiting_human":       False,
                "tool_calls":           [],
                "plan":                 f"[approval-response:{decision}]",
            }

    # ── Phase 2: LLM planner routing ─────────────────────────────────────
    tool_descriptions = get_tool_descriptions()
    planner_system    = _build_planner_prompt(tool_descriptions)
    recent_history    = state["history"][-6:] if len(state["history"]) > 6 else state["history"]

    raw_decision = await llm.generate_response(
        system_prompt=planner_system,
        history=recent_history,
        user_message=user_message,
    )

    parsed = _parse_planner_response(raw_decision)

    if not parsed.get("needs_tool") or not parsed.get("tool_name"):
        return {
            "needs_tools":          False,
            "tool_calls":           [],
            "awaiting_human":       False,
            "is_approval_response": False,
            "pending_action":       {},
            "plan":                 raw_decision,
        }

    tool_name      = parsed["tool_name"]
    tool_args      = parsed.get("tool_args", {})
    req_approval   = parsed.get("requires_approval", False)

    # Server-side safety net: also flag based on HIGH_RISK_TOOLS set
    is_high_risk   = req_approval or (tool_name.lower() in HIGH_RISK_TOOLS)

    if is_high_risk:
        # High-risk: park the action for human approval — do NOT execute yet
        return {
            "needs_tools":          False,   # don't execute via tool_executor
            "tool_calls":           [{"name": tool_name, "args": tool_args}],
            "awaiting_human":       True,
            "is_approval_response": False,
            "pending_action":       {},      # filled by node_create_pending
            "plan":                 raw_decision,
        }

    # Low-risk: proceed to tool_executor immediately
    return {
        "needs_tools":          True,
        "tool_calls":           [{"name": tool_name, "args": tool_args}],
        "awaiting_human":       False,
        "is_approval_response": False,
        "pending_action":       {},
        "plan":                 raw_decision,
    }


async def node_create_pending(state: AgentState) -> dict:
    """
    NODE: create_pending
    --------------------
    Creates a pending action entry in pending_actions.json.
    Builds a context block so node_call_llm generates a natural approval
    request message for the user.

    The actual tool is NOT executed here — it waits for "Approve".
    """
    tool_call   = state["tool_calls"][0] if state.get("tool_calls") else {}
    tool_name   = tool_call.get("name", "action")
    tool_args   = tool_call.get("args", {})

    # Human-readable description of what's pending
    args_text   = ", ".join(f"{k}: {v}" for k, v in tool_args.items()) if tool_args else "no details"
    description = f"{tool_name.replace('_', ' ').title()} — {args_text}"

    action = pending_svc.create_pending_action(
        agent_id    = state["agent_id"],
        agent_name  = state["agent_name"],
        tool        = tool_name,
        args        = tool_args,
        description = description,
    )

    # Build context for node_call_llm → it will generate the approval request message
    context = {
        "name":    "pending_approval",
        "success": True,
        "result":  (
            f"PENDING ACTION CREATED\n"
            f"Action: {tool_name.replace('_', ' ').title()}\n"
            f"Details: {json.dumps(tool_args, ensure_ascii=False)}\n"
            f"Status: Waiting for user approval\n"
            f"Action ID: {action['id']}\n\n"
            f"INSTRUCTION: Tell the user what action you've prepared (in natural language). "
            f"Ask them to reply 'Approve' to proceed or 'Cancel' to discard. "
            f"Do NOT mention 'Action ID' or technical details."
        ),
    }

    return {
        "tool_results":  [context],
        "pending_action": action,
        "awaiting_human": True,
    }


async def node_approval_handler(state: AgentState) -> dict:
    """
    NODE: approval_handler
    ----------------------
    Handles the user's Approve / Cancel response to a pending action.

    Approve: marks action as approved, simulates execution, builds success context.
    Cancel:  marks action as cancelled, builds cancellation context.

    Future (Task 7 — MCP): replace the simulated execution block with real
    MCP tool calls when the corresponding MCP server is available.
    """
    decision = state.get("approval_decision", "cancel")
    action   = state.get("pending_action", {})
    action_id = action.get("id", "")
    tool_name = action.get("tool", "action")
    tool_args = action.get("args", {})

    if decision == "approve":
        # Resolve the pending action
        pending_svc.resolve_action(action_id, "approved")

        # ── Simulated execution ───────────────────────────────────────────
        # Task 7 (MCP): replace this block with real tool/MCP calls.
        # Example:
        #   if tool_name == "send_email":
        #       result = await mcp_gmail.send(tool_args)
        # ─────────────────────────────────────────────────────────────────
        args_summary = ", ".join(f"{k}: {v}" for k, v in tool_args.items()) if tool_args else "no parameters"
        simulated_result = (
            f"ACTION APPROVED AND EXECUTED (simulated)\n"
            f"Action: {tool_name.replace('_', ' ').title()}\n"
            f"Parameters: {args_summary}\n"
            f"Result: Success\n\n"
            f"INSTRUCTION: Confirm to the user that the action was completed successfully. "
            f"Be brief and natural. Do not mention 'simulated' — present it as done."
        )

        context = {
            "name":    "action_approved",
            "success": True,
            "result":  simulated_result,
        }

    else:  # cancel
        pending_svc.resolve_action(action_id, "cancelled")

        context = {
            "name":    "action_cancelled",
            "success": True,
            "result":  (
                f"ACTION CANCELLED\n"
                f"Action: {tool_name.replace('_', ' ').title()}\n\n"
                f"INSTRUCTION: Acknowledge the cancellation politely. "
                f"Offer to help with anything else."
            ),
        }

    return {
        "tool_results":   [context],
        "awaiting_human": False,
    }


async def node_tool_executor(state: AgentState) -> dict:
    """
    NODE: tool_executor
    -------------------
    Executes every LOW-RISK tool_call in state and collects structured results.
    High-risk actions never reach this node — they go through node_create_pending.

    Task 7 (MCP): replace or supplement with node_mcp_bridge for external tools.
    """
    from tools import TOOL_REGISTRY  # lazy import

    results = []
    for call in state.get("tool_calls", []):
        tool_name = call.get("name", "")
        tool_args = call.get("args", {})

        if tool_name in TOOL_REGISTRY:
            try:
                result = await TOOL_REGISTRY[tool_name].execute(tool_args)
            except Exception as exc:
                result = {"name": tool_name, "success": False, "error": f"Tool crashed: {exc}"}
        else:
            result = {
                "name":    tool_name,
                "success": False,
                "error":   f"Tool '{tool_name}' is not registered.",
            }
        results.append(result)

    return {"tool_results": results}


async def node_call_llm(state: AgentState) -> dict:
    """
    NODE: call_llm
    --------------
    Sends system_prompt + history + context (tool/approval results) + user_message
    to OpenRouter and writes the final reply into state.

    Handles four context types:
    - Regular tool results (calculator, datetime, memory_lookup, delegation)
    - Pending approval context (approval request message)
    - Approval confirmed context (success message)
    - Cancellation context (cancellation message)
    """
    user_message = state["user_message"]
    history      = state["history"]

    tool_results = state.get("tool_results", [])
    if tool_results:
        tool_lines = []
        for r in tool_results:
            if r.get("success"):
                source = f"[{r.get('delegated_agent', r['name'])}]"
                tool_lines.append(f"{source}\n{r['result']}")
            else:
                source = f"[{r.get('delegated_agent', r['name'])}]"
                tool_lines.append(f"{source} unavailable — {r.get('error', 'unknown error')}")

        tool_block = (
            "CONTEXT (use to generate your response — do not expose technical names or IDs):\n\n"
            + "\n\n".join(tool_lines)
        )
        history = list(history) + [{"role": "assistant", "content": tool_block}]

    system_prompt = state["system_prompt"]
    business_context = state.get("business_context")
    if business_context:
        system_prompt += f"\n\nBUSINESS CONTEXT (facts about the user's business):\n{json.dumps(business_context, indent=2, ensure_ascii=False)}"

    # Tool 9: Explain Reasoning
    system_prompt += "\n\nREASONING INSTRUCTION:\nYou must wrap your internal thought process (e.g. why you chose a tool, why you made a recommendation) inside <thought>...</thought> blocks before providing the final answer."

    reply = await llm.generate_response(
        system_prompt=system_prompt,
        history=history,
        user_message=user_message,
    )
    
    # Extract thought blocks
    import re
    import os
    from services.storage import append_json
    from datetime import datetime, timezone

    DEBUG_MODE = os.environ.get("DEBUG_MODE", "True").lower() in ("true", "1", "yes")
    
    thought_match = re.search(r'<thought>(.*?)</thought>', reply, re.DOTALL)
    if thought_match:
        thought_content = thought_match.group(1).strip()
        # Log to agent_logs
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent": state["agent_id"],
            "reasoning": thought_content,
            "status": "reasoning_logged"
        }
        append_json("agent_logs.json", log_entry)
        
        # Strip from reply if not in debug mode
        if not DEBUG_MODE:
            reply = re.sub(r'<thought>.*?</thought>\n*', '', reply, flags=re.DOTALL).strip()

    return {"reply": reply}


# ═══════════════════════════════════════════════════════════════════════════
# Future Node Stub (Task 7 — MCP)
# ═══════════════════════════════════════════════════════════════════════════

# async def node_mcp_bridge(state: AgentState) -> dict:
#     """
#     Task 7 — Route APPROVED high-risk tool calls through MCP server.
#     Called from node_approval_handler after user confirms.
#     Replace simulated execution in node_approval_handler with:
#         result = await node_mcp_bridge(state)
#     """
#     ...
#     return {"tool_results": [...]}


# ═══════════════════════════════════════════════════════════════════════════
# Conditional router
# ═══════════════════════════════════════════════════════════════════════════

def _route_after_planner(state: AgentState) -> str:
    """
    Return the next node name based on the planner's decision.

    Priority order:
    1. is_approval_response — user replied Approve/Cancel to a pending action
    2. awaiting_human       — planner detected a new high-risk action
    3. needs_tools          — planner found a low-risk tool to run
    4. default              — go straight to LLM
    """
    if state.get("is_approval_response"):
        return "node_approval_handler"
    if state.get("awaiting_human"):
        return "node_create_pending"
    if state.get("needs_tools") and state.get("tool_calls"):
        return "node_tool_executor"
    return "node_call_llm"


# ═══════════════════════════════════════════════════════════════════════════
# Graph Builder
# ═══════════════════════════════════════════════════════════════════════════

def build_agent_graph(system_prompt: str):  # noqa: ARG001
    """
    Build and compile a LangGraph StateGraph for one agent.

    The compiled graph is stateless — `system_prompt` is stored in the
    initial state dict passed by each agent's process() at ainvoke time.

    Returns
    -------
    CompiledStateGraph  — call `await graph.ainvoke(initial_state)` to run.
    """
    graph: StateGraph = StateGraph(AgentState)

    # ── Register nodes ────────────────────────────────────────────────────
    graph.add_node("node_load_memory",    node_load_memory)
    graph.add_node("node_planner",        node_planner)
    graph.add_node("node_approval_handler", node_approval_handler)
    graph.add_node("node_create_pending", node_create_pending)
    graph.add_node("node_tool_executor",  node_tool_executor)
    graph.add_node("node_call_llm",       node_call_llm)

    # ── Fixed edges ───────────────────────────────────────────────────────
    graph.add_edge(START,                   "node_load_memory")
    graph.add_edge("node_load_memory",      "node_planner")

    # ── Conditional branch after planner ─────────────────────────────────
    graph.add_conditional_edges(
        "node_planner",
        _route_after_planner,
        {
            "node_approval_handler": "node_approval_handler",
            "node_create_pending":   "node_create_pending",
            "node_tool_executor":    "node_tool_executor",
            "node_call_llm":         "node_call_llm",
        },
    )

    # ── Converging paths → node_call_llm → END ────────────────────────────
    graph.add_edge("node_approval_handler", "node_call_llm")
    graph.add_edge("node_create_pending",   "node_call_llm")
    graph.add_edge("node_tool_executor",    "node_call_llm")
    graph.add_edge("node_call_llm",         END)

    return graph.compile()
