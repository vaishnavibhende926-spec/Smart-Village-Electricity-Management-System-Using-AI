import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

import joblib
import os

# --------------------------------------------------
# 1. Load electricity demand dataset
# --------------------------------------------------

file_path = "data/raw/powerdemand_5min_2021_to_2024_with weather.csv"

print("Loading electricity demand dataset...")

df = pd.read_csv(file_path)

print("Dataset shape:", df.shape)
print("\nColumns:")
print(df.columns.tolist())

# --------------------------------------------------
# 2. Convert datetime
# --------------------------------------------------

df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")

df = df.dropna(subset=["datetime"])

# --------------------------------------------------
# 3. Create time features
# --------------------------------------------------

df["hour"] = df["datetime"].dt.hour
df["day"] = df["datetime"].dt.day
df["month"] = df["datetime"].dt.month
df["day_of_week"] = df["datetime"].dt.dayofweek

# --------------------------------------------------
# 4. Remove missing values
# --------------------------------------------------

df = df.dropna()

# --------------------------------------------------
# 5. Select features
# --------------------------------------------------

features = [
    "hour",
    "day",
    "month",
    "day_of_week"
]

target = "Power demand"

X = df[features]
y = df[target]

print("\nFeatures:")
print(features)

print("\nTarget:")
print(target)

# --------------------------------------------------
# 6. Split data
# --------------------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42
)

print("\nTraining samples:", len(X_train))
print("Testing samples:", len(X_test))

# --------------------------------------------------
# 7. Train Random Forest Regressor
# --------------------------------------------------

print("\nTraining load forecasting model...")

model = RandomForestRegressor(
    n_estimators=100,
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)

print("Training completed!")

# --------------------------------------------------
# 8. Prediction
# --------------------------------------------------

y_pred = model.predict(X_test)

# --------------------------------------------------
# 9. Evaluation
# --------------------------------------------------

mae = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r2 = r2_score(y_test, y_pred)

print("\n================================")
print("LOAD FORECASTING RESULTS")
print("================================")

print("MAE :", round(mae, 2))
print("RMSE:", round(rmse, 2))
print("R2 Score:", round(r2, 4))

# --------------------------------------------------
# 10. Save model
# --------------------------------------------------

os.makedirs("models", exist_ok=True)

model_path = "models/load_forecasting_model.pkl"

joblib.dump(model, model_path)

print("\n================================")
print("MODEL SAVED SUCCESSFULLY")
print("================================")

print(model_path)