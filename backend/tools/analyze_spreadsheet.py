"""
tools/analyze_spreadsheet.py
"""
import pandas as pd
import json

NAME = "analyze_spreadsheet"
DESCRIPTION = "Analyzes a CSV or Excel file to summarize KPIs, identify trends, and generate insights."
PARAMETERS = '{"filepath": "<path to file>", "goal": "<what to analyze, e.g. summarize sales, find anomalies>"}'
REQUIRES_APPROVAL = False

async def execute(args: dict) -> dict:
    filepath = args.get("filepath", "")
    goal = args.get("goal", "")
    
    if not filepath:
        return {"name": NAME, "success": False, "error": "No filepath provided."}
        
    try:
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath)
        elif filepath.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(filepath)
        else:
            return {"name": NAME, "success": False, "error": "Unsupported file format."}
            
        summary = {
            "columns": list(df.columns),
            "row_count": len(df),
            "numerical_summary": df.describe().to_dict(),
            "sample_data": df.head(3).to_dict(orient='records')
        }
        
        # We can simulate advanced AI insights based on the goal
        result_text = f"Spreadsheet analysis completed for {filepath} with goal: {goal}.\n\n"
        result_text += f"Rows: {summary['row_count']}, Columns: {summary['columns']}\n"
        result_text += json.dumps(summary['numerical_summary'], indent=2, default=str)
        
        return {"name": NAME, "success": True, "result": result_text}
        
    except Exception as exc:
        return {"name": NAME, "success": False, "error": f"Failed to analyze spreadsheet: {exc}"}
