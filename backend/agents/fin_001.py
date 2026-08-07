"""
Agent: Finance Expert  (fin-001)
----------------------------------
Financial advisor for SMEs — budgeting, cash flow, profit analysis, funding,
and Tally integration guidance.
"""

from services import memory
from workflow.graph import build_agent_graph

AGENT_ID   = "fin-001"
AGENT_NAME = "Finance Expert"

SYSTEM_PROMPT = """You are the Finance Expert.
Role: Chief Financial Officer.
Expert in: Cash flow, Profit, Expenses, Budgets, Revenue, Pricing, Forecasting, Invoices, Taxes.
Tone: Analytical, Precise.

Rules:
- Whenever numbers appear automatically use the Calculator tool. Never guess calculations.
- You share business memory with all agents. Use it automatically. Do not ask for facts already known.
- Avoid one-line answers. Provide structured professional responses.
- Explain reasoning. Suggest next steps. Offer practical recommendations.
- When appropriate use bullet points and action plans.
"""

_graph = build_agent_graph(SYSTEM_PROMPT)


async def process(message: str) -> str:
    result = await _graph.ainvoke({
        "agent_id":       AGENT_ID,
        "agent_name":     AGENT_NAME,
        "system_prompt":  SYSTEM_PROMPT,
        "user_message":   message,
        "history":        [],
        "reply":          "",
        "plan":           "",
        "needs_tools":    False,
        "tool_calls":     [],
        "tool_results":   [],
        "awaiting_human":       False,
        "is_approval_response": False,
        "approval_decision":    "",
        "pending_action":       {},
    })
    reply = result["reply"]
    memory.save_turn(AGENT_ID, AGENT_NAME, message, reply)
    return reply
