@echo off
REM Start FastAPI server for local development
REM Try to activate the `ocrenv` virtual environment if it exists, then start uvicorn
if exist "%~dp0ocrenv\Scripts\activate.bat" (
	call "%~dp0ocrenv\Scripts\activate.bat"
) else (
	echo Warning: virtual environment 'ocrenv' not found in project root; continuing without activation
)

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
