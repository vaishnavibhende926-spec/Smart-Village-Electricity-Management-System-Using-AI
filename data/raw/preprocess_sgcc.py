import pandas as pd
import os

# --------------------------------------------------
# 1. File paths
# --------------------------------------------------

input_file = "data/raw/data set.csv/data set.csv"
output_file = "data/processed/sgcc_processed.csv"

print("Loading original SGCC dataset...")

# --------------------------------------------------
# 2. Read original dataset
# --------------------------------------------------

df = pd.read_csv(input_file)

print("Original shape:", df.shape)

# --------------------------------------------------
# 3. Separate consumption and target
# --------------------------------------------------

consumption = df.iloc[:, 1:-1].apply(
    pd.to_numeric,
    errors="coerce"
)

target = pd.to_numeric(
    df.iloc[:, -1],
    errors="coerce"
)

# --------------------------------------------------
# 4. Handle missing consumption values
# --------------------------------------------------

print("Handling missing values...")

row_mean = consumption.mean(axis=1)

consumption = consumption.T.fillna(row_mean).T

# --------------------------------------------------
# 5. Create features
# --------------------------------------------------

processed = pd.DataFrame({
    "mean_consumption": consumption.mean(axis=1),
    "max_consumption": consumption.max(axis=1),
    "min_consumption": consumption.min(axis=1),
    "std_consumption": consumption.std(axis=1),
    "total_consumption": consumption.sum(axis=1),
    "FLAG": target
})

# --------------------------------------------------
# 6. Remove invalid rows
# --------------------------------------------------

processed = processed.dropna()

processed["FLAG"] = processed["FLAG"].astype(int)

# --------------------------------------------------
# 7. Create output directory
# --------------------------------------------------

os.makedirs("data/processed", exist_ok=True)

# --------------------------------------------------
# 8. Save clean CSV
# --------------------------------------------------

processed.to_csv(
    output_file,
    index=False,
    encoding="utf-8",
    sep=","
)

print("\nProcessed shape:", processed.shape)

print("\nColumns:")
print(processed.columns.tolist())

print("\nMissing values:")
print(processed.isnull().sum())

print("\nFLAG distribution:")
print(processed["FLAG"].value_counts())

print("\nSUCCESS!")
print("Clean SGCC dataset saved at:")
print(output_file)