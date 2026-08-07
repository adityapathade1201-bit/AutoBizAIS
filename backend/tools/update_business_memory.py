"""
tools/update_business_memory.py
===============================
Extracts and saves structured business information into the shared business memory.
"""

import json
from services import memory as mem

NAME        = "update_business_memory"
DESCRIPTION = (
    "Extracts important business facts provided by the user (like company name, industry, "
    "products, suppliers, preferences) and saves them into the shared business memory."
)
PARAMETERS  = (
    '{"facts": {"company_name": "SK Commerce", "industry": "Cosmetics", "supplier": "ABC Traders"}}'
)

async def execute(args: dict) -> dict:
    """
    Save the given facts into business.json.
    
    Args
    ----
    args["facts"] : dict — Key-value pairs of the facts to save.
    
    Returns
    -------
    dict with success/result.
    """
    facts = args.get("facts", {})
    if not isinstance(facts, dict) or not facts:
        return {
            "name": NAME,
            "success": False,
            "error": "No valid 'facts' dictionary provided."
        }
        
    try:
        updated_data = mem.update_business_memory(facts)
        return {
            "name": NAME,
            "success": True,
            "result": f"Successfully updated business memory. Current memory: {json.dumps(updated_data, ensure_ascii=False)}"
        }
    except Exception as e:
        return {
            "name": NAME,
            "success": False,
            "error": f"Failed to update business memory: {e}"
        }
