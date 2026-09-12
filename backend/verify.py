import traceback
try:
    from main import app
    print('Loaded successfully without exceptions.')
except Exception as e:
    traceback.print_exc()
