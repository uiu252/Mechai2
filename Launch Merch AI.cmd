@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto localenv
if exist "..\..\work\venv\Scripts\python.exe" goto workspaceenv
where py >nul 2>nul
if errorlevel 1 goto trypython
py -3 -m venv .venv
if errorlevel 1 goto failed
goto install
:trypython
where python >nul 2>nul
if errorlevel 1 goto nopython
python -m venv .venv
if errorlevel 1 goto failed
:install
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
:localenv
".venv\Scripts\python.exe" launch.py
goto end
:workspaceenv
"..\..\work\venv\Scripts\python.exe" launch.py
goto end
:nopython
echo Python 3.10 or newer is required. Install it from python.org, then run this file again.
pause
exit /b 1
:failed
echo Setup failed. See the error above and the README for manual setup.
pause
exit /b 1
:end
if errorlevel 1 pause
endlocal
