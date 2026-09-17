
import re

import cv2
import numpy as np
import pytesseract

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)
    if image_array.size == 0:
        raise ValueError("Uploaded image is empty.")

    gray = cv2.cvtColor(
        image_array,
        cv2.COLOR_RGB2GRAY
    )

    height, width = gray.shape

    # Prevent extremely large uploads
    # from consuming excessive memory.
    max_dimension = 1800

    if max(height, width) > max_dimension:
        scale = max_dimension / max(height, width)

        gray = cv2.resize(
            gray,
            (
                int(width * scale),
                int(height * scale)
            ),
            interpolation=cv2.INTER_AREA
        )

    # Upscale monitor digits.
    height, width = gray.shape

    gray = cv2.resize(
        gray,
        (
            width * 2,
            height * 2
        ),
        interpolation=cv2.INTER_CUBIC
    )

    # Improve contrast.
    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    enhanced = clahe.apply(gray)

    # Light denoising.
    enhanced = cv2.GaussianBlur(
        enhanced,
        (3, 3),
        0
    )

    return enhanced


def extract_text(image):
    processed = preprocess_image(image)

    data = pytesseract.image_to_data(
        processed,
        config="--psm 11",
        output_type=pytesseract.Output.DICT
    )

    detected_text = []

    for i, text in enumerate(data["text"]):

        text = str(text).strip()

        if not text:
            continue

        try:
            confidence = float(
                data["conf"][i]
            )
        except (ValueError, TypeError):
            confidence = 0.0

        x = data["left"][i]
        y = data["top"][i]
        w = data["width"][i]
        h = data["height"][i]

        box = [
            [x, y],
            [x + w, y],
            [x + w, y + h],
            [x, y + h]
        ]

        detected_text.append(
            {
                "text": text,
                "confidence": max(
                    0.0,
                    confidence / 100.0
                ),
                "box": box
            }
        )

    return detected_text


def extract_bp_candidates(image):
    processed = preprocess_image(image)

    # BP displays generally contain
    # digits, slash, or dash.
    config = (
        "--psm 11 "
        "-c tessedit_char_whitelist=0123456789/-"
    )

    text = pytesseract.image_to_string(
        processed,
        config=config
    )

    candidates = []

    # Find values such as:
    # 120/80
    # 118/76
    # 140/90
    matches = re.findall(
        r"\b(\d{2,3})\s*/\s*(\d{2,3})\b",
        text
    )

    for systolic, diastolic in matches:

        candidates.append(
            {
                "text": f"{systolic}/{diastolic}",
                "confidence": None,
                "box": None
            }
        )

    return candidates

