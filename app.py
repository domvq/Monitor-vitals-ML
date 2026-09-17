
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
    layout="wide"
)


# ============================================================
# STYLE
# ============================================================

st.markdown(
    """
    <style>

    /* ==========================================
       VITALSIGHT THEME-AWARE STYLING
       ========================================== */

    /* ---------- Main title ---------- */

    .title {
        font-size: 2.6rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        color: var(--text-color);
    }

    .subtitle {
        color: var(--secondary-text-color);
        margin-bottom: 1.25rem;
        font-size: 1rem;
    }


    /* ---------- Warning ---------- */

    .warning {
        padding: 16px 18px;
        border-radius: 10px;

        background: rgba(245, 158, 11, 0.10);
        border: 1px solid rgba(245, 158, 11, 0.30);
        border-left: 4px solid #f59e0b;

        color: var(--text-color);

        margin-bottom: 20px;
        line-height: 1.55;
    }


    /* ---------- Reference ---------- */

    .reference {
        padding: 16px 18px;
        border-radius: 10px;

        background: rgba(59, 130, 246, 0.10);
        border: 1px solid rgba(59, 130, 246, 0.30);
        border-left: 4px solid #3b82f6;

        color: var(--text-color);

        margin-bottom: 15px;
        line-height: 1.55;
    }


    /* ---------- Vital cards ---------- */

    .vital {
        background: var(--secondary-background-color);

        border: 1px solid rgba(128, 128, 128, 0.25);
        border-radius: 12px;

        padding: 18px 12px;

        text-align: center;
        min-height: 125px;

        box-shadow: none;

        transition:
            border-color 0.15s ease,
            transform 0.15s ease;
    }

    .vital:hover {
        border-color: rgba(59, 130, 246, 0.50);
        transform: translateY(-1px);
    }


    /* ---------- Card label ---------- */

    .label {
        color: var(--secondary-text-color);

        font-weight: 600;
        font-size: 0.82rem;

        letter-spacing: 0.01em;
    }


    /* ---------- Card value ---------- */

    .value {
        color: var(--text-color);

        font-size: 1.7rem;
        font-weight: 800;

        margin: 8px 0;

        letter-spacing: -0.02em;
    }


    /* ---------- Confidence ---------- */

    .confidence-high {
        color: #34d399;

        font-size: 0.78rem;
        font-weight: 600;
    }

    .confidence-medium {
        color: #fbbf24;

        font-size: 0.78rem;
        font-weight: 600;
    }

    .confidence-low {
        color: #f87171;

        font-size: 0.78rem;
        font-weight: 600;
    }


    /* ---------- Headings ---------- */

    h1, h2, h3 {
        color: var(--text-color);
    }


    /* ---------- Buttons ---------- */

    .stButton > button {
        border-radius: 9px;
        font-weight: 650;
        min-height: 42px;
    }


    /* ---------- Metrics ---------- */

    [data-testid="stMetric"] {
        background: var(--secondary-background-color);

        border: 1px solid rgba(128, 128, 128, 0.25);
        border-radius: 10px;

        padding: 12px;
    }


    /* ---------- Dataframe ---------- */

    [data-testid="stDataFrame"] {
        border-radius: 10px;
        overflow: hidden;
    }


    /* ---------- Dividers ---------- */

    hr {
        border-color: rgba(128, 128, 128, 0.20);
    }

    </style>
    """,
    unsafe_allow_html=True
)

# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="title">🚑 VitalSight</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Monitor image reader • OCR • ML trend analysis • '
    'clinical reference'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="warning">
    <strong>⚠️ Reference / educational prototype</strong><br>
    VitalSight is not a medical device and has not been
    clinically validated. Extracted values must be verified
    against the actual monitor and patient assessment.
    Do not use this application as a substitute for clinical
    judgment, medical direction, or local protocols.
    </div>
    """,
    unsafe_allow_html=True
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
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("Patient Context")

    age = st.number_input(
        "Age",
        min_value=0,
        max_value=120,
        value=30
    )

    complaint = st.text_input(
        "Chief complaint",
        placeholder="Optional"
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
    type=["jpg", "jpeg", "png"]
)


if uploaded:

    image = Image.open(
        uploaded
    ).convert("RGB")

    st.image(
        image,
        caption="Uploaded monitor",
        use_container_width=True
    )

    if st.button(
        "🔍 Read Monitor",
        type="primary",
        use_container_width=True
    ):

        with st.spinner(
            "Reading monitor..."
        ):

            try:

                # ------------------------------------------------
                # OCR
                # ------------------------------------------------

                ocr_results = extract_text(
                    image
                )

                if not isinstance(
                    ocr_results,
                    list
                ):

                    ocr_results = []

                st.session_state.ocr = (
                    ocr_results
                )

                # ------------------------------------------------
                # Parse vitals
                # ------------------------------------------------

                vitals = parse_vitals(
                    ocr_results
                )

                if not isinstance(
                    vitals,
                    dict
                ):

                    vitals = {}

                # ------------------------------------------------
                # BP-specific OCR
                # ------------------------------------------------

                bp_results = extract_bp_candidates(
                    image
                )

                best_bp = None
                best_bp_confidence = None

                for result in bp_results:

                    text = str(
                        result.get(
                            "text",
                            ""
                        )
                    )

                    confidence = float(
                        result.get(
                            "confidence",
                            0
                        )
                    )

                    match = re.search(
                        r"(\d{2,3})\s*[/\-]\s*(\d{2,3})",
                        text
                    )

                    if not match:
                        continue

                    systolic = int(
                        match.group(1)
                    )

                    diastolic = int(
                        match.group(2)
                    )

                    if not (
                        50 <= systolic <= 250
                        and 20 <= diastolic <= 150
                        and systolic > diastolic
                    ):

                        continue

                    if (
                        best_bp_confidence is None
                        or confidence > best_bp_confidence
                    ):

                        best_bp = (
                            systolic,
                            diastolic
                        )

                        best_bp_confidence = (
                            confidence
                        )

                if best_bp:

                    vitals["bp_sys"] = (
                        best_bp[0]
                    )

                    vitals["bp_dia"] = (
                        best_bp[1]
                    )

                    vitals["bp_confidence"] = (
                        best_bp_confidence
                    )

                st.session_state.vitals = (
                    vitals
                )

                st.success(
                    "Monitor reading complete."
                )

            except Exception as e:

                st.error(
                    f"Reader error: {e}"
                )


# ============================================================
# CONFIDENCE
# ============================================================

def find_confidence(
    vital_name,
    value,
    ocr_results
):

    vitals = st.session_state.vitals

    if isinstance(
        vitals,
        dict
    ):

        parser_confidence = vitals.get(
            f"{vital_name}_confidence"
        )

        if isinstance(
            parser_confidence,
            (int, float)
        ):

            return float(
                parser_confidence
            )

    if value is None:
        return None

    best = None

    for item in ocr_results:

        if not isinstance(
            item,
            dict
        ):

            continue

        text = str(
            item.get(
                "text",
                ""
            )
        )

        confidence = float(
            item.get(
                "confidence",
                0
            )
        )

        numbers = re.findall(
            r"\d+(?:\.\d+)?",
            text
        )

        if not numbers:
            continue

        if vital_name == "bp":

            if "/" in text:

                if (
                    best is None
                    or confidence > best
                ):

                    best = confidence

            continue

        try:

            detected = float(
                numbers[0]
            )

        except ValueError:

            continue

        try:

            target = float(
                value
            )

        except (
            TypeError,
            ValueError
        ):

            continue

        if abs(
            detected - target
        ) < 0.01:

            if (
                best is None
                or confidence > best
            ):

                best = confidence

    return best


def confidence_html(
    confidence
):

    if confidence is None:

        return (
            '<span class="confidence-low">'
            'OCR confidence unavailable'
            '</span>'
        )

    if confidence >= 0.80:

        css = "confidence-high"

    elif confidence >= 0.50:

        css = "confidence-medium"

    else:

        css = "confidence-low"

    return (
        f'<span class="{css}">'
        f'OCR confidence: {confidence:.0%}'
        f'</span>'
    )


def safe_int(
    value,
    minimum,
    maximum
):

    if isinstance(
        value,
        (int, float)
    ):

        if minimum <= value <= maximum:

            return int(value)

    return 0


# ============================================================
# VITAL DASHBOARD
# ============================================================

if st.session_state.vitals:

    vitals = st.session_state.vitals

    st.divider()

    st.subheader(
        "❤️ Extracted Vital Signs"
    )

    hr = vitals.get("hr")
    spo2 = vitals.get("spo2")
    bp_sys = vitals.get("bp_sys")
    bp_dia = vitals.get("bp_dia")
    rr = vitals.get("rr")
    etco2 = vitals.get("etco2")

    if (
        isinstance(bp_sys, (int, float))
        and isinstance(bp_dia, (int, float))
    ):

        bp_display = (
            f"{bp_sys:.0f}/"
            f"{bp_dia:.0f} mmHg"
        )

    else:

        bp_display = "--"

    cards = [

        (
            "HR",
            (
                f"{hr:.0f} bpm"
                if isinstance(
                    hr,
                    (int, float)
                )
                else "--"
            ),
            find_confidence(
                "hr",
                hr,
                st.session_state.ocr
            )
        ),

        (
            "SpO₂",
            (
                f"{spo2:.0f}%"
                if isinstance(
                    spo2,
                    (int, float)
                )
                else "--"
            ),
            find_confidence(
                "spo2",
                spo2,
                st.session_state.ocr
            )
        ),

        (
            "Blood Pressure",
            bp_display,
            find_confidence(
                "bp",
                bp_display,
                st.session_state.ocr
            )
        ),

        (
            "RR",
            (
                f"{rr:.0f} /min"
                if isinstance(
                    rr,
                    (int, float)
                )
                else "--"
            ),
            find_confidence(
                "rr",
                rr,
                st.session_state.ocr
            )
        ),

        (
            "EtCO₂",
            (
                f"{etco2:.0f} mmHg"
                if isinstance(
                    etco2,
                    (int, float)
                )
                else "--"
            ),
            find_confidence(
                "etco2",
                etco2,
                st.session_state.ocr
            )
        )
    ]

    columns = st.columns(5)

    for column, card in zip(
        columns,
        cards
    ):

        label, value, confidence = card

        with column:

            st.markdown(
                f"""
                <div class="vital">

                <div class="label">
                {label}
                </div>

                <div class="value">
                {value}
                </div>

                {confidence_html(confidence)}

                </div>
                """,
                unsafe_allow_html=True
            )


    # ========================================================
    # VERIFY
    # ========================================================

    st.subheader(
        "✏️ Verify Values"
    )

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
            value=safe_int(
                hr,
                0,
                300
            )
        )

        verified_spo2 = st.number_input(
            "SpO₂",
            min_value=0,
            max_value=100,
            value=safe_int(
                spo2,
                0,
                100
            )
        )

    with c2:

        verified_sys = st.number_input(
            "Systolic BP",
            min_value=0,
            max_value=300,
            value=safe_int(
                bp_sys,
                0,
                300
            )
        )

        verified_dia = st.number_input(
            "Diastolic BP",
            min_value=0,
            max_value=200,
            value=safe_int(
                bp_dia,
                0,
                200
            )
        )

    with c3:

        verified_rr = st.number_input(
            "RR",
            min_value=0,
            max_value=100,
            value=safe_int(
                rr,
                0,
                100
            )
        )

        verified_etco2 = st.number_input(
            "EtCO₂",
            min_value=0,
            max_value=150,
            value=safe_int(
                etco2,
                0,
                150
            )
        )


    if st.button(
        "➕ Add Verified Reading",
        use_container_width=True
    ):

        st.session_state.history.append(
            {
                "time": datetime.now(),
                "HR": verified_hr,
                "SpO2": verified_spo2,
                "BP Sys": verified_sys,
                "BP Dia": verified_dia,
                "RR": verified_rr,
                "EtCO2": verified_etco2
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

    with st.expander(
        "🔎 OCR Details"
    ):

        for item in st.session_state.ocr:

            if not isinstance(
                item,
                dict
            ):

                continue

            text = item.get(
                "text",
                ""
            )

            confidence = float(
                item.get(
                    "confidence",
                    0
                )
            )

            st.write(
                f"**{text}** — "
                f"{confidence:.0%}"
            )


# ============================================================
# TIMELINE
# ============================================================

if st.session_state.history:

    st.divider()

    st.subheader(
        "📈 Patient Timeline"
    )

    df = pd.DataFrame(
        st.session_state.history
    )

    display_df = df.copy()

    display_df["time"] = (
        pd.to_datetime(
            display_df["time"]
        ).dt.strftime(
            "%H:%M:%S"
        )
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )


    # ========================================================
    # TREND GRAPH
    # ========================================================

    chart_df = pd.DataFrame(
        st.session_state.history
    )

    fig = go.Figure()

    for column in [
        "HR",
        "SpO2",
        "RR",
        "EtCO2"
    ]:

        fig.add_trace(
            go.Scatter(
                x=chart_df["time"],
                y=chart_df[column],
                mode="lines+markers",
                name=column
            )
        )

    fig.update_layout(
        template="plotly_white",
        height=400,
        xaxis_title="Time",
        yaxis_title="Value"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


    # ========================================================
    # ML TREND MODEL
    # ========================================================

    st.divider()

    st.subheader(
        "🤖 ML Trend Estimate"
    )

    st.markdown(
        """
        <div class="reference">
        <strong>Prototype model:</strong>
        This section estimates the direction of the recorded
        vital-sign trajectory. It is not a clinical deterioration
        score and should not be interpreted as one.
        </div>
        """,
        unsafe_allow_html=True
    )

    if len(
        st.session_state.history
    ) < 3:

        st.info(
            "Add at least 3 verified readings to generate "
            "a prototype trend estimate."
        )

    else:

        try:

            from src.ml import (
                train_trend_model,
                predict_trend
            )

            model = train_trend_model()

            prediction, confidence, probabilities = (
                predict_trend(
                    model,
                    st.session_state.history
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
                    f"{probabilities.get('improving', 0):.0%}"
                )

            with p2:

                st.metric(
                    "Stable",
                    f"{probabilities.get('stable', 0):.0%}"
                )

            with p3:

                st.metric(
                    "Worsening",
                    f"{probabilities.get('worsening', 0):.0%}"
                )

            st.caption(
                "Model probabilities are outputs of the "
                "prototype training data and are not "
                "clinical risk probabilities."
            )

        except Exception as e:

            st.warning(
                f"ML trend model unavailable: {e}"
            )


# ============================================================
# CLINICAL REFERENCE / DIFFERENTIAL
# ============================================================

if st.session_state.vitals:

    st.divider()

    st.subheader(
        "🩺 Clinical Reference / Differential Considerations"
    )

    st.markdown(
        """
        <div class="reference">
        <strong>Reference only — not a diagnosis.</strong><br>
        The items below are possible clinical considerations
        that may be associated with combinations of observed
        findings. They are not intended to identify the patient's
        actual condition. Correlate with history, physical
        examination, monitor data, ECG, treatment response,
        medical direction, and applicable protocols.
        </div>
        """,
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # Pull values
    # --------------------------------------------------------

    hr_value = st.session_state.vitals.get(
        "hr"
    )

    spo2_value = st.session_state.vitals.get(
        "spo2"
    )

    systolic_value = st.session_state.vitals.get(
        "bp_sys"
    )

    rr_value = st.session_state.vitals.get(
        "rr"
    )

    etco2_value = st.session_state.vitals.get(
        "etco2"
    )


    considerations = []


    # --------------------------------------------------------
    # Tachycardia
    # --------------------------------------------------------

    if (
        isinstance(hr_value, (int, float))
        and hr_value > 100
    ):

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
                    "Primary cardiac rhythm disturbance"
                ]
            }
        )


    # --------------------------------------------------------
    # Bradycardia
    # --------------------------------------------------------

    if (
        isinstance(hr_value, (int, float))
        and hr_value < 60
    ):

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
                    "Hypoxia or other physiologic stressors"
                ]
            }
        )


    # --------------------------------------------------------
    # Low oxygen saturation
    # --------------------------------------------------------

    if (
        isinstance(spo2_value, (int, float))
        and spo2_value < 94
    ):

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
                    "Measurement artifact or poor probe signal"
                ]
            }
        )


    # --------------------------------------------------------
    # Hypotension
    # --------------------------------------------------------

    if (
        isinstance(
            systolic_value,
            (int, float)
        )
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
                    "Measurement error or artifact"
                ]
            }
        )


    # --------------------------------------------------------
    # Tachypnea
    # --------------------------------------------------------

    if (
        isinstance(rr_value, (int, float))
        and rr_value > 20
    ):

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
                    "Pulmonary pathology"
                ]
            }
        )


    # --------------------------------------------------------
    # Low EtCO2
    # --------------------------------------------------------

    if (
        isinstance(etco2_value, (int, float))
        and etco2_value < 35
    ):

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
                    "Sampling or equipment issues"
                ]
            }
        )


    # --------------------------------------------------------
    # Display
    # --------------------------------------------------------

    if not considerations:

        st.info(
            "No reference patterns were triggered by the "
            "current entered values."
        )

    else:

        for item in considerations:

            with st.expander(
                item["title"]
            ):

                st.write(
                    "**Observed finding(s)**"
                )

                for finding in item["findings"]:

                    st.write(
                        f"- {finding}"
                    )

                st.write(
                    "**Possible clinical considerations**"
                )

                for consideration in item[
                    "considerations"
                ]:

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
