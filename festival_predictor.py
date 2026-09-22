import joblib
import pandas as pd
import numpy as np

MODEL_FILE = "models/festival_demand_forecasting_model.pkl"
DATA_FILE = "data/processed/final_forecasting_data.csv"

model = joblib.load(MODEL_FILE)
df = pd.read_csv(DATA_FILE)

# ---------------------------------
# USER INPUT
# ---------------------------------

location = input("Location: ")
festival = input("Festival: ")

people = int(input("Normal number of people: "))
extra_people = int(input("Extra visitors: "))

temperature = float(input("Temperature (°C): "))

fan = int(input("Number of fans: "))
ac = int(input("Number of ACs: "))
tv = int(input("Number of TVs: "))
fridge = int(input("Number of refrigerators: "))
pump = int(input("Number of water pumps: "))
geyser = int(input("Number of geysers: "))
lights = int(input("Number of lights: "))

usage_hours = float(
    input("Average appliance usage hours: ")
)

# ---------------------------------
# BASELINE
# ---------------------------------

latest = df.dropna().iloc[-1]

hour = 19
day = 15
month = 9
day_of_week = 5

# ---------------------------------
# TIME FEATURES
# ---------------------------------

hour_sin = np.sin(2 * np.pi * hour / 24)
hour_cos = np.cos(2 * np.pi * hour / 24)

month_sin = np.sin(2 * np.pi * month / 12)
month_cos = np.cos(2 * np.pi * month / 12)

is_weekend = int(day_of_week >= 5)

# ---------------------------------
# FESTIVAL FEATURES
# ---------------------------------

is_festival = 1
is_public_holiday = 1
festival_day = 1

# ---------------------------------
# HISTORICAL DEMAND FEATURES
# ---------------------------------

demand_lag_1 = latest["demand_lag_1"]
demand_lag_48 = latest["demand_lag_48"]
demand_lag_96 = latest["demand_lag_96"]
demand_lag_336 = latest["demand_lag_336"]

rolling_mean_48 = latest["rolling_mean_48"]
rolling_mean_336 = latest["rolling_mean_336"]

# ---------------------------------
# WEATHER
# ---------------------------------

dwpt = latest["dwpt"]
rhum = latest["rhum"]
wdir = latest["wdir"]
wspd = latest["wspd"]
pres = latest["pres"]

# ---------------------------------
# MODEL INPUT
# ---------------------------------

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

input_data = pd.DataFrame([[
    hour,
    day,
    month,
    day_of_week,
    is_weekend,
    hour_sin,
    hour_cos,
    month_sin,
    month_cos,
    temperature,
    dwpt,
    rhum,
    wdir,
    wspd,
    pres,
    is_festival,
    is_public_holiday,
    festival_day,
    demand_lag_1,
    demand_lag_48,
    demand_lag_96,
    demand_lag_336,
    rolling_mean_48,
    rolling_mean_336
]], columns=features)

# ---------------------------------
# AI PREDICTION
# ---------------------------------

base_prediction = model.predict(input_data)[0]

# ---------------------------------
# SCENARIO ADJUSTMENT
# ---------------------------------
# This is a scenario estimate, NOT
# learned migration data.

total_people = people + extra_people

people_factor = 1 + (extra_people / max(people, 1)) * 0.10

appliance_count = (
    fan +
    ac +
    tv +
    fridge +
    pump +
    geyser +
    lights
)

appliance_factor = 1 + (
    appliance_count * usage_hours * 0.005
)

final_prediction = (
    base_prediction *
    people_factor *
    appliance_factor
)

# ---------------------------------
# OUTPUT
# ---------------------------------

print("\n====================================")
print(" SMART VILLAGE ELECTRICITY FORECAST")
print("====================================")

print("Location:", location)
print("Festival:", festival)

print("\nPeople:")
print("Normal:", people)
print("Extra visitors:", extra_people)
print("Total:", total_people)

print("\nAI baseline demand:",
      round(base_prediction, 2))

print("Scenario demand:",
      round(final_prediction, 2))

print("\nAdditional scenario demand:",
      round(final_prediction - base_prediction, 2))

print("\nNote:")
print("Extra people and appliance values are")
print("scenario inputs, not historical migration data.")

print("\nForecast completed.")