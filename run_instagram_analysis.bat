@echo off
echo.
echo ========================================
echo Instagram Follower Analysis Runner
echo ========================================
echo.
echo This will run the complete workflow:
echo 1. Format curl command
echo 2. Scrape Instagram data  
echo 3. Compare followers
echo.
echo Press any key to start...
pause >nul

python run_instagram_analysis.py

echo.
echo ========================================
echo Workflow completed!
echo ========================================
echo.
echo Press any key to exit...
pause >nul 