import json
from datetime import datetime, timezone
from services import llm
from services.storage import load_json, save_json, append_json

_EXTRACTOR_SYSTEM = """
You are a background Business Fact Extractor.
The user has sent a message to an AI assistant. Check if the user mentioned any persistent facts about their business.
Examples of facts: company name, industry, products they sell, suppliers they buy from, clients, revenue, employee count, GST numbers, personal preferences (e.g., preferred language).

If NO new or updated facts are present, output exactly:
{"extracted": false}

If facts ARE present, output a JSON object containing ONLY the NEW or UPDATED facts, matching this exact schema:
{
  "extracted": true,
  "company": {
    "name": "...",
    "industry": "...",
    "gst_number": "...",
    "employees": 12,
    "monthly_revenue": 400000,
    "preferred_language": "..."
  },
  "products": ["..."],
  "suppliers": ["..."],
  "customers": ["..."],
  "notes": ["..."]
}

Important:
- Only include fields that the user explicitly mentioned in the message.
- For numbers like employees or revenue, output raw numbers (e.g. 400000 not "4 lakh").
- Do not make up information or guess.
- Return ONLY valid JSON.
"""

async def process_message_for_business_facts(user_message: str, agent_id: str):
    # Skip trivial messages to save API calls
    msg_lower = user_message.lower().strip()
    if len(msg_lower) < 4 or msg_lower in ["approve", "cancel", "yes", "no", "ok", "okay"]:
        return

    try:
        raw_response = await llm.generate_response(
            system_prompt=_EXTRACTOR_SYSTEM,
            history=[],
            user_message=user_message
        )
        
        text = raw_response.strip()
        if text.startswith("```"):
            lines = text.split('\n')
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()
            
        data = json.loads(text)
        if not data.get("extracted"):
            return
            
        # Merge facts into business.json
        current = load_json("business.json")
        if not isinstance(current, dict):
            current = {}

        if "company" not in current:
            current["company"] = {}
        for list_key in ["products", "suppliers", "customers", "notes"]:
            if list_key not in current:
                current[list_key] = []

        changes_made = []

        # Merge company object
        if "company" in data and isinstance(data["company"], dict):
            for k, v in data["company"].items():
                if v and current["company"].get(k) != v:
                    old_val = current["company"].get(k)
                    changes_made.append({"field": f"company.{k}", "old": old_val, "new": v})
                    current["company"][k] = v
        
        # Merge array fields (prevent duplicates)
        for list_key in ["products", "suppliers", "customers", "notes"]:
            if list_key in data and isinstance(data[list_key], list):
                for item in data[list_key]:
                    if item and item not in current[list_key]:
                        changes_made.append({"field": list_key, "old": None, "new": item})
                        current[list_key].append(item)
                        
        if changes_made:
            save_json("business.json", current)
            
            # Log the business memory change
            timestamp = datetime.now(timezone.utc).isoformat()
            for change in changes_made:
                log_entry = {
                    "timestamp": timestamp,
                    "agent": agent_id,
                    "user_message": user_message,
                    "tools_used": ["business_extractor"],
                    "delegated_agents": [],
                    "execution_time": 0.0,
                    "status": "business_memory_updated",
                    "field": change["field"],
                    "old_value": change["old"],
                    "new_value": change["new"]
                }
                append_json("agent_logs.json", log_entry)
                
    except Exception:
        # Silently fail background extraction to not break chat
        pass
