@echo off
set "CH=C:\Program Files\Google\Chrome\Application\chrome.exe"
if not exist "%CH%" set "CH=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
if not exist "%CH%" set "CH=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
if not exist "%CH%" (echo Chrome tidak ketemu. & pause & exit /b 1)
curl -s -m 2 http://127.0.0.1:9222/json/version >nul 2>nul && (echo Chrome debug sudah hidup. Pakai jendela itu. & goto :end)
start "" "%CH%" --remote-debugging-port=9222 --user-data-dir="%LOCALAPPDATA%\Google\Chrome\AutomationProfile" https://app.envato.com
echo Chrome dibuka. LOGIN Envato di jendela itu, lalu biarkan terbuka.
:end
if /i not "%1"=="nopause" pause
