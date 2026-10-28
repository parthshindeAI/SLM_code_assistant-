#!/usr/bin/env bash
# One-click runner for Linux / macOS / WSL.
# Usage:  ./run.sh
set -e

cd "$(dirname "$0")"

echo "1/3 Creating the virtual environment (only the first time)..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

echo "2/3 Installing the packages..."
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

echo "3/3 Starting the app..."
echo "   -> open http://localhost:8501"
echo "   -> press Ctrl+C to stop"
streamlit run app.py
