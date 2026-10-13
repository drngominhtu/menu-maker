"""Tìm và nạp font TrueType hỗ trợ tiếng Việt cho việc render ảnh bằng Pillow."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from PIL import ImageFont

# Các thư mục thường chứa font trên Linux / macOS / Windows.
_SEARCH_DIRS = [
    "/usr/share/fonts",
    "/usr/local/share/fonts",
    str(Path.home() / ".fonts"),
    str(Path.home() / ".local/share/fonts"),
    "C:/Windows/Fonts",
    "/Library/Fonts",
    "/System/Library/Fonts",
    "/System/Library/Fonts/Supplemental",
]

# Ưu tiên font hỗ trợ tiếng Việt tốt.
_REGULAR_CANDIDATES = [
    "NotoSans-Regular.ttf",
    "DejaVuSans.ttf",
    "LiberationSans-Regular.ttf",
    "Roboto-Regular.ttf",
    "arial.ttf",
    "Arial.ttf",
    "segoeui.ttf",
    "Helvetica.ttc",
]
_BOLD_CANDIDATES = [
    "NotoSans-Bold.ttf",
    "NotoSans-SemiBold.ttf",
    "DejaVuSans-Bold.ttf",
    "LiberationSans-Bold.ttf",
    "Roboto-Bold.ttf",
    "arialbd.ttf",
    "Arial Bold.ttf",
    "segoeuib.ttf",
    "Helvetica.ttc",
]


@lru_cache(maxsize=None)
def _find_font(candidates: tuple[str, ...]) -> str | None:
    """Trả về đường dẫn font đầu tiên tìm thấy trong các thư mục tìm kiếm."""
    for wanted in candidates:
        for base in _SEARCH_DIRS:
            base_path = Path(base)
            if not base_path.exists():
                continue
            # Tìm trực tiếp (nhanh) rồi mới đệ quy (chậm hơn nhưng chắc chắn).
            direct = base_path / wanted
            if direct.exists():
                return str(direct)
            try:
                for found in base_path.rglob(wanted):
                    return str(found)
            except (OSError, PermissionError):
                continue
    return None


@lru_cache(maxsize=None)
def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Nạp font theo cỡ chữ. Tự tìm font phù hợp, fallback về font mặc định."""
    candidates = tuple(_BOLD_CANDIDATES if bold else _REGULAR_CANDIDATES)
    path = _find_font(candidates)
    if path:
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            pass
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # Pillow < 10.1 không hỗ trợ tham số size
        return ImageFont.load_default()
