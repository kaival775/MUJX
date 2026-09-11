import sys
print(f"Python executable: {sys.executable}")
print(f"Path: {sys.path}")
try:
    import fastapi
    print("FastAPI imported.")
    import pydantic
    print("Pydantic imported.")
    from auth import router
    print("Auth Router imported.")
    from auth.email_service import email_auth_service
    print("Email Service imported.")
    import main
    print("Main imported.")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
