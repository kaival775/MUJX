import sys
import traceback

modules = [
    "fastapi",
    "uvicorn",
    "dotenv",
    "google.generativeai",
    "google.genai",
    "langchain_google_genai",
    "langgraph",
    "supabase",
    "twilio",
    "tensorflow",
    "cv2",
    "web3",
    "shapely",
    "geopy",
    "requests",
    "PIL",
    "reportlab",
    "sklearn",
    "xgboost",
]

print("=" * 50)
print("BACKEND IMPORT CHECK")
print("=" * 50)

failed = []
for mod in modules:
    try:
        __import__(mod)
        print(f"[OK]  {mod}")
    except ImportError as e:
        print(f"[ERR] {mod} => {e}")
        failed.append((mod, str(e)))
    except Exception as e:
        print(f"[WARN] {mod} => {e}")

print("\n" + "=" * 50)
if failed:
    print(f"FAILED IMPORTS ({len(failed)}):")
    for m, e in failed:
        print(f"  - {m}: {e}")
else:
    print("ALL IMPORTS OK!")
print("=" * 50)
