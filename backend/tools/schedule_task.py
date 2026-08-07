"""
tools/schedule_task.py
"""
from services.storage import append_json

NAME = "schedule_task"
DESCRIPTION = "Creates a calendar event, meeting agenda, or reminder."
PARAMETERS = '{"title": "<event title>", "datetime": "<ISO datetime>", "description": "<agenda or details>"}'
REQUIRES_APPROVAL = True

async def execute(args: dict) -> dict:
    title = args.get("title", "").strip()
    date_time = args.get("datetime", "").strip()
    description = args.get("description", "").strip()

    if not title or not date_time:
        return {"name": NAME, "success": False, "error": "Title and datetime are required."}

    task_entry = {
        "title": title,
        "datetime": date_time,
        "description": description,
        "status": "scheduled"
    }
    
    append_json("tasks.json", task_entry)

    return {"name": NAME, "success": True, "result": f"Task '{title}' scheduled for {date_time} successfully."}
