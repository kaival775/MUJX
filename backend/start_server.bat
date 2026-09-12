@echo off
set PYTHONIOENCODING=utf-8
echo Starting FastAPI Server...
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000