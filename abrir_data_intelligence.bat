@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m streamlit run "app\streamlit_app.py"
) else (
    python -m streamlit run "app\streamlit_app.py"
)

if errorlevel 1 (
    echo.
    echo Nao foi possivel abrir o aplicativo.
    echo Instale as dependencias com: python -m pip install -e ".[excel,app]"
    pause
)

endlocal
