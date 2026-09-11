import os
import sys
import random
from datetime import datetime, timedelta

# Add backend directory to sys.path to import core modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.supabase_client import supabase

def seed_data():
    print("Seeding Inspection Data...")
    
    districts = ["Nashik", "Pune", "Aurangabad", "Nagpur", "Satara"]
    crops = ["Cotton", "Soybean", "Maize", "Wheat", "Sugarcane"]
    farmers = [
        {"name": "Rajesh Kumar", "phone": "9876543210"},
        {"name": "Suresh Patil", "phone": "9876543211"},
        {"name": "Vikas Deshemukh", "phone": "9876543212"},
        {"name": "Anita Shinde", "phone": "9876543213"},
        {"name": "Mohan Lal", "phone": "9876543214"}
    ]

    claims = []
    
    for i, farmer in enumerate(farmers):
        district = random.choice(districts)
        crop = random.choice(crops)
        
        # Determine status
        # 1. New Request
        # 2. Assigned
        # 3. Visited
        
        status_case = i % 3
        
        # Base Application
        claim = {
             "reference_no": f"CLM-2026-{random.randint(1000, 9999)}",
             "user_id": f"user_{random.randint(100,999)}", # Mock User ID
             "farmer_name": farmer['name'],
             "farmer_phone": farmer['phone'],
             "aadhaar_number": f"XXXXXXXX{random.randint(1000,9999)}",
             "scheme_name": "PM Fasal Bima Yojana",
             "claim_type": "crop_loss",
             "land_size": random.uniform(2.0, 10.0),
             "land_unit": "Acres",
             "crop_name": crop,
             "ndvi_value": random.uniform(0.3, 0.6),
             "crop_loss_percentage": random.uniform(20, 80) if status_case > 0 else None,
             "application_details": {
                 "district": district,
                 "village": "Rampur"
             },
             # Status Mapping
             "status": "under_review" if status_case > 0 else "submitted",
             
             # The new fields (We add them, if DB rejects, we know migration is needed)
             "assigned_inspector_id": f"officer-00{random.randint(1,3)}" if status_case >= 1 else None,
             "inspection_status": "pending" if status_case == 0 else ("scheduled" if status_case == 1 else "report_submitted"),
             "inspection_deadline": (datetime.now() + timedelta(days=3)).isoformat() if status_case >= 1 else None,
             "created_at": (datetime.now() - timedelta(days=random.randint(1, 10))).isoformat()
        }
        
        if status_case == 2:
             claim["inspection_report"] = {
                 "visited_at": datetime.now().isoformat(),
                 "loss_estimate": random.randint(40, 90),
                 "remarks": "Heavy rainfall damage observed directly on crop.",
                 "geo_photos": ["https://placehold.co/600x400?text=Field+Visit"]
             }

        claims.append(claim)

    # Insert
    for c in claims:
        try:
            # First try inserting with new columns
            res = supabase.table("claim_applications").insert(c).execute()
            print(f"Inserted claim {c['reference_no']}")
        except Exception as e:
            print(f"Error inserting {c['reference_no']}: {e}")
            print("Trying fallback insert (schema might not be updated)...")
            try:
                # Remove new columns and insert
                legacy_c = {k:v for k,v in c.items() if k not in ['assigned_inspector_id', 'inspection_status', 'inspection_deadline', 'inspection_report', 'official_pdf_url']}
                # We store the extra data in 'application_details' as backup
                legacy_c['application_details'].update({
                    'assigned_inspector_id': c.get('assigned_inspector_id'),
                    'inspection_status': c.get('inspection_status'),
                    'inspection_deadline': c.get('inspection_deadline')
                })
                supabase.table("claim_applications").insert(legacy_c).execute()
                print(f"Inserted legacy claim {c['reference_no']}")
            except Exception as e2:
                print(f"Legacy insert also failed: {e2}")

if __name__ == "__main__":
    seed_data()
