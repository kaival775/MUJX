"""
Script to create default users for ANNADATA SAATHI
Run this script once to create admin, farmer, and user accounts.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import bcrypt
from datetime import datetime
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_password.decode('utf-8')

def create_user(supabase, full_name, email, password, role):
    """Create a user if they don't exist"""
    try:
        # Check if user exists
        existing = supabase.table("users").select("id").eq("email", email).execute()
        if existing.data:
            print(f"[WARN] User {email} already exists. Skipping...")
            return existing.data[0]
        
        # Create new user
        hashed_pw = get_password_hash(password)
        new_user = {
            "full_name": full_name,
            "email": email,
            "password_hash": hashed_pw,
            "role": role,
            "created_at": datetime.now().isoformat(),
            "is_active": True
        }
        
        response = supabase.table("users").insert(new_user).execute()
        if response.data:
            print(f"[OK] Created {role}: {email}")
            return response.data[0]
        else:
            print(f"[ERROR] Failed to create {email}")
            return None
    except Exception as e:
        print(f"[ERROR] Error creating {email}: {e}")
        return None

def main():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("[ERROR] Missing SUPABASE_URL or SUPABASE_KEY in .env")
        return
    
    print(">>> ANNADATA SAATHI - Creating Default Users")
    print("=" * 50)
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Define default users
    users = [
        {
            "full_name": "Admin User",
            "email": "admin@annadatasaathi.in",
            "password": "Admin@123",
            "role": "admin"
        },
        {
            "full_name": "Ramesh Patil",
            "email": "farmer@annadatasaathi.in",
            "password": "Farmer@123",
            "role": "farmer"
        },
        {
            "full_name": "Priya Sharma",
            "email": "user@annadatasaathi.in",
            "password": "User@123",
            "role": "user"
        }
    ]
    
    for user in users:
        # Try to create user
        result = create_user(supabase, user["full_name"], user["email"], user["password"], user["role"])
        
        # Fallback for 'user' role if DB constraint fails
        if not result and user["role"] == 'user':
            print(f"[WARN] Database might not support 'user' role. Falling back to 'farmer' role for {user['email']}...")
            create_user(supabase, user["full_name"], user["email"], user["password"], "farmer")
    
    print("\n" + "=" * 50)
    print(">>> Default users setup complete!")
    print("\n[LOGIN CREDENTIALS]")
    print("-" * 50)
    print("| Role    | Email                      | Password    |")
    print("-" * 50)
    print("| ADMIN   | admin@annadatasaathi.in    | Admin@123   |")
    print("| FARMER  | farmer@annadatasaathi.in   | Farmer@123  |")
    print("| USER    | user@annadatasaathi.in     | User@123    |")
    print("-" * 50)

if __name__ == "__main__":
    main()
