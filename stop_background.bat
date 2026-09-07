@echo off
echo Stopping Discord Rich Presence background process...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Discord Rich Presence*" 2>nul
powershell -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*clever-davinci*main.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
echo Stopped successfully!
pause
