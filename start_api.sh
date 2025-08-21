#!/bin/bash

echo "Starting ID Card OCR API..."
echo "Installing dependencies..."
pip install -r requirements.txt

echo "Starting FastAPI server..."
echo "API will be available at: http://localhost:8000"
echo "API documentation at: http://localhost:8000/docs"
echo "Press Ctrl+C to stop the server"

python -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload