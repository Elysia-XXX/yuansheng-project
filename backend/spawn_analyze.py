# -*- coding: utf-8 -*-
"""分离式后台启动 analyze_shop_qa.py，避免被父 shell 回收。

用法：python spawn_analyze.py
"""
import subprocess
import sys

PY = r"C:\Users\Elysia\Desktop\yuan\original-soundtrack\backend\.venv\Scripts\python.exe"
SCRIPT = r"C:\Users\Elysia\Desktop\yuan\original-soundtrack\backend\analyze_shop_qa.py"
WORKDIR = r"C:\Users\Elysia\Desktop\yuan\original-soundtrack\backend"
OUT = r"C:\Users\Elysia\Desktop\yuan\original-soundtrack\backend\analyze_qa_bg.log"
ERR = r"C:\Users\Elysia\Desktop\yuan\original-soundtrack\backend\analyze_qa_bg.err.log"

flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
with open(OUT, "wb") as out_f, open(ERR, "wb") as err_f:
    proc = subprocess.Popen(
        [PY, SCRIPT],
        cwd=WORKDIR,
        stdout=out_f,
        stderr=err_f,
        creationflags=flags,
        close_fds=True,
    )
print("spawned pid:", proc.pid)
