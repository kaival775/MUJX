import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

print(f"URL: {url}")
print(f"KEY: {key[:10]}..." if key else "KEY: None")

if not url or not key:
    print("Error: SUPABASE_URL or SUPABASE_KEY not found in .env")
    exit(1)

try:
    supabase = create_client(url, key)
    print("Client created successfully.")

    # Test User Upsert
    user_id = "123e4567-e89b-12d3-a456-426614174000"
    print(f"Attempting to upsert user {user_id}...")
    user_data = {"id": user_id, "phone_number": f"debug-{user_id}"}
    user_res = supabase.table("users").upsert(user_data).execute()
    print("User upsert successful!", user_res.data)

    # Test Land Insert
    print("Attempting to insert land record...")
    land_data = {
        "user_id": user_id,
        "polygon_coordinates": [{"lat": 20.0, "lng": 78.0}, {"lat": 21.0, "lng": 79.0}, {"lat": 20.0, "lng": 79.0}],
        "area_sqm": 1234.56,
        "status": "PENDING"
    }
    land_res = supabase.table("lands").insert(land_data).execute()
    print("Land insert successful!", land_res.data)

except Exception as e:
    print("-" * 30)
    print("CRITICAL ERROR DURING DB OPERATION:")
    print(e)
    print("-" * 30)
