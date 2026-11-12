@echo off
set "PROJECT_ROOT=%~dp0"
echo =======================================================
echo          Job-Manager Independent Feeder Runner
echo =======================================================
echo Pulling live jobs from Greenhouse, Lever, and feeds...
echo.

"%PROJECT_ROOT%ai-service\venv\Scripts\python.exe" -m feeder.cli run-all --api-url http://localhost:8005/api

echo.
echo Feeder run completed.
pause
