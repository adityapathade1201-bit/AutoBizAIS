"""
tools/memory_lookup.py
======================
Searches shared local.json for facts mentioned by the user in any prior
conversation with any agent.

Extracts structured facts (company name, owner, location, business type, etc.)
using keyword pattern matching across the full conversation history.
Returns matched facts as a plain-English summary.
"""

import re
from services.memory import load_all

NAME        = "memory_lookup"
DESCRIPTION = (
    "Searches past conversations to retrieve facts like company name, owner name, "
    "business type, location, products, team size, etc."
)
PARAMETERS  = '{"query": "<what you are looking for, e.g. company name, owner name, location>"}'

# ── Fact patterns ─────────────────────────────────────────────────────────────
# Each pattern: (label, list_of_regex_patterns)
# The first captured group is the extracted value.

_FACT_PATTERNS: list[tuple[str, list[str]]] = [
    ("Company name", [
        r"(?:my company is|company name is|company called|we are called|business name is)\s+([A-Z][^\.\,\n]{1,50})",
        r"(?:company|business)\s+(?:name\s+)?[:\-–]?\s*([A-Z][^\.\,\n]{1,50})",
    ]),
    ("Owner / My name", [
        r"(?:my name is|i am|i'm)\s+([A-Z][a-zA-Z\s]{1,40})",
        r"(?:owner name is|proprietor is|founder is)\s+([A-Z][a-zA-Z\s]{1,40})",
    ]),
    ("Business type / Industry", [
        r"(?:we (?:are|do|sell|provide|run)|our business is|industry is|sector is)\s+([^\.\,\n]{3,80})",
        r"(?:type of business|business type)[:\-–]?\s+([^\.\,\n]{3,80})",
    ]),
    ("Location / City", [
        r"(?:located in|based in|our office is in|city is|from)\s+([A-Z][a-zA-Z\s,]{2,50})",
        r"(?:location|address)[:\-–]?\s+([^\.\,\n]{3,80})",
    ]),
    ("Products / Services", [
        r"(?:we sell|we offer|our products? (?:are|include)|our services? (?:are|include))\s+([^\.\,\n]{3,100})",
        r"(?:products?|services?)[:\-–]?\s+([^\.\,\n]{3,100})",
    ]),
    ("Team size", [
        r"(?:team of|we have|staff of|employees?)\s+(\d+[^\.\,\n]{0,30})",
        r"(?:team size|headcount)[:\-–]?\s+([^\.\,\n]{2,40})",
    ]),
    ("Revenue / Finance", [
        r"(?:revenue is|turnover is|monthly revenue|annual revenue)[:\-–]?\s+([^\.\,\n]{2,60})",
        r"(?:₹|Rs\.?|INR)\s?([\d,\.]+\s*(?:lakh|crore|k|thousand|million)?[^\.\,\n]{0,20})",
    ]),
]


def _extract_facts(history: list[dict]) -> dict[str, str]:
    """
    Scan all user turns in history and extract fact key-value pairs.
    Returns the most recently mentioned value for each fact category.
    """
    facts: dict[str, str] = {}

    for turn in history:
        user_text = turn.get("user", "")
        if not user_text:
            continue

        for label, patterns in _FACT_PATTERNS:
            for pattern in patterns:
                match = re.search(pattern, user_text, re.IGNORECASE)
                if match:
                    value = match.group(1).strip().rstrip(".,;")
                    facts[label] = value  # later turns overwrite earlier ones
                    break

    return facts


def _filter_by_query(facts: dict[str, str], query: str) -> dict[str, str]:
    """Return only facts whose label or value contains query keywords."""
    if not query:
        return facts

    query_lower = query.lower()
    keywords = re.split(r"\W+", query_lower)
    keywords = [k for k in keywords if len(k) > 2]

    if not keywords:
        return facts

    filtered = {}
    for label, value in facts.items():
        combined = (label + " " + value).lower()
        if any(kw in combined for kw in keywords):
            filtered[label] = value

    # If nothing matched the filter, return everything (graceful fallback)
    return filtered if filtered else facts


async def execute(args: dict) -> dict:
    """
    Args
    ----
    args["query"] : str — what to look for (e.g. "company name", "location")

    Returns
    -------
    {"name": "memory_lookup", "success": True,  "result": "Company name: SK Commerce\\nLocation: Pune"}
    {"name": "memory_lookup", "success": False, "error":  "No relevant facts found in memory."}
    """
    query = args.get("query", "").strip()

    try:
        from services.storage import get_all_business_facts
        business_data = get_all_business_facts()

        # ── 1. Check Structured Business Memory ──────────────────────────────
        # Flatten the business memory into searchable key-value pairs
        structured_facts = {}
        if isinstance(business_data, dict):
            company = business_data.get("company", {})
            for k, v in company.items():
                if v:
                    structured_facts[f"Company {k.replace('_', ' ').title()}"] = str(v)
            
            for list_key in ["products", "suppliers", "customers", "notes"]:
                items = business_data.get(list_key, [])
                if items:
                    structured_facts[list_key.title()] = ", ".join(items)

        if structured_facts:
            relevant_business = _filter_by_query(structured_facts, query)
            if relevant_business:
                result_lines = [f"{label}: {value}" for label, value in relevant_business.items()]
                return {
                    "name": NAME,
                    "success": True,
                    "result": "[From Business Memory]\n" + "\n".join(result_lines),
                }

        # ── 2. Fallback to Conversation History ──────────────────────────────
        history = load_all()
        all_facts = _extract_facts(history)

        if not all_facts:
            return {
                "name": NAME,
                "success": False,
                "error": "No facts found in business memory or conversation history.",
            }

        relevant_history = _filter_by_query(all_facts, query)

        if not relevant_history:
            return {
                "name": NAME,
                "success": False,
                "error": f"No information matching '{query}' found in memory.",
            }

        result_lines = [f"{label}: {value}" for label, value in relevant_history.items()]
        return {
            "name": NAME,
            "success": True,
            "result": "[From Chat History]\n" + "\n".join(result_lines),
        }

    except Exception as exc:
        return {"name": NAME, "success": False, "error": f"Memory lookup failed: {exc}"}
