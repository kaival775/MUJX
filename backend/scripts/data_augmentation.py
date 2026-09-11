import random
import pandas as pd

# Load district master (ALL INDIA)
districts_df = pd.read_csv("india_districts.csv")

# Crop master (40 crops)
crops = {
    "Rice": {"duration": 130, "water": "High"},
    "Wheat": {"duration": 120, "water": "Medium"},
    "Maize": {"duration": 110, "water": "High"},
    "Bajra": {"duration": 85, "water": "Low"},
    "Jowar": {"duration": 100, "water": "Low"},
    "Ragi": {"duration": 105, "water": "Low"},
    "Soybean": {"duration": 90, "water": "Medium"},
    "Groundnut": {"duration": 100, "water": "Medium"},
    "Mustard": {"duration": 95, "water": "Low"},
    "Sunflower": {"duration": 95, "water": "Medium"},
    "Cotton": {"duration": 160, "water": "High"},
    "Sugarcane": {"duration": 300, "water": "Very High"},
    "Potato": {"duration": 90, "water": "Medium"},
    "Onion": {"duration": 120, "water": "Medium"},
    "Tomato": {"duration": 90, "water": "Medium"},
    "Chickpea": {"duration": 100, "water": "Low"},
    "PigeonPea": {"duration": 180, "water": "Low"},
    "Lentil": {"duration": 95, "water": "Low"},
    "GreenGram": {"duration": 70, "water": "Low"},
    "BlackGram": {"duration": 75, "water": "Low"},
    "Peas": {"duration": 90, "water": "Medium"},
    "Barley": {"duration": 110, "water": "Low"},
    "Oats": {"duration": 100, "water": "Medium"},
    "Millet": {"duration": 90, "water": "Low"},
    "Sesame": {"duration": 85, "water": "Low"},
    "Castor": {"duration": 120, "water": "Low"},
    "Linseed": {"duration": 95, "water": "Low"},
    "Jute": {"duration": 140, "water": "High"},
    "Tea": {"duration": 365, "water": "High"},
    "Coffee": {"duration": 365, "water": "Medium"},
    "Banana": {"duration": 300, "water": "High"},
    "Papaya": {"duration": 270, "water": "Medium"},
    "Mango": {"duration": 365, "water": "Medium"},
    "Grapes": {"duration": 180, "water": "Medium"},
    "Apple": {"duration": 365, "water": "Medium"},
    "Orange": {"duration": 365, "water": "Medium"},
    "Chilli": {"duration": 150, "water": "Medium"},
    "Turmeric": {"duration": 240, "water": "Medium"},
    "Ginger": {"duration": 210, "water": "Medium"}
}


seasons = ["Kharif", "Rabi", "Zaid"]

rows = []

for _ in range(1000):  # change to 5000 or 10000 later
    row = districts_df.sample(1).iloc[0]
    crop = random.choice(list(crops.keys()))
    season = random.choice(seasons)

    soil_n = random.randint(20, 65)
    soil_p = random.randint(10, 40)
    soil_k = random.randint(10, 45)
    soil_ph = round(random.uniform(5.5, 7.8), 1)

    soil_moisture = random.randint(15, 45)
    humidity = random.randint(35, 80)

    avg_temp = random.randint(18, 38)
    rainfall = random.randint(300, 1200)

    base_yield = random.uniform(1.5, 5.0)

    climate_factor = 1 if rainfall > 500 else 0.75
    soil_factor = 1 if soil_n > 35 else 0.85

    yield_val = round(base_yield * climate_factor * soil_factor, 2)

    risk = round(
        1 - (yield_val / (base_yield + 0.6)) +
        (0.25 if crops[crop]["water"] in ["High", "Very High"] and rainfall < 500 else 0),
        2
    )

    rows.append([
        row["district"], row["state"], row["latitude"], row["longitude"], row["soil_type"],
        soil_n, soil_p, soil_k, soil_ph,
        soil_moisture, humidity,
        avg_temp, rainfall,
        season,
        random.choice(list(crops.keys())),
        crop,
        crops[crop]["duration"],
        crops[crop]["water"],
        yield_val,
        min(max(risk, 0.05), 0.95)
    ])

df = pd.DataFrame(rows, columns=[
    "district", "state", "latitude", "longitude", "soil_type",
    "soil_n", "soil_p", "soil_k", "soil_ph",
    "soil_moisture", "humidity",
    "avg_temperature", "seasonal_rainfall",
    "climate_season",
    "previous_crop",
    "crop_name", "crop_duration_days", "crop_water_requirement",
    "yield_tonnes_per_hectare", "risk_score"
])

df.to_csv("crop_recommendation_training_data.csv", index=False)
print("Dataset generated successfully")
