import joblib
import pandas as pd

# Load trained model
model_path = "models/load_forecasting_model.pkl"

print("Loading load forecasting model...")

model = joblib.load(model_path)

# Example future time
# 15 September 2026, 18:00
new_data = pd.DataFrame({
    "hour": [18],
    "day": [15],
    "month": [9],
    "day_of_week": [1]
})

print("\nInput:")
print(new_data)

# Predict electricity demand
prediction = model.predict(new_data)

print("\n================================")
print("LOAD FORECAST")
print("================================")

print(
    "Predicted Electricity Demand:",
    round(prediction[0], 2)
)

print("\nPrediction completed successfully!")