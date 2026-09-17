
import streamlit as st

st.set_page_config(
    page_title="VitalSight Diagnostic",
    page_icon="🚑",
    layout="wide",
)

st.title("🚑 VitalSight Diagnostic")

st.success("Base Streamlit works.")

# ------------------------------------------------------------
# Standard dependencies
# ------------------------------------------------------------

try:
    import pandas as pd
    st.success("✅ pandas")
except Exception as e:
    st.error(f"❌ pandas: {e}")

try:
    import plotly.graph_objects as go
    st.success("✅ plotly")
except Exception as e:
    st.error(f"❌ plotly: {e}")

try:
    from PIL import Image
    st.success("✅ Pillow")
except Exception as e:
    st.error(f"❌ Pillow: {e}")

try:
    import cv2
    st.success("✅ OpenCV")
except Exception as e:
    st.error(f"❌ OpenCV: {e}")

try:
    import numpy as np
    st.success("✅ NumPy")
except Exception as e:
    st.error(f"❌ NumPy: {e}")

try:
    import pytesseract
    st.success("✅ pytesseract")
except Exception as e:
    st.error(f"❌ pytesseract: {e}")

# ------------------------------------------------------------
# Project modules
# ------------------------------------------------------------

try:
    from src.ocr import extract_text, extract_bp_candidates
    st.success("✅ src.ocr")
except Exception as e:
    st.error(f"❌ src.ocr: {e}")

try:
    from src.parser import parse_vitals
    st.success("✅ src.parser")
except Exception as e:
    st.error(f"❌ src.parser: {e}")

try:
    from src.ml import train_trend_model, predict_trend
    st.success("✅ src.ml")
except Exception as e:
    st.error(f"❌ src.ml: {e}")

st.divider()
st.write("If everything above is green, the imports are not causing the black screen.")

