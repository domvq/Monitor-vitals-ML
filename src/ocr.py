
import os
import re

import cv2
import numpy as np
import pytesseract


# ============================================================
# TESSERACT CONFIGURATION
# ============================================================

# Streamlit Cloud runs Linux.
# Windows commonly installs Tesseract here.
if os.name == "nt":

    windows_path = (
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    )

    if os.path.exists(windows_path):
        pytesseract.pytesseract.tesseract_cmd = (
            windows_path
        )


# ============================================================
# IMAGE PREPROCESSING
# ============================================================

def preprocess_image(image):

    image_array = np.array(
        image.convert("RGB")
    )

    if image_array.size == 0:
        raise ValueError(
            "Uploaded image is empty."
        )

    gray = cv2.cvtColor(
        image_array,
        cv2.COLOR_RGB2GRAY
    )

    height, width = gray.shape

    # Prevent extremely large images
    # from consuming excessive memory.
    max_dimension = 1800

    if max(height, width) > max_dimension:

        scale = (
            max_dimension
            / max(height, width)
        )

        gray = cv2.resize(
            gray,
            (
                int(width * scale),
                int(height * scale)
            ),
            interpolation=cv2.INTER_AREA
        )

    # Upscale digits.
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

    enhanced = clahe.apply(
        gray
    )

    # Light noise reduction.
    enhanced = cv2.GaussianBlur(
        enhanced,
        (3, 3),
        0
    )

    return enhanced


# ============================================================
# GENERAL OCR
# ============================================================

def extract_text(image):

    processed = preprocess_image(
        image
    )

    data = pytesseract.image_to_data(
        processed,
        config="--psm 11",
        output_type=pytesseract.Output.DICT
    )

    detected_text = []

    for i, text in enumerate(
        data["text"]
    ):

        text = str(text).strip()

        if not text:
            continue

        try:

            confidence = float(
                data["conf"][i]
            )

        except (
            ValueError,
            TypeError
        ):

            confidence = 0.0

        x = int(
            data["left"][i]
        )

        y = int(
            data["top"][i]
        )

        w = int(
            data["width"][i]
        )

        h = int(
            data["height"][i]
        )

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


# ============================================================
# BLOOD PRESSURE OCR
# ============================================================

def extract_bp_candidates(image):

    processed = preprocess_image(
        image
    )

    config = (
        "--psm 11 "
        "-c tessedit_char_whitelist=0123456789/-"
    )

    text = pytesseract.image_to_string(
        processed,
        config=config
    )

    candidates = []

    matches = re.findall(
        r"\b(\d{2,3})\s*/\s*(\d{2,3})\b",
        text
    )

    for systolic, diastolic in matches:

        candidates.append(
            {
                "text": (
                    f"{systolic}/{diastolic}"
                ),
                "confidence": None,
                "box": None
            }
        )

    return candidates

