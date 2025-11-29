import requests
from fastapi import HTTPException
from pdf2image import convert_from_bytes
from app.ocr_engine import ocr_image_bytes

def extract_from_url(url: str):
    try:
        resp = requests.get(url, timeout=25)
    except:
        raise HTTPException(400, "Unable to fetch URL")

    if resp.status_code != 200:
        raise HTTPException(400, f"Bad URL status {resp.status_code}")

    content_type = resp.headers.get("content-type", "")
    url_lower = url.lower()
    
    # Treat as PDF if header says pdf OR URL ends in .pdf
    is_pdf = ("pdf" in content_type) or url_lower.endswith(".pdf")
    
    if is_pdf:
        pages = convert_from_bytes(resp.content)
        all_text = []
        for pg in pages:
            text = ocr_image_bytes(pg.tobytes(), pg.size, pg.mode)
            all_text.extend(text)
        return {"text": all_text}

    else:
        # assume image
        text = ocr_image_bytes(resp.content)
        return {"text": text}
