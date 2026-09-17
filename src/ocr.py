
import easyocr
import numpy as np
import cv2
import streamlit as st


# ============================================================
# OCR MODEL
# ============================================================

@st.cache_resource(show_spinner="Loading OCR model...")
def get_reader():

    return easyocr.Reader(
        ["en"],
        gpu=False
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

    # Keep very large images from consuming
    # excessive memory during OCR.
    max_dimension = 1800

    if max(
        height,
        width
    ) > max_dimension:

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

    # Moderate upscale
    height, width = gray.shape

    gray = cv2.resize(
        gray,
        (
            width * 2,
            height * 2
        ),
        interpolation=cv2.INTER_CUBIC
    )

    # Contrast enhancement
    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    enhanced = clahe.apply(
        gray
    )

    # Light noise reduction
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

    reader = get_reader()

    processed = preprocess_image(
        image
    )

    results = reader.readtext(
        processed,
        detail=1,
        paragraph=False
    )

    detected_text = []

    for box, text, confidence in results:

        text = str(
            text
        ).strip()

        if not text:
            continue

        detected_text.append(
            {
                "text": text,
                "confidence": float(
                    confidence
                ),
                "box": box
            }
        )

    return detected_text


# ============================================================
# BLOOD PRESSURE OCR
# ============================================================

def extract_bp_candidates(image):

    reader = get_reader()

    image_array = np.array(
        image.convert("RGB")
    )

    if image_array.size == 0:

        return []

    gray = cv2.cvtColor(
        image_array,
        cv2.COLOR_RGB2GRAY
    )

    height, width = gray.shape

    # Prevent huge images from creating
    # excessive memory usage.
    max_dimension = 1800

    if max(
        height,
        width
    ) > max_dimension:

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

    # BP-specific upscale
    height, width = gray.shape

    gray = cv2.resize(
        gray,
        (
            width * 2,
            height * 2
        ),
        interpolation=cv2.INTER_CUBIC
    )

    gray = cv2.equalizeHist(
        gray
    )

    results = reader.readtext(
        gray,
        detail=1,
        paragraph=False,
        allowlist="0123456789/-"
    )

    candidates = []

    for box, text, confidence in results:

        text = str(
            text
        ).strip()

        if "/" not in text:
            continue

        candidates.append(
            {
                "text": text,
                "confidence": float(
                    confidence
                ),
                "box": box
            }
        )

    return candidates

