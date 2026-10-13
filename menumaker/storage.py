"""Đọc / ghi dữ liệu người dùng (thương hiệu + danh sách món ăn) ra file JSON.

Kèm cơ chế **sao lưu tự động**: trước khi ghi đè, bản cũ được chép vào
config.BACKUP_DIR (nằm NGOÀI thư mục data/ để phòng khi data/ bị xóa nhầm).
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from . import config

DEFAULT_DATA: dict[str, Any] = {
    "brand": {
        "name": "",
        "logo": "",
        "phone": "",
        "zalo": "",
        "address": "",
        "custom_info": "",
    },
    "dishes": [],
}


def _merge_defaults(data: dict) -> dict:
    """Bổ sung các khóa còn thiếu để dữ liệu cũ vẫn đọc được."""
    merged = {
        "brand": {**DEFAULT_DATA["brand"], **(data.get("brand") or {})},
        "dishes": list(data.get("dishes") or []),
    }
    return merged


def load_data() -> dict:
    """Đọc dữ liệu từ file. Trả về dữ liệu mặc định nếu file chưa tồn tại."""
    if not config.DATA_FILE.exists():
        return json.loads(json.dumps(DEFAULT_DATA))
    try:
        with open(config.DATA_FILE, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
    except (json.JSONDecodeError, OSError):
        return json.loads(json.dumps(DEFAULT_DATA))
    return _merge_defaults(raw)


# ---------------------------------------------------------------------------
# Sao lưu tự động
# ---------------------------------------------------------------------------
def _backup_files() -> list[Path]:
    if not config.BACKUP_DIR.exists():
        return []
    files = list(config.BACKUP_DIR.glob("data_*.json"))
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files


def _prune_backups() -> None:
    for old in _backup_files()[config.MAX_BACKUPS:]:
        try:
            old.unlink()
        except OSError:
            pass


def _maybe_backup(force: bool = False) -> None:
    """Chép bản data.json hiện tại thành một bản sao lưu (có giới hạn tần suất)."""
    if not config.DATA_FILE.exists():
        return

    newest = _backup_files()
    if newest and not force:
        try:
            age = datetime.now().timestamp() - newest[0].stat().st_mtime
            if age < config.BACKUP_INTERVAL_SECONDS:
                return
        except OSError:
            pass

    config.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = config.BACKUP_DIR / f"data_{stamp}.json"
    counter = 1
    while dest.exists():
        dest = config.BACKUP_DIR / f"data_{stamp}_{counter}.json"
        counter += 1
    try:
        shutil.copy2(config.DATA_FILE, dest)
    except OSError:
        return
    _prune_backups()


def save_data(data: dict, force_backup: bool = False) -> None:
    """Ghi dữ liệu ra file JSON (tạo thư mục nếu cần) + sao lưu bản cũ."""
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    _maybe_backup(force=force_backup)
    tmp = config.DATA_FILE.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    tmp.replace(config.DATA_FILE)


def list_backups() -> list[tuple[Path, datetime, int]]:
    """Danh sách bản sao lưu: (đường dẫn, thời điểm, số món), mới nhất trước."""
    result: list[tuple[Path, datetime, int]] = []
    for path in _backup_files():
        try:
            with open(path, "r", encoding="utf-8") as fh:
                info = json.load(fh)
            count = len(info.get("dishes") or [])
            when = datetime.fromtimestamp(path.stat().st_mtime)
        except (OSError, json.JSONDecodeError):
            continue
        result.append((path, when, count))
    result.sort(key=lambda item: item[1], reverse=True)
    return result


def restore_backup(path: str | Path) -> dict:
    """Đọc một bản sao lưu và ghi thành dữ liệu hiện tại. Trả về dữ liệu đã khôi phục."""
    with open(path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    data = _merge_defaults(raw)
    # luôn sao lưu bản hiện tại trước khi khôi phục để có thể hoàn tác
    save_data(data, force_backup=True)
    return data
