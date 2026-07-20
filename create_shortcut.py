import os
import subprocess

desktop = os.path.join(os.path.expanduser("~"), "Desktop")
shortcut_path = os.path.join(desktop, "IT Saha Takip Otomasyonu.lnk")
target = r"C:\Users\User\Desktop\IT Saha Ziyaret ve Takip Otomasyonu\BASLAT_SESSİZ.vbs"
workdir = r"C:\Users\User\Desktop\IT Saha Ziyaret ve Takip Otomasyonu"

vbs_content = f'''Set w = CreateObject("WScript.Shell")
Set s = w.CreateShortcut("{shortcut_path}")
s.TargetPath = "{target}"
s.WorkingDirectory = "{workdir}"
s.Description = "IT Saha Ziyaret ve Takip Otomasyonu"
s.Save
'''

vbs_file = os.path.join(workdir, "mk.vbs")
with open(vbs_file, "w", encoding="utf-8") as f:
    f.write(vbs_content)

subprocess.run(["cscript", "//nologo", vbs_file], check=True)
if os.path.exists(vbs_file):
    os.remove(vbs_file)
print("SUCCESS: Desktop Shortcut Created!")
