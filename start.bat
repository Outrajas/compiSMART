@echo off
echo Starting CompiSMART services...

:: Check if Docker is running (simple check)
docker ps >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not running. Please start Docker Desktop first.
    pause
    exit /b 1
)

:: Start Qdrant in a new window
start "Qdrant" cmd /c "docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant"
echo Qdrant starting...

:: Wait a moment for Qdrant to initialize
timeout /t 5 /nobreak >nul

:: Start Backend in a new window
start "Backend" cmd /c "cd /d %~dp0backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo Backend starting...

:: Start Frontend in a new window
start "Frontend" cmd /c "cd /d %~dp0frontend && npm run dev"
echo Frontend starting...

echo All services launched. Close the Qdrant, Backend, and Frontend windows when done.
pause