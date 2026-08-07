"""
Agent: Manager  (mgr-001)
---------------------------
The orchestrator — big-picture thinking, business planning, decision support,
and delegation across all business functions.
"""

import asyncio
import os
import re
from datetime import datetime, timezone
import time

from services import memory, llm, storage
from agents.registry import AGENT_REGISTRY

AGENT_ID   = "mgr-001"
AGENT_NAME = "Manager"

SYSTEM_PROMPT = """You are the Manager.
Role: The Manager is NOT another chatbot. The Manager is the CEO.

Responsibilities:
- Understand the user's request.
- Decide which specialist agents are required.
- Delegate work using delegate_to_agent.
- Collect specialist responses.
- Combine them into one professional answer.

Delegation Rules:
- Finance questions -> Finance Expert
- Reports -> Data Analyser
- Marketing -> Marketing Lead
- Sales -> Sales Agent
- Bookkeeping -> Ledgerer
- Meetings -> Alarmy
- Legal -> Legal Assistance
- Multi-domain requests -> Manager delegates to multiple specialists.

Rules:
- Never expose internal delegation. The user should only see one final polished response.
- You share business memory with all agents. Use it automatically. Do not ask for facts already known.
- Avoid one-line answers. Provide structured professional responses.
- Explain reasoning. Suggest next steps. Offer practical recommendations.
- When appropriate use bullet points and action plans.
"""

# Determine if Debug mode is enabled
DEBUG_MODE = os.environ.get("DEBUG_MODE", "True").lower() in ("true", "1", "yes")

_KEYWORD_RULES = {
    "ledger": ["invoice", "bookkeeping", "ledger", "transaction", "purchase", "expense", "receipt"],
    "finance": ["profit", "budget", "tax", "revenue", "cost", "cash flow", "pricing", "margin", "finance"],
    "marketing": ["campaign", "marketing", "seo", "ad", "instagram", "facebook", "branding", "social media"],
    "messenger": ["email", "message", "letter", "draft", "write", "whatsapp", "communicate"],
    "alarmy": ["meeting", "remind", "schedule", "agenda", "appointment", "calendar", "deadline"],
    "sales": ["sales", "lead", "conversion", "crm", "negotiation", "prospect", "pitch"],
    "data": ["report", "analytics", "trend", "kpi", "forecast", "analyze", "data", "metrics"],
    "legal": ["contract", "legal", "policy", "compliance", "law", "terms", "agreement"]
}

async def _classify_intent_llm(message: str) -> list:
    prompt = f"""
    The user asked: "{message}"
    Which of these specialist domains are needed to fully answer the request? 
    Options: ledger, finance, marketing, messenger, alarmy, sales, data, legal.
    Return ONLY a comma-separated list of the domains. If none apply, return "none".
    """
    try:
        reply = await llm.generate_response(system_prompt="You are a classifier. Reply with domains only.", history=[], user_message=prompt)
        domains = [d.strip() for d in reply.lower().split(",")]
        return [d for d in domains if d in _KEYWORD_RULES.keys()]
    except Exception:
        return []

async def _delegate(agent_key: str, task: str) -> str:
    from tools.delegate_to_agent import execute as delegate_exec
    result = await delegate_exec({"agent": agent_key, "task": task})
    if result.get("success"):
        return result.get("result", "")
    return result.get("error", "")

async def process(message: str) -> str:
    start_time = time.time()
    
    # 0. Check for approval keywords
    msg_lower = message.lower().strip()
    approval_keywords = {"approve", "yes", "confirm", "ok", "okay", "proceed", "go ahead", "send it", "do it", "execute", "go", "sure", "accept", "agreed", "done", "yep", "yup", "cancel", "no", "stop", "discard", "don't", "do not", "abort", "reject", "decline", "nope", "nah", "skip"}
    is_approval = False
    
    if msg_lower in approval_keywords or any(kw in msg_lower.split() for kw in approval_keywords):
        # We must route directly to the graph to allow node_approval_handler to catch it
        is_approval = True
        
    # 1. Deterministic Routing
    selected_agents = set()
    if not is_approval:
        for agent_key, keywords in _KEYWORD_RULES.items():
            if any(kw in msg_lower for kw in keywords):
                selected_agents.add(agent_key)
                
        # 2. LLM Fallback (if deterministic rules yield nothing)
        if not selected_agents:
            llm_agents = await _classify_intent_llm(message)
            selected_agents.update(llm_agents)
        
    # If still no agents selected, or it's an approval response, the manager handles it
    if not selected_agents:
        from workflow.graph import build_agent_graph
        graph = build_agent_graph(SYSTEM_PROMPT)
        result = await graph.ainvoke({
            "agent_id": AGENT_ID, "agent_name": AGENT_NAME,
            "system_prompt": SYSTEM_PROMPT, "user_message": message,
            "history": [], "reply": "", "business_context": memory.load_business_memory(),
            "plan": "", "needs_tools": False, "tool_calls": [], "tool_results": [],
            "awaiting_human": False, "is_approval_response": False, 
            "approval_decision": "", "pending_action": {}
        })
        reply = result["reply"]
        memory.save_turn(AGENT_ID, AGENT_NAME, message, reply)
        return reply

    # 3. Parallel Delegation
    delegated_agent_names = [AGENT_REGISTRY[k]["name"] for k in selected_agents]
    execution_type = "parallel" if len(selected_agents) > 1 else "sequential"
    
    tasks = []
    for agent_key in selected_agents:
        tasks.append(_delegate(agent_key, message))
        
    results = await asyncio.gather(*tasks)
    
    # 4. Result Synthesis
    combined_context = "\n\n".join([f"--- Response from {name} ---\n{res}" for name, res in zip(delegated_agent_names, results)])
    
    synthesis_prompt = SYSTEM_PROMPT + f"\n\nYou have delegated this task to specialists. Here are their responses:\n{combined_context}\n\nSynthesize this into a single, cohesive, professional response to the user. Remove duplicates, resolve conflicts, and do not expose internal delegation (e.g. don't say 'The Finance Expert said'). Present it as your unified answer. Maintain a professional tone. If any agent reported uncertainty or lack of confidence, you must either offer a clarification question or reflect that limitation honestly."
    
    history = memory.build_conversation_messages()
    business_context = memory.load_business_memory()
    if business_context:
        import json
        synthesis_prompt += f"\n\nBUSINESS CONTEXT:\n{json.dumps(business_context, indent=2, ensure_ascii=False)}"
        
    synthesis_prompt += "\n\nREASONING INSTRUCTION:\nYou must wrap your internal thought process (e.g. why you synthesized the way you did, what facts you prioritized) inside <thought>...</thought> blocks before providing the final answer."
        
    final_reply = await llm.generate_response(
        system_prompt=synthesis_prompt,
        history=history,
        user_message=message
    )
    
    thought_match = re.search(r'<thought>(.*?)</thought>', final_reply, re.DOTALL)
    if thought_match:
        thought_content = thought_match.group(1).strip()
        log_entry_thought = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent": AGENT_ID,
            "reasoning": thought_content,
            "status": "reasoning_logged"
        }
        storage.append_json("agent_logs.json", log_entry_thought)
        
        if not DEBUG_MODE:
            final_reply = re.sub(r'<thought>.*?</thought>\n*', '', final_reply, flags=re.DOTALL).strip()
            
    # 5. Debug Mode
    if DEBUG_MODE:
        debug_trace = f"[DEBUG TRACE: Manager \u2193 {', '.join(delegated_agent_names)} \u2193 Final Synthesis]\n\n"
        final_reply = debug_trace + final_reply

    # 6. Logging Extended
    exec_time = time.time() - start_time
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent": AGENT_ID,
        "user_message": message,
        "tools_used": ["delegate_to_agent"],
        "delegated_agents": delegated_agent_names,
        "execution_order": execution_type,
        "parallel_or_sequential": execution_type,
        "execution_time": round(exec_time, 2),
        "approval_required": False,
        "final_agent": AGENT_ID,
        "status": "success"
    }
    storage.append_json("agent_logs.json", log_entry)
    
    memory.save_turn(AGENT_ID, AGENT_NAME, message, final_reply)
    return final_reply
