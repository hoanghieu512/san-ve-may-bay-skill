#!/usr/bin/env python3
"""Chế độ gọn của gf_booking.js -> file raw đúng schema cho job.json khoá "xac_nhan".

    python3 gf_booking_gon.py gf_booking_gon.txt checkpoint.json gf_booking_raw.json

`gf_booking.js` với `GON = true` trả về text nhiều dòng và bỏ `url` của từng chuyến. `url`
là thứ dài nhất trong kết quả (tfs protobuf base64url ~250 ký tự mỗi chuyến) và cũng là thứ
duy nhất dựng lại được mà không cần đọc trang: script này lấy từ `link_chuyen` trong
checkpoint, chính là link merge_sources.py đã dựng để in ra danh sách FLIGHTS, nên khớp
từng byte. Mọi thứ khác đi qua nguyên văn.

Vì sao cần: Playwright không ghi được file (không có `fs`, `filename` vô dụng khi đổi phiên,
xem references/playwright-path.md), nên kết quả bắt buộc đi qua context. Chép tay 67 chuyến
x 5 người bán thì sai sót là chuyện chắc chắn xảy ra. Ngày 01/11/2026 đã phải sửa
script giữa lúc chạy để có dạng gọn; đây là đường đã test cho việc đó.

Dòng F không tìm được chuyến trong checkpoint là LỖI, không bỏ qua: sai số hiệu hay sai ngày
mà im lặng thì chuyến đó mất khỏi sheet Mua vé và không ai biết.
"""
import json
import os
import re
import sys


def so_hieu(sh):
    """'VJ-632' / 'VJ632' -> 'VJ 632', hoặc None. Giống merge_sources.so_hieu."""
    m = re.match(r'^\s*([A-Z0-9]{2})[\s-]*(\d{1,4})\s*$', (sh or '').split(',')[0].upper())
    return '%s %s' % (m.group(1), m.group(2)) if m else None


def iso(d):
    """'03/12/2026' hoặc '2026-12-03' -> '2026-12-03'."""
    m = re.match(r'^(\d{2})/(\d{2})/(\d{4})$', d or '')
    return '%s-%s-%s' % (m.group(3), m.group(2), m.group(1)) if m else d


def ban_do_link(cp):
    """(ngày iso, số hiệu, giờ đi) -> link_chuyen. Khoá trùng mà link khác nhau là lỗi."""
    out = {}
    for c in cp.get('caps', []):
        for leg in ('di', 've'):
            for f in c.get(leg, {}).get('chuyen', []):
                p, url = so_hieu(f.get('sh')), f.get('link_chuyen') or ''
                if not p or not url:
                    continue
                k = (iso(c.get('ngay_' + leg)), p, f.get('dep'))
                if k in out and out[k] != url:
                    sys.exit('LỖI: checkpoint có hai link khác nhau cho %s. Không đoán được '
                             'link nào đúng.' % (k,))
                out[k] = url
    return out


def doc_gon(text):
    """Text gọn -> ([bản ghi chưa có url], chỉ số con_lai, lý do dừng)."""
    ket_qua, con_lai, dung, cur = [], [], '', None
    for ln, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        c = line.split('\t')
        if c[0] == '# GON':
            continue
        if c[0] == '# CON_LAI':
            v = c[1] if len(c) > 1 else ''
            con_lai = [] if v.strip() in ('', '(het)') else [int(x) for x in v.split(',')]
            continue
        if c[0] == '# DUNG':
            v = (c[1] if len(c) > 1 else '').strip()
            dung = '' if v in ('', '(khong)') else v
            continue
        if c[0] == 'F':
            if len(c) < 8:
                sys.exit('LỖI dòng %d: F cần ít nhất 8 cột, có %d.' % (ln, len(c)))
            c += [''] * (10 - len(c))
            cur = dict(ngay=c[1], tu=c[2], den=c[3], sh=c[4], dep=c[5], luc=c[6],
                       trang_thai=c[7], ly_do=c[8], chuyen=c[9], ban=[], hanh_ly=[])
            ket_qua.append(cur)
            continue
        if cur is None:
            sys.exit('LỖI dòng %d: dòng %r đứng trước dòng F đầu tiên.' % (ln, c[0]))
        if c[0] == 'H':
            cur['hanh_ly'] = [x.strip() for x in (c[1] if len(c) > 1 else '').split(';;')
                              if x.strip()]
        elif c[0] == 'B':
            if len(c) < 4:
                sys.exit('LỖI dòng %d: B cần ít nhất 4 cột, có %d.' % (ln, len(c)))
            if c[2] not in ('H', 'D'):
                sys.exit("LỖI dòng %d: loại người bán %r, phải là 'H' hoặc 'D'." % (ln, c[2]))
            cur['ban'].append(dict(
                nguoi_ban=c[1],
                loai='Hãng hàng không' if c[2] == 'H' else 'Đại lý',
                gia=int(c[3]) if c[3].strip() else None,
                ghi_chu=c[4] if len(c) > 4 else ''))
        else:
            sys.exit('LỖI dòng %d: không hiểu loại dòng %r.' % (ln, c[0]))
    return ket_qua, con_lai, dung


def main(gon_path, cp_path, out_path):
    with open(gon_path, encoding='utf-8') as fh:
        text = fh.read()
    if not text.lstrip().startswith('# GON'):
        sys.exit('LỖI: %s không bắt đầu bằng "# GON". Nếu đây là JSON do gf_booking.js trả về '
                 'với GON = false thì khai báo thẳng vào job.json "xac_nhan", không cần script '
                 'này.' % gon_path)
    with open(cp_path, encoding='utf-8') as fh:
        cp = json.load(fh)

    ket_qua, con_lai, dung = doc_gon(text)
    link = ban_do_link(cp)
    thieu = []
    for r in ket_qua:
        p = so_hieu(r['sh'])
        r['url'] = link.get((iso(r['ngay']), p, r['dep']), '') if p else ''
        if not r['url']:
            thieu.append('%s %s %s %s-%s' % (r['ngay'], r['sh'], r['dep'], r['tu'], r['den']))
    if thieu:
        sys.exit('LỖI: %d chuyến không có trong checkpoint, nên không dựng được link mua:\n  '
                 % len(thieu) + '\n  '.join(thieu)
                 + '\nKiểm lại số hiệu / ngày / giờ đi ở dòng F, hoặc chạy lại merge_sources.py '
                   'để checkpoint khớp với danh sách FLIGHTS vừa quét.')

    # Thứ tự khoá giống gf_booking.js với GON = false, để hai đường cho ra file so sánh được.
    rows = [{k: r[k] for k in ('url', 'sh', 'dep', 'ngay', 'tu', 'den', 'luc', 'trang_thai',
                               'ly_do', 'chuyen', 'ban', 'hanh_ly')} for r in ket_qua]
    out = dict(ket_qua=rows, con_lai=[], dung=dung)
    # merge_sources.py không đọc con_lai; giữ chỉ số lại làm bằng chứng của lượt chạy.
    if con_lai:
        out['_con_lai_chi_so'] = con_lai
    with open(out_path, 'w', encoding='utf-8') as fh:
        json.dump(out, fh, ensure_ascii=False)

    n_ban = sum(len(r['ban']) for r in rows)
    n_ok = sum(1 for r in rows if r['trang_thai'] == 'OK')
    print(json.dumps(dict(chuyen=len(rows), ok=n_ok, nguoi_ban=n_ban,
                          con_lai=len(con_lai), dung=dung or '(khong)',
                          ra=os.path.basename(out_path)), ensure_ascii=False))
    if n_ok < len(rows):
        print('CẢNH BÁO: %d/%d chuyến không OK, xem `ly_do` từng dòng và sheet Log.'
              % (len(rows) - n_ok, len(rows)), file=sys.stderr)
    if con_lai:
        print('CÒN LẠI: chỉ số %s trong FLIGHTS của lượt vừa chạy. Gọi lại gf_booking.js với '
              'phần đó, lưu file thứ hai, khai báo cả hai trong "xac_nhan".'
              % ','.join(map(str, con_lai)), file=sys.stderr)
    if dung:
        print('BỊ CHẶN: %s. Dừng, báo người dùng (SKILL.md §1.5).' % dung, file=sys.stderr)


if __name__ == '__main__':
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:4])
