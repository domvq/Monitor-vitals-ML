
import re
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from PIL import Image

from src.ocr import extract_text, extract_bp_candidates
from src.parser import parse_vitals


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="VitalSight",
    page_icon="🚑",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# THEME-AWARE CSS
# ============================================================

st.markdown(
    """
    <style>

    /* Main content */
    .block-container {
        max-width: 1400px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    /* Header */
    .vs-title {
        font-size: 2.6rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        color: var(--text-color);
        margin-bottom: 0.1rem;
    }

    .vs-subtitle {
        color: var(--secondary-text-color);
        margin-bottom: 1.25rem;
    }

    /* Information boxes */
    .vs-warning,
    .vs-reference {
        padding: 16px 18px;
        border-radius: 10px;
        margin-bottom: 18px;
        line-height: 1.55;
        color: var(--text-color);
    }

    .vs-warning {
        background: rgba(245, 158, 11, 0.10);
        border: 1px solid rgba(245, 158, 11, 0.28);
        border-left: 4px solid #f59e0b;
    }

    .vs-reference {
        background: rgba(59, 130, 246, 0.10);
        border: 1px solid rgba(59, 130, 246, 0.28);
        border-left: 4px solid #3b82f6;
    }

    /* Vital cards */
    .vs-vital {
        background: var(--secondary-background-color);
        color: var(--text-color);
        border: 1px solid rgba(128, 128, 128, 0.25);
        border-radius: 12px;
        padding: 18px 10px;
        text-align: center;
        min-height: 125px;
    }

    .vs-label {
        color: var(--secondary-text-color);
        font-weight: 600;
        font-size: 0.82rem;
    }

    .vs-value {
        color: var(--text-color);
        font-size: 1.65rem;
        font-weight: 800;
        margin: 8px 0;
    }

    .vs-confidence-high {
        color: #22c55e;
        font-size: 0.78rem;
        font-weight: 600;
    }

    .vs-confidence-medium {
        color: #eab308;
        font-size: 0.78rem;
        font-weight: 600;
    }

    .vs-confidence-low {
        color: #ef4444;
        font-size: 0.78rem;
        font-weight: 600;
    }

    /* Metrics */
    [data-testid="stMetric"] {
        background: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.25);
        border-radius: 10px;
        padding: 12px;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 9px;
        font-weight: 650;
        min-height: 42px;
    }

    /* Dividers */
    hr {
        border-color: rgba(128, 128, 128, 0.20);
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

if "vitals" not in st.session_state:
    st.session_state.vitals = None

if "ocr" not in st.session_state:
    st.session_state.ocr = []

if "history" not in st.session_state:
    st.session_state.history = []


# ============================================================
# HELPERS
# ============================================================

def as_number(value):
    """Safely convert a value to float."""
    if value is None:
        return None

    try:
        value = float(value)
    except (TypeError, ValueError):
        return None

    return value


def safe_int(value, minimum=0, maximum=1000):
    """Safely convert a value to an integer inside bounds."""
    number = as_number(value)

    if number is None:
        return minimum

    if minimum <= number <= maximum:
        return int(round(number))

    return minimum


def safe_confidence(value):
    """Normalize OCR confidence to 0.0-1.0."""
    if value is None:
        return None

    try:
        value = float(value)
    except (TypeError, ValueError):
        return None

    if value > 1:
        value /= 100

    return max(0.0, min(1.0, value))


def find_confidence(vital_name, value, ocr_results):
    """Find the strongest OCR confidence associated with a value."""

    if value is None:
        return None

    vitals = st.session_state.get("vitals")

    if isinstance(vitals, dict):

        direct = safe_confidence(
            vitals.get(f"{vital_name}_confidence")
        )

        if direct is not None:
            return direct

    target = as_number(value)

    if target is None:
        return None

    best = None

    for item in ocr_results:

        if not isinstance(item, dict):
            continue

        text = str(item.get("text", ""))

        confidence = safe_confidence(
            item.get("confidence")
        )

        if confidence is None:
            continue

        if vital_name == "bp":

            if re.search(
                r"\d{2,3}\s*[/\-]\s*\d{2,3}",
                text
            ):
                best = (
                    confidence
                    if best is None
                    else max(best, confidence)
                )

            continue

        numbers = re.findall(
            r"\d+(?:\.\d+)?",
            text
        )

        for number in numbers:

            try:
                detected = float(number)
            except ValueError:
                continue

            if abs(detected - target) < 0.01:

                best = (
                    confidence
                    if best is None
                    else max(best, confidence)
                )

    return best


def confidence_html(confidence):

    if confidence is None:

        return (
            '<span class="vs-confidence-low">'
            'OCR confidence unavailable'
            '</span>'
        )

    if confidence >= 0.80:
        css = "vs-confidence-high"
    elif confidence >= 0.50:
        css = "vs-confidence-medium"
    else:
        css = "vs-confidence-low"

    return (
        f'<span class="{css}">'
        f'OCR confidence: {confidence:.0%}'
        f'</span>'
    )


def normalize_history():

    normalized = []

    for reading in st.session_state.history:

        normalized.append(
            {
                "time": reading.get("time", datetime.now()),
                "hr": safe_int(reading.get("hr"), 0, 300),
                "spo2": safe_int(reading.get("spo2"), 0, 100),
                "bp_sys": safe_int(reading.get("bp_sys"), 0, 300),
                "bp_dia": safe_int(reading.get("bp_dia"), 0, 200),
                "rr": safe_int(reading.get("rr"), 0, 100),
                "etco2": safe_int(reading.get("etco2"), 0, 150),
            }
        )

    return normalized


def run_bp_ocr(image):

    try:
        results = extract_bp_candidates(image)
    except Exception:
        return None, None

    if not isinstance(results, list):
        return None, None

    best_bp = None
    best_confidence = None

    for result in results:

        if not isinstance(result, dict):
            continue

        text = str(result.get("text", ""))

        confidence = safe_confidence(
            result.get("confidence")
        )

        match = re.search(
            r"(\d{2,3})\s*[/\-]\s*(\d{2,3})",
            text
        )

        if not match:
            continue

        systolic = int(match.group(1))
        diastolic = int(match.group(2))

        if not (
            50 <= systolic <= 250
            and 20 <= diastolic <= 150
            and systolic > diastolic
        ):
            continue

        if best_bp is None:
            best_bp = (systolic, diastolic)
            best_confidence = confidence
            continue

        current_score = (
            -1
            if confidence is None
            else confidence
        )

        best_score = (
            -1
            if best_confidence is None
            else best_confidence
        )

        if current_score > best_score:
            best_bp = (systolic, diastolic)
            best_confidence = confidence

    return best_bp, best_confidence


def make_dark_safe_chart(chart_df):

    fig = go.Figure()

    traces = [
        ("HR", "#ef4444"),
        ("SpO2", "#22c55e"),
        ("RR", "#3b82f6"),
        ("EtCO2", "#a855f7"),
    ]

    for column, color in traces:

        if column not in chart_df.columns:
            continue

        fig.add_trace(
            go.Scatter(
                x=chart_df["time"],
                y=chart_df[column],
                mode="lines+markers",
                name=column,
                line={
                    "color": color,
                    "width": 2,
                },
                marker={
                    "color": color,
                    "size": 7,
                },
            )
        )

    fig.update_layout(
        height=420,
        margin=dict(
            l=20,
            r=20,
            t=30,
            b=20,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            color="#9ca3af"
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0)"
        ),
        xaxis=dict(
            title="Time",
            gridcolor="rgba(128,128,128,0.18)",
            zerolinecolor="rgba(128,128,128,0.18)",
        ),
        yaxis=dict(
            title="Value",
            gridcolor="rgba(128,128,128,0.18)",
            zerolinecolor="rgba(128,128,128,0.18)",
        ),
    )

    return fig


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="vs-title">🚑 VitalSight</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="vs-subtitle">'
    'Monitor image reader • OCR • ML trend analysis • '
    'clinical reference'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="vs-warning">
    <strong>⚠️ Reference / educational prototype</strong><br>
    VitalSight is not a medical device and has not been
    clinically validated. Extracted values must be verified
    against the actual monitor and patient assessment.
    Do not use this application as a substitute for clinical
    judgment, medical direction, or local protocols.
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("Patient Context")

    age = st.number_input(
        "Age",
        min_value=0,
        max_value=120,
        value=30,
    )

    complaint = st.text_input(
        "Chief complaint",
        placeholder="Optional",
    )

    st.divider()

    st.caption(
        "Educational / portfolio prototype."
    )


# ============================================================
# IMAGE UPLOAD
# ============================================================

st.subheader("📷 Monitor Image")

uploaded = st.file_uploader(
    "Upload a monitor photograph",
    type=["jpg", "jpeg", "png"],
)

if uploaded:

    try:

        image = Image.open(uploaded).convert("RGB")

        st.image(
            image,
            caption="Uploaded monitor",
            use_container_width=True,
        )

    except Exception as error:

        st.error(
            f"Could not open the image: {error}"
        )

        st.stop()

    if st.button(
        "🔍 Read Monitor",
        type="primary",
        use_container_width=True,
    ):

        with st.spinner("Reading monitor..."):

            try:

                # OCR
                ocr_results = extract_text(image)

                if not isinstance(ocr_results, list):
                    ocr_results = []

                st.session_state.ocr = ocr_results

                # Parse values
                vitals = parse_vitals(ocr_results)

                if not isinstance(vitals, dict):
                    vitals = {}

                # BP-specific OCR
                best_bp, best_bp_confidence = run_bp_ocr(image)

                if best_bp is not None:

                    vitals["bp_sys"] = best_bp[0]
                    vitals["bp_dia"] = best_bp[1]

                    if best_bp_confidence is not None:
                        vitals["bp_confidence"] = (
                            best_bp_confidence
                        )

                st.session_state.vitals = vitals

                st.success(
                    "Monitor reading complete."
                )

            except Exception as error:

                st.session_state.vitals = None

                st.error(
                    f"Reader error: {error}"
                )


# ============================================================
# VITAL DASHBOARD
# ============================================================

if st.session_state.vitals:

    vitals = st.session_state.vitals

    st.divider()

    st.subheader(
        "❤️ Extracted Vital Signs"
    )

    hr = as_number(vitals.get("hr"))
    spo2 = as_number(vitals.get("spo2"))
    bp_sys = as_number(vitals.get("bp_sys"))
    bp_dia = as_number(vitals.get("bp_dia"))
    rr = as_number(vitals.get("rr"))
    etco2 = as_number(vitals.get("etco2"))

    if bp_sys is not None and bp_dia is not None:
        bp_display = (
            f"{bp_sys:.0f}/{bp_dia:.0f} mmHg"
        )
    else:
        bp_display = "--"

    cards = [
        (
            "HR",
            f"{hr:.0f} bpm" if hr is not None else "--",
            find_confidence(
                "hr",
                hr,
                st.session_state.ocr,
            ),
        ),
        (
            "SpO₂",
            f"{spo2:.0f}%" if spo2 is not None else "--",
            find_confidence(
                "spo2",
                spo2,
                st.session_state.ocr,
            ),
        ),
        (
            "Blood Pressure",
            bp_display,
            find_confidence(
                "bp",
                bp_display,
                st.session_state.ocr,
            ),
        ),
        (
            "RR",
            f"{rr:.0f} /min" if rr is not None else "--",
            find_confidence(
                "rr",
                rr,
                st.session_state.ocr,
            ),
        ),
        (
            "EtCO₂",
            f"{etco2:.0f} mmHg"
            if etco2 is not None
            else "--",
            find_confidence(
                "etco2",
                etco2,
                st.session_state.ocr,
            ),
        ),
    ]

    columns = st.columns(5)

    for column, card in zip(columns, cards):

        label, value, confidence = card

        with column:

            st.markdown(
                f"""
                <div class="vs-vital">
                    <div class="vs-label">
                        {label}
                    </div>

                    <div class="vs-value">
                        {value}
                    </div>

                    {confidence_html(confidence)}
                </div>
                """,
                unsafe_allow_html=True,
            )


    # ========================================================
    # VERIFY
    # ========================================================

    st.subheader("✏️ Verify Values")

    st.caption(
        "Confirm the displayed values against the monitor "
        "before adding them to the timeline."
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        verified_hr = st.number_input(
            "HR",
            min_value=0,
            max_value=300,
            value=safe_int(hr, 0, 300),
        )

        verified_spo2 = st.number_input(
            "SpO₂",
            min_value=0,
            max_value=100,
            value=safe_int(spo2, 0, 100),
        )

    with c2:

        verified_sys = st.number_input(
            "Systolic BP",
            min_value=0,
            max_value=300,
            value=safe_int(bp_sys, 0, 300),
        )

        verified_dia = st.number_input(
            "Diastolic BP",
            min_value=0,
            max_value=200,
            value=safe_int(bp_dia, 0, 200),
        )

    with c3:

        verified_rr = st.number_input(
            "RR",
            min_value=0,
            max_value=100,
            value=safe_int(rr, 0, 100),
        )

        verified_etco2 = st.number_input(
            "EtCO₂",
            min_value=0,
            max_value=150,
            value=safe_int(etco2, 0, 150),
        )

    if st.button(
        "➕ Add Verified Reading",
        use_container_width=True,
    ):

        # IMPORTANT:
        # Keep these keys lowercase because src.ml expects
        # lowercase vital names.
        st.session_state.history.append(
            {
                "time": datetime.now(),
                "hr": verified_hr,
                "spo2": verified_spo2,
                "bp_sys": verified_sys,
                "bp_dia": verified_dia,
                "rr": verified_rr,
                "etco2": verified_etco2,
            }
        )

        st.success(
            "Verified reading added."
        )


# ============================================================
# OCR DETAILS
# ============================================================

if st.session_state.ocr:

    st.divider()

    with st.expander("🔎 OCR Details"):

        for item in st.session_state.ocr:

            if not isinstance(item, dict):
                continue

            text = item.get("text", "")

            confidence = safe_confidence(
                item.get("confidence")
            )

            if confidence is None:
                confidence_text = "N/A"
            else:
                confidence_text = f"{confidence:.0%}"

            st.write(
                f"**{text}** — {confidence_text}"
            )


# ============================================================
# TIMELINE
# ============================================================

if st.session_state.history:

    st.divider()

    st.subheader("📈 Patient Timeline")

    history = normalize_history()

    chart_df = pd.DataFrame(history)

    display_df = chart_df.copy()

    display_df["time"] = (
        pd.to_datetime(
            display_df["time"]
        ).dt.strftime("%H:%M:%S")
    )

    display_df = display_df.rename(
        columns={
            "hr": "HR",
            "spo2": "SpO₂",
            "bp_sys": "BP Sys",
            "bp_dia": "BP Dia",
            "rr": "RR",
            "etco2": "EtCO₂",
        }
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )


    # ========================================================
    # TREND GRAPH
    # ========================================================

    st.subheader("📊 Vital Trends")

    fig = make_dark_safe_chart(chart_df)

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": False,
        },
    )


    # ========================================================
    # ML TREND MODEL
    # ========================================================

    st.divider()

    st.subheader("🤖 ML Trend Estimate")

    st.markdown(
        """
        <div class="vs-reference">
        <strong>Prototype model:</strong>
        This section estimates the direction of the recorded
        vital-sign trajectory. It is not a clinical deterioration
        score and should not be interpreted as one.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if len(history) < 3:

        st.info(
            "Add at least 3 verified readings to generate "
            "a prototype trend estimate."
        )

    else:

        try:

            from src.ml import (
                train_trend_model,
                predict_trend,
            )

            model = train_trend_model()

            prediction, confidence, probabilities = (
                predict_trend(
                    model,
                    history,
                )
            )

            if prediction == "improving":

                st.success(
                    f"🟢 Trend estimate: Improving "
                    f"({confidence:.0%} model confidence)"
                )

            elif prediction == "worsening":

                st.error(
                    f"🔴 Trend estimate: Worsening "
                    f"({confidence:.0%} model confidence)"
                )

            else:

                st.warning(
                    f"🟡 Trend estimate: Stable "
                    f"({confidence:.0%} model confidence)"
                )

            p1, p2, p3 = st.columns(3)

            with p1:

                st.metric(
                    "Improving",
                    f"{probabilities.get('improving', 0):.0%}",
                )

            with p2:

                st.metric(
                    "Stable",
                    f"{probabilities.get('stable', 0):.0%}",
                )

            with p3:

                st.metric(
                    "Worsening",
                    f"{probabilities.get('worsening', 0):.0%}",
                )

            st.caption(
                "Model probabilities are outputs of the "
                "prototype training data and are not "
                "clinical risk probabilities."
            )

        except Exception as error:

            st.warning(
                f"ML trend model unavailable: {error}"
            )


# ============================================================
# CLINICAL REFERENCE
# ============================================================

if st.session_state.vitals:

    st.divider()

    st.subheader(
        "🩺 Clinical Reference / Differential Considerations"
    )

    st.markdown(
        """
        <div class="vs-reference">
        <strong>Reference only — not a diagnosis.</strong><br>
        The items below are possible clinical considerations
        that may be associated with combinations of observed
        findings. They are not intended to identify the patient's
        actual condition. Correlate with history, physical
        examination, monitor data, ECG, treatment response,
        medical direction, and applicable protocols.
        </div>
        """,
        unsafe_allow_html=True,
    )

    hr_value = as_number(
        st.session_state.vitals.get("hr")
    )

    spo2_value = as_number(
        st.session_state.vitals.get("spo2")
    )

    systolic_value = as_number(
        st.session_state.vitals.get("bp_sys")
    )

    rr_value = as_number(
        st.session_state.vitals.get("rr")
    )

    etco2_value = as_number(
        st.session_state.vitals.get("etco2")
    )

    considerations = []

    if hr_value is not None and hr_value > 100:

        considerations.append(
            {
                "title": "Tachycardia pattern",
                "findings": [
                    f"HR approximately {hr_value:.0f} bpm"
                ],
                "considerations": [
                    "Pain or physiologic stress",
                    "Fever or systemic illness",
                    "Hypovolemia",
                    "Hypoxemia",
                    "Medication or stimulant effect",
                    "Primary cardiac rhythm disturbance",
                ],
            }
        )

    if hr_value is not None and hr_value < 60:

        considerations.append(
            {
                "title": "Bradycardia pattern",
                "findings": [
                    f"HR approximately {hr_value:.0f} bpm"
                ],
                "considerations": [
                    "Normal variant in some patients",
                    "Medication effect",
                    "Hypothermia",
                    "Conduction disturbance",
                    "Hypoxia or other physiologic stressors",
                ],
            }
        )

    if spo2_value is not None and spo2_value < 94:

        considerations.append(
            {
                "title": "Low oxygen saturation pattern",
                "findings": [
                    f"SpO₂ approximately {spo2_value:.0f}%"
                ],
                "considerations": [
                    "Ventilation or oxygenation impairment",
                    "Pulmonary disease",
                    "Airway obstruction",
                    "V/Q mismatch",
                    "Measurement artifact or poor probe signal",
                ],
            }
        )

    if (
        systolic_value is not None
        and systolic_value < 90
    ):

        considerations.append(
            {
                "title": "Low systolic blood pressure pattern",
                "findings": [
                    f"Systolic BP approximately "
                    f"{systolic_value:.0f} mmHg"
                ],
                "considerations": [
                    "Volume depletion",
                    "Distributive physiology",
                    "Cardiac causes",
                    "Medication effect",
                    "Measurement error or artifact",
                ],
            }
        )

    if rr_value is not None and rr_value > 20:

        considerations.append(
            {
                "title": "Tachypnea pattern",
                "findings": [
                    f"RR approximately {rr_value:.0f}/min"
                ],
                "considerations": [
                    "Respiratory distress",
                    "Metabolic acidosis",
                    "Pain or anxiety",
                    "Fever",
                    "Pulmonary pathology",
                ],
            }
        )

    if etco2_value is not None and etco2_value < 35:

        considerations.append(
            {
                "title": "Low EtCO₂ pattern",
                "findings": [
                    f"EtCO₂ approximately "
                    f"{etco2_value:.0f} mmHg"
                ],
                "considerations": [
                    "Hyperventilation",
                    "Reduced pulmonary perfusion",
                    "Low cardiac output states",
                    "Ventilation-perfusion changes",
                    "Sampling or equipment issues",
                ],
            }
        )

    if not considerations:

        st.info(
            "No reference patterns were triggered by the "
            "current entered values."
        )

    else:

        for item in considerations:

            with st.expander(item["title"]):

                st.write(
                    "**Observed finding(s)**"
                )

                for finding in item["findings"]:
                    st.write(f"- {finding}")

                st.write(
                    "**Possible clinical considerations**"
                )

                for consideration in item["considerations"]:
                    st.write(
                        f"- {consideration}"
                    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "VitalSight • Educational computer-vision + ML prototype • "
    "Verify all extracted values against the source monitor."
)

