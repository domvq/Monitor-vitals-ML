
import streamlit as st

st.set_page_config(
    page_title="Monitor Vitals ML",
    page_icon="🩺",
    layout="wide"
)

st.title("🩺 Monitor Vitals ML")

st.success("Application is running.")

st.markdown(
    """
    ### Upload a monitor image

    This is a test of the application interface.
    """
)

uploaded_file = st.file_uploader(
    "Choose a monitor image",
    type=["png", "jpg", "jpeg"]
)

if uploaded_file is not None:

    st.image(
        uploaded_file,
        caption="Uploaded monitor image",
        width="stretch"
    )

    st.success("Image uploaded successfully.")
