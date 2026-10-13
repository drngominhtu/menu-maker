#!/usr/bin/env bash
# Build Menu Maker thanh 1 file chay duoc tren Linux/macOS.
# (Tren Windows hay dung build_exe.bat de tao .exe)
set -e
cd "$(dirname "$0")"

PY="python3"
if [ -x ".venv/bin/python" ]; then
    PY=".venv/bin/python"
fi

echo "== [1/2] Cai dat thu vien =="
"$PY" -m pip install -q --upgrade pip
"$PY" -m pip install -q -r requirements.txt pyinstaller

echo "== [2/2] Build =="
"$PY" -m PyInstaller --noconfirm --clean --onefile --windowed \
    --name MenuMaker \
    --hidden-import PIL.ImageTk \
    --hidden-import PIL._tkinter_finder \
    --exclude-module numpy --exclude-module pytest --exclude-module matplotlib \
    app.py

echo
echo "Hoan tat! File chay: dist/MenuMaker"
