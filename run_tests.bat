@echo off
echo ========================================================
echo   Running Automated Unit Tests (23 comprehensive tests)
echo ========================================================
cd backend
python -m unittest discover tests
pause
