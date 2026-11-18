@echo off
cd /d "%~dp0"
"C:\Users\Admin\AppData\Local\Programs\Python\Python314\python.exe" -m streamlit run "%~dp0stress_app.py"
if errorlevel 1 pause
