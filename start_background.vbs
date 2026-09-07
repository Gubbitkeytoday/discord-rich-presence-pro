' รันแบบเงียบ (ไม่มีหน้าต่างดำ) ด้วย pythonw.exe โดยตรง — log อยู่ที่ rpc.log
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh  = CreateObject("WScript.Shell")
dir = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = dir
If Not fso.FileExists(dir & "\.venv\Scripts\pythonw.exe") Then
    sh.Run "cmd /c """ & dir & "\start.bat""", 1, True
End If
sh.Run """" & dir & "\.venv\Scripts\pythonw.exe"" """ & dir & "\main.py""", 0, False
