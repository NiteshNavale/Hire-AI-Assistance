#!/bin/bash
echo "Installing dependencies..."
pip install -r requirements.txt
echo "Starting HireAI..."
streamlit run app.py --server.port=8501 --server.address=0.0.0.0
