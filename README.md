# 🍜 Menu Maker

Ứng dụng Python (Tkinter + Pillow) tạo **menu món ăn** và xuất ra **ảnh PNG độ phân giải cao**.

- Chiều rộng ảnh **cố định 1080px**, chiều cao **tự giãn** theo số lượng món.
- **Mỗi tag xuất thành một file menu riêng**: `menu_mon_chinh.png`, `menu_mon_nuoc.png`, `menu_an_kem.png`, `menu_dong_lanh.png`.
- Bố cục bảng món **3 cột cố định** (tên món • giá/đơn vị tính • ảnh) nên **không bao giờ lệch hàng hay lệch cột**.

## Tính năng

| Nhóm | Chi tiết |
|------|----------|
| Tag món ăn | Món chính, Món nước, Món ăn kèm, Món bảo quản đông lạnh |
| Thêm món | Cửa sổ riêng: chọn tag, tên món, giá tiền, đơn vị tính, chọn ảnh từ máy |
| Ảnh món | Tự cắt thành **ô vuông cố định**, phóng lấp đầy và **căn giữa tâm ảnh** (mọi kích cỡ ảnh đều ra một cỡ vuông) |
| Quản lý | Sửa, xóa (nút **Xóa** hoặc **chuột phải**), di chuyển món lên/xuống theo ý muốn |
| Thương hiệu | Cửa sổ riêng: logo (import ảnh), tên thương hiệu, SĐT, Zalo, địa chỉ |
| Thông tin tùy chỉnh | Ô nhập trực tiếp trên cửa sổ chính (nhiều dòng, tự lưu), in ở đầu menu |
| Xuất ảnh | PNG 1080px, tự động căn lề, bo góc ảnh, có thanh màu nhấn |
| Sao lưu | Tự động sao lưu ra `backups/` (ngoài `data/`) + nút **Khôi phục dữ liệu** |
| Lưu trữ | Tự động lưu vào `data/data.json`; ảnh được sao chép vào `data/images/` |

## Cài đặt

### Cách 1 — Dùng venv (khuyến nghị, đầy đủ tính năng)

```bash
cd menu_maker
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

> Trên Windows: `.venv\Scripts\pip install -r requirements.txt`

### Cách 2 — Dùng Python hệ thống

```bash
pip install -r requirements.txt
# Trên Ubuntu/Debian, cần thêm gói hiển thị ảnh:
sudo apt install python3-pil.imagetk
```

> Nếu thiếu `PIL.ImageTk`, ứng dụng vẫn chạy và **xuất menu bình thường**, chỉ tạm ẩn ảnh thu nhỏ trong giao diện.

## Chạy ứng dụng

```bash
python3 app.py            # cách 1
# hoặc
.venv/bin/python app.py   # nếu dùng venv
# hoặc
./run.sh
```

## Hướng dẫn sử dụng

1. Bấm **Thông tin thương hiệu** để nhập logo, tên, SĐT/Zalo, địa chỉ (nhập 1 lần).
2. Gõ thêm **thông tin tùy chỉnh** vào ô ở đầu cửa sổ (giờ mở cửa, fanpage, ghi chú…). Nội dung tự lưu và in ở đầu menu.
3. Chọn tag ở cột bên trái → bấm **Thêm món**.
4. Trong cửa sổ hiện ra: chọn tag, nhập tên món, giá, đơn vị tính, chọn ảnh từ máy → **Lưu**.
5. Dùng nút **▲ ▼** để sắp xếp thứ tự. Bấm **Sửa** / **Xóa** (hoặc **chuột phải** vào món) để chỉnh.
6. Bấm **Xuất tất cả menu** (hoặc **Xuất mục đang chọn**) → chọn thư mục lưu.

Kết quả: mỗi tag có món sẽ tạo một file PNG 1080px.

## Đóng gói thành file .exe (Windows)

> **Quan trọng:** PyInstaller **không thể** tạo file `.exe` Windows từ Linux/macOS.
> Bước build phải chạy **trên máy Windows**.

**Cách làm (1 cú nháy đúp):**

1. Cài Python 3.10+ cho Windows từ https://www.python.org/downloads/
   (nhớ **tick “Add python.exe to PATH”** khi cài).
2. Nháy đúp file **`build_exe.bat`** trong thư mục dự án.
3. Chờ vài phút. Xong sẽ có: **`dist\MenuMaker.exe`** (một file duy nhất).

**Lưu ý khi dùng:**

- Copy `MenuMaker.exe` đi đâu cũng chạy. Lần đầu chạy, chương trình tự tạo thư mục
  `data\` **ngay cạnh file exe** để lưu món ăn và ảnh.
- Nên đặt exe ở thư mục thường (Desktop, Documents…), **tránh `Program Files`** để
  không bị chặn quyền ghi.
- Lần đầu chạy, Windows có thể hiện cảnh báo SmartScreen → bấm **More info → Run anyway**.
- Nếu app không mở, sửa `--windowed` thành `--console` trong `build_exe.bat` rồi build lại
  để xem thông báo lỗi.

**Trên Linux/macOS:** chạy `./build_exe.sh` → tạo `dist/MenuMaker`.

## Sao lưu & khôi phục dữ liệu

- Mỗi khi lưu, app tự tạo bản sao lưu `data.json` (tối thiểu 2 phút/lần), giữ tối đa 30 bản.
- Các bản sao lưu nằm ở thư mục **`backups/`** — **nằm ngoài** `data/`, nên nếu lỡ xóa
  `data/` thì bản sao lưu vẫn còn.
- Muốn khôi phục: bấm nút **Khôi phục dữ liệu…** trên thanh công cụ → chọn thời điểm → Khôi phục.
  (Bản đang dùng cũng được sao lưu lại trước khi ghi đè, nên thao tác này hoàn tác được.)

## Bố cục ảnh xuất ra

```
┌──────────────────────────────────────────────┐  ← thanh màu nhấn
│                  [ LOGO ]                     │
│            TÊN THƯƠNG HIỆU (giữa)              │
│        ĐT …  •  Zalo …                          │
│        Địa chỉ: …                              │
│        (thông tin tùy chỉnh nhiều dòng)        │
│ ══════════════════════════════════════════════ │  ← đường kẻ nhấn
│              MÓN CHÍNH (tiêu đề tag)          │
│                                                │
│  Phở bò tái nạm      [ 50.000đ ]  [ ảnh món ] │
│                       [  phần   ]             │
│ ────────────────────────────────────────────── │
│  Bún chả Hà Nội       [ 60.000đ ]  [ ảnh món ] │
│                       [  suất   ]             │
│                                                │
└──────────────────────────────────────────────┘  ← thanh màu nhấn
```

- 3 cột có tọa độ **cố định**: tên món (x=48), giá (x=455), ảnh (x=712).
- Mọi hàng cùng chiều cao 320px → ảnh và chữ luôn thẳng hàng.
- Ảnh món luôn được **cắt thành ô vuông 284×284px**: phóng lấp đầy rồi lấy **tâm ảnh làm chính giữa**, nên ảnh dọc/ngang/vuông đều ra cùng một cỡ.

## Tùy chỉnh giao diện / bố cục

Mở `menumaker/config.py` để đổi màu sắc, kích thước chữ, kích thước ảnh, số cột… Ví dụ:

```python
ACCENT_COLOR = (198, 74, 40)   # màu nhấn
IMAGE_BOX = (300, 300)         # khung ảnh (ô vuông) — đổi để tăng/giảm cỡ ảnh
ROW_HEIGHT = 320               # chiều cao hàng
COL_NAME_W = 360               # độ rộng cột tên món
```

## Cấu trúc dự án

```
menu_maker/
├── app.py                 # điểm khởi chạy
├── run.sh                 # chạy nhanh (Linux/macOS)
├── build_exe.bat          # build ra .exe (chạy trên Windows)
├── build_exe.sh           # build cho Linux/macOS
├── requirements.txt
├── menumaker/
│   ├── config.py          # hằng số cấu hình + bố cục ảnh
│   ├── storage.py         # đọc/ghi data.json + sao lưu tự động
│   ├── fonts.py           # tìm font hỗ trợ tiếng Việt
│   ├── exporter.py        # render ảnh menu bằng Pillow
│   └── ui.py              # giao diện Tkinter
├── data/                  # (tự tạo) dữ liệu + ảnh đã import
├── backups/               # (tự tạo) các bản sao lưu data.json
└── exports/               # (tự tạo) menu xuất ra
```
