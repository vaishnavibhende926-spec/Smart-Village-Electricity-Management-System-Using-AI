import pandas as pd

file_path = "data/raw/powerdemand_5min_2021_to_2024_with weather.csv"

print("Reading electricity demand dataset...")

df = pd.read_csv(file_path)

print("\nFirst 5 rows:")
print(df.head())

print("\nColumn names:")
print(df.columns.tolist())

print("\nDataset size:")
print(df.shape)

print("\nMissing values:")
print(df.isnull().sum())

print("\nData types:")
print(df.dtypes)