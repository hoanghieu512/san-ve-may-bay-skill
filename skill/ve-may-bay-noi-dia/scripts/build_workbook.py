#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dựng workbook so sánh giá vé từ checkpoint JSON.

    python3 build_workbook.py checkpoint.json output.xlsx

4 sheet: Summary (mỗi cặp một dòng, có nơi mua + link từng chiều), Mua vé (người bán
của từng chuyến đề xuất), Data (mọi chuyến, mọi nguồn), Log.
Số cột giá sinh động theo meta.nguon (cũng là thứ tự ưu tiên của Giá chốt).
Cột 'Chênh lệch max %' chỉ xuất hiện khi có >= 2 nguồn.
Sau khi chạy: recalc.py, rồi verify_workbook.py. Xem SKILL.md §8.
"""
import json, os, sys, datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.formatting.rule import FormulaRule
from openpyxl.utils import get_column_letter as L

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shortlist  # noqa: E402

NA, MONEY, AR = "Không khả dụng", '#,##0 "₫"', 'Arial'
CHUA_XN = "Chưa xác nhận"
# Lệch >= mức này giữa hai nguồn cho cùng một chuyến -> tô cam. Trùng với
# NGUONG_DIEU_TRA của merge_sources.py và ngưỡng bắt buộc điều tra ở SKILL.md §6.
NGUONG_DIEU_TRA = 0.25
# Nguồn chỉ so giá, không bán vé: không đưa vào danh sách người bán ở sheet Mua vé.
METASEARCH = {'Google Flights'}
F_TITLE = Font(name=AR, size=14, bold=True)
F_GRP   = Font(name=AR, size=11, bold=True, color='FFFFFF')
F_HDR   = Font(name=AR, size=10, bold=True)
F_B     = Font(name=AR, size=10)
F_BB    = Font(name=AR, size=10, bold=True)
F_NOTE  = Font(name=AR, size=9, italic=True, color='666666')
F_LINK  = Font(name=AR, size=9, color='0563C1', underline='single')
F_WARN  = Font(name=AR, size=10, color='C00000')
FI_GRP  = PatternFill('solid', fgColor='1F4E79')
FI_HDR  = PatternFill('solid', fgColor='DDEBF7')
FI_BLK  = PatternFill('solid', fgColor='FCE4D6')
FI_YEL  = PatternFill('solid', fgColor='FFF200')
FI_WARN = PatternFill('solid', fgColor='FFC000')
FI_GRN  = PatternFill('solid', fgColor='C6EFCE')
_t = Side(style='thin', color='BFBFBF')
BD = Border(left=_t, right=_t, top=_t, bottom=_t)
CEN = Alignment(horizontal='center', vertical='center', wrap_text=True)
TOP = Alignment(wrap_text=True, vertical='top')


def hhmm(s):
    h, m = s.split(':')
    return datetime.time(int(h), int(m))


def header(ws, r, names):
    for i, h in enumerate(names, 1):
        c = ws.cell(r, i, h); c.font = F_HDR; c.fill = FI_HDR; c.border = BD; c.alignment = CEN


def link(ws, r, col, url, text=None):
    c = ws.cell(r, col, (text or url) if url else NA)
    if url:
        c.hyperlink = url; c.font = F_LINK
    else:
        c.font = F_B
    return c


def lech(f):
    v = [x for x in f.get('gia', {}).values() if x is not None]
    return max(v) / min(v) - 1 if len(v) >= 2 else 0


def nguoi_ban(f, chang, SRC, meta):
    """Mọi nơi bán đã thấy cho một chuyến, rẻ trước. Mỗi dòng: dict.
    Nguồn 1: trang đặt vé Google Flights (bước xác nhận). Nguồn 2: nguồn quét trực tiếp
    là người bán (Traveloka), giá lúc quét."""
    rows = []
    m = f.get('mua') or {}
    if m.get('trang_thai') == 'OK':
        for b in m.get('ban', []):
            if b.get('gia') is None:
                continue
            rows.append(dict(ten=b['nguoi_ban'], loai=b['loai'], gia=b['gia'],
                             ghi_chu=b.get('ghi_chu', ''), hanh_ly='; '.join(m.get('hanh_ly') or []),
                             url=m.get('url', ''), luc=m.get('luc', ''),
                             nguon='Trang đặt vé Google Flights'))
    for s in SRC:
        if s in METASEARCH or f.get('gia', {}).get(s) is None:
            continue
        rows.append(dict(ten=s, loai='Đại lý', gia=f['gia'][s], ghi_chu='', hanh_ly='',
                         url=chang.get('link', {}).get(s, ''),
                         luc=chang.get('thu_thap', {}).get(s, meta['thu_thap']),
                         nguon='Quét trực tiếp %s' % s))
    return sorted(rows, key=lambda x: x['gia'])


def ten_ban(b):
    return '%s (%s)' % (b['ten'], 'hãng' if b['loai'] == 'Hãng hàng không' else 'đại lý')


def build(cp, out):
    meta = cp['meta']
    SRC = meta['nguon']                       # thứ tự = thứ tự ưu tiên
    n = len(SRC)
    hdr = ["Cặp ngày", "Ngày bay", "Số hiệu chuyến", "Hãng", "Giờ khởi hành", "Giờ hạ cánh"]
    hdr += ["Giá %s (1 người lớn)" % s for s in SRC]
    c_src0, c_src1 = 7, 6 + n                 # dải cột giá
    c_chot = c_src1 + 1
    hdr.append("Giá chốt (nguồn ưu tiên)")
    c_min = c_nmin = c_diff = 0
    if n >= 2:
        c_min = c_chot + 1; hdr.append("Giá thấp nhất (mọi nguồn)")
        c_nmin = c_min + 1; hdr.append("Nguồn giá thấp nhất")
        c_diff = c_nmin + 1; hdr.append("Chênh lệch max %")
    c_fl   = len(hdr) + 1; hdr.append("Link chuyến này (trang đặt vé)")
    c_link = len(hdr) + 1; hdr.append("Link tìm kiếm của nguồn Giá chốt")
    c_ts   = len(hdr) + 1; hdr.append("Thời điểm thu thập")
    NC = len(hdr)
    HDR_C = ["Loại phương án", "Chuyến đi (số hiệu + giờ)", "Giá đi",
             "Chuyến về (số hiệu + giờ)", "Giá về", "Tổng theo Giá chốt"]
    if c_min:
        HDR_C.append("Tổng theo giá thấp nhất")
    HDR_C.append("Ghi chú")
    NC_C = len(HDR_C)
    c_tmin, c_ghi = (7, 8) if c_min else (0, 7)

    wb = Workbook()
    s2 = wb.active; s2.title = "Summary"
    s4 = wb.create_sheet("Mua vé")
    ws = wb.create_sheet("Data")
    s3 = wb.create_sheet("Log")

    # ---------------- Data ----------------
    ws['A1'] = "%s: %s, %s, %s" % (meta['chang'], meta['khach'], meta['hang_ve'], meta['loai'])
    ws['A1'].font = F_TITLE
    ws['A2'] = ("Thu thập: %s. Nguồn: %s. Khung giờ đi %s, về %s. Giá cho 1 người lớn, đã gồm thuế phí "
                "bắt buộc. Giá vé thay đổi liên tục: bảng này là ảnh chụp một thời điểm, không phải giá "
                "bảo đảm. Giá chốt = giá của nguồn đầu tiên có số theo thứ tự ưu tiên, KHÔNG phải giá thấp "
                "nhất. Ô vàng = rẻ nhất trong chiều. Ô cam = hai nguồn lệch >=%d%%, số đáng ngờ: đọc sheet "
                "Log trước khi tin. Muốn mua: xem sheet Summary và Mua vé."
                % (meta['thu_thap'], ", ".join(SRC),
                   meta.get('khung_di', 'không lọc'), meta.get('khung_ve', 'không lọc'),
                   NGUONG_DIEU_TRA * 100))
    ws['A2'].font = F_NOTE

    r, first_hdr, cf, summary = 4, None, [], []
    for P in cp['caps']:
        ws.cell(r, 1, "%s: %s → %s (%s)" % (P['ten'], P['ngay_di'], P['ngay_ve'], P.get('thu', '')))
        for c in range(1, NC + 1):
            ws.cell(r, c).fill = FI_GRP; ws.cell(r, c).font = F_GRP
        r += 1
        blk = {}
        for leg, lbl, day in (('di', 'BLOCK A: Chuyến đi, khởi hành %s' % meta.get('khung_di', 'cả ngày'), P['ngay_di']),
                              ('ve', 'BLOCK B: Chuyến về, khởi hành %s' % meta.get('khung_ve', 'cả ngày'), P['ngay_ve'])):
            ws.cell(r, 1, lbl).font = F_HDR
            for c in range(1, NC + 1): ws.cell(r, c).fill = FI_BLK
            r += 1
            if first_hdr is None: first_hdr = r
            header(ws, r, hdr)
            r += 1
            start = r
            links = P[leg].get('link', {})
            gio = P[leg].get('thu_thap', {})
            for f in P[leg]['chuyen']:
                ws.cell(r, 1, P['ten']).font = F_B
                ws.cell(r, 2, day).font = F_B
                ws.cell(r, 3, f.get('sh') or '-').font = F_B
                ws.cell(r, 4, f['hang']).font = F_B
                for col, v in ((5, f['dep']), (6, f['arr'])):
                    cc = ws.cell(r, col, hhmm(v) if v else NA); cc.number_format = 'hh:mm'
                    cc.font = F_B; cc.alignment = Alignment(horizontal='center')
                first_src = None
                for k, s in enumerate(SRC):
                    cc = ws.cell(r, 7 + k)
                    if f.get('gia', {}).get(s) is not None:
                        cc.value = f['gia'][s]; cc.number_format = MONEY
                        if first_src is None: first_src = s
                    else:
                        cc.value = NA
                    cc.font = F_B
                expr = '"%s"' % NA
                for k in range(n - 1, -1, -1):
                    col = L(7 + k)
                    expr = 'IF(ISNUMBER({c}{r}),{c}{r},{e})'.format(c=col, r=r, e=expr)
                cc = ws.cell(r, c_chot, '=' + expr); cc.number_format = MONEY; cc.font = F_BB
                if c_min:
                    cc = ws.cell(r, c_min, '=IF(COUNT({a}{r}:{b}{r})=0,"{na}",MIN({a}{r}:{b}{r}))'
                                 .format(a=L(c_src0), b=L(c_src1), r=r, na=NA))
                    cc.number_format = MONEY; cc.font = F_B
                    g = {s: v for s, v in f.get('gia', {}).items() if v is not None}
                    lo = min(g.values()) if g else None
                    ws.cell(r, c_nmin, ", ".join(s for s in SRC if g.get(s) == lo) if g else NA).font = F_B
                if c_diff:
                    cc = ws.cell(r, c_diff, '=IFERROR((MAX({a}{r}:{b}{r})-MIN({a}{r}:{b}{r}))/MIN({a}{r}:{b}{r}),"")'
                                 .format(a=L(c_src0), b=L(c_src1), r=r))
                    cc.number_format = '0.0%'; cc.font = F_B
                if f.get('link_chuyen'):
                    link(ws, r, c_fl, f['link_chuyen'], "Mở trang đặt vé %s" % f['sh'])
                else:
                    ws.cell(r, c_fl, "Chưa có số hiệu").font = F_B
                link(ws, r, c_link, links.get(first_src or (SRC[0] if SRC else ''), ''))
                ws.cell(r, c_ts, gio.get(first_src, meta['thu_thap'])).font = F_B
                for c in range(1, NC + 1): ws.cell(r, c).border = BD
                r += 1
            blk[leg] = (start, r - 1)
            cf.append((start, r - 1))
            r += 1

        # ---- Block C ----
        ws.cell(r, 1, 'BLOCK C: Phương án ghép').font = F_HDR
        for c in range(1, NC_C + 1): ws.cell(r, c).fill = FI_BLK
        r += 1
        header(ws, r, HDR_C)
        r += 1
        for name, A, B, note in shortlist.phuong_an(P, SRC):
            ra, rb = blk['di'][0] + A[0], blk['ve'][0] + B[0]
            ws.cell(r, 1, name).font = F_BB
            for col, x in ((2, ra), (4, rb)):
                ws.cell(r, col, '=C{0}&" "&TEXT(E{0},"hh:mm")'.format(x)).font = F_B
            for col, x in ((3, ra), (5, rb)):
                cc = ws.cell(r, col, '=%s%d' % (L(c_chot), x)); cc.number_format = MONEY; cc.font = F_B
            cc = ws.cell(r, 6, '=C{0}+E{0}'.format(r)); cc.number_format = MONEY; cc.font = F_BB
            if c_tmin:
                cc = ws.cell(r, c_tmin, '={m}{a}+{m}{b}'.format(m=L(c_min), a=ra, b=rb))
                cc.number_format = MONEY; cc.font = F_B
            ws.cell(r, c_ghi, note).font = F_B
            for c in range(1, NC_C + 1): ws.cell(r, c).border = BD
            if name == "Rẻ nhất":
                summary.append(dict(P=P, row=r, A=A, B=B))
            r += 1
        ws.cell(r, 1, "Vé nội địa VN không có discount khứ hồi: tổng = đi + về.").font = F_NOTE
        r += 2

    for s, e in cf:
        if e < s:
            continue
        ws.conditional_formatting.add(
            "{c}{s}:{c}{e}".format(c=L(c_chot), s=s, e=e),
            FormulaRule(formula=['AND(ISNUMBER(${c}{s}),${c}{s}=MIN(${c}${s}:${c}${e}))'
                                 .format(c=L(c_chot), s=s, e=e)], fill=FI_YEL, stopIfTrue=False))
        if c_diff:
            # Lệch lớn giữa hai nguồn = dữ liệu đáng ngờ, không phải giá đáng tin.
            # Tô cả dải giá + Giá chốt của dòng đó để không đọc nhầm thành giá thật.
            ws.conditional_formatting.add(
                "{a}{s}:{d}{e}".format(a=L(c_src0), d=L(c_diff), s=s, e=e),
                FormulaRule(formula=['AND(ISNUMBER(${c}{s}),${c}{s}>={t})'
                                     .format(c=L(c_diff), s=s, t=NGUONG_DIEU_TRA)],
                            fill=FI_WARN, stopIfTrue=False))
    ws.conditional_formatting.add("A4:%s%d" % (L(NC_C), r),
        FormulaRule(formula=['$A4="Rẻ nhất"'], fill=FI_YEL, stopIfTrue=False))
    ws.freeze_panes = "A4"
    if first_hdr: ws.auto_filter.ref = "A%d:%s%d" % (first_hdr, L(NC), r)
    for i, w in enumerate([10, 12, 14, 20, 13, 13] + [18] * n + [18]
                          + ([18, 18, 14] if c_diff else []) + [24, 42, 22], 1):
        ws.column_dimensions[L(i)].width = w

    # ---------------- Summary ----------------
    H2 = ["Cặp ngày", "Thứ (đi → về)", "Chuyến đi", "Chuyến về", "Tổng theo Giá chốt"]
    if c_min: H2.append("Tổng theo giá thấp nhất")
    H2 += ["Tổng mua được rẻ nhất", "Nơi mua rẻ nhất (đi / về)", "Tổng nếu mua thẳng từ hãng",
           "Link chuyến đi", "Link chuyến về", "Nguồn Giá chốt (đi / về)", "Cảnh báo"]
    col2 = {h: i for i, h in enumerate(H2, 1)}
    NC2 = len(H2)
    s2['A1'] = "%s: tóm tắt %d cặp ngày, giá cho 1 người lớn" % (meta['chang'], len(cp['caps']))
    s2['A1'].font = F_TITLE
    s2['A2'] = ("Thu thập %s. Mỗi cặp là phương án Rẻ nhất theo Giá chốt (Block C sheet Data). "
                "'Tổng mua được rẻ nhất' = giá thấp nhất ở người bán cho đúng hai chuyến đó (sheet Mua vé, "
                "có giờ đọc giá). Link mở trang đặt vé của đúng chuyến: bấm 'Tiếp tục' ở người bán muốn mua."
                % meta['thu_thap'])
    s2['A2'].font = F_NOTE
    header(s2, 4, H2)
    rr = 5
    for it in sorted(summary, key=lambda x: x['A'][1] + x['B'][1]):
        P, A, B = it['P'], it['A'], it['B']
        fa, fb = A[2], B[2]
        ba, bb = nguoi_ban(fa, P['di'], SRC, meta), nguoi_ban(fb, P['ve'], SRC, meta)
        ha = [x for x in ba if x['loai'] == 'Hãng hàng không']
        hb = [x for x in bb if x['loai'] == 'Hãng hàng không']
        src_a = next((s for s in SRC if fa.get('gia', {}).get(s) is not None), SRC[0])
        src_b = next((s for s in SRC if fb.get('gia', {}).get(s) is not None), SRC[0])
        canh_bao = []
        for nhan, f, b in (('Chiều đi', fa, ba), ('Chiều về', fb, bb)):
            if lech(f) >= NGUONG_DIEU_TRA:
                canh_bao.append('%s: hai nguồn lệch %.0f%%, đọc Log' % (nhan, lech(f) * 100))
            if (f.get('mua') or {}).get('trang_thai') != 'OK':
                canh_bao.append('%s: chưa xác nhận nơi mua' % nhan)

        s2.cell(rr, col2["Cặp ngày"], "%s (%s → %s)" % (P['ten'], P['ngay_di'], P['ngay_ve'])).font = F_B
        s2.cell(rr, col2["Thứ (đi → về)"], P.get('thu', '')).font = F_B
        for h, f in (("Chuyến đi", fa), ("Chuyến về", fb)):
            s2.cell(rr, col2[h], "%s %s, %s" % (f['hang'], f.get('sh') or '-', f['dep'])).font = F_B
        cc = s2.cell(rr, col2["Tổng theo Giá chốt"], "=Data!F%d" % it['row'])
        cc.number_format = MONEY; cc.font = F_BB
        if c_min:
            cc = s2.cell(rr, col2["Tổng theo giá thấp nhất"], "=Data!%s%d" % (L(c_tmin), it['row']))
            cc.number_format = MONEY; cc.font = F_B
        cc = s2.cell(rr, col2["Tổng mua được rẻ nhất"],
                     ba[0]['gia'] + bb[0]['gia'] if ba and bb else CHUA_XN)
        cc.number_format = MONEY; cc.font = F_BB
        s2.cell(rr, col2["Nơi mua rẻ nhất (đi / về)"],
                "%s / %s" % (ten_ban(ba[0]) if ba else CHUA_XN, ten_ban(bb[0]) if bb else CHUA_XN)).font = F_B
        cc = s2.cell(rr, col2["Tổng nếu mua thẳng từ hãng"],
                     ha[0]['gia'] + hb[0]['gia'] if ha and hb else CHUA_XN)
        cc.number_format = MONEY; cc.font = F_B
        for h, f, chang, s in (("Link chuyến đi", fa, P['di'], src_a), ("Link chuyến về", fb, P['ve'], src_b)):
            if f.get('link_chuyen'):
                link(s2, rr, col2[h], f['link_chuyen'], "Đặt vé %s" % f['sh'])
            else:   # không có số hiệu: đành trỏ về trang tìm kiếm
                link(s2, rr, col2[h], chang.get('link', {}).get(s, ''), "Tìm kiếm (%s)" % s)
        s2.cell(rr, col2["Nguồn Giá chốt (đi / về)"], "%s / %s" % (src_a, src_b)).font = F_B
        cw = s2.cell(rr, col2["Cảnh báo"], "; ".join(canh_bao))
        cw.font = F_WARN if canh_bao else F_B
        for c in range(1, NC2 + 1):
            s2.cell(rr, c).border = BD
            s2.cell(rr, c).alignment = TOP
        rr += 1
    if rr > 5:
        # Ô xanh thêm TRƯỚC dòng vàng: quy tắc thêm trước có ưu tiên cao hơn, không bị đè.
        cm = L(col2["Tổng mua được rẻ nhất"])
        s2.conditional_formatting.add("%s5:%s%d" % (cm, cm, rr - 1),
            FormulaRule(formula=['AND(ISNUMBER(%s5),%s5=MIN($%s$5:$%s$%d))' % (cm, cm, cm, cm, rr - 1)],
                        fill=FI_GRN, stopIfTrue=True))
        ct = L(col2["Tổng theo Giá chốt"])
        s2.conditional_formatting.add("A5:%s%d" % (L(NC2), rr - 1),
            FormulaRule(formula=['$%s5=MIN($%s$5:$%s$%d)' % (ct, ct, ct, rr - 1)], fill=FI_YEL, stopIfTrue=False))
        s2.auto_filter.ref = "A4:%s%d" % (L(NC2), rr - 1)
    s2.freeze_panes = "A5"
    s2.cell(rr + 1, 1, "Dòng vàng = cặp rẻ nhất theo Giá chốt. Ô xanh ở cột 'Tổng mua được rẻ nhất' = cặp mua được "
                       "rẻ nhất. Giá chốt = giá của nguồn đầu tiên có số theo thứ tự ưu tiên (%s). Người bán là "
                       "đại lý: kiểm tra uy tín và điều kiện đổi/hoàn trước khi trả tiền." % ", ".join(SRC)).font = F_NOTE
    for i, w in enumerate([28, 14, 30, 30, 18] + ([18] if c_min else []) + [18, 34, 18, 22, 22, 30, 40], 1):
        s2.column_dimensions[L(i)].width = w

    # ---------------- Mua vé ----------------
    H4 = ["Cặp ngày", "Chiều", "Ngày bay", "Chuyến", "Hãng", "Giờ đi", "Lý do đề xuất", "Người bán",
          "Loại người bán", "Giá (1 người lớn)", "So với Giá chốt lúc quét", "Ghi chú", "Hành lý",
          "Link mua", "Thời điểm", "Nguồn dữ liệu"]
    col4 = {h: i for i, h in enumerate(H4, 1)}
    s4['A1'] = "Nơi mua vé cho các chuyến đề xuất"
    s4['A1'].font = F_TITLE
    s4['A2'] = ("Giá cho 1 người lớn, đã gồm thuế phí bắt buộc theo nguồn. Link 'Trang đặt vé Google Flights' "
                "mở đúng chuyến: bấm 'Tiếp tục' ở dòng người bán muốn mua. Đại lý: kiểm tra uy tín và điều "
                "kiện đổi/hoàn trước khi trả tiền. Giá đổi liên tục, xem cột Thời điểm. Ô vàng = rẻ nhất "
                "của chuyến đó.")
    s4['A2'].font = F_NOTE
    header(s4, 4, H4)
    rr = 5
    n_ban = 0
    de_xuat = cp.get('de_xuat')
    if not de_xuat:
        s4.cell(rr, 1, "Checkpoint không có danh sách đề xuất: chạy lại merge_sources.py (bản 1.5.0 trở lên).").font = F_WARN
    for e in de_xuat or []:
        P = next((c for c in cp['caps'] if c['ten'] in e['cap']), None)
        if not P:
            continue
        chang = P[e['chieu']]
        f = next((x for x in chang['chuyen'] if x['dep'] == e['dep'] and x['hang'] == e['hang']), None)
        if not f:
            continue
        gc = shortlist.gia_chot(f, SRC)
        m = f.get('mua') or {}
        rows = []
        if m.get('trang_thai') != 'OK':
            rows.append(dict(ten=m.get('trang_thai') or CHUA_XN, loai='', gia=None,
                             ghi_chu=m.get('ly_do') or 'Chưa chạy trang đặt vé Google Flights cho chuyến này',
                             hanh_ly='', url=f.get('link_chuyen', ''), luc=m.get('luc', ''),
                             nguon='Trang đặt vé Google Flights'))
        ban = nguoi_ban(f, chang, SRC, meta)
        rows += ban
        lo = ban[0]['gia'] if ban else None
        for b in rows:
            vals = {"Cặp ngày": ", ".join(e['cap']),
                    "Chiều": "%s %s → %s" % ('Đi' if e['chieu'] == 'di' else 'Về', e['tu'], e['den']),
                    "Ngày bay": P['ngay_' + e['chieu']], "Chuyến": f.get('sh') or '-', "Hãng": f['hang'],
                    "Lý do đề xuất": ", ".join(e.get('ly_do', [])), "Người bán": b['ten'],
                    "Loại người bán": b['loai'], "Ghi chú": b['ghi_chu'], "Hành lý": b['hanh_ly'],
                    "Thời điểm": b['luc'], "Nguồn dữ liệu": b['nguon']}
            for h, v in vals.items():
                s4.cell(rr, col4[h], v).font = F_B
            cc = s4.cell(rr, col4["Giờ đi"], hhmm(f['dep'])); cc.number_format = 'hh:mm'; cc.font = F_B
            cc = s4.cell(rr, col4["Giá (1 người lớn)"], b['gia'] if b['gia'] is not None else NA)
            cc.number_format = MONEY; cc.font = F_BB
            if b['gia'] is not None:
                n_ban += 1
                if gc:
                    cc = s4.cell(rr, col4["So với Giá chốt lúc quét"], b['gia'] / gc - 1)
                    cc.number_format = '+0.0%;-0.0%;0.0%'; cc.font = F_B
            link(s4, rr, col4["Link mua"], b['url'],
                 "Mở trang đặt vé" if 'google.com/travel' in (b['url'] or '') else "Mở trang tìm kiếm")
            if b['gia'] is None:
                s4.cell(rr, col4["Người bán"]).font = F_WARN
            for c in range(1, len(H4) + 1):
                s4.cell(rr, c).border = BD
                s4.cell(rr, c).alignment = TOP
                if b['gia'] is not None and b['gia'] == lo:
                    s4.cell(rr, c).fill = FI_YEL
            rr += 1
        rr += 1                                   # một dòng trống giữa các chuyến
    s4.freeze_panes = "A5"
    for i, w in enumerate([16, 16, 12, 10, 20, 8, 26, 22, 16, 16, 12, 30, 34, 20, 22, 26], 1):
        s4.column_dimensions[L(i)].width = w

    # ---------------- Log ----------------
    header(s3, 1, ["Thời điểm", "Cặp ngày", "Nguồn", "Trạng thái", "Lý do chi tiết", "Ghi chú"])
    rr = 2
    for e in cp.get('log', []):
        for i, k in enumerate(['thoi_diem', 'cap', 'nguon', 'trang_thai', 'ly_do', 'ghi_chu'], 1):
            c = s3.cell(rr, i, e.get(k, '')); c.font = F_B; c.border = BD; c.alignment = TOP
        rr += 1
    s3.freeze_panes = "A2"
    if rr > 2: s3.auto_filter.ref = "A1:F%d" % (rr - 1)
    for i, w in enumerate([22, 16, 30, 20, 80, 42], 1): s3.column_dimensions[L(i)].width = w

    for sh in (s2, s4):                       # in ra: ngang, vừa một trang bề rộng
        sh.page_setup.orientation = 'landscape'
        sh.page_setup.fitToWidth, sh.page_setup.fitToHeight = 1, 0
        sh.sheet_properties.pageSetUpPr.fitToPage = True
    wb.active = 0
    wb.save(out)
    nf = sum(len(P[l]['chuyen']) for P in cp['caps'] for l in ('di', 've'))
    have = sum(1 for P in cp['caps'] for l in ('di', 've') for f in P[l]['chuyen']
               for s in SRC if f.get('gia', {}).get(s) is not None)
    canh_bao = sum(1 for P in cp['caps'] for l in ('di', 've') for f in P[l]['chuyen']
                   if len(SRC) >= 2 and lech(f) >= NGUONG_DIEU_TRA)
    xn = sum(1 for e in de_xuat or [] for P in cp['caps'] if P['ten'] == e['cap'][0]
             for f in P[e['chieu']]['chuyen']
             if f['dep'] == e['dep'] and f['hang'] == e['hang'] and (f.get('mua') or {}).get('trang_thai') == 'OK')
    print(json.dumps({"file": out, "chuyen": nf, "o_co_gia": have,
                      "o_tong": nf * len(SRC),
                      "phu_%": round(100.0 * have / max(1, nf * len(SRC)), 1),
                      "can_dieu_tra": canh_bao,
                      "de_xuat": len(de_xuat or []), "da_xac_nhan": xn, "dong_nguoi_ban": n_ban},
                     ensure_ascii=False))
    if canh_bao:
        print("CẢNH BÁO: %d chuyến lệch >=%d%% giữa các nguồn. SKILL.md §6 bắt buộc điều tra "
              "và ghi Log trước khi giao file." % (canh_bao, NGUONG_DIEU_TRA * 100), file=sys.stderr)
    if de_xuat is not None and xn < len(de_xuat):
        print("CẢNH BÁO: mới xác nhận nơi mua %d/%d chuyến đề xuất (sheet Mua vé có dòng '%s')."
              % (xn, len(de_xuat), CHUA_XN), file=sys.stderr)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    with open(sys.argv[1], encoding='utf-8') as fh:
        build(json.load(fh), sys.argv[2])
