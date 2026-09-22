import joblib
import pandas as pd

MODEL_FILE = "models/festival_demand_forecasting_model.pkl"
DATA_FILE = "data/processed/final_forecasting_data.csv"

print("Loading model...")
model = joblib.load(MODEL_FILE)

print("Loading forecasting data...")
df = pd.read_csv(DATA_FILE)

# Same features used during training
features = [
    "hour",
    "day",
    "month",
    "day_of_week",
    "is_weekend",
    "hour_sin",
    "hour_cos",
    "month_sin",
    "month_cos",
    "temp",
    "dwpt",
    "rhum",
    "wdir",
    "wspd",
    "pres",
    "is_festival",
    "is_public_holiday",
    "festival_day",
    "demand_lag_1",
    "demand_lag_48",
    "demand_lag_96",
    "demand_lag_336",
    "rolling_mean_48",
    "rolling_mean_336"
]

# Take one real historical record
sample = df.dropna(subset=features).iloc[-1]

X = pd.DataFrame(
    [[sample[f] for f in features]],
    columns=features
)

prediction = model.predict(X)[0]

actual = sample["Power demand"]

print("\n==============================")
print("FORECAST TEST")
print("==============================")

print("Date/time       :", sample["datetime"])
print("Festival        :", sample["festival"])
print("Actual demand   :", round(actual, 2))
print("Predicted demand:", round(prediction, 2))

error = abs(actual - prediction)

print("Absolute error  :", round(error, 2))

print("\nModel test completed.")