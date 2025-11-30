# app/ocr_engine.py
import io
from paddleocr import PaddleOCR
from pdf2image import convert_from_bytes
from typing import List

ocr = PaddleOCR(use_angle_cls=True, lang="en")

def _ocr_image_pil_list(pil_images: List):
    lines = []
    for img in pil_images:
        # convert PIL image to OpenCV-compatible BGR array via numpy
        import numpy as np
        import cv2
        arr = np.array(img)  # PIL -> RGB ndarray
        img_bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
        result = ocr.ocr(img_bgr, cls=True)

        for line in result:
            # result line format: [box, (text, confidence)]
            for box, text_conf in line:
                text = text_conf[0]
                if text and text.strip():
                    lines.append(text.strip())
    return lines

def extract_text(file_bytes: bytes) -> str:
    """
    Accepts raw bytes. Detects if PDF or image.
    Returns a single string with newline-separated OCR lines.
    """
    # quick PDF sniff: PDF files start with "%PDF"
    if file_bytes[:4] == b"%PDF":
        # convert PDF pages to images (PIL list)
        pil_images = convert_from_bytes(file_bytes)  # uses poppler in your PATH
        lines = _ocr_image_pil_list(pil_images)
    else:
        # treat as single image
        # read bytes into PIL directly
        from PIL import Image
        img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        lines = _ocr_image_pil_list([img])

    return "\n".join(lines)
