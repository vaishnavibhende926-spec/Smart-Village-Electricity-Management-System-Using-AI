import joblib
import pandas as pd

# Load trained model
model_path = "models/sgcc_random_forest.pkl"

print("Loading trained model...")
model = joblib.load(model_path)

# Example electricity consumption features
# These values are only for testing the model
new_data = pd.DataFrame({
    "mean_consumption": [1.5],
    "max_consumption": [4.2],
    "min_consumption": [0.1],
    "std_consumption": [0.8],
    "total_consumption": [1500]
})

print("\nInput electricity data:")
print(new_data)

# Prediction
prediction = model.predict(new_data)

print("\n================================")
print("AI PREDICTION")
print("================================")

if prediction[0] == 1:
    print("⚠️ Abnormal consumption detected")
    print("Risk: Possible electricity theft / abnormal usage")
else:
    print("✅ Normal consumption")
    print("Risk: Low")