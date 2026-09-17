
import easyocr
import numpy as np
import cv2
import streamlit as st


# ============================================================
# OCR MODEL
# ============================================================

@st.cache_resource
def get_reader():
    """
    Load EasyOCR once and reuse the model across Streamlit
    reruns and image-processing calls.
    """
    return easyocr.Reader(
        ["en"],
        gpu=False
    )


reader = get_reader()


# ============================================================
# IMAGE PREPROCESSING
# ============================================================

def preprocess_image(image, scale=2):

    image_array = np.array(image)

    # Make sure the image is RGB
    if len(image_array.shape) == 2:
        gray = image_array
    else:
        gray = cv2.cvtColor(
            image_array,
            cv2.COLOR_RGB2GRAY
        )

    height, width = gray.shape

    # Prevent extremely large images from consuming
    # excessive memory.
    max_dimension = 2000

    if max(height, width) > max_dimension:

        ratio = max_dimension / max(height, width)

        width = int(width * ratio)
        height = int(height * ratio)

        gray = cv2.resize(
            gray,
            (width, height),
            interpolation=cv2.INTER_AREA
        )

    # Upscale
    if scale > 1:

        height, width = gray.shape

        gray = cv2.resize(
            gray,
            (width * scale, height * scale),
            interpolation=cv2.INTER_CUBIC
        )

    # Improve contrast
    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    enhanced = clahe.apply(gray)

    # Reduce noise
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
        image,
        scale=2
    )

    try:

        results = reader.readtext(
            processed,
            detail=1,
            paragraph=False
        )

    finally:

        # Release the temporary OpenCV image
        del processed

    detected_text = []

    for box, text, confidence in results:

        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            confidence = 0.0

        detected_text.append({
            "text": str(text),
            "confidence": confidence,
            "box": box
        })

    return detected_text


# ============================================================
# BLOOD PRESSURE OCR
# ============================================================

def extract_bp_candidates(image):

    image_array = np.array(image)

    if len(image_array.shape) == 2:

        gray = image_array

    else:

        gray = cv2.cvtColor(
            image_array,
            cv2.COLOR_RGB2GRAY
        )

    height, width = gray.shape

    # Keep BP preprocessing from creating enormous arrays.
    max_dimension = 1600

    if max(height, width) > max_dimension:

        ratio = max_dimension / max(height, width)

        width = int(width * ratio)
        height = int(height * ratio)

        gray = cv2.resize(
            gray,
            (width, height),
            interpolation=cv2.INTER_AREA
        )

    # 2x rather than 3x to reduce memory usage
    height, width = gray.shape

    gray = cv2.resize(
        gray,
        (width * 2, height * 2),
        interpolation=cv2.INTER_CUBIC
    )

    gray = cv2.equalizeHist(gray)

    try:

        results = reader.readtext(
            gray,
            detail=1,
            paragraph=False,
            allowlist="0123456789/-"
        )

    finally:

        del gray

    candidates = []

    for box, text, confidence in results:

        text = str(text).strip()

        if "/" not in text:
            continue

        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            confidence = 0.0

        candidates.append({
            "text": text,
            "confidence": confidence,
            "box": box
        })

    return candidates

