import pandas as pd
import os

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib

# --------------------------------------------------
# 1. Load processed dataset
# --------------------------------------------------

file_path = "data/processed/sgcc_processed.csv"

print("Loading processed SGCC dataset...")

df = pd.read_csv(file_path)

print("Dataset shape:", df.shape)
print("\nColumns:")
print(df.columns.tolist())

# --------------------------------------------------
# 2. Select features
# --------------------------------------------------

features = [
    "mean_consumption",
    "max_consumption",
    "min_consumption",
    "std_consumption",
    "total_consumption"
]

X = df[features]
y = df["FLAG"]

print("\nFeatures selected:")
print(features)

print("\nTarget:")
print("FLAG")

# --------------------------------------------------
# 3. Split dataset
# --------------------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("\nTraining samples:", len(X_train))
print("Testing samples:", len(X_test))

# --------------------------------------------------
# 4. Create Random Forest model
# --------------------------------------------------

model = RandomForestClassifier(
    n_estimators=100,
    random_state=42,
    class_weight="balanced"
)

# --------------------------------------------------
# 5. Train model
# --------------------------------------------------

print("\nTraining Random Forest model...")

model.fit(X_train, y_train)

print("Model training completed!")

# --------------------------------------------------
# 6. Prediction
# --------------------------------------------------

y_pred = model.predict(X_test)

# --------------------------------------------------
# 7. Accuracy
# --------------------------------------------------

accuracy = accuracy_score(y_test, y_pred)

print("\n================================")
print("MODEL RESULTS")
print("================================")

print("Accuracy:", round(accuracy * 100, 2), "%")

# --------------------------------------------------
# 8. Classification report
# --------------------------------------------------

print("\nClassification Report:")
print(classification_report(y_test, y_pred))

# --------------------------------------------------
# 9. Confusion matrix
# --------------------------------------------------

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))

# --------------------------------------------------
# 10. Save model
# --------------------------------------------------

os.makedirs("models", exist_ok=True)

model_path = "models/sgcc_random_forest.pkl"

joblib.dump(model, model_path)

print("\n================================")
print("MODEL SAVED SUCCESSFULLY")
print("================================")
print(model_path)