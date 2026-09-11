
import pandas as pd
import os

# Source and Destination
source_path = "crop_recommendation_training_data.csv"
dest_dir = "backend/feature4_drl"
dest_path = os.path.join(dest_dir, "Crop_recommendation.csv")

# Load generated data
if not os.path.exists(source_path):
    print(f"Source file {source_path} not found.")
    exit(1)

df = pd.read_csv(source_path)

# Rename columns to match Kaggle format
# Kaggle: N,P,K,temperature,humidity,ph,rainfall,label
# Generated: soil_n, soil_p, soil_k, avg_temperature, humidity, soil_ph, seasonal_rainfall, crop_name

rename_map = {
    "soil_n": "N",
    "soil_p": "P",
    "soil_k": "K",
    "avg_temperature": "temperature",
    "humidity": "humidity",
    "soil_ph": "ph",
    "seasonal_rainfall": "rainfall",
    "crop_name": "label"
}

# Check if columns exist before renaming
missing_cols = [col for col in rename_map.keys() if col not in df.columns]
if missing_cols:
    print(f"Missing columns in source: {missing_cols}")
    # Just generic fallback or exit
    exit(1)

df_renamed = df.rename(columns=rename_map)

# Keep only necessary columns
final_cols = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall", "label"]
df_final = df_renamed[final_cols]

# Ensure destination directory exists
os.makedirs(dest_dir, exist_ok=True)

# Save
df_final.to_csv(dest_path, index=False)
print(f"Converted and saved dataset to {dest_path}")
print(f"Saved {len(df_final)} rows.")
