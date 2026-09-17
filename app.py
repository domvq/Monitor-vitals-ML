
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

    .block-container {
        max-width: 1400px;
        padding-top: 2rem;
    }

    .title {
        font-size: 2.6rem;
        font-weight: 800;
        color: #0f172a;
    }

    .subtitle {
        color: #64748b;
        margin-bottom: 1rem;
    }

    .warning {
        padding: 15px;
        border-radius: 10px;
        background: #fff7ed;
        border-left: 5px solid #f97316;
        color: #7c2d12;
        margin-bottom: 20px;
    }

    .reference {
        padding: 15px;
        border-radius: 10px;
        background: #eff6ff;
        border-left: 5px solid #3b82f6;
        color: #1e3a8a;
        margin-bottom: 15px;
    }

    .vital {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 18px;
        text-align: center;
        min-height: 125px;
    }

    .label {
        color: #64748b;
        font-weight: 600;
        font-size: 0.85rem;
    }

    .value {
        color: #0f172a;
        font-size: 1.7rem;
        font-weight: 800;
        margin: 6px 0;
    }

    .confidence-high {
        color: #15803d;
        font-size: 0.8rem;
        font-weight: 600;
    }

    .confidence-medium {
        color: #ca8a04;
        font-size: 0.8rem;
        font-weight: 600;
    }

    .confidence-low {
        color: #dc2626;
        font-size: 0.8rem;
        font-weight: 600;
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

st.subheader("📷 Monitor Images")

uploaded_files = st.file_uploader(
    "Upload up to 5 monitor photographs",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True
)

# Limit to 5 images
if len(uploaded_files) > 5:
    st.error("Please upload a maximum of 5 images.")
    uploaded_files = uploaded_files[:5]


if uploaded_files:

    st.write(
        f"**{len(uploaded_files)} image(s) selected**"
    )

    # Preview images
    preview_columns = st.columns(
        min(len(uploaded_files), 5)
    )

    for column, uploaded in zip(
        preview_columns,
        uploaded_files
    ):

        with column:

            try:

                image = Image.open(
                    uploaded
                ).convert("RGB")

                st.image(
                    image,
                    caption=uploaded.name,
                    use_container_width=True
                )

            except Exception as e:

                st.error(
                    f"Could not open {uploaded.name}: {e}"
                )


    # ========================================================
    # READ ALL IMAGES
    # ========================================================

    if st.button(
        "🔍 Read All Monitors",
        type="primary",
        use_container_width=True
    ):

        # Clear previous OCR results
        st.session_state.ocr = []
        st.session_state.vitals = None

        all_readings = []

        progress = st.progress(0)
        status = st.empty()

        for index, uploaded in enumerate(
            uploaded_files
        ):

            try:

                status.info(
                    f"Reading image {index + 1} "
                    f"of {len(uploaded_files)}: "
                    f"{uploaded.name}"
                )

                # ------------------------------------------------
                # Open image
                # ------------------------------------------------

                image = Image.open(
                    uploaded
                ).convert("RGB")

                # ------------------------------------------------
                # General OCR
                # ------------------------------------------------

                ocr_results = extract_text(
                    image
                )

                if not isinstance(
                    ocr_results,
                    list
                ):
                    ocr_results = []

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

                    if not isinstance(
                        result,
                        dict
                    ):
                        continue

                    text = str(
                        result.get(
                            "text",
                            ""
                        )
                    )

                    try:

                        confidence = float(
                            result.get(
                                "confidence",
                                0
                            )
                        )

                    except (
                        TypeError,
                        ValueError
                    ):

                        confidence = 0.0

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

                    # Sanity check
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

                # ------------------------------------------------
                # Store reading
                # ------------------------------------------------

                all_readings.append(
                    {
                        "filename": uploaded.name,
                        "vitals": vitals,
                        "ocr": ocr_results
                    }
                )

                # Keep the most recent reading available
                st.session_state.vitals = vitals

                st.session_state.ocr = (
                    ocr_results
                )

                # ------------------------------------------------
                # Release image memory
                # ------------------------------------------------

                del image

                progress.progress(
                    (index + 1) /
                    len(uploaded_files)
                )

            except Exception as e:

                st.error(
                    f"Error processing "
                    f"{uploaded.name}: {e}"
                )

                progress.progress(
                    (index + 1) /
                    len(uploaded_files)
                )

        status.success(
            f"Finished processing "
            f"{len(all_readings)} image(s)."
        )

        # Save batch results
        st.session_state.batch_readings = (
            all_readings
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
