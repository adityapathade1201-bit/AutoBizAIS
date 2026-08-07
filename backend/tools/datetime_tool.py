"""
tools/datetime_tool.py
======================
Returns the current date, time, and timezone.
No external dependencies — uses Python's standard library.
"""

from datetime import datetime
import zoneinfo

NAME        = "datetime_tool"
DESCRIPTION = "Returns the current date and time. Use when the user asks what time or date it is."
PARAMETERS  = '{"timezone": "<optional IANA timezone string, e.g. Asia/Kolkata — defaults to IST>"}'

_DEFAULT_TZ = "Asia/Kolkata"  # Indian Standard Time — suits the SME target market


async def execute(args: dict) -> dict:
    """
    Args
    ----
    args["timezone"] : str (optional) — IANA timezone name

    Returns
    -------
    {"name": "datetime_tool", "success": True, "result": "Thursday, 26 June 2026 — 10:45 AM IST"}
    """
    tz_name = args.get("timezone", _DEFAULT_TZ)

    try:
        tz = zoneinfo.ZoneInfo(tz_name)
    except (zoneinfo.ZoneInfoNotFoundError, Exception):
        tz = zoneinfo.ZoneInfo(_DEFAULT_TZ)
        tz_name = _DEFAULT_TZ

    now = datetime.now(tz)
    # Friendly format: "Thursday, 26 June 2026 — 10:45 AM IST"
    tz_abbr = now.strftime("%Z")
    formatted = now.strftime(f"%A, %d %B %Y — %I:%M %p {tz_abbr}")

    return {"name": NAME, "success": True, "result": formatted}
