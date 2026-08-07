import pandas as pd
from fastapi import UploadFile

async def parse_document(file: UploadFile) -> str:
    """
    Parse uploaded documents into structured text.
    Supports TXT, CSV, Excel natively.
    Mocks PDF, DOCX, Images for demonstration purposes.
    """
    ext = file.filename.split('.')[-1].lower()
    content = await file.read()
    
    if ext == 'txt':
        return content.decode('utf-8')
    elif ext == 'csv':
        # Use pandas to read CSV bytes
        from io import BytesIO
        df = pd.read_csv(BytesIO(content))
        return df.to_json(orient='records')
    elif ext in ['xls', 'xlsx']:
        from io import BytesIO
        df = pd.read_excel(BytesIO(content))
        return df.to_json(orient='records')
    elif ext == 'json':
        return content.decode('utf-8')
    elif ext in ['pdf', 'docx', 'png', 'jpg', 'jpeg']:
        # MOCK FOR DEMONSTRATION
        return f"[MOCK PARSER] Successfully extracted text from {file.filename}. Content includes standard business document data."
    else:
        return f"Unsupported file type: {ext}"

async def ocr_invoice(file: UploadFile) -> dict:
    """
    Tool 2: OCR. Simulates extracting structured JSON from an invoice or receipt.
    """
    await file.read() # Read bytes to simulate processing
    
    # Mock OCR extraction JSON for demonstration
    return {
        "invoice_number": f"INV-{len(file.filename)}024",
        "vendor": "Tech Supplies Inc." if "tech" in file.filename.lower() else "Generic Vendor Ltd",
        "date": "2024-05-10",
        "amount": 4500.00,
        "tax": 450.00,
        "currency": "INR",
        "items": [
            {"description": "Laptop Stand", "quantity": 2, "price": 1000.00},
            {"description": "Wireless Mouse", "quantity": 5, "price": 500.00}
        ]
    }
