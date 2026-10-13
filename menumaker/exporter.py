"""Render ảnh menu PNG bằng Pillow.

- Mỗi tag (danh mục) xuất thành một file menu riêng.
- Ngoài ra có thể GỘP TẤT CẢ tag thành MỘT ảnh: logo/thương hiệu ở trên cùng,
  bên dưới mỗi tag là một CỘT (món giữ kiểu hàng ngang tên | giá | ảnh),
  chiều rộng tự mở rộng theo số tag, chiều cao tính theo cột DÀI NHẤT.

Bố cục dùng lưới cố định: mọi hàng có cùng chiều cao, mọi cột có cùng tọa độ x
-> không bao giờ lệch hàng hay lệch cột dù tên món dài ngắn khác nhau.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

from . import config
from .fonts import load_font


# ---------------------------------------------------------------------------
# Tiện ích
# ---------------------------------------------------------------------------
def _load_rgba(path: str | Path) -> Image.Image | None:
    """Mở ảnh, xoay theo EXIF và chuyển sang RGBA. Trả về None nếu lỗi."""
    try:
        img = Image.open(path)
        img = ImageOps.exif_transpose(img)
        return img.convert("RGBA")
    except (OSError, ValueError):
        return None


def _contain(img: Image.Image, box_w: int, box_h: int) -> Image.Image:
    """Thu ảnh vừa khít khung, giữ nguyên tỉ lệ (không cắt mất món ăn)."""
    ratio = min(box_w / img.width, box_h / img.height)
    new_size = (max(1, round(img.width * ratio)), max(1, round(img.height * ratio)))
    resample = Image.LANCZOS if hasattr(Image, "LANCZOS") else Image.BICUBIC
    return img.resize(new_size, resample)


def _cover(img: Image.Image, box_w: int, box_h: int) -> Image.Image:
    """Phóng ảnh lấp đầy khung rồi cắt phần thừa, lấy TÂM ảnh làm chính giữa.

    Nhờ vậy mọi ảnh dù kích cỡ/tỉ lệ khác nhau đều thành cùng một kích cỡ vuông.
    """
    ratio = max(box_w / img.width, box_h / img.height)
    new_size = (max(1, round(img.width * ratio)), max(1, round(img.height * ratio)))
    resample = Image.LANCZOS if hasattr(Image, "LANCZOS") else Image.BICUBIC
    resized = img.resize(new_size, resample)

    left = (resized.width - box_w) // 2
    top = (resized.height - box_h) // 2
    return resized.crop((left, top, left + box_w, top + box_h))


def _rounded_mask(size: tuple[int, int], radius: int) -> Image.Image:
    """Tạo mặt nạ bo góc để dán ảnh/khung cho đẹp."""
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle(
        [0, 0, size[0] - 1, size[1] - 1], radius=radius, fill=255
    )
    return mask


def _draw_corner_strokes(img: Image.Image, pad: int, width: int, height: int) -> None:
    """Vẽ nét góc (chữ L) ở hai góc đối diện: trên-trái và dưới-phải."""
    draw = ImageDraw.Draw(img)
    col = config.FRAME_ACCENT_COLOR
    t = config.FRAME_ACCENT_WIDTH
    length = config.FRAME_ACCENT_LEN
    inset0 = config.FRAME_ACCENT_INSET

    # Hai nét lồng nhau cho tinh tế (vẫn gọn), nét trong ngắn hơn.
    for extra in (0, t + 6):
        inset = inset0 + extra
        arm = length - extra
        if arm <= 0 or inset + arm > pad:
            continue
        # Góc trên-trái
        draw.rectangle([inset, inset, inset + arm, inset + t], fill=col)
        draw.rectangle([inset, inset, inset + t, inset + arm], fill=col)
        # Góc dưới-phải
        draw.rectangle([width - inset - arm, height - inset - t, width - inset, height - inset], fill=col)
        draw.rectangle([width - inset - t, height - inset - arm, width - inset, height - inset], fill=col)


def _add_frame(content: Image.Image) -> Image.Image:
    """Bọc nội dung menu bằng viền trang trí: nền hồng cam + thẻ trắng bo góc."""
    if not config.FRAME_ENABLED or config.FRAME_PAD <= 0:
        return content

    pad = config.FRAME_PAD
    w, h = content.size
    W, H = w + pad * 2, h + pad * 2

    frame = Image.new("RGB", (W, H), config.FRAME_COLOR)

    # Bóng đổ nhẹ dưới thẻ menu
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        [pad, pad + 6, pad + w, pad + h + 6],
        radius=config.FRAME_CORNER_RADIUS,
        fill=config.FRAME_SHADOW + (110,),
    )
    frame = Image.alpha_composite(frame.convert("RGBA"), shadow)

    # Thẻ menu trắng bo góc
    card_mask = _rounded_mask((w, h), config.FRAME_CORNER_RADIUS)
    frame.paste(content, (pad, pad), card_mask)

    frame = frame.convert("RGB")
    _draw_corner_strokes(frame, pad, W, H)
    return frame



def _wrap(font, text: str, max_width: int, max_lines: int | None = None) -> list[str]:
    """Ngắt dòng văn bản theo chiều rộng cột. Có thể giới hạn số dòng."""
    text = (text or "").strip()
    if not text:
        return []

    lines: list[str] = []
    for paragraph in text.split("\n"):
        if not paragraph.strip():
            lines.append("")  # giữ dòng trống để cách dòng theo ý người dùng
            continue
        words = paragraph.split()
        current = ""
        for word in words:
            trial = f"{current} {word}".strip()
            if not current or font.getlength(trial) <= max_width:
                current = trial
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)

    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while last and font.getlength(last + "…") > max_width:
            last = last[:-1]
        lines[-1] = last.rstrip() + "…"
    return lines


def format_price(price: str, unit: str) -> str:
    """Chuẩn hóa giá: '50000' -> '50.000đ'. Giữ nguyên nếu là chữ tự do."""
    price = (price or "").strip()
    unit = (unit or "").strip()
    digits = price.replace(".", "").replace(",", "").replace(" ", "")
    if digits.isdigit() and digits:
        text = f"{int(digits):,}".replace(",", ".") + "đ"
    else:
        text = price
    return text


# ---------------------------------------------------------------------------
# Phông chữ & kích thước dòng dùng chung
# ---------------------------------------------------------------------------
def _load_fonts() -> dict:
    return {
        "brand": load_font(config.BRAND_FONT_SIZE, bold=True),
        "contact": load_font(config.CONTACT_FONT_SIZE),
        "custom": load_font(config.CUSTOM_FONT_SIZE),
        "title": load_font(config.CATEGORY_TITLE_FONT_SIZE, bold=True),
        "name": load_font(config.NAME_FONT_SIZE, bold=True),
        "price": load_font(config.PRICE_FONT_SIZE, bold=True),
        "unit": load_font(config.UNIT_FONT_SIZE),
        "placeholder": load_font(28),
    }


def _line_heights() -> dict:
    return {
        "brand": int(config.BRAND_FONT_SIZE * 1.25),
        "contact": int(config.CONTACT_FONT_SIZE * 1.5),
        "custom": int(config.CUSTOM_FONT_SIZE * config.CUSTOM_LINE_FACTOR),
        "title": int(config.CATEGORY_TITLE_FONT_SIZE * 1.3),
        "name": int(config.NAME_FONT_SIZE * config.NAME_LINE_FACTOR),
        "price": int(config.PRICE_FONT_SIZE * config.PRICE_LINE_FACTOR),
        "unit": int(config.UNIT_FONT_SIZE * 1.4),
    }


# ---------------------------------------------------------------------------
# Header dùng chung (logo + tên + liên hệ + thông tin tùy chỉnh)
# ---------------------------------------------------------------------------
def _build_header(brand: dict, content_w: int) -> dict:
    """Chuẩn bị nội dung header và tính chiều cao, dùng chung cho mọi bố cục."""
    fonts = _load_fonts()
    lh = _line_heights()

    logo_img = None
    logo_path = (brand.get("logo") or "").strip()
    if logo_path and Path(logo_path).exists():
        src = _load_rgba(logo_path)
        if src is not None:
            logo_img = _contain(src, config.LOGO_MAX_W, config.LOGO_MAX_H)

    brand_lines = _wrap(fonts["brand"], brand.get("name", ""), content_w)

    contact_raw: list[str] = []
    hotline_parts = []
    if (brand.get("phone") or "").strip():
        hotline_parts.append(f"ĐT: {brand['phone'].strip()}")
    if (brand.get("zalo") or "").strip():
        hotline_parts.append(f"Zalo: {brand['zalo'].strip()}")
    if hotline_parts:
        contact_raw.append("   •   ".join(hotline_parts))
    if (brand.get("address") or "").strip():
        contact_raw.append(f"Địa chỉ: {brand['address'].strip()}")

    contact_lines: list[str] = []
    for raw in contact_raw:
        contact_lines.extend(_wrap(fonts["contact"], raw, content_w))

    custom_lines = _wrap(fonts["custom"], brand.get("custom_info", ""), content_w)

    header_h = config.TOP_BAR_H + config.HEADER_PAD
    if logo_img is not None:
        header_h += logo_img.height + 26
    if brand_lines:
        header_h += len(brand_lines) * lh["brand"] + 12
    if contact_lines:
        header_h += len(contact_lines) * lh["contact"]
    if custom_lines:
        header_h += 14 + len(custom_lines) * lh["custom"]

    header_h += config.HEADER_PAD
    divider_y = header_h
    header_h += 3

    return {
        "fonts": fonts,
        "lh": lh,
        "logo_img": logo_img,
        "brand_lines": brand_lines,
        "contact_lines": contact_lines,
        "custom_lines": custom_lines,
        "header_h": header_h,
        "divider_y": divider_y,
    }


def _draw_header(canvas: Image.Image, draw: ImageDraw.ImageDraw, header: dict, width: int) -> None:
    fonts = header["fonts"]
    lh = header["lh"]

    # Thanh nhấn trên cùng
    draw.rectangle([0, 0, width, config.TOP_BAR_H], fill=config.ACCENT_COLOR)

    y = config.TOP_BAR_H + config.HEADER_PAD
    logo_img = header["logo_img"]
    if logo_img is not None:
        lx = (width - logo_img.width) // 2
        canvas.paste(logo_img, (lx, y), logo_img)
        y += logo_img.height + 26

    for line in header["brand_lines"]:
        lw = fonts["brand"].getlength(line)
        draw.text(((width - lw) / 2, y), line, font=fonts["brand"], fill=config.DARK)
        y += lh["brand"]
    if header["brand_lines"]:
        y += 12

    for line in header["contact_lines"]:
        lw = fonts["contact"].getlength(line)
        draw.text(((width - lw) / 2, y), line, font=fonts["contact"], fill=config.CONTACT_COLOR)
        y += lh["contact"]

    if header["custom_lines"]:
        y += 14
        for line in header["custom_lines"]:
            if line:
                lw = fonts["custom"].getlength(line)
                draw.text(((width - lw) / 2, y), line, font=fonts["custom"], fill=config.CUSTOM_COLOR)
            y += lh["custom"]

    # Đường kẻ phân cách dưới header
    draw.rectangle(
        [config.MARGIN, header["divider_y"], width - config.MARGIN, header["divider_y"] + 3],
        fill=config.ACCENT_COLOR,
    )


def _draw_title(
    draw: ImageDraw.ImageDraw, header: dict, title: str, center_x: float, y: int
) -> None:
    tw = header["fonts"]["title"].getlength(title)
    draw.text(
        (center_x - tw / 2, y), title,
        font=header["fonts"]["title"], fill=config.ACCENT_COLOR,
    )


# ---------------------------------------------------------------------------
# Vẽ một hàng món (3 cột cố định: tên | giá/đvt | ảnh)
# ---------------------------------------------------------------------------
def _draw_dish_row(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    header: dict,
    dish: dict,
    row_top: int,
    content_left: float,
    is_last: bool,
) -> None:
    fonts = header["fonts"]
    lh = header["lh"]

    col_name_x = content_left
    col_price_x = col_name_x + config.COL_NAME_W + config.COL_GAP
    col_image_x = col_price_x + config.COL_PRICE_W + config.COL_GAP

    box_w, box_h = config.IMAGE_BOX

    # --- Cột 1: tên món (canh trái, canh giữa theo chiều dọc) ---
    name_lines = _wrap(fonts["name"], dish.get("name", ""), config.COL_NAME_W, max_lines=4)
    block_h = len(name_lines) * lh["name"]
    ny = row_top + (config.ROW_HEIGHT - block_h) / 2
    for line in name_lines:
        draw.text((col_name_x, ny), line, font=fonts["name"], fill=config.DARK)
        ny += lh["name"]

    # --- Cột 2: giá / đơn vị tính ---
    price_lines = _wrap(fonts["price"], format_price(dish.get("price", ""), ""), config.COL_PRICE_W, max_lines=2)
    unit_lines = _wrap(fonts["unit"], dish.get("unit", ""), config.COL_PRICE_W, max_lines=1)
    block_h = len(price_lines) * lh["price"] + len(unit_lines) * lh["unit"]
    py = row_top + (config.ROW_HEIGHT - block_h) / 2
    for line in price_lines:
        lw = fonts["price"].getlength(line)
        draw.text((col_price_x + (config.COL_PRICE_W - lw) / 2, py), line, font=fonts["price"], fill=config.DARK)
        py += lh["price"]
    for line in unit_lines:
        lw = fonts["unit"].getlength(line)
        draw.text((col_price_x + (config.COL_PRICE_W - lw) / 2, py), line, font=fonts["unit"], fill=config.GRAY)
        py += lh["unit"]

    # --- Cột 3: ảnh món (khung cố định -> thẳng hàng tuyệt đối) ---
    bx = col_image_x + (config.COL_IMAGE_W - box_w) // 2
    by = row_top + (config.ROW_HEIGHT - box_h) // 2

    frame_mask = _rounded_mask((box_w, box_h), config.IMAGE_RADIUS)
    frame = Image.new("RGBA", (box_w, box_h), config.IMAGE_BG + (255,))
    frame_draw = ImageDraw.Draw(frame)
    frame_draw.rounded_rectangle(
        [0, 0, box_w - 1, box_h - 1],
        radius=config.IMAGE_RADIUS,
        outline=config.IMAGE_BORDER + (255,),
        width=2,
    )
    canvas.paste(frame, (bx, by), frame_mask)

    inner_w = box_w - config.IMAGE_INNER_PAD * 2
    inner_h = box_h - config.IMAGE_INNER_PAD * 2

    dish_img = None
    img_path = (dish.get("image") or "").strip()
    if img_path and Path(img_path).exists():
        src = _load_rgba(img_path)
        if src is not None:
            dish_img = _cover(src, inner_w, inner_h)

    if dish_img is not None:
        ix = bx + config.IMAGE_INNER_PAD
        iy = by + config.IMAGE_INNER_PAD
        img_mask = _rounded_mask(dish_img.size, max(6, config.IMAGE_RADIUS - config.IMAGE_INNER_PAD))
        canvas.paste(dish_img, (ix, iy), img_mask)
    else:
        text = "Chưa có ảnh"
        tw = fonts["placeholder"].getlength(text)
        th = fonts["placeholder"].getbbox("Ag")[3]
        draw.text(
            (bx + (box_w - tw) / 2, by + (box_h - th) / 2),
            text,
            font=fonts["placeholder"],
            fill=config.GRAY,
        )

    # --- Đường kẻ giữa các hàng ---
    if not is_last:
        ly = row_top + config.ROW_HEIGHT - 1
        draw.rectangle(
            [content_left, ly, content_left + config.CONTENT_WIDTH, ly],
            fill=config.LINE_COLOR,
        )


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------
def render_menu(category_key: str, dishes: list[dict], brand: dict, out_path) -> str:
    """Xuất một menu PNG cho một tag. Trả về đường dẫn file đã ghi."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    width = config.EXPORT_WIDTH
    content_w = config.CONTENT_WIDTH

    header = _build_header(brand, content_w)
    lh = header["lh"]

    title_block_h = 0
    if category_key:
        title_block_h = config.CATEGORY_TITLE_PAD_TOP + lh["title"] + config.CATEGORY_TITLE_PAD_BOTTOM

    table_top = header["header_h"] + title_block_h
    total_h = table_top + max(1, len(dishes)) * config.ROW_HEIGHT + config.BOTTOM_BAR_H

    canvas = Image.new("RGB", (width, total_h), config.BG_COLOR)
    draw = ImageDraw.Draw(canvas)

    _draw_header(canvas, draw, header, width)

    content_left = config.MARGIN

    # ---- Tiêu đề danh mục ----
    if category_key:
        _draw_title(
            draw, header, config.category_label(category_key).upper(),
            width / 2, header["header_h"] + config.CATEGORY_TITLE_PAD_TOP,
        )

    # ---- Bảng món ăn (3 cột cố định) ----
    for index, dish in enumerate(dishes):
        row_top = table_top + index * config.ROW_HEIGHT
        _draw_dish_row(
            canvas, draw, header, dish, row_top, content_left,
            is_last=(index == len(dishes) - 1),
        )

    # Thanh nhấn dưới cùng
    draw.rectangle(
        [0, total_h - config.BOTTOM_BAR_H, width, total_h],
        fill=config.ACCENT_COLOR,
    )

    canvas = _add_frame(canvas)
    canvas.save(out_path, format="PNG", dpi=(300, 300))
    return str(out_path)


def render_merged_menu(categories: list[tuple[str, list[dict]]], brand: dict, out_path) -> str:
    """Gộp mọi tag vào MỘT ảnh: header ở trên, mỗi tag là một CỘT.

    - Chiều rộng = số tag × bề rộng một cột (tự mở rộng theo số tag).
    - Chiều cao = chiều cao cột DÀI NHẤT (tag nhiều món nhất).
    - Giữa các cột tag có đường kẻ dọc phân tách.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    categories = [(k, d) for k, d in categories if d]
    if not categories:
        raise ValueError("Không có món nào để gộp menu.")

    n = len(categories)
    gap = config.MERGE_TAG_GAP
    col_w = config.CONTENT_WIDTH

    content_total_w = n * col_w + (n - 1) * gap
    width = config.MARGIN * 2 + content_total_w

    header = _build_header(brand, content_total_w)
    lh = header["lh"]

    title_block_h = config.CATEGORY_TITLE_PAD_TOP + lh["title"] + config.CATEGORY_TITLE_PAD_BOTTOM
    table_top = header["header_h"] + title_block_h

    max_dishes = max(len(dishes) for _, dishes in categories)
    total_h = table_top + max(1, max_dishes) * config.ROW_HEIGHT + config.BOTTOM_BAR_H

    canvas = Image.new("RGB", (width, total_h), config.BG_COLOR)
    draw = ImageDraw.Draw(canvas)

    _draw_header(canvas, draw, header, width)

    body_bottom = total_h - config.BOTTOM_BAR_H

    for i, (key, dishes) in enumerate(categories):
        content_left = config.MARGIN + i * (col_w + gap)

        # Đường kẻ dọc phân tách giữa các cột tag
        if i > 0:
            sep_x = content_left - gap // 2
            draw.rectangle(
                [sep_x, header["header_h"], sep_x + 1, body_bottom],
                fill=config.LINE_COLOR,
            )

        # Tiêu đề tag (canh giữa trong cột)
        _draw_title(
            draw, header, config.category_label(key).upper(),
            content_left + col_w / 2,
            header["header_h"] + config.CATEGORY_TITLE_PAD_TOP,
        )

        # Bảng món của tag
        for index, dish in enumerate(dishes):
            row_top = table_top + index * config.ROW_HEIGHT
            _draw_dish_row(
                canvas, draw, header, dish, row_top, content_left,
                is_last=(index == len(dishes) - 1),
            )

    # Thanh nhấn dưới cùng
    draw.rectangle(
        [0, total_h - config.BOTTOM_BAR_H, width, total_h],
        fill=config.ACCENT_COLOR,
    )

    canvas = _add_frame(canvas)
    canvas.save(out_path, format="PNG", dpi=(300, 300))
    return str(out_path)
