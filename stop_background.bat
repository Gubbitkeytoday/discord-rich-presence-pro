@echo off
echo Stopping Discord Rich Presence...
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*%~dp0main.py*' -or ($_.CommandLine -like '*main.py*' -and $_.ExecutablePath -like '*clever-davinci*') } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force; Write-Host ('  stopped PID ' + $_.ProcessId) }"
echo Done.
timeout /t 2 >nul
