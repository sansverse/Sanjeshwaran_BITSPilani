# app/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import json
from dotenv import load_dotenv

# Load .env before anything else
load_dotenv()

from app.ocr_engine import extract_text
from app.extract import extract_structured_data

app = FastAPI()


class DocumentRequest(BaseModel):
    document: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/extract-bill-data")
def extract_bill_data(req: DocumentRequest):

    # 1. Download document
    try:
        response = requests.get(req.document, timeout=20)
        response.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to download document: {e}")

    file_bytes = response.content

    # 2. OCR
    try:
        ocr_text = extract_text(file_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR failed: {e}")

    # 3. LLM extraction
    try:
        llm_output_text, usage = extract_structured_data(ocr_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM extraction failed: {e}")

    # 4. CLEAN OUTPUT → remove junk like ```json blocks, explanation text, etc.
    if isinstance(llm_output_text, dict):
        # Already JSON from model — accept safely
        cleaned_text = json.dumps(llm_output_text)
    else:
        cleaned_text = (
            llm_output_text.replace("```json", "")
            .replace("```", "")
            .strip()
        )

    # 5. Parse JSON
    try:
        parsed_json = json.loads(cleaned_text)
    except Exception:
        # Fallback: LLM returned garbage — wrap raw text
        parsed_json = {
            "pagewise_line_items": [],
            "total_item_count": 0,
            "raw_llm_output": cleaned_text
        }

    # 6. Guarantee required fields exist
    if "pagewise_line_items" not in parsed_json:
        parsed_json["pagewise_line_items"] = []

    if "total_item_count" not in parsed_json:
        parsed_json["total_item_count"] = sum(
            len(page.get("bill_items", []))
            for page in parsed_json["pagewise_line_items"]
        )

    # 7. Build final response
    final_output = {
        "is_success": True,
        "token_usage": {
            "total_tokens": usage.get("total_tokens", 0) if isinstance(usage, dict) else 0,
            "input_tokens": usage.get("input_tokens", 0) if isinstance(usage, dict) else 0,
            "output_tokens": usage.get("output_tokens", 0) if isinstance(usage, dict) else 0,
        },
        "data": parsed_json
    }

    return final_output
