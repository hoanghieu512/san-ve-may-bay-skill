# -*- coding: utf-8 -*-
"""Chọn chuyến: dùng chung cho merge_sources.py (danh sách cần xác nhận nơi mua)
và build_workbook.py (Block C). Một chỗ duy nhất để hai bên không chọn lệch nhau.

Mọi lựa chọn chạy theo Giá chốt = giá của nguồn đầu tiên có số theo thứ tự
`meta.nguon` (SKILL.md §8). Hoà giá thì lấy chuyến đứng trước trong `chuyen`
(checkpoint đã sắp theo giờ khởi hành), để kết quả không đổi giữa các lần chạy.
"""

# Số chuyến rẻ nhất mỗi chiều đưa vào danh sách xác nhận, ngoài các chuyến của Block C.
TOP_MOI_CHIEU = 3


def gia_chot(f, nguon):
    """Giá theo thứ tự ưu tiên nguồn, hoặc None nếu không nguồn nào có số."""
    for s in nguon:
        v = f.get('gia', {}).get(s)
        if v is not None:
            return v
    return None


def tot_nhat(chuyen, nguon, hang=None):
    """-> (chỉ số trong chuyen, Giá chốt, chuyến) rẻ nhất, hoặc None."""
    b = None
    for i, f in enumerate(chuyen):
        if hang and f['hang'] != hang:
            continue
        v = gia_chot(f, nguon)
        if v is None:
            continue
        if b is None or v < b[1]:
            b = (i, v, f)
    return b


def phuong_an(cap, nguon):
    """Các phương án ghép của Block C: [(tên, A, B, ghi chú)], A/B dạng tot_nhat()."""
    di, ve = cap['di']['chuyen'], cap['ve']['chuyen']
    out = []
    a, b = tot_nhat(di, nguon), tot_nhat(ve, nguon)
    if a and b:
        out.append(("Rẻ nhất", a, b,
                    "Chiều đi rẻ nhất + chiều về rẻ nhất (không cần cùng hãng)"))
    same = None
    for h in sorted({f['hang'] for f in di} & {f['hang'] for f in ve}):
        x, y = tot_nhat(di, nguon, h), tot_nhat(ve, nguon, h)
        if x and y and (same is None or x[1] + y[1] < same[0]):
            same = (x[1] + y[1], h, x, y)
    if same:
        out.append(("Cùng hãng rẻ nhất", same[2], same[3],
                    "Hai chặng cùng %s, tiện đổi/hoãn vé" % same[1]))
    return out


def de_xuat(cap, nguon, top=TOP_MOI_CHIEU):
    """-> {'di': {chỉ số: [lý do]}, 've': {...}}: các chuyến cần xác nhận nơi mua."""
    out = {'di': {}, 've': {}}
    for ten, a, b, _ in phuong_an(cap, nguon):
        out['di'].setdefault(a[0], []).append(ten)
        out['ve'].setdefault(b[0], []).append(ten)
    for leg in ('di', 've'):
        co_gia = [(gia_chot(f, nguon), i) for i, f in enumerate(cap[leg]['chuyen'])
                  if gia_chot(f, nguon) is not None]
        for _, i in sorted(co_gia)[:top]:
            out[leg].setdefault(i, []).append('Top %d rẻ nhất chiều' % top)
    return out
