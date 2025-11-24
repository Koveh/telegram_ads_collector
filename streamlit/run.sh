#!/bin/bash
# Script to run Streamlit dashboard with virtual environment

cd "$(dirname "$0")/.."
source venv/bin/activate
streamlit run streamlit/app.py

