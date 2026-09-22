import pandas as pd
import numpy as np
import os
import joblib

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# ==========================================
# FILE PATHS
# ==========================================

INPUT_FILE = "data/processed/final_forecasting_data.csv"
MODEL_FILE = "models/festival_demand_forecasting_model.pkl"


# ==========================================
# LOAD DATA
# ==========================================

print("Loading forecasting dataset...")

df = pd.read_csv(INPUT_FILE)

df["datetime"] = pd.to_datetime(
    df["datetime"],
    errors="coerce"
)

df = df.sort_values("datetime").reset_index(drop=True)


# ==========================================
# FEATURES
# ==========================================

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


target = "Power demand"


# ==========================================
# KEEP REQUIRED COLUMNS
# ==========================================

df = df.dropna(
    subset=features + [target]
).copy()


X = df[features]
y = df[target]


# ==========================================
# CHRONOLOGICAL SPLIT
# ==========================================

split_index = int(len(df) * 0.80)

X_train = X.iloc[:split_index]
X_test = X.iloc[split_index:]

y_train = y.iloc[:split_index]
y_test = y.iloc[split_index:]

print("\nTraining rows:", len(X_train))
print("Testing rows:", len(X_test))

print(
    "\nTraining period:",
    df["datetime"].iloc[0],
    "to",
    df["datetime"].iloc[split_index - 1]
)

print(
    "Testing period:",
    df["datetime"].iloc[split_index],
    "to",
    df["datetime"].iloc[-1]
)


# ==========================================
# TRAIN MODEL
# ==========================================

print("\nTraining Random Forest...")

model = RandomForestRegressor(
    n_estimators=200,
    max_depth=20,
    random_state=42,
    n_jobs=-1
)

model.fit(
    X_train,
    y_train
)


# ==========================================
# PREDICTION
# ==========================================

print("Generating predictions...")

predictions = model.predict(X_test)


# ==========================================
# EVALUATION
# ==========================================

mae = mean_absolute_error(
    y_test,
    predictions
)

rmse = np.sqrt(
    mean_squared_error(
        y_test,
        predictions
    )
)

r2 = r2_score(
    y_test,
    predictions
)


print("\n================================")
print("MODEL PERFORMANCE")
print("================================")

print(f"MAE  : {mae:.2f}")
print(f"RMSE : {rmse:.2f}")
print(f"R²   : {r2:.4f}")


# ==========================================
# FEATURE IMPORTANCE
# ==========================================

importance = pd.DataFrame({
    "feature": features,
    "importance": model.feature_importances_
})

importance = importance.sort_values(
    "importance",
    ascending=False
)

print("\nTop important features:")

print(
    importance.head(15).to_string(
        index=False
    )
)


# ==========================================
# SAVE MODEL
# ==========================================

os.makedirs(
    "models",
    exist_ok=True
)

joblib.dump(
    model,
    MODEL_FILE
)

print("\nModel saved successfully:")
print(MODEL_FILE)