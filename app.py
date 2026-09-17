
import os
import re
import shutil

import cv2
import numpy as np
import pytesseract


# ============================================================
# TESSERACT CONFIGURATION
# ============================================================

def configure_tesseract():
    """
    Configure Tesseract for both local Windows development
    and Linux-based deployments such as Streamlit Cloud.
    """

    # Windows
    if os.name == "nt":

        windows_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        ]

        for path in windows_paths:

            if os.path.exists(path):

                pytesseract.pytesseract.tesseract_cmd = path

                return

    # Linux / macOS / Streamlit Cloud
    tesseract_path = shutil.which("tesseract")

    if tesseract_path:

        pytesseract.pytesseract.tesseract_cmd = (
            tesseract_path
        )


configure_tesseract()


# ============================================================
# TESSERACT AVAILABILITY
# ============================================================

def check_tesseract():
    """
    Verify that the Tesseract executable is available.
    """

    try:

        version = pytesseract.get_tesseract_version()

        return True, str(version)

    except Exception as exc:

        return False, str(exc)


# ============================================================
# IMAGE PREPROCESSING
# ============================================================

def preprocess_image(image):

    if image is None:

        raise ValueError(
            "No image was provided."
        )

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

    max_dimension = 1800

    if max(height, width) > max_dimension:

        scale = (
            max_dimension
            / max(height, width)
        )

        gray = cv2.resize(
            gray,
            (
                max(1, int(width * scale)),
                max(1, int(height * scale))
            ),
            interpolation=cv2.INTER_AREA
        )

    height, width = gray.shape

    gray = cv2.resize(
        gray,
        (
            width * 2,
            height * 2
        ),
        interpolation=cv2.INTER_CUBIC
    )

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    enhanced = clahe.apply(
        gray
    )

    enhanced = cv2.GaussianBlur(
        enhanced,
        (3, 3),
        0
    )

    return enhanced


# ============================================================
# SAFE CONFIDENCE CONVERSION
# ============================================================

def safe_confidence(value):

    if value is None:

        return 0.0

    try:

        confidence = float(value)

    except (
        ValueError,
        TypeError
    ):

        return 0.0

    if not np.isfinite(confidence):

        return 0.0

    confidence = max(
        0.0,
        min(100.0, confidence)
    )

    return confidence / 100.0


# ============================================================
# GENERAL OCR
# ============================================================

def extract_text(image):

    available, error = check_tesseract()

    if not available:

        raise RuntimeError(
            "Tesseract OCR is not available. "
            "Make sure Tesseract is installed on the "
            "deployment environment. "
            f"Details: {error}"
        )

    processed = preprocess_image(
        image
    )

    data = pytesseract.image_to_data(
        processed,
        config="--psm 11",
        output_type=pytesseract.Output.DICT
    )

    detected_text = []

    texts = data.get("text", [])
    confidences = data.get("conf", [])
    lefts = data.get("left", [])
    tops = data.get("top", [])
    widths = data.get("width", [])
    heights = data.get("height", [])

    for i, raw_text in enumerate(texts):

        text = str(raw_text).strip()

        if not text:

            continue

        confidence = safe_confidence(
            confidences[i]
            if i < len(confidences)
            else 0
        )

        try:

            x = int(lefts[i])
            y = int(tops[i])
            w = int(widths[i])
            h = int(heights[i])

        except (
            ValueError,
            TypeError,
            IndexError
        ):

            continue

        box = [
            [x, y],
            [x + w, y],
            [x + w, y + h],
            [x, y + h]
        ]

        detected_text.append(
            {
                "text": text,
                "confidence": confidence,
                "box": box
            }
        )

    return detected_text


# ============================================================
# BLOOD PRESSURE OCR
# ============================================================

def extract_bp_candidates(image):

    available, error = check_tesseract()

    if not available:

        raise RuntimeError(
            "Tesseract OCR is not available. "
            "Make sure Tesseract is installed on the "
            "deployment environment. "
            f"Details: {error}"
        )

    processed = preprocess_image(
        image
    )

    config = (
        "--psm 11 "
        "-c tessedit_char_whitelist=0123456789/-"
    )

    # Use image_to_data instead of image_to_string
    # so we can preserve OCR confidence information.

    data = pytesseract.image_to_data(
        processed,
        config=config,
        output_type=pytesseract.Output.DICT
    )

    candidates = []

    texts = data.get("text", [])
    confidences = data.get("conf", [])
    lefts = data.get("left", [])
    tops = data.get("top", [])
    widths = data.get("width", [])
    heights = data.get("height", [])

    for i, raw_text in enumerate(texts):

        text = str(raw_text).strip()

        if not text:

            continue

        # Normalize common OCR separators.
        normalized = text.replace(
            " ",
            ""
        )

        matches = re.findall(
            r"(\d{2,3})[/-](\d{2,3})",
            normalized
        )

        if not matches:

            continue

        confidence = safe_confidence(
            confidences[i]
            if i < len(confidences)
            else 0
        )

        try:

            x = int(lefts[i])
            y = int(tops[i])
            w = int(widths[i])
            h = int(heights[i])

            box = [
                [x, y],
                [x + w, y],
                [x + w, y + h],
                [x, y + h]
            ]

        except (
            ValueError,
            TypeError,
            IndexError
        ):

            box = None

        for systolic, diastolic in matches:

            systolic = int(systolic)
            diastolic = int(diastolic)

            # Basic plausibility filtering.
            if not (
                50 <= systolic <= 250
                and 20 <= diastolic <= 150
                and systolic > diastolic
            ):

                continue

            candidates.append(
                {
                    "text": (
                        f"{systolic}/{diastolic}"
                    ),
                    "confidence": confidence,
                    "box": box
                }
            )

    return candidates

