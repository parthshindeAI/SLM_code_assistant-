@echo off
REM One-click runner for Windows (VS Code terminal, PowerShell or CMD).
REM Usage:  run.bat

cd /d "%~dp0"

echo 1/3 Creating the virtual environment (only the first time)...
if not exist ".venv" (
    python -m venv .venv
)

echo 2/3 Installing the packages...
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt

echo 3/3 Starting the app...
echo    -^> open http://localhost:8501
echo    -^> press Ctrl+C to stop
streamlit run app.py
