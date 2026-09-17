id="4k7q1z"
import streamlit as st
from PIL import Image

from src.ocr import extract_text
from src.parser import parse_vitals


st.set_page_config(
    page_title="VitalSight",
    page_icon="🚑",
    layout="wide",
)


st.title("🚑 VitalSight")

st.caption(
    "OCR + parser diagnostic"
)


uploaded = st.file_uploader(
    "Upload a monitor photograph",
    type=["jpg", "jpeg", "png"],
)


if uploaded:

    image = Image.open(
        uploaded
    ).convert("RGB")

    st.image(
        image,
        caption="Uploaded monitor",
        use_container_width=True,
    )


    if st.button(
        "🔍 Read Monitor",
        type="primary",
    ):

        # ====================================================
        # OCR
        # ====================================================

        try:

            with st.spinner(
                "Running OCR..."
            ):

                ocr_results = extract_text(
                    image
                )

            st.success(
                "OCR completed."
            )

        except Exception as e:

            st.error(
                "OCR failed."
            )

            st.exception(e)

            st.stop()


        # ====================================================
        # PARSER
        # ====================================================

        try:

            with st.spinner(
                "Parsing vital signs..."
            ):

                vitals = parse_vitals(
                    ocr_results
                )

            st.success(
                "Parser completed."
            )

            st.subheader(
                "Parsed Vitals"
            )

            st.write(
                vitals
            )

            st.write(
                "Type:",
                type(vitals).__name__,
            )

            if isinstance(
                vitals,
                dict,
            ):

                for key, value in vitals.items():

                    st.write(
                        f"**{key}:** {value}"
                    )

        except Exception as e:

            st.error(
                "Parser failed."
            )

            st.exception(e)

