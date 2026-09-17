
import easyocr
import numpy as np
import cv2


# Load OCR model once
reader = easyocr.Reader(["en"])


def preprocess_image(image):

    image_array = np.array(image)

    gray = cv2.cvtColor(
        image_array,
        cv2.COLOR_RGB2GRAY
    )

    height, width = gray.shape

    # Upscale image
    gray = cv2.resize(
        gray,
        (width * 2, height * 2),
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


def extract_text(image):

    processed = preprocess_image(image)

    results = reader.readtext(
        processed,
        detail=1,
        paragraph=False
    )

    detected_text = []

    for box, text, confidence in results:

        detected_text.append({
            "text": text,
            "confidence": float(confidence),
            "box": box
        })

    return detected_text


def extract_bp_candidates(image):

    image_array = np.array(image)

    gray = cv2.cvtColor(
        image_array,
        cv2.COLOR_RGB2GRAY
    )

    height, width = gray.shape

    # Larger upscale for BP digits
    gray = cv2.resize(
        gray,
        (width * 3, height * 3),
        interpolation=cv2.INTER_CUBIC
    )

    # Contrast enhancement
    gray = cv2.equalizeHist(gray)

    results = reader.readtext(
        gray,
        detail=1,
        paragraph=False,
        allowlist="0123456789/-"
    )

    candidates = []

    for box, text, confidence in results:

        text = text.strip()

        if "/" in text:

            candidates.append({
                "text": text,
                "confidence": float(confidence),
                "box": box
            })

    return candidates

