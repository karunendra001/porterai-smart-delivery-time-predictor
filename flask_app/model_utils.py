import os
import joblib
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARTIFACTS_DIR = os.path.join(BASE_DIR, "artifacts")
MODELS_DIR = os.path.join(os.path.dirname(BASE_DIR), "models")

MODEL_PATH = os.path.join(MODELS_DIR, "best_model.pkl")
SCALER_PATH = os.path.join(ARTIFACTS_DIR, "scaler.pkl")

def load_artifacts():
    model = joblib.load(MODEL_PATH) if os.path.exists(MODEL_PATH) else None
    scaler = joblib.load(SCALER_PATH) if os.path.exists(SCALER_PATH) else None
    return model, scaler

try:
    model, scaler = load_artifacts()
except Exception:
    model, scaler = None, None

def preprocess_input(input_data: dict) -> pd.DataFrame:
    df = pd.DataFrame([input_data])
    if scaler is not None:
        try:
            return scaler.transform(df)
        except Exception:
            return df
    return df

def predict_delivery_time(input_data: dict) -> float:
    if model is None:
        dist = float(input_data.get('distance', 0))
        partners = int(input_data.get('total_onshift_partners', 1))
        estimated_time = 15.0 + (dist * 4.5) - (partners * 0.3)
        return float(np.round(max(5.0, estimated_time), 2))
    
    try:
        processed_features = preprocess_input(input_data)
        prediction = model.predict(processed_features)
        predicted_time = float(np.round(prediction[0], 2))
        return max(0.0, predicted_time)
    except Exception as e:
        print(f"Prediction error: {e}")
        return 25.0