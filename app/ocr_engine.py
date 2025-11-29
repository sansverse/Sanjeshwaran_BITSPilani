from paddleocr import PaddleOCR

ocr = PaddleOCR(
    use_angle_cls=True,
    lang='en'
)

def ocr_image_bytes(image_bytes: bytes):
    import numpy as np
    import cv2

    img_array = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    result = ocr.ocr(img, cls=True)

    lines = []
    for line in result:
        for box, text in line:
            lines.append(text[0])

    return {"text": lines}
