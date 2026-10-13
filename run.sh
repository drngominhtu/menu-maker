#!/usr/bin/env bash
# Chạy Menu Maker (ưu tiên venv nếu có).
set -e
cd "$(dirname "$0")"

if [ -x ".venv/bin/python" ]; then
    exec .venv/bin/python app.py
elif [ -x ".venv/Scripts/python.exe" ]; then
    exec .venv/Scripts/python.exe app.py
else
    exec python3 app.py
fi
