from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from pdf2image import convert_from_bytes
from app.ocr_engine import ocr_image_bytes

app = FastAPI()

class DocumentRequest(BaseModel):
    document: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/extract")
def extract(req: DocumentRequest):
    url = req.document

    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to download document: {e}")

    content_type = response.headers.get("Content-Type", "").lower()

    results = []

    if "pdf" in content_type:
        # Convert PDF pages to images
        pages = convert_from_bytes(response.content)
        for page in pages:
            img_bytes = page.tobytes("jpeg", "RGB")
            result = ocr_image_bytes(img_bytes)
            results.append(result)

    elif "image" in content_type:
        img_bytes = response.content
        result = ocr_image_bytes(img_bytes)
        results.append(result)

    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    return {"extracted": results}
