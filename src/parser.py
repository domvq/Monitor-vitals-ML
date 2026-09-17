
import re


def parse_vitals(ocr_results):

    vitals = {
        "hr": None,
        "spo2": None,
        "bp_sys": None,
        "bp_dia": None,
        "rr": None,
        "etco2": None
    }

    numbers = []

    # Collect every number OCR found
    for item in ocr_results:

        if not isinstance(item, dict):
            continue

        text = str(item.get("text", ""))
        confidence = float(item.get("confidence", 0))

        found = re.findall(r"\d+(?:\.\d+)?", text)

        for value in found:

            number = float(value)

            numbers.append({
                "number": number,
                "text": text,
                "confidence": confidence
            })

    # --------------------------------------------------------
    # BP
    # --------------------------------------------------------

    for item in ocr_results:

        if not isinstance(item, dict):
            continue

        text = str(item.get("text", ""))

        match = re.search(
            r"(\d{2,3})\s*[/\-]\s*(\d{2,3})",
            text
        )

        if match:

            systolic = float(match.group(1))
            diastolic = float(match.group(2))

            if (
                systolic > diastolic
                and 50 <= systolic <= 250
                and 20 <= diastolic <= 150
            ):

                vitals["bp_sys"] = systolic
                vitals["bp_dia"] = diastolic

                break

    # --------------------------------------------------------
    # High-confidence numbers
    # --------------------------------------------------------

    good_numbers = [
        x["number"]
        for x in numbers
        if x["confidence"] >= 0.80
    ]

    # --------------------------------------------------------
    # SpO2
    # --------------------------------------------------------

    for number in good_numbers:

        if 85 <= number <= 100:

            vitals["spo2"] = number
            break

    # --------------------------------------------------------
    # RR
    # --------------------------------------------------------

    for number in good_numbers:

        if (
            8 <= number <= 50
            and number != vitals["spo2"]
        ):

            vitals["rr"] = number
            break

    # --------------------------------------------------------
    # HR
    # --------------------------------------------------------

    for number in good_numbers:

        if (
            40 <= number <= 220
            and number != vitals["spo2"]
            and number != vitals["rr"]
        ):

            vitals["hr"] = number
            break

    # --------------------------------------------------------
    # EtCO2
    # --------------------------------------------------------

    for number in good_numbers:

        if (
            20 <= number <= 60
            and number != vitals["hr"]
            and number != vitals["spo2"]
            and number != vitals["rr"]
        ):

            vitals["etco2"] = number
            break

    return vitals
