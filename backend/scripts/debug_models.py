
import os
import pickle
import sys

# Add backend to path to allow imports if needed, though we are checking raw pickle load
sys.path.append(os.getcwd())

model_dir = r"c:\Users\kavya\Desktop\codes\Let_Go_3.0\backend\feature4_drl\crop_recommendation_models"

print("Checking environment...")
try:
    import pandas
    print("pandas: OK")
except ImportError as e:
    print(f"pandas: MISSING ({e})")

try:
    import numpy
    print("numpy: OK")
except ImportError as e:
    print(f"numpy: MISSING ({e})")

try:
    import sklearn
    print("sklearn: OK")
except ImportError as e:
    print(f"sklearn: MISSING ({e})")

try:
    import xgboost
    print("xgboost: OK")
except ImportError as e:
    print(f"xgboost: MISSING ({e})")

print("\nAttempting to load models...")
try:
    with open(os.path.join(model_dir, "yield_model.pkl"), "rb") as f:
        pickle.load(f)
    print("yield_model.pkl: LOADED")
except Exception as e:
    print(f"yield_model.pkl: FAILED - {e}")

try:
    with open(os.path.join(model_dir, "risk_model.pkl"), "rb") as f:
        pickle.load(f)
    print("risk_model.pkl: LOADED")
except Exception as e:
    print(f"risk_model.pkl: FAILED - {e}")
