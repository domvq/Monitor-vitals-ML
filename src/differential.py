def generate_differential(vitals, age, chief_complaint):
    """
    Educational/reference differential generator.

    This is a rule-based prototype, not a diagnostic model.
    """

    considerations = []

    hr = vitals.get("hr")
    spo2 = vitals.get("spo2")
    sbp = vitals.get("bp_sys")
    rr = vitals.get("rr")
    etco2 = vitals.get("etco2")

    # Tachycardia
    if hr is not None and hr >= 100:
        considerations.append({
            "condition": "Tachycardia-related causes",
            "findings": [
                f"HR {hr} bpm"
            ],
            "note": (
                "Consider physiologic and pathologic causes "
                "of an elevated heart rate."
            )
        })

    # Hypoxemia
    if spo2 is not None and spo2 < 92:
        considerations.append({
            "condition": "Hypoxemia / respiratory compromise",
            "findings": [
                f"SpO₂ {spo2}%"
            ],
            "note": (
                "Consider respiratory and cardiopulmonary "
                "causes of reduced oxygen saturation."
            )
        })

    # Hypotension
    if sbp is not None and sbp < 90:
        considerations.append({
            "condition": "Hypoperfusion / shock physiology",
            "findings": [
                f"SBP {sbp} mmHg"
            ],
            "note": (
                "Consider volume loss, distributive, "
                "cardiogenic, or obstructive causes in context."
            )
        })

    # Tachypnea
    if rr is not None and rr > 20:
        considerations.append({
            "condition": "Increased respiratory drive",
            "findings": [
                f"RR {rr}/min"
            ],
            "note": (
                "Consider pulmonary, metabolic, infectious, "
                "or other causes depending on presentation."
            )
        })

    # Low EtCO2
    if etco2 is not None and etco2 < 30:
        considerations.append({
            "condition": "Low EtCO₂ pattern",
            "findings": [
                f"EtCO₂ {etco2} mmHg"
            ],
            "note": (
                "Interpret alongside respiratory rate, "
                "perfusion, ventilation, and clinical presentation."
            )
        })

    # Chest pain
    if chief_complaint:
        complaint = chief_complaint.lower()

        if "chest" in complaint:

            considerations.append({
                "condition": "Acute coronary syndrome",
                "findings": [
                    "Chief complaint includes chest pain"
                ],
                "note": (
                    "Requires clinical assessment and appropriate "
                    "ECG/history findings."
                )
            })

            considerations.append({
                "condition": "Pulmonary embolic process",
                "findings": [
                    "Chest-pain presentation"
                ],
                "note": (
                    "Consider in the appropriate clinical context; "
                    "vital signs alone cannot establish this diagnosis."
                )
            })

    # Respiratory complaint
    if chief_complaint:

        complaint = chief_complaint.lower()

        if any(
            word in complaint
            for word in [
                "shortness",
                "dyspnea",
                "breathing",
                "respiratory"
            ]
        ):

            considerations.append({
                "condition": "Acute respiratory process",
                "findings": [
                    "Respiratory complaint"
                ],
                "note": (
                    "Consider airway, pulmonary, cardiac, "
                    "and metabolic causes."
                )
            })

    return considerations