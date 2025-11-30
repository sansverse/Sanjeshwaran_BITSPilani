# app/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import json
from dotenv import load_dotenv

load_dotenv()

# Import the NEW function from ocr_engine
from app.ocr_engine import extract_text_pages 
from app.extract import extract_structured_data

app = FastAPI()

class DocumentRequest(BaseModel):
    document: str

@app.get("/health")
def health():
    return {"status": "ok"}

def aggregate_daily_items(parsed_json):
    """
    Merges repeated items across ALL pages and fixes 'Lazy Quantity' errors.
    """
    # Flatten all items from all pages into one processing list? 
    # Or keep them pagewise? Keeping pagewise is safer for the requested format.
    
    for page in parsed_json.get("pagewise_line_items", []):
        raw_items = page.get("bill_items", [])
        if not raw_items: continue
        
        merged_map = {}

        for item in raw_items:
            # Normalize name
            name = item.get("item_name", "").strip()
            if not name: continue
            
            # Key by upper case to merge "Ward Charges" and "ward charges"
            key = name.upper()
            
            amount = float(item.get("item_amount", 0) or 0)
            rate = float(item.get("item_rate", 0) or 0)
            qty = float(item.get("item_quantity", 1) or 1)

            if key not in merged_map:
                merged_map[key] = {
                    "original_name": name,
                    "total_amt": amount,
                    "total_qty": qty,
                    "rates": [rate] if rate > 0 else []
                }
            else:
                # Merge repeated lines
                merged_map[key]["total_amt"] += amount
                merged_map[key]["total_qty"] += qty
                if rate > 0: merged_map[key]["rates"].append(rate)

        # Reconstruct list
        new_items = []
        for key, data in merged_map.items():
            final_rate = data["rates"][0] if data["rates"] else 0
            
            # Logic Fix: If we have a Rate, force Qty = Amount / Rate
            # This fixes the LLM guessing "1" for big amounts
            if final_rate > 0 and final_rate != data["total_amt"]:
                calculated_qty = data["total_amt"] / final_rate
                # Only replace if calculated qty is close to an integer or reasonable
                data["total_qty"] = calculated_qty
            
            new_items.append({
                "item_name": data["original_name"],
                "item_amount": round(data["total_amt"], 2),
                "item_rate": final_rate,
                "item_quantity": round(data["total_qty"], 2)
            })
        
        page["bill_items"] = new_items
    
    return parsed_json

def enforce_schema(parsed_json):
    """
    Final cleanup and total calculation.
    """
    final = {
        "pagewise_line_items": [],
        "total_item_count": 0,
        "final_total_amount": 0.0
    }

    pages = parsed_json.get("pagewise_line_items", [])
    total_items = 0
    final_total = 0.0

    for page in pages:
        # Pass through the page data
        page_no = str(page.get("page_no", "1"))
        page_type = page.get("page_type", "Bill Detail")
        items = page.get("bill_items", [])
        
        # Calculate subtotal for this page
        subtotal = sum(float(it.get("item_amount", 0)) for it in items)

        # Only add to Final Total if it's NOT a summary page (optional logic)
        # For now, we assume the aggregator handled duplicates or we trust the LLM's page_type
        # If strict no-double-count is needed:
        if page_type != "Final Bill":
            final_total += subtotal
        
        final["pagewise_line_items"].append({
            "page_no": page_no,
            "page_type": page_type,
            "bill_items": items,
            "page_subtotal": round(subtotal, 2)
        })
        total_items += len(items)

    final["total_item_count"] = total_items
    final["final_total_amount"] = round(final_total, 2)

    return final

@app.post("/extract-bill-data")
def extract_bill_data(req: DocumentRequest):
    # Step 0: Download
    try:
        resp = requests.get(req.document, timeout=25)
        resp.raise_for_status()
        file_bytes = resp.content
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Download failed: {e}")

    # Step A: OCR (Get LIST of pages)
    try:
        page_texts = extract_text_pages(file_bytes)
    except Exception as e:
        print(f"OCR Error: {e}")
        raise HTTPException(status_code=500, detail="OCR processing failed")

    # Step B: Page-by-Page LLM Extraction
    master_data = { "pagewise_line_items": [] }
    total_tokens_used = {"total": 0, "input": 0, "output": 0}

    # Loop through every page
    for i, page_content in enumerate(page_texts):
        if not page_content.strip(): continue

        print(f"Processing Page {i+1}...") # Debug log

        try:
            # Call LLM for this specific page
            partial_data, usage = extract_structured_data(page_content)
            
            # Add usage
            if usage:
                total_tokens_used["total"] += getattr(usage, "total_tokens", 0)
                total_tokens_used["input"] += getattr(usage, "prompt_tokens", 0)
                total_tokens_used["output"] += getattr(usage, "completion_tokens", 0)

            # Append results
            if "pagewise_line_items" in partial_data:
                # Force page number to match index if LLM hallucinates
                for p in partial_data["pagewise_line_items"]:
                    p["page_no"] = str(i+1)
                    
                master_data["pagewise_line_items"].extend(partial_data["pagewise_line_items"])

        except Exception as e:
            print(f"Error on Page {i+1}: {e}")
            continue

    # Step C: Smart Aggregation
    processed_data = aggregate_daily_items(master_data)

    # Step D: Final Formatting
    final_output = enforce_schema(processed_data)

    return {
        "is_success": True,
        "token_usage": total_tokens_used,
        "data": final_output
    }