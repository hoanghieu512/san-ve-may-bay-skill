#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ghép dữ liệu thô của nhiều nguồn thành checkpoint JSON.

    python3 merge_sources.py job.json checkpoint.json

`job.json` mô tả chặng, cặp ngày và đường dẫn file thô — spec đầy đủ ở
`references/merge-sources.md`. Schema đầu ra ở `references/checkpoint-schema.md`.

Khoá ghép là (giờ khởi hành, hãng đã chuẩn hoá) vì Google Flights không cấp số
hiệu chuyến khi chưa bung từng dòng. Số hiệu lấy từ nguồn nào có.

Tự sinh dòng `Log` cho: chuyến thiếu ở một nguồn, hai nguồn lệch quá ngưỡng, và
nhiều dòng cùng khoá trong một nguồn. KHÔNG bao giờ sửa hay bỏ giá — chỉ ghi.
"""
import json, sys, os, datetime

# Lệch >= mức này giữa hai nguồn cho cùng một chuyến -> ghi Log mức "Lỗi".
NGUONG_LOG = 0.10
# Lệch >= mức này -> SKILL.md §6 bắt buộc điều tra trước khi build workbook.
NGUONG_DIEU_TRA = 0.25

# Traveloka viết tên hãng khác Google Flights. Bổ sung thêm qua job["hang_alias"].
ALIAS = {
    'VietJet Air': 'Vietjet',
    'SUN PhuQuoc AIRWAYS': 'Sun PhuQuoc Airways',
    'Bamboo Airways': 'Bamboo Airways',
    'Pacific Airlines': 'Pacific Airlines',
}

GF_URL = ('https://www.google.com/travel/flights?q=Oneway%20flights%20from={o}%20to={d}'
          '%20on={iso}&curr=VND&hl=vi&gl=VN')
TVL_URL = ('https://www.traveloka.com/vi-vn/flight/fullsearch?ap={o}.{d}'
           '&dt={dmy}.NA&ps=1.0.0&sc=ECONOMY')
URL = {'Google Flights': GF_URL, 'Traveloka': TVL_URL}


def iso(dmy):
    """'14/08/2026' -> '2026-08-14'"""
    return '%s-%s-%s' % (dmy[6:10], dmy[3:5], dmy[0:2])


def doc_raw(job, base):
    """-> {nguon: {'di': {iso: [dict]}, 've': {...}}} , đã map cột theo job."""
    out = {}
    for src, spec in job['raw'].items():
        cot = spec['cot']
        legs = {}
        if 'file' in spec:                       # 1 file chứa cả hai chiều
            d = json.load(open(os.path.join(base, spec['file']), encoding='utf-8'))
            for leg in ('di', 've'):
                legs[leg] = d.get(leg, {})
        else:                                    # mỗi chiều một file
            for leg in ('di', 've'):
                legs[leg] = json.load(open(os.path.join(base, spec[leg]), encoding='utf-8'))
        out[src] = {leg: {day: [dict(zip(cot, row)) for row in rows]
                          for day, rows in days.items()}
                    for leg, days in legs.items()}
    return out


def merge(job, raw, ts):
    nguon = job['nguon']
    alias = dict(ALIAS, **job.get('hang_alias', {}))
    norm = lambda h: alias.get(h, h)
    bo = {norm(h) for h in job.get('loai_hang', [])}
    ap = job['san_bay']
    log = []

    def gop(leg, day_dmy, nhan):
        day = iso(day_dmy)
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
                    # chuyến — xem site-quirks.md) và ghi lại để người đọc biết.
                    cu, moi = slot[src], row
                    giu, bod = (cu, moi) if cu['gia'] <= moi['gia'] else (moi, cu)
                    log.append(dict(
                        thoi_diem=ts, cap=day_dmy, nguon=src, trang_thai='Lỗi',
                        ly_do='Nhiều dòng cùng (giờ %s, %s) trong một nguồn — giữ giá thấp nhất'
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
            sh = next((r['sh'].replace('-', ' ') for r in co if r.get('sh')), '')
            arr = next((r['arr'] for r in co if r.get('arr')), '')

            for s in nguon:
                if s not in slot:
                    log.append(dict(
                        thoi_diem=ts, cap=day_dmy, nguon=s, trang_thai='Không khả dụng',
                        ly_do='Nguồn này không trả chuyến (không bán, hết chỗ, hoặc bị loại khỏi danh sách)',
                        ghi_chu='%s %s %s %s' % (nhan, sh or '—', dep, hang)))

            if len(gia) >= 2:
                lo, hi = min(gia.values()), max(gia.values())
                lech = hi / lo - 1
                if lech >= NGUONG_LOG:
                    canh_bao = 'CẦN ĐIỀU TRA — ' if lech >= NGUONG_DIEU_TRA else ''
                    log.append(dict(
                        thoi_diem=ts, cap=day_dmy, nguon='Đối chiếu', trang_thai='Lỗi',
                        ly_do='%sHai nguồn lệch %.1f%%' % (canh_bao, lech * 100),
                        ghi_chu='%s %s %s %s — %s' % (
                            nhan, sh or '—', dep, hang,
                            ' / '.join('%s %s' % (s, format(v, ',d')) for s, v in gia.items()))))
            out.append(dict(sh=sh, hang=hang, dep=dep, arr=arr, gia=gia))
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
                chuyen=gop(leg, ngay, nhan))
        caps.append(cap)
    return caps, log


def main(job_path, out_path):
    base = os.path.dirname(os.path.abspath(job_path))
    job = json.load(open(job_path, encoding='utf-8'))
    ts = job.get('thu_thap') or datetime.datetime.now().strftime('%d/%m/%Y %H:%M') + ' (giờ VN)'

    caps, log = merge(job, doc_raw(job, base), ts)
    log = [dict(thoi_diem=ts, **e) if 'thoi_diem' not in e else e
           for e in job.get('log_them', [])] + log

    meta = dict(job['meta'], thu_thap=ts, nguon=job['nguon'])
    cp = dict(meta=meta, caps=caps, log=log)
    json.dump(cp, open(out_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    n_ch = sum(len(c[l]['chuyen']) for c in caps for l in ('di', 've'))
    n_o = sum(len(f['gia']) for c in caps for l in ('di', 've') for f in c[l]['chuyen'])
    tong = n_ch * len(job['nguon'])
    dieu_tra = sum(1 for e in log if 'CẦN ĐIỀU TRA' in e.get('ly_do', ''))
    print(json.dumps({'file': out_path, 'cap': len(caps), 'chuyen': n_ch,
                      'o_co_gia': n_o, 'o_tong': tong,
                      'phu_%': round(100.0 * n_o / max(1, tong), 1),
                      'log': len(log), 'can_dieu_tra': dieu_tra}, ensure_ascii=False))
    if dieu_tra:
        print('CẢNH BÁO: %d dòng lệch >=%d%% — SKILL.md §6 bắt buộc điều tra trước khi build.'
              % (dieu_tra, NGUONG_DIEU_TRA * 100), file=sys.stderr)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
