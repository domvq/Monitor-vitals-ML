id="r3kq8m"
import streamlit as st

st.set_page_config(
    page_title="VitalSight",
    page_icon="🚑",
    layout="wide",
)

# ============================================================
# SIMPLE THEME-SAFE CSS
# ============================================================

st.markdown(
    """
    <style>

    .vital-card {
        padding: 20px;
        border-radius: 12px;
        border: 1px solid rgba(128,128,128,0.25);
        background: rgba(128,128,128,0.06);
        text-align: center;
    }

    .vital-label {
        font-size: 0.85rem;
        opacity: 0.70;
        font-weight: 600;
    }

    .vital-value {
        font-size: 1.7rem;
        font-weight: 800;
        margin-top: 8px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# HEADER
# ============================================================

st.title("🚑 VitalSight")

st.caption(
    "Monitor image reader • OCR • ML trend analysis • "
    "clinical reference"
)

st.warning(
    "Reference / educational prototype. "
    "Extracted values must be verified against the actual "
    "monitor and patient assessment."
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

# ============================================================
# UPLOAD
# ============================================================

st.subheader("📷 Monitor Image")

uploaded = st.file_uploader(
    "Upload a monitor photograph",
    type=["jpg", "jpeg", "png"],
)

if uploaded:

    st.success("Image uploaded successfully.")

    st.image(
        uploaded,
        caption="Uploaded monitor",
        use_container_width=True,
    )

# ============================================================
# TEST CARDS
# ============================================================

st.divider()

st.subheader("❤️ Extracted Vital Signs")

columns = st.columns(5)

test_cards = [
    ("HR", "--"),
    ("SpO₂", "--"),
    ("Blood Pressure", "--"),
    ("RR", "--"),
    ("EtCO₂", "--"),
]

for column, (label, value) in zip(
    columns,
    test_cards,
):

    with column:

        st.markdown(
            f"""
            <div class="vital-card">
                <div class="vital-label">
                    {label}
                </div>
                <div class="vital-value">
                    {value}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ============================================================
# PLOTLY TEST
# ============================================================

st.divider()

st.subheader("📈 Patient Timeline")

import plotly.graph_objects as go

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=["10:00", "10:05", "10:10"],
        y=[80, 84, 82],
        mode="lines+markers",
        name="HR",
        line=dict(
            color="#60a5fa",
            width=3,
        ),
    )
)

fig.update_layout(
    height=350,
    template="plotly_dark",
)

st.plotly_chart(
    fig,
    use_container_width=True,
)

st.success("UI test completed successfully.")

