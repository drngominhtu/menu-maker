"""Giao diện Tkinter cho Menu Maker.

- Sidebar chọn tag (danh mục).
- Danh sách món có ảnh thu nhỏ, nút sửa / xóa / di chuyển lên xuống.
- Cửa sổ riêng để nhập thông tin thương hiệu (logo, tên, SĐT/Zalo, địa chỉ).
- Cửa sổ riêng để thêm/sửa món (tag, tên, giá, đơn vị tính, chọn ảnh).
- Nút xuất menu ra PNG (mỗi tag một file).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from PIL import Image, ImageOps

try:  # Trên một số bản Linux, ImageTk nằm ở gói riêng (python3-pil.imagetk)
    from PIL import ImageTk

    HAVE_IMAGETK = True
except ImportError:  # pragma: no cover - phụ thuộc môi trường
    ImageTk = None  # type: ignore[assignment]
    HAVE_IMAGETK = False

from . import config, storage
from .exporter import format_price, render_menu, render_merged_menu

IMAGE_FILETYPES = [
    ("Ảnh", "*.png *.jpg *.jpeg *.webp *.bmp *.gif *.tif *.tiff"),
    ("Tất cả tệp", "*.*"),
]


# ---------------------------------------------------------------------------
# Tiện ích dùng chung
# ---------------------------------------------------------------------------
def import_image(src: str) -> str:
    """Sao chép ảnh người dùng chọn vào thư mục dữ liệu để không bị mất."""
    config.IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    src_path = Path(src)
    ext = src_path.suffix.lower() or ".png"
    dest = config.IMAGE_DIR / f"{uuid.uuid4().hex}{ext}"
    shutil.copy2(src_path, dest)
    return str(dest)


def load_thumbnail(path: str, size: tuple[int, int]) -> ImageTk.PhotoImage | None:
    """Tạo ảnh thu nhỏ (PhotoImage) để hiển thị trong giao diện."""
    if not HAVE_IMAGETK or not path:
        return None
    p = Path(path)
    if not p.exists():
        return None
    try:
        img = Image.open(p)
        img = ImageOps.exif_transpose(img).convert("RGB")
        img.thumbnail(size, Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    except (OSError, ValueError):
        return None


def load_square_thumbnail(path: str, size: int) -> ImageTk.PhotoImage | None:
    """Ảnh thu nhỏ dạng ô VUÔNG: lấp đầy rồi cắt giữa (giống ảnh khi xuất ra)."""
    if not HAVE_IMAGETK or not path:
        return None
    p = Path(path)
    if not p.exists():
        return None
    try:
        img = Image.open(p)
        img = ImageOps.exif_transpose(img).convert("RGB")
        w, h = img.size
        side = min(w, h)
        left, top = (w - side) // 2, (h - side) // 2
        img = img.crop((left, top, left + side, top + side)).resize((size, size), Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    except (OSError, ValueError):
        return None


def open_folder(path: Path) -> None:
    """Mở thư mục bằng ứng dụng mặc định của hệ điều hành."""
    target = str(path)
    try:
        if sys.platform.startswith("win"):
            os.startfile(target)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", target])
        else:
            subprocess.Popen(["xdg-open", target])
    except Exception:
        pass


def center_over(window: tk.Toplevel, parent: tk.Misc) -> None:
    """Căn cửa sổ con ra giữa cửa sổ cha."""
    window.update_idletasks()
    pw, ph = parent.winfo_width(), parent.winfo_height()
    px, py = parent.winfo_rootx(), parent.winfo_rooty()
    w, h = window.winfo_width(), window.winfo_height()
    x = px + (pw - w) // 2
    y = py + (ph - h) // 2
    window.geometry(f"+{max(0, x)}+{max(0, y)}")


class ScrollableFrame(ttk.Frame):
    """Frame có thanh cuộn dọc (dùng Canvas + Frame bên trong)."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0, bg="white")
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.inner = ttk.Frame(self.canvas)
        self._win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.inner.bind("<Configure>", self._on_inner_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<Enter>", self._bind_wheel)
        self.canvas.bind("<Leave>", self._unbind_wheel)

    def _on_inner_configure(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfigure(self._win, width=event.width)

    def _bind_wheel(self, _event=None):
        self.canvas.bind_all("<MouseWheel>", self._on_wheel)
        self.canvas.bind_all("<Button-4>", self._on_wheel)
        self.canvas.bind_all("<Button-5>", self._on_wheel)

    def _unbind_wheel(self, _event=None):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_wheel(self, event):
        if getattr(event, "num", None) == 4:
            delta = -1
        elif getattr(event, "num", None) == 5:
            delta = 1
        else:
            delta = -1 if event.delta > 0 else 1
        self.canvas.yview_scroll(delta, "units")

    def clear(self):
        for child in self.inner.winfo_children():
            child.destroy()


# ---------------------------------------------------------------------------
# Cửa sổ thông tin thương hiệu
# ---------------------------------------------------------------------------
class BrandDialog(tk.Toplevel):
    def __init__(self, master, brand: dict):
        super().__init__(master)
        self.title("Thông tin thương hiệu")
        self.resizable(False, False)
        self.transient(master)
        self.result: dict | None = None

        self._brand = dict(brand)
        self._pending_logo: str | None = None
        self._logo_preview: ImageTk.PhotoImage | None = None

        self._build()
        self.grab_set()
        center_over(self, master)
        self.wait_window(self)

    def _build(self):
        pad = {"padx": 12, "pady": 6}
        frm = ttk.Frame(self, padding=16)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="Logo thương hiệu:").grid(row=0, column=0, sticky="w", **pad)
        logo_row = ttk.Frame(frm)
        logo_row.grid(row=0, column=1, sticky="w", **pad)
        ttk.Button(logo_row, text="Chọn ảnh logo…", command=self._choose_logo).pack(side="left")
        self.logo_name = ttk.Label(logo_row, text="(chưa chọn)", foreground="#888")
        self.logo_name.pack(side="left", padx=8)

        self.logo_preview = ttk.Label(frm)
        self.logo_preview.grid(row=1, column=1, sticky="w", padx=12)

        ttk.Label(frm, text="Tên thương hiệu:").grid(row=2, column=0, sticky="w", **pad)
        self.name_var = tk.StringVar(value=self._brand.get("name", ""))
        ttk.Entry(frm, textvariable=self.name_var, width=42).grid(row=2, column=1, sticky="we", **pad)

        ttk.Label(frm, text="Số điện thoại:").grid(row=3, column=0, sticky="w", **pad)
        self.phone_var = tk.StringVar(value=self._brand.get("phone", ""))
        ttk.Entry(frm, textvariable=self.phone_var, width=42).grid(row=3, column=1, sticky="we", **pad)

        ttk.Label(frm, text="Zalo:").grid(row=4, column=0, sticky="w", **pad)
        self.zalo_var = tk.StringVar(value=self._brand.get("zalo", ""))
        ttk.Entry(frm, textvariable=self.zalo_var, width=42).grid(row=4, column=1, sticky="we", **pad)

        ttk.Label(frm, text="Địa chỉ:").grid(row=5, column=0, sticky="w", **pad)
        self.addr_var = tk.StringVar(value=self._brand.get("address", ""))
        ttk.Entry(frm, textvariable=self.addr_var, width=42).grid(row=5, column=1, sticky="we", **pad)

        btns = ttk.Frame(frm)
        btns.grid(row=6, column=0, columnspan=2, sticky="e", pady=(16, 0))
        ttk.Button(btns, text="Hủy", command=self.destroy).pack(side="right", padx=6)
        ttk.Button(btns, text="Lưu", style="Accent.TButton", command=self._save).pack(side="right")

        frm.columnconfigure(1, weight=1)
        self._refresh_logo_preview(self._brand.get("logo", ""))

    def _choose_logo(self):
        path = filedialog.askopenfilename(title="Chọn ảnh logo", filetypes=IMAGE_FILETYPES)
        if not path:
            return
        self._pending_logo = path
        self._refresh_logo_preview(path)

    def _refresh_logo_preview(self, path: str):
        photo = load_thumbnail(path, (260, 120))
        self._logo_preview = photo
        if photo is not None:
            self.logo_preview.configure(image=photo, text="")
            self.logo_name.configure(text=Path(path).name)
            return
        self.logo_preview.configure(image="")
        if path and Path(path).exists():
            self.logo_preview.configure(text=f"Đã chọn: {Path(path).name}")
            self.logo_name.configure(text=Path(path).name)
        else:
            self.logo_preview.configure(text="(chưa chọn)")
            self.logo_name.configure(text="(chưa chọn)")

    def _save(self):
        logo = self._brand.get("logo", "")
        if self._pending_logo:
            try:
                logo = import_image(self._pending_logo)
            except OSError as exc:
                messagebox.showerror("Lỗi", f"Không sao chép được logo:\n{exc}", parent=self)
                return
        self.result = {
            "name": self.name_var.get().strip(),
            "logo": logo,
            "phone": self.phone_var.get().strip(),
            "zalo": self.zalo_var.get().strip(),
            "address": self.addr_var.get().strip(),
        }
        self.destroy()


# ---------------------------------------------------------------------------
# Cửa sổ thêm / sửa món ăn
# ---------------------------------------------------------------------------
class DishDialog(tk.Toplevel):
    def __init__(self, master, dish: dict | None = None, default_category: str | None = None):
        super().__init__(master)
        self.title("Sửa món ăn" if dish else "Thêm món ăn")
        self.resizable(False, False)
        self.transient(master)
        self.result: dict | None = None

        self._dish = dict(dish) if dish else None
        self._pending_image: str | None = None
        self._image_preview: ImageTk.PhotoImage | None = None

        self._build(default_category)
        self.grab_set()
        center_over(self, master)
        self.wait_window(self)

    def _build(self, default_category: str | None):
        pad = {"padx": 12, "pady": 6}
        frm = ttk.Frame(self, padding=16)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="Tag / danh mục:").grid(row=0, column=0, sticky="w", **pad)
        labels = [label for _, label in config.CATEGORIES]
        self._label_to_key = {label: key for key, label in config.CATEGORIES}
        self._key_to_label = {key: label for key, label in config.CATEGORIES}
        if self._dish:  # khi sửa: giữ đúng tag hiện tại của món
            default_category = self._dish.get("category") or default_category
        self.cat_var = tk.StringVar(value=self._key_to_label[default_category or config.CATEGORY_KEYS[0]])
        ttk.Combobox(
            frm, textvariable=self.cat_var, values=labels, state="readonly", width=40
        ).grid(row=0, column=1, sticky="we", **pad)

        ttk.Label(frm, text="Tên món ăn:").grid(row=1, column=0, sticky="w", **pad)
        self.name_var = tk.StringVar(value=(self._dish or {}).get("name", ""))
        name_entry = ttk.Entry(frm, textvariable=self.name_var, width=42)
        name_entry.grid(row=1, column=1, sticky="we", **pad)

        ttk.Label(frm, text="Giá tiền:").grid(row=2, column=0, sticky="w", **pad)
        self.price_var = tk.StringVar(value=(self._dish or {}).get("price", ""))
        ttk.Entry(frm, textvariable=self.price_var, width=42).grid(row=2, column=1, sticky="we", **pad)
        ttk.Label(frm, text="Ví dụ: 50000  (sẽ tự hiển thị 50.000đ)", foreground="#888").grid(
            row=2, column=2, sticky="w"
        )

        ttk.Label(frm, text="Đơn vị tính:").grid(row=3, column=0, sticky="w", **pad)
        self.unit_var = tk.StringVar(value=(self._dish or {}).get("unit", ""))
        ttk.Entry(frm, textvariable=self.unit_var, width=42).grid(row=3, column=1, sticky="we", **pad)
        ttk.Label(frm, text="Ví dụ: phần, tô, ly, kg…", foreground="#888").grid(row=3, column=2, sticky="w")

        ttk.Label(frm, text="Ảnh món ăn:").grid(row=4, column=0, sticky="w", **pad)
        img_row = ttk.Frame(frm)
        img_row.grid(row=4, column=1, columnspan=2, sticky="we", **pad)
        ttk.Button(img_row, text="Chọn ảnh…", command=self._choose_image).pack(side="left")
        self.img_name = ttk.Label(img_row, text="(chưa chọn)", foreground="#888")
        self.img_name.pack(side="left", padx=8)

        self.image_preview = ttk.Label(frm)
        self.image_preview.grid(row=5, column=1, sticky="w", padx=12, pady=(4, 0))

        btns = ttk.Frame(frm)
        btns.grid(row=6, column=0, columnspan=3, sticky="e", pady=(16, 0))
        ttk.Button(btns, text="Hủy", command=self.destroy).pack(side="right", padx=6)
        ttk.Button(btns, text="Lưu", style="Accent.TButton", command=self._save).pack(side="right")

        frm.columnconfigure(1, weight=1)

        existing_image = (self._dish or {}).get("image", "")
        self._refresh_image_preview(existing_image)
        name_entry.focus_set()

    def _choose_image(self):
        path = filedialog.askopenfilename(title="Chọn ảnh món ăn", filetypes=IMAGE_FILETYPES)
        if not path:
            return
        self._pending_image = path
        self._refresh_image_preview(path)

    def _refresh_image_preview(self, path: str):
        photo = load_thumbnail(path, (240, 200))
        self._image_preview = photo
        if photo is not None:
            self.image_preview.configure(image=photo, text="")
            self.img_name.configure(text=Path(path).name)
            return
        self.image_preview.configure(image="")
        if path and Path(path).exists():
            self.image_preview.configure(text=f"Đã chọn: {Path(path).name}")
            self.img_name.configure(text=Path(path).name)
        else:
            self.image_preview.configure(text="(chưa chọn ảnh)")
            self.img_name.configure(text="(chưa chọn)")

    def _save(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập tên món ăn.", parent=self)
            return

        image = (self._dish or {}).get("image", "")
        if self._pending_image:
            try:
                image = import_image(self._pending_image)
            except OSError as exc:
                messagebox.showerror("Lỗi", f"Không sao chép được ảnh:\n{exc}", parent=self)
                return

        self.result = {
            "category": self._label_to_key[self.cat_var.get()],
            "name": name,
            "price": self.price_var.get().strip(),
            "unit": self.unit_var.get().strip(),
            "image": image,
        }
        self.destroy()


# ---------------------------------------------------------------------------
# Cửa sổ khôi phục từ bản sao lưu
# ---------------------------------------------------------------------------
class BackupDialog(tk.Toplevel):
    """Hiển thị danh sách bản sao lưu để người dùng chọn khôi phục."""

    def __init__(self, master, backups):
        super().__init__(master)
        self.title("Khôi phục dữ liệu từ bản sao lưu")
        self.transient(master)
        self.result = None
        self._backups = backups
        self._build()
        self.grab_set()
        center_over(self, master)
        self.wait_window(self)

    def _build(self):
        frm = ttk.Frame(self, padding=16)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="Chọn một bản sao lưu rồi bấm “Khôi phục”:").pack(anchor="w")
        self.listbox = tk.Listbox(frm, width=54, height=12, activestyle="dotbox")
        self.listbox.pack(fill="both", expand=True, pady=8)
        for _path, when, count in self._backups:
            self.listbox.insert("end", f"{when:%Y-%m-%d %H:%M:%S}    •    {count} món")
        if self._backups:
            self.listbox.selection_set(0)
        self.listbox.bind("<Double-Button-1>", lambda _e: self._restore())

        btns = ttk.Frame(frm)
        btns.pack(fill="x")
        ttk.Label(btns, text="Sao lưu tự động được tạo khi lưu dữ liệu.",
                  style="Sub.TLabel").pack(side="left")
        ttk.Button(btns, text="Đóng", command=self.destroy).pack(side="right", padx=4)
        ttk.Button(btns, text="Khôi phục", style="Accent.TButton",
                   command=self._restore).pack(side="right")

    def _restore(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn một bản sao lưu.", parent=self)
            return
        self.result = self._backups[sel[0]][0]
        self.destroy()


# ---------------------------------------------------------------------------
# Cửa sổ chính
# ---------------------------------------------------------------------------
class MenuMakerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(config.APP_TITLE)
        self.geometry("1080x720")
        self.minsize(940, 600)

        self.data = storage.load_data()
        self.current_cat = config.CATEGORY_KEYS[0]
        self._thumb_refs: list[ImageTk.PhotoImage] = []
        self._cat_buttons: dict[str, tk.Button] = {}
        self._note_after = None

        self._setup_style()
        self._build_ui()
        self._refresh_sidebar()
        self._render_dishes()

    # -- Giao diện ------------------------------------------------------
    def _setup_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Accent.TButton", background="#C64A28", foreground="white")
        style.map("Accent.TButton", background=[("active", "#A83C1F")])
        style.configure("Title.TLabel", font=("", 15, "bold"))
        style.configure("Sub.TLabel", foreground="#666")
        style.configure("DishName.TLabel", font=("", 12, "bold"))
        style.configure("Empty.TLabel", foreground="#999", font=("", 12))

    def _build_ui(self):
        toolbar = ttk.Frame(self, padding=(12, 10))
        toolbar.pack(fill="x")
        ttk.Label(toolbar, text="Menu Maker", style="Title.TLabel").pack(side="left")
        ttk.Button(toolbar, text="Khôi phục dữ liệu…", command=self.restore_backup).pack(
            side="left", padx=(12, 4)
        )
        ttk.Button(toolbar, text="Xuất tất cả menu", style="Accent.TButton",
                   command=self.export_all).pack(side="right", padx=4)
        ttk.Button(toolbar, text="Gộp tất cả menu", command=self.export_merged).pack(side="right", padx=4)
        ttk.Button(toolbar, text="Xuất mục đang chọn", command=self.export_current).pack(side="right", padx=4)
        ttk.Button(toolbar, text="Thông tin thương hiệu", command=self.edit_brand).pack(side="right", padx=4)

        # Ô nhập thông tin tùy chỉnh (gõ trực tiếp, không cần mở cửa sổ)
        note_frame = ttk.LabelFrame(
            self,
            text="Thông tin tùy chỉnh — hiển thị ở đầu menu (gõ trực tiếp vào đây)",
            padding=(10, 6),
        )
        note_frame.pack(fill="x", padx=12, pady=(0, 8))
        self.note_text = tk.Text(note_frame, height=3, wrap="word", font=("", 10),
                                 relief="solid", bd=1)
        self.note_text.pack(fill="x")
        self.note_text.insert("1.0", self.data["brand"].get("custom_info", ""))
        self.note_text.bind("<KeyRelease>", self._schedule_note_save)
        self.note_text.bind("<FocusOut>", lambda _e: self._save_note())

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # Sidebar
        sidebar = ttk.Frame(body, width=230)
        sidebar.pack(side="left", fill="y", padx=(0, 12))
        sidebar.pack_propagate(False)
        ttk.Label(sidebar, text="DANH MỤC", style="Sub.TLabel").pack(anchor="w", pady=(0, 6))
        for key, label in config.CATEGORIES:
            btn = tk.Button(
                sidebar, text=label, anchor="w", relief="flat", bd=0,
                padx=12, pady=10, cursor="hand2",
                command=lambda k=key: self.select_category(k),
            )
            btn.pack(fill="x", pady=2)
            self._cat_buttons[key] = btn

        self.brand_info = ttk.Label(sidebar, text="", style="Sub.TLabel", wraplength=210, justify="left")
        self.brand_info.pack(anchor="w", pady=(16, 0))

        # Khu vực danh sách món
        right = ttk.Frame(body)
        right.pack(side="left", fill="both", expand=True)

        head = ttk.Frame(right)
        head.pack(fill="x", pady=(0, 8))
        self.cat_title = ttk.Label(head, text="", style="Title.TLabel")
        self.cat_title.pack(side="left")
        ttk.Button(head, text="Thêm món", style="Accent.TButton",
                   command=self.add_dish).pack(side="right")

        self.list_frame = ScrollableFrame(right)
        self.list_frame.pack(fill="both", expand=True)

    # -- Dữ liệu --------------------------------------------------------
    def dishes_of(self, key: str) -> list[dict]:
        items = [d for d in self.data["dishes"] if d.get("category") == key]
        return sorted(items, key=lambda d: d.get("order", 0))

    def _next_order(self, key: str) -> int:
        orders = [d.get("order", 0) for d in self.data["dishes"] if d.get("category") == key]
        return (max(orders) + 1) if orders else 1

    def _reindex(self, key: str) -> None:
        for i, dish in enumerate(self.dishes_of(key), start=1):
            dish["order"] = i

    def _save(self):
        storage.save_data(self.data)

    def _schedule_note_save(self, _event=None):
        """Lưu thông tin tùy chỉnh sau khi người dùng ngừng gõ 0.6 giây."""
        if self._note_after is not None:
            self.after_cancel(self._note_after)
        self._note_after = self.after(600, self._save_note)

    def _save_note(self):
        if self._note_after is not None:
            try:
                self.after_cancel(self._note_after)
            except tk.TclError:
                pass
            self._note_after = None
        text = self.note_text.get("1.0", "end-1c")
        if text != self.data["brand"].get("custom_info", ""):
            self.data["brand"]["custom_info"] = text
            self._save()

    # -- Sidebar --------------------------------------------------------
    def _refresh_sidebar(self):
        for key, btn in self._cat_buttons.items():
            count = len(self.dishes_of(key))
            label = config.category_label(key)
            btn.configure(text=f"{label}  ({count})")
            if key == self.current_cat:
                btn.configure(bg="#C64A28", fg="white", activebackground="#A83C1F",
                              activeforeground="white")
            else:
                btn.configure(bg="#EDEDED", fg="#333", activebackground="#DDD", activeforeground="#333")

        brand = self.data.get("brand", {})
        info_lines = []
        if brand.get("name"):
            info_lines.append(brand["name"])
        if brand.get("phone"):
            info_lines.append(f"ĐT: {brand['phone']}")
        if brand.get("zalo"):
            info_lines.append(f"Zalo: {brand['zalo']}")
        if brand.get("address"):
            info_lines.append(brand["address"])
        self.brand_info.configure(text="\n".join(info_lines) if info_lines else "(chưa có thông tin thương hiệu)")

    def select_category(self, key: str):
        self.current_cat = key
        self._refresh_sidebar()
        self._render_dishes()

    # -- Danh sách món --------------------------------------------------
    def _render_dishes(self):
        self.list_frame.clear()
        self._thumb_refs = []
        self.cat_title.configure(text=config.category_label(self.current_cat))

        dishes = self.dishes_of(self.current_cat)
        if not dishes:
            ttk.Label(
                self.list_frame.inner,
                text="Chưa có món nào. Bấm “Thêm món” để bắt đầu.",
                style="Empty.TLabel",
            ).pack(pady=40)
            return

        for index, dish in enumerate(dishes):
            self._build_row(index, dish)

    def _build_row(self, index: int, dish: dict):
        row = tk.Frame(self.list_frame.inner, bg="white", highlightbackground="#EEE",
                       highlightthickness=1)
        row.pack(fill="x", pady=4)

        # Ảnh thu nhỏ dạng ô VUÔNG cố định
        has_img = bool(dish.get("image"))
        thumb = load_square_thumbnail(dish.get("image", ""), 92)
        thumb_box = tk.Frame(row, width=92, height=92, bg="#F6F3F0")
        thumb_box.pack(side="left", padx=8, pady=8)
        thumb_box.pack_propagate(False)
        thumb_lbl = tk.Label(thumb_box, bg="#F6F3F0")
        thumb_lbl.pack(fill="both", expand=True)
        if thumb is not None:
            self._thumb_refs.append(thumb)
            thumb_lbl.configure(image=thumb)
        else:
            thumb_lbl.configure(text="Ảnh" if has_img else "Không\nảnh", fg="#999")

        # Thông tin
        info = tk.Frame(row, bg="white")
        info.pack(side="left", fill="x", expand=True, padx=6)
        name_lbl = tk.Label(info, text=dish.get("name", ""), bg="white", anchor="w",
                            font=("", 12, "bold"))
        name_lbl.pack(fill="x", anchor="w")
        price_text = format_price(dish.get("price", ""), "")
        unit = dish.get("unit", "").strip()
        line2 = price_text + (f" / {unit}" if unit else "")
        price_lbl = tk.Label(info, text=line2, bg="white", anchor="w", fg="#C64A28")
        price_lbl.pack(fill="x", anchor="w")

        # Nút thao tác
        actions = tk.Frame(row, bg="white")
        actions.pack(side="right", padx=8)
        ttk.Button(actions, text="▲", width=3,
                   command=lambda d=dish: self.move_dish(d, -1)).pack(side="left", padx=2)
        ttk.Button(actions, text="▼", width=3,
                   command=lambda d=dish: self.move_dish(d, 1)).pack(side="left", padx=2)
        ttk.Button(actions, text="Sửa",
                   command=lambda d=dish: self.edit_dish(d)).pack(side="left", padx=2)
        ttk.Button(actions, text="Xóa",
                   command=lambda d=dish: self.delete_dish(d)).pack(side="left", padx=2)

        # Chuột phải: sửa / xóa / di chuyển nhanh
        menu = tk.Menu(row, tearoff=0)
        menu.add_command(label="Sửa món", command=lambda: self.edit_dish(dish))
        menu.add_command(label="Xóa món", command=lambda: self.delete_dish(dish))
        menu.add_separator()
        menu.add_command(label="Di chuyển lên", command=lambda: self.move_dish(dish, -1))
        menu.add_command(label="Di chuyển xuống", command=lambda: self.move_dish(dish, 1))

        def popup(event):
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()

        for widget in (row, thumb_box, thumb_lbl, info, name_lbl, price_lbl):
            widget.bind("<Button-3>", popup)

    # -- Thao tác món ---------------------------------------------------
    def add_dish(self):
        dlg = DishDialog(self, default_category=self.current_cat)
        if not dlg.result:
            return
        result = dlg.result
        dish = {
            "id": uuid.uuid4().hex,
            "category": result["category"],
            "name": result["name"],
            "price": result["price"],
            "unit": result["unit"],
            "image": result["image"],
            "order": self._next_order(result["category"]),
        }
        self.data["dishes"].append(dish)
        self._reindex(result["category"])
        self._save()
        self.current_cat = result["category"]
        self._refresh_sidebar()
        self._render_dishes()

    def edit_dish(self, dish: dict):
        dlg = DishDialog(self, dish=dish)
        if not dlg.result:
            return
        old_cat = dish.get("category")
        result = dlg.result
        dish.update({
            "category": result["category"],
            "name": result["name"],
            "price": result["price"],
            "unit": result["unit"],
            "image": result["image"],
        })
        if result["category"] != old_cat:
            dish["order"] = self._next_order(result["category"])
        self._reindex(old_cat)
        self._reindex(result["category"])
        self._save()
        self._refresh_sidebar()
        self._render_dishes()

    def delete_dish(self, dish: dict):
        if not messagebox.askyesno("Xóa món", f"Xóa món “{dish.get('name', '')}”?", parent=self):
            return
        self.data["dishes"] = [d for d in self.data["dishes"] if d.get("id") != dish.get("id")]
        # Xóa ảnh đã sao chép nếu nằm trong thư mục dữ liệu
        img = dish.get("image", "")
        if img:
            try:
                p = Path(img).resolve()
                if p.is_relative_to(config.IMAGE_DIR.resolve()) and p.exists():
                    p.unlink()
            except (OSError, ValueError):
                pass
        self._reindex(dish.get("category"))
        self._save()
        self._refresh_sidebar()
        self._render_dishes()

    def move_dish(self, dish: dict, delta: int):
        key = dish.get("category")
        siblings = self.dishes_of(key)
        try:
            i = siblings.index(dish)
        except ValueError:
            return
        j = i + delta
        if j < 0 or j >= len(siblings):
            return
        siblings[i], siblings[j] = siblings[j], siblings[i]
        for order, d in enumerate(siblings, start=1):
            d["order"] = order
        self._save()
        self._render_dishes()

    # -- Thương hiệu ----------------------------------------------------
    def edit_brand(self):
        dlg = BrandDialog(self, self.data.get("brand", {}))
        if dlg.result is None:
            return
        # giữ lại custom_info (được nhập trực tiếp trên cửa sổ chính)
        self.data.setdefault("brand", {}).update(dlg.result)
        self._save()
        self._refresh_sidebar()

    # -- Khôi phục từ sao lưu -------------------------------------------
    def restore_backup(self):
        backups = storage.list_backups()
        if not backups:
            messagebox.showinfo(
                "Chưa có bản sao lưu",
                "Chưa có bản sao lưu nào.\n\n"
                "Bản sao lưu được tạo tự động khi bạn lưu dữ liệu\n"
                "(nằm trong thư mục “backups” cạnh chương trình).",
                parent=self,
            )
            return

        dlg = BackupDialog(self, backups)
        if not dlg.result:
            return
        if not messagebox.askyesno(
            "Khôi phục dữ liệu",
            "Ghi đè dữ liệu hiện tại bằng bản sao lưu đã chọn?\n\n"
            "Bản hiện tại cũng sẽ được sao lưu lại trước khi ghi đè.",
            parent=self,
        ):
            return

        try:
            self.data = storage.restore_backup(dlg.result)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Lỗi khôi phục", str(exc), parent=self)
            return

        self.note_text.delete("1.0", "end")
        self.note_text.insert("1.0", self.data["brand"].get("custom_info", ""))
        self._refresh_sidebar()
        self._render_dishes()
        messagebox.showinfo("Đã khôi phục", "Dữ liệu đã được khôi phục từ bản sao lưu.",
                            parent=self)

    # -- Xuất menu ------------------------------------------------------
    def _prepare_export_dir(self) -> Path:
        config.DEFAULT_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        return config.DEFAULT_EXPORT_DIR

    def export_all(self):
        cats = [k for k in config.CATEGORY_KEYS if self.dishes_of(k)]
        if not cats:
            messagebox.showinfo("Chưa có dữ liệu", "Bạn chưa thêm món ăn nào.", parent=self)
            return
        self._do_export(cats)

    def export_current(self):
        dishes = self.dishes_of(self.current_cat)
        if not dishes:
            messagebox.showinfo("Chưa có dữ liệu",
                                f"Mục “{config.category_label(self.current_cat)}” chưa có món nào.",
                                parent=self)
            return
        self._do_export([self.current_cat])

    def export_merged(self):
        """Gộp tất cả tag (có món) vào MỘT ảnh: header trên cùng, mỗi tag một cột."""
        cats = [(k, self.dishes_of(k)) for k in config.CATEGORY_KEYS if self.dishes_of(k)]
        if not cats:
            messagebox.showinfo("Chưa có dữ liệu", "Bạn chưa thêm món ăn nào.", parent=self)
            return

        config.DEFAULT_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        out = filedialog.asksaveasfilename(
            title="Lưu menu gộp",
            defaultextension=".png",
            initialdir=str(config.DEFAULT_EXPORT_DIR),
            initialfile="menu_tong_hop.png",
            filetypes=[("Ảnh PNG", "*.png"), ("Tất cả tệp", "*.*")],
        )
        if not out:
            return

        brand = self.data.get("brand", {})
        try:
            render_merged_menu(cats, brand, out)
        except Exception as exc:  # noqa: BLE001 - báo lỗi cho người dùng
            messagebox.showerror("Lỗi xuất menu gộp", str(exc), parent=self)
            return

        if messagebox.askyesno(
            "Xuất thành công",
            f"Đã tạo menu gộp từ {len(cats)} tag:\n{Path(out).name}\n\nMở thư mục chứa file?",
            parent=self,
        ):
            open_folder(Path(out).parent)

    def _do_export(self, cats: list[str]):
        folder = filedialog.askdirectory(
            title="Chọn thư mục lưu menu",
            initialdir=str(self._prepare_export_dir()),
        )
        if not folder:
            return
        folder_path = Path(folder)
        brand = self.data.get("brand", {})
        written = []
        errors = []
        for key in cats:
            out = folder_path / f"menu_{key}.png"
            try:
                render_menu(key, self.dishes_of(key), brand, out)
                written.append(out)
            except Exception as exc:  # noqa: BLE001 - báo lỗi cho người dùng
                errors.append(f"{config.category_label(key)}: {exc}")
        self._refresh_sidebar()

        if errors:
            messagebox.showerror("Có lỗi khi xuất", "\n".join(errors), parent=self)
        if written:
            listing = "\n".join(f"• {p.name}" for p in written)
            if messagebox.askyesno(
                "Xuất thành công",
                f"Đã xuất {len(written)} file menu:\n{listing}\n\nMở thư mục chứa file?",
                parent=self,
            ):
                open_folder(folder_path)


def run():
    app = MenuMakerApp()
    if not HAVE_IMAGETK:
        app.after(400, lambda: messagebox.showwarning(
            "Thiếu thành phần hiển thị ảnh",
            "Không tìm thấy PIL.ImageTk nên ảnh thu nhỏ tạm thời bị ẩn.\n\n"
            "Để hiển thị ảnh trong ứng dụng, hãy cài đặt một trong hai cách:\n"
            "  • Ubuntu/Debian:  sudo apt install python3-pil.imagetk\n"
            "  • Dùng venv:      python3 -m venv .venv\n"
            "                    .venv/bin/pip install -r requirements.txt\n\n"
            "Lưu ý: chức năng xuất menu ra ảnh PNG vẫn hoạt động bình thường.",
            parent=app,
        ))
    app.mainloop()
