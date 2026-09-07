@echo off
:: สร้าง shortcut ใน Startup folder -> เปิดเครื่องแล้วรันเองแบบเงียบ
set "LNK=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Discord Rich Presence.lnk"
powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%LNK%'); $s.TargetPath='wscript.exe'; $s.Arguments='\"%~dp0start_background.vbs\"'; $s.WorkingDirectory='%~dp0'; $s.Save()"
echo Autostart enabled: "%LNK%"
pause
