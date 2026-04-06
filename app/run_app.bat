@echo off
if exist "D:\DSAI\ESG\env\Scripts\activate.bat" (
    call "D:\DSAI\ESG\env\Scripts\activate.bat"
) else (
    echo Error: Environment not found at D:\DSAI\ESG\env
    pause
    exit /b
)
cd /d "%~dp0"
streamlit run app.py
pause
