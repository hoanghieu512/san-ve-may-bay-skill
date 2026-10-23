#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ghép dữ liệu thô của nhiều nguồn thành checkpoint JSON.

    python3 merge_sources.py job.json checkpoint.json [--de-xuat]

`job.json` mô tả chặng, cặp ngày và đường dẫn file thô. Spec đầy đủ ở
`references/merge-sources.md`. Schema đầu ra ở `references/checkpoint-schema.md`.

Khoá ghép là (giờ khởi hành, hãng đã chuẩn hoá) vì Google Flights không cấp số
hiệu chuyến khi chưa bung từng dòng. Số hiệu lấy từ nguồn nào có.

Mỗi chuyến có số hiệu được dựng sẵn link tới trang đặt vé Google Flights của đúng
chuyến đó (`link_chuyen`). `--de-xuat` in danh sách chuyến cần xác nhận nơi mua,
dán thẳng vào `scripts/gf_booking.js`. Kết quả gf_booking khai báo ở `xac_nhan`
trong job.json rồi chạy lại script này. Xem `references/gf-booking.md`.

Tự sinh dòng `Log` cho: chuyến thiếu ở một nguồn, hai nguồn lệch quá ngưỡng,
nhiều dòng cùng khoá trong một nguồn, và kết quả bước xác nhận nơi mua.
KHÔNG bao giờ sửa hay bỏ giá, chỉ ghi.
"""
import base64, datetime, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shortlist  # noqa: E402

# Lệch >= mức này giữa hai nguồn cho cùng một chuyến -> ghi Log mức "Lỗi".
NGUONG_LOG = 0.10
# Lệch >= mức này -> SKILL.md §6 bắt buộc điều tra trước khi build workbook.
NGUONG_DIEU_TRA = 0.25

# Việt Nam không có giờ mùa hè: UTC+7 cố định. Không dùng giờ máy, sandbox chạy UTC.
GIO_VN = datetime.timezone(datetime.timedelta(hours=7))

# Traveloka viết tên hãng khác Google Flights. Bổ sung thêm qua job["hang_alias"].
ALIAS = {
    'VietJet Air': 'Vietjet',
    'SUN PhuQuoc AIRWAYS': 'Sun PhuQuoc Airways',
    'Bamboo Airways': 'Bamboo Airways',
    'Pacific Airlines': 'Pacific Airlines',
}

GF_URL = ('https://www.google.com/travel/flights?q=Oneway%20flights%20from%20{o}%20to%20{d}'
          '%20on%20{iso}&curr=VND&hl=vi&gl=VN')
TVL_URL = ('https://www.traveloka.com/vi-vn/flight/fullsearch?ap={o}.{d}'
           '&dt={dmy}.NA&ps=1.0.0&sc=ECONOMY')
URL = {'Google Flights': GF_URL, 'Traveloka': TVL_URL}
GF_BOOKING = 'https://www.google.com/travel/flights/booking?tfs={tfs}&hl=vi&gl=VN&curr=VND'


def bay_gio():
    return datetime.datetime.now(GIO_VN).strftime('%d/%m/%Y %H:%M') + ' (giờ VN)'


def iso(dmy):
    """'14/08/2026' -> '2026-08-14'"""
    return '%s-%s-%s' % (dmy[6:10], dmy[3:5], dmy[0:2])


def dmy(iso_):
    return '%s/%s/%s' % (iso_[8:10], iso_[5:7], iso_[0:4])


def so_hieu(sh):
    """'VJ-632' / 'VJ632' / 'VJ 632,VN 1234' -> ('VJ', '632'), hoặc None."""
    m = re.match(r'^\s*([A-Z0-9]{2})[\s-]*(\d{1,4})\s*$', (sh or '').split(',')[0].upper())
    return (m.group(1), m.group(2)) if m else None


def _varint(n):
    out = bytearray()
    while True:
        b, n = n & 0x7f, n >> 7
        out.append(b | (0x80 if n else 0))
        if not n:
            return bytes(out)


def _pb(field, v):
    if isinstance(v, int):
        return _varint(field << 3) + _varint(v)
    b = v.encode() if isinstance(v, str) else v
    return _varint(field << 3 | 2) + _varint(len(b)) + b


def gf_booking_url(ngay_iso, o, d, sh):
    """Link trang đặt vé Google Flights của MỘT chuyến bay thẳng, một chiều, 1 người lớn,
    phổ thông. None nếu không tách được số hiệu.

    `tfs` là protobuf base64url. Dựng lại đúng từng byte link bắt được trên trang thật
    ngày 23/10/2026 (test ở tests/test_scripts.py). Trường đã rõ nghĩa: 3 = hành trình
    (4 = chặng đã chọn: từ, ngày, đến, mã hãng, số hiệu), 8 = hành khách (1 = người lớn),
    9 = hạng (1 = phổ thông), 19 = loại chuyến (2 = một chiều). Các trường còn lại chép
    nguyên từ link thật.
    """
    p = so_hieu(sh)
    if not p:
        return None
    seg = _pb(1, o) + _pb(2, ngay_iso) + _pb(3, d) + _pb(5, p[0]) + _pb(6, p[1])
    leg = (_pb(2, ngay_iso) + _pb(4, seg) + _pb(13, _pb(1, 1) + _pb(2, o))
           + _pb(14, _pb(1, 1) + _pb(2, d)))
    body = (_pb(1, 28) + _pb(2, 2) + _pb(3, leg) + _pb(8, 1) + _pb(9, 1) + _pb(14, 1)
            + _pb(16, _pb(1, 2 ** 64 - 1)) + _pb(19, 2))
    return GF_BOOKING.format(tfs=base64.urlsafe_b64encode(body).decode().rstrip('='))


def doc_json(base, path):
    with open(os.path.join(base, path), encoding='utf-8') as fh:
        return json.load(fh)


def doc_raw(job, base):
    """-> (raw, gio).
    raw = {nguon: {'di': {iso: [dict]}, 've': {...}}}, đã map cột theo job.
    gio = {nguon: {'di': {iso: thời điểm quét}, 've': {...}}}, từ khoá `_thu_thap`.
    Khoá bắt đầu bằng `_` không phải ngày bay."""
    raw, gio = {}, {}
    for src, spec in job['raw'].items():
        cot = spec['cot']
        legs = {}
        if 'file' in spec:                       # 1 file chứa cả hai chiều
            d = doc_json(base, spec['file'])
            for leg in ('di', 've'):
                legs[leg] = d.get(leg, {})
        else:                                    # mỗi chiều một file
            for leg in ('di', 've'):
                legs[leg] = doc_json(base, spec[leg])
        raw[src] = {leg: {day: [dict(zip(cot, row)) for row in rows]
                          for day, rows in days.items() if not day.startswith('_')}
                    for leg, days in legs.items()}
        gio[src] = {leg: dict(days.get('_thu_thap', {})) for leg, days in legs.items()}
        if spec.get('thu_thap'):                 # một mốc cho cả nguồn, khi không có theo ngày
            for leg in gio[src]:
                for day in raw[src][leg]:
                    gio[src][leg].setdefault(day, spec['thu_thap'])
    return raw, gio


def merge(job, raw, gio, ts):
    nguon = job['nguon']
    alias = dict(ALIAS, **job.get('hang_alias', {}))
    norm = lambda h: alias.get(h, h)
    bo = {norm(h) for h in job.get('loai_hang', [])}
    ap = job['san_bay']
    log = []

    def gop(leg, day_dmy, nhan):
        day = iso(day_dmy)
        o, d = ap[leg]
        m = {}
        for src in nguon:
            for row in raw[src][leg].get(day, []):
                hang = norm(row['hang'])
                if hang in bo:
                    continue
                key = (row['dep'], hang)
                slot = m.setdefault(key, {})
                if src in slot:
                    # Cùng khoá xuất hiện nhiều lần trong MỘT nguồn: giữ giá thấp
                    # nhất (Traveloka liệt kê nhiều hạng vé rời nhau cho một
                    # chuyến, xem site-quirks.md) và ghi lại để người đọc biết.
                    cu, moi = slot[src], row
                    giu, bod = (cu, moi) if cu['gia'] <= moi['gia'] else (moi, cu)
                    log.append(dict(
                        thoi_diem=ts, cap=day_dmy, nguon=src, trang_thai='Lỗi',
                        ly_do='Nhiều dòng cùng (giờ %s, %s) trong một nguồn, giữ giá thấp nhất'
                              % (row['dep'], hang),
                        ghi_chu='%s giữ %s, bỏ %s' % (nhan, format(giu['gia'], ',d'),
                                                      format(bod['gia'], ',d'))))
                    slot[src] = giu
                else:
                    slot[src] = row

        out = []
        for (dep, hang), slot in sorted(m.items()):
            gia = {s: slot[s]['gia'] for s in nguon if s in slot}
            co = [slot[s] for s in nguon if s in slot]
            # 'VJ-652' (Traveloka) / 'VJ\u00a0636' (Google Flights chèn NBSP) -> 'VJ 636'
            sh = next((re.sub(r'\s+', ' ', r['sh'].replace('-', ' ')).strip()
                       for r in co if r.get('sh')), '')
            arr = next((r['arr'] for r in co if r.get('arr')), '')

            for s in nguon:
                if s not in slot:
                    log.append(dict(
                        thoi_diem=ts, cap=day_dmy, nguon=s, trang_thai='Không khả dụng',
                        ly_do='Nguồn này không trả chuyến (không bán, hết chỗ, hoặc bị loại khỏi danh sách)',
                        ghi_chu='%s %s %s %s' % (nhan, sh or '-', dep, hang)))

            if len(gia) >= 2:
                lo, hi = min(gia.values()), max(gia.values())
                lech = hi / lo - 1
                if lech >= NGUONG_LOG:
                    canh_bao = 'CẦN ĐIỀU TRA: ' if lech >= NGUONG_DIEU_TRA else ''
                    log.append(dict(
                        thoi_diem=ts, cap=day_dmy, nguon='Đối chiếu', trang_thai='Lỗi',
                        ly_do='%sHai nguồn lệch %.1f%%' % (canh_bao, lech * 100),
                        ghi_chu='%s %s %s %s: %s' % (
                            nhan, sh or '-', dep, hang,
                            ' / '.join('%s %s' % (s, format(v, ',d')) for s, v in gia.items()))))
            out.append(dict(sh=sh, hang=hang, dep=dep, arr=arr, gia=gia,
                            link_chuyen=gf_booking_url(day, o, d, sh) or ''))
        return sorted(out, key=lambda x: x['dep'])

    caps = []
    for c in job['caps']:
        cap = dict(id=c['id'], ten=c.get('ten', 'Cặp %d' % c['id']),
                   ngay_di=c['ngay_di'], ngay_ve=c['ngay_ve'], thu=c.get('thu', ''))
        for leg, nhan in (('di', 'đi'), ('ve', 'về')):
            o, d = ap[leg]
            ngay = c['ngay_%s' % leg]
            cap[leg] = dict(
                link={s: URL[s].format(o=o, d=d, iso=iso(ngay), dmy=ngay.replace('/', '-'))
                      for s in nguon if s in URL},
                thu_thap={s: gio[s][leg][iso(ngay)] for s in nguon
                          if iso(ngay) in gio.get(s, {}).get(leg, {})},
                chuyen=gop(leg, ngay, nhan))
        caps.append(cap)
    return caps, log


def danh_sach_de_xuat(caps, nguon, ap):
    """Các chuyến cần xác nhận nơi mua, mỗi chuyến một lần dù nằm trong nhiều cặp."""
    seen = {}
    for c in caps:
        dx = shortlist.de_xuat(c, nguon)
        for leg in ('di', 've'):
            o, d = ap[leg]
            ngay = iso(c['ngay_' + leg])
            for i, ly_do in sorted(dx[leg].items()):
                f = c[leg]['chuyen'][i]
                e = seen.setdefault((ngay, o, d, f['dep'], f['hang']), dict(
                    ngay=ngay, tu=o, den=d, sh=f['sh'], dep=f['dep'], hang=f['hang'],
                    url=f['link_chuyen'], chieu=leg, cap=[], ly_do=[]))
                if c['ten'] not in e['cap']:
                    e['cap'].append(c['ten'])
                e['ly_do'] += [x for x in ly_do if x not in e['ly_do']]
    return sorted(seen.values(), key=lambda e: (e['ngay'], e['tu'], e['dep']))


def doc_xac_nhan(job, base):
    """-> ({(ngày, từ, đến, số hiệu): [kết quả]}, [lý do dừng]). File sau đè file trước."""
    files = job.get('xac_nhan', [])
    files = [files] if isinstance(files, str) else files
    kq, dung = {}, []
    for path in files:
        d = doc_json(base, path)
        if isinstance(d, str):                   # dán nguyên chuỗi JSON gf_booking trả về
            d = json.loads(d)
        rows = d.get('ket_qua', []) if isinstance(d, dict) else d
        if isinstance(d, dict) and d.get('dung'):
            dung.append(d['dung'])
        for r in rows:
            p = so_hieu(r.get('sh'))
            if p:
                kq.setdefault((r['ngay'], r['tu'], r['den'], '%s %s' % p), []).insert(0, r)
    return kq, dung


def gan_xac_nhan(job, base, caps, de_xuat, ts):
    """Gắn kết quả gf_booking vào từng chuyến (`mua`) và sinh Log của bước xác nhận."""
    log = []
    nhom = 'Xác nhận nơi mua'
    if 'xac_nhan' not in job:
        log.append(dict(thoi_diem=ts, cap='(toàn bộ)', nguon=nhom, trang_thai='Không khả dụng',
                        ly_do='Chưa chạy bước xác nhận nơi mua (scripts/gf_booking.js)',
                        ghi_chu='Sheet Mua vé chỉ có giá lúc quét, chưa có danh sách người bán'))
        return log, 0
    kq, dung = doc_xac_nhan(job, base)
    for ly_do in dung:
        log.append(dict(thoi_diem=ts, cap='(toàn bộ)', nguon=nhom, trang_thai='Lỗi',
                        ly_do='Bị chặn khi xác nhận nơi mua: %s' % ly_do,
                        ghi_chu='SKILL.md §1.5: dừng, báo người dùng'))

    def tim(ngay, o, d, f):
        p = so_hieu(f['sh'])
        ds = kq.get((ngay, o, d, '%s %s' % p), []) if p else []
        return next((r for r in ds if r.get('dep') == f['dep']), ds[0] if ds else None)

    ap = job['san_bay']
    for c in caps:
        for leg in ('di', 've'):
            o, d = ap[leg]
            for f in c[leg]['chuyen']:
                r = tim(iso(c['ngay_' + leg]), o, d, f)
                if r:
                    f['mua'] = {k: r.get(k) for k in
                                ('url', 'luc', 'trang_thai', 'ly_do', 'chuyen', 'ban', 'hanh_ly')}

    n_ok = 0
    for e in de_xuat:
        c = next(c for c in caps if c['ten'] == e['cap'][0])
        f = next(f for f in c[e['chieu']]['chuyen'] if f['dep'] == e['dep'] and f['hang'] == e['hang'])
        nhan = '%s %s-%s %s %s %s' % ('đi' if e['chieu'] == 'di' else 'về', e['tu'], e['den'],
                                     e['sh'] or '-', e['dep'], e['hang'])
        m = f.get('mua')
        if not m:
            log.append(dict(thoi_diem=ts, cap=dmy(e['ngay']), nguon=nhom, trang_thai='Không khả dụng',
                            ly_do='Chưa xác nhận nơi mua: '
                                  + ('không có kết quả gf_booking cho chuyến này' if e['url']
                                     else 'thiếu số hiệu, không dựng được link trang đặt vé'),
                            ghi_chu=nhan))
            continue
        if m['trang_thai'] != 'OK':
            log.append(dict(thoi_diem=m['luc'] or ts, cap=dmy(e['ngay']), nguon=nhom,
                            trang_thai=m['trang_thai'], ly_do=m['ly_do'] or 'Không đọc được trang đặt vé',
                            ghi_chu=nhan))
            continue
        n_ok += 1
        hang = next((b for b in m['ban'] if b['loai'] == 'Hãng hàng không' and b['gia']), None)
        cu = f['gia'].get('Google Flights')
        if hang and cu and hang['gia'] != cu:
            log.append(dict(thoi_diem=m['luc'], cap=dmy(e['ngay']), nguon=nhom, trang_thai='OK',
                            ly_do='Giá hãng trên trang đặt vé đổi sau khi quét: %s -> %s (%+.1f%%)'
                                  % (format(cu, ',d'), format(hang['gia'], ',d'),
                                     (hang['gia'] / cu - 1) * 100),
                            ghi_chu=nhan + '. Sheet Mua vé dùng giá mới, sheet Data giữ giá lúc quét'))
    return log, n_ok


def main(job_path, out_path, in_de_xuat=False):
    base = os.path.dirname(os.path.abspath(job_path))
    job = doc_json(base, os.path.basename(job_path))
    ts = job.get('thu_thap') or bay_gio()

    raw, gio = doc_raw(job, base)
    caps, log = merge(job, raw, gio, ts)
    de_xuat = danh_sach_de_xuat(caps, job['nguon'], job['san_bay'])
    log_xn, n_ok = gan_xac_nhan(job, base, caps, de_xuat, ts)
    log = [dict(thoi_diem=ts, **e) if 'thoi_diem' not in e else e
           for e in job.get('log_them', [])] + log + log_xn

    meta = dict(job['meta'], thu_thap=ts, nguon=job['nguon'])
    if meta.get('khach', '1 người lớn').strip() != '1 người lớn':
        log.append(dict(thoi_diem=ts, cap='(toàn bộ)', nguon='Tham số', trang_thai='Lỗi',
                        ly_do='Mọi giá và link trong file là cho 1 người lớn, không phải "%s"'
                              % meta['khach'],
                        ghi_chu='Mở link rồi đổi số khách trên trang để xem tổng cho đoàn'))
        print('CẢNH BÁO: giá trong file là giá 1 người lớn, meta.khach = "%s".' % meta['khach'],
              file=sys.stderr)
    cp = dict(meta=meta, caps=caps, de_xuat=de_xuat, log=log)
    with open(out_path, 'w', encoding='utf-8') as fh:
        json.dump(cp, fh, ensure_ascii=False, indent=1)

    n_ch = sum(len(c[l]['chuyen']) for c in caps for l in ('di', 've'))
    n_o = sum(len(f['gia']) for c in caps for l in ('di', 've') for f in c[l]['chuyen'])
    tong = n_ch * len(job['nguon'])
    dieu_tra = sum(1 for e in log if 'CẦN ĐIỀU TRA' in e.get('ly_do', ''))
    print(json.dumps({'file': out_path, 'cap': len(caps), 'chuyen': n_ch,
                      'o_co_gia': n_o, 'o_tong': tong,
                      'phu_%': round(100.0 * n_o / max(1, tong), 1),
                      'log': len(log), 'can_dieu_tra': dieu_tra,
                      'de_xuat': len(de_xuat), 'xac_nhan_ok': n_ok}, ensure_ascii=False))
    if dieu_tra:
        print('CẢNH BÁO: %d dòng lệch >=%d%%. SKILL.md §6 bắt buộc điều tra trước khi build.'
              % (dieu_tra, NGUONG_DIEU_TRA * 100), file=sys.stderr)
    if 'xac_nhan' not in job:
        print('CẢNH BÁO: chưa có kết quả xác nhận nơi mua. Chạy lại với --de-xuat, dán danh sách '
              'vào scripts/gf_booking.js, rồi khai báo file kết quả ở job.json "xac_nhan".',
              file=sys.stderr)
    elif n_ok < len(de_xuat):
        print('CẢNH BÁO: mới xác nhận nơi mua %d/%d chuyến đề xuất, xem sheet Log.'
              % (n_ok, len(de_xuat)), file=sys.stderr)

    if in_de_xuat:
        co = [e for e in de_xuat if e['url']]
        print('FLIGHTS cho scripts/gf_booking.js (%d chuyến):' % len(co))
        print('[\n' + ',\n'.join(json.dumps({k: e[k] for k in ('url', 'sh', 'dep', 'ngay', 'tu', 'den')},
                                            ensure_ascii=False) for e in co) + '\n]')
        for e in de_xuat:
            if not e['url']:
                print('THIẾU SỐ HIỆU: %s %s-%s %s %s. Bung dòng này trên Google Flights để lấy số '
                      'hiệu, thêm vào file thô, rồi chạy lại merge.'
                      % (dmy(e['ngay']), e['tu'], e['den'], e['dep'], e['hang']), file=sys.stderr)


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if a != '--de-xuat']
    if len(args) != 2:
        sys.exit(__doc__)
    main(args[0], args[1], '--de-xuat' in sys.argv)
