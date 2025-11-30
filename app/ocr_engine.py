# app/ocr_engine.py
import io
import numpy as np
import cv2
from paddleocr import PaddleOCR
from pdf2image import convert_from_bytes
from typing import List
from PIL import Image

# Initialize PaddleOCR once
ocr = PaddleOCR(use_angle_cls=True, lang="en", use_gpu=False, show_log=False)

def _sort_boxes_spatially(dt_boxes, tolerance=10):
    """
    Sorts OCR bounding boxes top-to-bottom (Y), then left-to-right (X).
    Groups items that are roughly on the same Y-axis (row).
    """
    if not dt_boxes: return []
    
    # Sort primarily by Top-Left Y
    dt_boxes.sort(key=lambda x: x[0][0][1])
    
    rows = []
    current_row = []
    last_y = -1
    
    for box_data in dt_boxes:
        box, (text, conf) = box_data
        y = box[0][1]
        
        # If this box is significantly lower than the last one, start a new row
        if last_y != -1 and abs(y - last_y) > tolerance:
            # Sort the completed row by X coordinate (left to right)
            current_row.sort(key=lambda x: x[0][0][0])
            rows.append(current_row)
            current_row = []
            
        current_row.append(box_data)
        last_y = y
        
    # Append the final row
    if current_row:
        current_row.sort(key=lambda x: x[0][0][0])
        rows.append(current_row)
        
    return rows

def _ocr_image_to_text_pages(pil_images: List) -> List[str]:
    """
    Returns a LIST of strings. Each string represents one page.
    """
    page_texts = []
    
    for i, img in enumerate(pil_images):
        # Convert PIL to OpenCV format
        arr = np.array(img)
        if arr.shape[-1] == 4: arr = cv2.cvtColor(arr, cv2.COLOR_RGBA2RGB)
        img_bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
        
        result = ocr.ocr(img_bgr, cls=True)
        
        # Handle empty pages safely
        if not result or result[0] is None: 
            page_texts.append("")
            continue

        # Sort spatially to reconstruct lines
        sorted_rows = _sort_boxes_spatially(result[0], tolerance=15)
        
        # Build text for THIS page only
        current_page_text = f"--- PAGE {i+1} ---\n"
        for row in sorted_rows:
            # Join text in the same row with spaces (mimicking a table row)
            line_text = "   ".join([item[1][0] for item in row])
            current_page_text += line_text + "\n"
        
        page_texts.append(current_page_text)
        
    return page_texts

def extract_text_pages(file_bytes: bytes) -> List[str]:
    """
    Accepts raw bytes. Returns a LIST of page strings.
    """
    if file_bytes.startswith(b"%PDF"):
        pil_images = convert_from_bytes(file_bytes)
    else:
        img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        pil_images = [img]

    return _ocr_image_to_text_pages(pil_images)