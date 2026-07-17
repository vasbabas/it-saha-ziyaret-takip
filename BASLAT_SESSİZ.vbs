Set WshShell = CreateObject("WScript.Shell")

' Scriptin bulundugu dizine gecisi garanti et
strPath = Wscript.ScriptFullName
Set objFSO = CreateObject("Scripting.FileSystemObject")
Set objFile = objFSO.GetFile(strPath)
strFolder = objFSO.GetParentFolderName(objFile)
WshShell.CurrentDirectory = strFolder

' Streamlit'i arka planda (gizli pencereyle) baslat
WshShell.Run "cmd.exe /c baslat_arka_plan.bat", 0, false

' Uygulamanin baslamasi icin 2.5 saniye bekle
Wscript.Sleep 2500

' Varsayilan tarayicida uygulamayi ac
WshShell.Run "http://localhost:8501", 9
