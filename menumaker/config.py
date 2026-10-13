"""Cấu hình chung cho ứng dụng Menu Maker.

Toàn bộ hằng số bố cục của ảnh menu được gom về đây để dễ tinh chỉnh.
"""

from __future__ import annotations

import sys
from pathlib import Path

APP_TITLE = "Menu Maker - Tạo menu món ăn"


def _app_dir() -> Path:
    """Thư mục chứa dữ liệu (data/, exports/).

    - Chạy từ mã nguồn: thư mục dự án.
    - Chạy từ file đã đóng gói (.exe): thư mục chứa file .exe, để dữ liệu
      nằm ngay cạnh exe và không bị mất khi thoát.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Đường dẫn dữ liệu (đặt cạnh chương trình để dễ sao lưu / di chuyển)
# ---------------------------------------------------------------------------
APP_DIR = _app_dir()
DATA_DIR = APP_DIR / "data"
IMAGE_DIR = DATA_DIR / "images"
DATA_FILE = DATA_DIR / "data.json"
DEFAULT_EXPORT_DIR = APP_DIR / "exports"

# Sao lưu tự động — đặt RIÊNG ngoài thư mục data/ để không mất chung khi data/ bị xóa.
BACKUP_DIR = APP_DIR / "backups"
BACKUP_INTERVAL_SECONDS = 120   # tối thiểu 2 phút giữa 2 bản sao lưu
MAX_BACKUPS = 30                # giữ tối đa 30 bản gần nhất

# ---------------------------------------------------------------------------
# Danh mục (tag) món ăn
# ---------------------------------------------------------------------------
CATEGORIES = [
    ("mon_chinh", "Món chính"),
    ("mon_nuoc", "Món nước"),
    ("mon_an_kem", "Món ăn kèm"),
    ("mon_dong_lanh", "Món bảo quản đông lạnh"),
]
CATEGORY_KEYS = [key for key, _ in CATEGORIES]
CATEGORY_LABELS = {key: label for key, label in CATEGORIES}


def category_label(key: str) -> str:
    """Trả về nhãn tiếng Việt của một tag."""
    return CATEGORY_LABELS.get(key, key)


# ---------------------------------------------------------------------------
# Bố cục ảnh xuất ra (đơn vị: pixel)
# ---------------------------------------------------------------------------
EXPORT_WIDTH = 1080          # chiều rộng cố định
MARGIN = 48                  # lề trái/phải
CONTENT_WIDTH = EXPORT_WIDTH - MARGIN * 2

# Màu sắc (RGB)
BG_COLOR = (255, 255, 255)
ACCENT_COLOR = (198, 74, 40)      # cam gạch - màu nhấn
DARK = (33, 33, 33)               # chữ chính
GRAY = (120, 120, 120)            # chữ phụ
LINE_COLOR = (226, 226, 226)      # đường kẻ
IMAGE_BG = (246, 243, 240)        # nền khung ảnh
IMAGE_BORDER = (232, 224, 216)    # viền khung ảnh

# ---- Phần đầu (header) ----
TOP_BAR_H = 14               # thanh màu nhấn trên cùng
HEADER_PAD = 40              # khoảng đệm dọc của header
LOGO_MAX_W = 520
LOGO_MAX_H = 180
BRAND_FONT_SIZE = 60
CONTACT_FONT_SIZE = 30
CONTACT_COLOR = (90, 90, 90)

# Thông tin tùy chỉnh (gõ trực tiếp trên cửa sổ chính, in ở đầu menu)
CUSTOM_FONT_SIZE = 30
CUSTOM_COLOR = (95, 95, 95)
CUSTOM_LINE_FACTOR = 1.5

# ---- Bảng món: 3 cột cố định ----
ROW_HEIGHT = 320             # chiều cao mỗi hàng (cố định -> không lệch)
COL_NAME_W = 360             # cột tên món
COL_PRICE_W = 210            # cột giá / đơn vị tính
COL_IMAGE_W = 320            # cột ảnh
COL_GAP = 47                 # khoảng cách giữa các cột
IMAGE_BOX = (300, 300)       # khung ảnh vuông
IMAGE_INNER_PAD = 8          # đệm giữa viền khung và ảnh
IMAGE_RADIUS = 22            # bo góc khung ảnh

NAME_FONT_SIZE = 42
PRICE_FONT_SIZE = 42
UNIT_FONT_SIZE = 30
NAME_LINE_FACTOR = 1.32
PRICE_LINE_FACTOR = 1.30

# Tiêu đề danh mục (in giữa, phía trên bảng món)
CATEGORY_TITLE_FONT_SIZE = 46
CATEGORY_TITLE_PAD_TOP = 30
CATEGORY_TITLE_PAD_BOTTOM = 22

BOTTOM_BAR_H = 14            # thanh màu nhấn dưới cùng

# ---- Menu gộp (mọi tag xếp thành cột trong 1 ảnh) ----
MERGE_TAG_GAP = 56           # khoảng cách ngang giữa hai cột tag

# ---- Viền trang trí quanh menu (khung ngoài hồng cam, thẻ menu nền trắng) ----
FRAME_ENABLED = True
FRAME_PAD = 44               # độ dày viền hồng cam bao quanh menu
FRAME_COLOR = (255, 172, 141)        # nền ngoài - hồng cam dễ thương
FRAME_CORNER_RADIUS = 28     # bo góc thẻ menu trắng
FRAME_SHADOW = (228, 146, 118)       # bóng đổ nhẹ dưới thẻ menu

# Nét trang trí ở 2 góc đối diện (trên-trái và dưới-phải) cho gọn mắt
FRAME_ACCENT_COLOR = (198, 74, 40)   # màu nét góc
FRAME_ACCENT_WIDTH = 4               # độ dày nét
FRAME_ACCENT_LEN = 30                # độ dài mỗi cạnh nét góc
FRAME_ACCENT_INSET = 12              # khoảng cách từ nét góc tới mép ảnh
