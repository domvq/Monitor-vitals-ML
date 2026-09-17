Streamlit Host: https://monitor-vitals-ml.streamlit.app/


 Computer Vision + OCR + Machine Learning for Vital Sign Monitoring

VitalSight is an **educational computer-vision and machine-learning prototype** that extracts vital-sign data from photographs of patient monitors and presents the results through an interactive Streamlit dashboard.

The project combines **OCR-based text extraction, rule-based parsing, confidence assessment, data visualization, and a prototype ML trend model** to demonstrate how unstructured monitor images can be transformed into structured, reviewable data.

> ⚠️ **Important:** VitalSight is a portfolio/educational prototype. It is **not a medical device, diagnostic tool, or clinically validated system**. Extracted values must be verified against the source monitor and interpreted by qualified professionals using appropriate clinical context and protocols.

---

✨ Features

📷 Monitor Image OCR

Upload a photograph of a patient monitor in:

VitalSight processes the image and attempts to identify visible monitor values using OCR.

### ❤️ Vital Sign Extraction

The application extracts and displays:

| Vital                    | Example       |
| ------------------------ | ------------- |
| Heart Rate (HR)          | `82 bpm`      |
| Oxygen Saturation (SpO₂) | `98%`         |
| Blood Pressure           | `120/80 mmHg` |
| Respiratory Rate (RR)    | `16 /min`     |
| End-tidal CO₂ (EtCO₂)    | `36 mmHg`     |

### 🩸 Blood Pressure Detection

Blood pressure receives a dedicated OCR pass.

The application:

1. Extracts potential BP text.
2. Searches for systolic/diastolic patterns.
3. Validates physiologically reasonable numeric ranges.
4. Selects the highest-confidence valid candidate.
5. Adds the result to the extracted vital-sign data.

### 🎯 OCR Confidence

Vital signs can be displayed with an OCR confidence indicator:

* 🟢 **High** — ≥ 80%
* 🟡 **Medium** — 50–79%
* 🔴 **Low** — < 50%

Confidence is intended to help identify values that should receive additional verification.

### ✏️ Manual Verification

Extracted measurements are not automatically treated as final.

Users can review and modify:

* HR
* SpO₂
* Systolic BP
* Diastolic BP
* RR
* EtCO₂

Verified measurements can then be added to the patient timeline.

### 📈 Patient Timeline

Verified readings are timestamped and stored during the active application session.

The timeline provides a structured view of measurements over time.

### 📊 Trend Visualization

Vital-sign trends are visualized using Plotly.

Currently plotted:

* HR
* SpO₂
* RR
* EtCO₂

### 🤖 ML Trend Estimate

After at least three verified readings, VitalSight can run a prototype ML model that estimates the direction of the recorded trajectory:

* Improving
* Stable
* Worsening

The application also displays model probabilities.

> These probabilities represent outputs from the prototype model and **should not be interpreted as clinical risk probabilities or a validated deterioration score**.

### 🩺 Clinical Reference

VitalSight includes a rule-based reference section that identifies certain observed patterns, including:

* Tachycardia
* Bradycardia
* Low SpO₂
* Low systolic blood pressure
* Tachypnea
* Low EtCO₂

For each detected pattern, the application presents possible clinical considerations.

These are **reference considerations, not diagnoses**.



 🧠 System Workflow

                  ┌─────────────────┐
                  │ Monitor Image   │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │      OCR        │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Vital Parsing   │
                  └────────┬────────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
       ┌──────────────┐         ┌──────────────┐
       │ BP Detection │         │ OCR Confidence│
       └──────┬───────┘         └──────┬───────┘
              │                         │
              └────────────┬────────────┘
                           ▼
                  ┌─────────────────┐
                  │ Manual Verify   │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Patient Timeline│
                  └────────┬────────┘
                           │
                ┌──────────┴──────────┐
                ▼                     ▼
       ┌────────────────┐    ┌─────────────────┐
       │ Trend Graph    │    │ ML Trend Model  │
       └────────────────┘    └─────────────────┘


## 🛠️ Technology Stack

### Core

* **Python**
* **Streamlit**
* **Pandas**
* **Plotly**
* **Pillow (PIL)**

### Computer Vision / Data Processing

* OCR
* Regular expressions
* Structured value parsing
* Confidence scoring

### Machine Learning

The project includes a prototype trend-classification pipeline through:

```python
from src.ml import train_trend_model, predict_trend
```

The ML component is designed for experimentation and demonstration rather than clinical prediction.

---

## 📁 Project Structure

A typical project structure is:

```text
VitalSight/
│
├── app.py
│
├── src/
│   ├── __init__.py
│   ├── ocr.py
│   ├── parser.py
│   └── ml.py
│
├── requirements.txt
│
├── README.md
│
└── .gitignore

### `app.py`

Main Streamlit application containing:

* UI
* image upload
* OCR pipeline
* vital-sign dashboard
* verification interface
* timeline
* Plotly visualization
* ML trend interface
* clinical reference logic

### `src/ocr.py`

Handles monitor-image OCR and BP candidate extraction.

### `src/parser.py`

Converts OCR output into structured vital-sign values.

### `src/ml.py`

Contains the prototype trend-model training and prediction functions.

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/VitalSight.git
cd VitalSight
```

### 2. Create a virtual environment

#### macOS / Linux

```bash
python -m venv .venv
source .venv/bin/activate
```

#### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
streamlit run app.py
```

The Streamlit application should open in your browser.

---

## 📸 Using VitalSight

1. Launch the application.
2. Enter optional patient context such as age and chief complaint.
3. Upload a photograph of a patient monitor.
4. Select **Read Monitor**.
5. Review the extracted vital signs.
6. Check OCR confidence values.
7. Manually verify the measurements against the source monitor.
8. Select **Add Verified Reading**.
9. Repeat the process to build a timeline.
10. After three or more readings, review the prototype trend estimate.

---

## 🔬 Example Workflow

Given a monitor image containing:

```text
HR       102
SpO₂      94
BP       118/72
RR        24
EtCO₂     32
```

VitalSight attempts to convert the image into structured data:

```python
{
    "hr": 102,
    "spo2": 94,
    "bp_sys": 118,
    "bp_dia": 72,
    "rr": 24,
    "etco2": 32
}
```

After manual verification, the reading can be stored in the timeline and compared with subsequent measurements.

---

## 🧪 Prototype Limitations

VitalSight is intentionally designed as a prototype and has several limitations.

### OCR Limitations

OCR performance can be affected by:

* Image quality
* Glare
* Reflections
* Monitor angle
* Font differences
* Low contrast
* Cropping
* Motion blur
* Overlapping monitor elements

An OCR confidence score does not guarantee that a value is correct.

### Parsing Limitations

The parser uses pattern matching and validation rules. It may fail when monitor layouts or displayed formats differ from expected patterns.

### ML Limitations

The trend model is a prototype and depends on its training data and implementation.

It has **not been clinically validated** and should not be interpreted as:

* A diagnosis
* A deterioration score
* A clinical risk score
* A treatment recommendation
* A prediction of patient outcome

### Session Storage

The current application stores timeline readings in Streamlit session state. Data is therefore intended for demonstration rather than production-grade patient record management.

---

## 🔐 Privacy & Security

Do not upload real patient images or personally identifiable health information to an unvalidated development environment.

For experimentation, use:

* Synthetic monitor images
* Publicly available de-identified data
* Artificial test cases

A production implementation would require appropriate security, privacy, access-control, auditing, data-retention, and regulatory considerations.

---

## 🗺️ Future Improvements

Potential future development includes:

* [ ] Improved monitor-region detection
* [ ] Automatic image cropping and perspective correction
* [ ] More robust OCR preprocessing
* [ ] Support for additional monitor layouts
* [ ] Improved vital-sign parsing
* [ ] Automated artifact detection
* [ ] Persistent database-backed patient timelines
* [ ] Authentication and access control
* [ ] Unit and integration testing
* [ ] Model evaluation metrics
* [ ] Larger and better-curated training datasets
* [ ] Model explainability
* [ ] Exportable reports
* [ ] Improved visualization
* [ ] Deployment pipeline
* [ ] Comprehensive clinical validation before any real-world clinical use


## 🎯 Project Goals

VitalSight was created to explore the intersection of:

**Computer Vision + OCR + Machine Learning + Healthcare Data Visualization**

The primary goal is to demonstrate an end-to-end pipeline that takes an image containing unstructured information and turns it into structured data that can be reviewed, visualized, and analyzed.



## ⚠️ Disclaimer

**VitalSight is an educational and portfolio project.**

It is not a medical device and has not been clinically validated. The application may produce incorrect or incomplete measurements.

All extracted values should be independently verified against the original monitor and considered alongside appropriate patient assessment, clinical information, medical direction, and applicable protocols.

**Do not use VitalSight as a substitute for professional medical judgment or clinical care.**


## ⭐ Acknowledgments

This project uses open-source Python libraries and frameworks including Streamlit, Pandas, Plotly, and Pillow.

If you find the project useful or interesting, consider giving the repository a ⭐.
