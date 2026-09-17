
import numpy as np
import streamlit as st

from sklearn.ensemble import RandomForestClassifier


VITALS = [
    "HR",
    "SPO2",
    "BP_SYS",
    "BP_DIA",
    "RR",
    "ETCO2",
]


def calculate_features(readings):
    """
    Convert a patient timeline into ML features.

    Features include:
    - current value
    - total change
    - average change
    - volatility
    """

    features = []

    for vital in VITALS:

        values = np.array(
            [r[vital] for r in readings],
            dtype=float
        )

        if len(values) == 0:
            features.extend([0, 0, 0, 0])
            continue

        current = values[-1]

        total_change = (
            values[-1] - values[0]
        )

        if len(values) > 1:

            mean_change = np.mean(
                np.diff(values)
            )

        else:

            mean_change = 0

        volatility = np.std(values)

        features.extend([
            current,
            total_change,
            mean_change,
            volatility
        ])

    # --------------------------------------------------------
    # Derived features
    # --------------------------------------------------------

    latest = readings[-1]

    hr = latest["hr"]
    spo2 = latest["spo2"]
    sbp = latest["bp_sys"]
    dbp = latest["bp_dia"]
    rr = latest["rr"]
    etco2 = latest["etco2"]

    # Pulse pressure
    pulse_pressure = sbp - dbp

    # MAP approximation
    map_value = (
        dbp + (pulse_pressure / 3)
    )

    # Number of concerning directional changes
    concerning_changes = 0

    if len(readings) >= 2:

        first = readings[0]
        last = readings[-1]

        if last["hr"] > first["hr"]:
            concerning_changes += 1

        if last["spo2"] < first["spo2"]:
            concerning_changes += 1

        if last["bp_sys"] < first["bp_sys"]:
            concerning_changes += 1

        if last["rr"] > first["rr"]:
            concerning_changes += 1

        if last["etco2"] < first["etco2"]:
            concerning_changes += 1

    features.extend([
        pulse_pressure,
        map_value,
        concerning_changes
    ])

    return np.array(features, dtype=float)


@st.cache_resource
def train_trend_model():

    X = []
    y = []

    rng = np.random.default_rng(42)

    for _ in range(5000):

        readings = []

        baseline = np.array([
            rng.normal(90, 15),
            rng.normal(97, 2),
            rng.normal(120, 15),
            rng.normal(75, 10),
            rng.normal(18, 4),
            rng.normal(35, 5),
        ])

        trend = rng.choice(
            [
                "improving",
                "stable",
                "worsening"
            ]
        )

        for i in range(5):

            if trend == "improving":

                direction = np.array([
                    -1.0,
                    0.5,
                    1.0,
                    0.5,
                    -0.8,
                    0.2
                ])

            elif trend == "worsening":

                direction = np.array([
                    1.0,
                    -0.5,
                    -1.0,
                    -0.5,
                    0.8,
                    -0.2
                ])

            else:

                direction = np.zeros(6)

            noise = rng.normal(
                0,
                [2, 0.5, 2, 1, 1, 0.5],
                6
            )

            values = (
                baseline
                + direction * i * 2
                + noise
            )

            readings.append({
                "hr": values[0],
                "spo2": values[1],
                "bp_sys": values[2],
                "bp_dia": values[3],
                "rr": values[4],
                "etco2": values[5],
            })

        X.append(
            calculate_features(readings)
        )

        y.append(trend)

    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=12,
        random_state=42,
        class_weight="balanced"
    )

    model.fit(X, y)

    return model


def predict_trend(model, readings):

    features = calculate_features(
        readings
    )

    features = features.reshape(
        1, -1
    )

    prediction = model.predict(
        features
    )[0]

    probabilities = model.predict_proba(
        features
    )[0]

    confidence = float(
        max(probabilities)
    )

    probability_dict = {
        label: float(probability)
        for label, probability in zip(
            model.classes_,
            probabilities
        )
    }

    return (
        prediction,
        confidence,
        probability_dict
    )
