
import streamlit as st
from PIL import Image

from src.ocr import extract_text, extract_bp_candidates


st.set_page_config(
    page_title="VitalSight",
    page_icon="🚑",
    layout="wide",
)


st.title("🚑 VitalSight")

st.caption(
    "OCR diagnostic version"
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

        st.write("Starting OCR...")

        try:

            with st.spinner(
                "Reading monitor..."
            ):

                ocr_results = extract_text(
                    image
                )

            st.success(
                "General OCR completed."
            )

            st.write(
                f"Detected {len(ocr_results)} "
                "text regions."
            )

            if ocr_results:

                st.subheader(
                    "OCR Results"
                )

                for item in ocr_results:

                    st.write(
                        f"**{item.get('text', '')}** "
                        f"— "
                        f"{item.get('confidence', 0):.0%}"
                    )

        except Exception as e:

            st.error(
                "General OCR failed."
            )

            st.exception(e)


        # ====================================================
        # BLOOD PRESSURE
        # ====================================================

        st.divider()

        st.subheader(
            "Blood Pressure OCR"
        )

        try:

            with st.spinner(
                "Searching for blood pressure..."
            ):

                bp_results = extract_bp_candidates(
                    image
                )

            st.success(
                "Blood pressure OCR completed."
            )

            if bp_results:

                for result in bp_results:

                    st.write(
                        result
                    )

            else:

                st.info(
                    "No blood pressure candidates detected."
                )

        except Exception as e:

            st.error(
                "Blood pressure OCR failed."
            )

            st.exception(e)

