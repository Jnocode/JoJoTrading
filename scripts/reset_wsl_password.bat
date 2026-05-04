@echo off
echo ==========================================
echo   Resetting WSL Password for user 'jun'
echo ==========================================
echo.
echo You will be asked to enter a NEW password.
echo Note: When typing, the characters will be hidden (no stars *).
echo.
wsl -u root passwd jun
echo.
echo Password reset complete!
echo Now please run 'setup_wsl_openclaw.bat' again.
echo.
pause
