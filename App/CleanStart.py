import subprocess
import threading
import sys 

subprocess.Popen(["cmd", "/c", "python", ".\\App\\UI.py"], creationflags=subprocess.CREATE_NO_WINDOW)

sys.exit(0)