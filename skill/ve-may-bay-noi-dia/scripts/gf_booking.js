/* Google Flights: đọc TRANG ĐẶT VÉ của từng chuyến, xem ai bán, giá bao nhiêu, phí gì.
 *
 * DÙNG: dán vào mcp__playwright__browser_run_code_unsafe. Dán danh sách FLIGHTS mà
 *       `merge_sources.py job.json checkpoint.json --de-xuat` in ra vào khối tham số.
 * MỤC ĐÍCH: bước xác nhận nơi mua (SKILL.md §6). Chỉ ĐỌC trang: không bấm "Tiếp tục",
 *           không đăng nhập. Đọc references/gf-booking.md trước.
 * TRẢ VỀ: chuỗi JSON { ket_qua: [...], con_lai: [...], dung: "..." }.
 *         Lưu NGUYÊN VĂN ra file (vd gf_booking_raw.json) rồi khai báo trong job.json
 *         ở khoá "xac_nhan". `con_lai` khác rỗng = hết ngân sách thời gian, gọi lại
 *         script với FLIGHTS = con_lai, rồi gộp các mảng ket_qua vào cùng một file.
 *
 * Link trang đặt vé (tham số tfs) do merge_sources.py dựng từ ngày + chặng + số hiệu.
 * Đã kiểm chứng 23/10/2026: mở ở context trắng, không cookie, ra đúng chuyến 3/3 hãng.
 */
async (page) => {
  // ---- dán / sửa khối này ----
  const FLIGHTS = [
    // { url: '...', sh: 'VJ 632', dep: '20:10', ngay: '2026-11-14', tu: 'SGN', den: 'DAD' },
  ];
  const BUDGET_MS = 25000;   // dừng sớm, tránh chạm trần thời gian của một MCP request
  const WAIT_MS   = 15000;   // tối đa chờ một trang đặt vé
  // -----------------------------

  const t0 = Date.now();
  const OK_MARK   = 'Giá bao gồm các loại phí';                  // chân khối "Tùy chọn đặt vé"
  const GONE_MARK = 'hành trình trước đây bạn chọn bây giờ không còn nữa';
  const BLOCK_RE  = /lưu lượng truy cập bất thường|unusual traffic/i;   // trang captcha của Google
  const luc = () => new Date().toLocaleString('sv-SE', { timeZone: 'Asia/Ho_Chi_Minh' })
    .replace(/^(\d{4})-(\d{2})-(\d{2}) (\d{2}:\d{2}).*$/, '$3/$2/$1 $4') + ' (giờ VN)';
  const vnd = s => +s.replace(/[^\d]/g, '');

  const ket_qua = [], con_lai = [];
  let dung = '';

  for (const f of FLIGHTS) {
    if (dung || Date.now() - t0 > BUDGET_MS) { con_lai.push(f); continue; }
    const r = { ...f, luc: '', trang_thai: 'Lỗi', ly_do: '', chuyen: '', ban: [], hanh_ly: [] };
    try {
      await page.goto(f.url, { waitUntil: 'domcontentloaded', timeout: WAIT_MS });
      await page.waitForFunction(([a, b]) => {
        const t = document.body ? document.body.innerText : '';
        return t.includes(a) || t.includes(b) || /lưu lượng truy cập bất thường|unusual traffic/i.test(t);
      }, [OK_MARK, GONE_MARK], { timeout: WAIT_MS });
    } catch (e) { /* xử lý theo nội dung trang ở dưới */ }
    r.luc = luc();

    const url = page.url();
    const t = (await page.evaluate(() => document.body ? document.body.innerText : ''))
      .replace(/\u00a0/g, ' ');
    if (/\/sorry\/|consent\.google/.test(url) || BLOCK_RE.test(t)) {
      // Captcha hoặc trang consent: SKILL.md §1.5, dừng toàn bộ, báo người dùng.
      // Đã gặp 23/10/2026 sau ~25 lượt tải trang Google liên tiếp từ một IP.
      r.ly_do = 'Google chặn (captcha/consent) tại ' + url.slice(0, 80);
      ket_qua.push(r); dung = r.ly_do; continue;
    }
    if (t.includes(GONE_MARK)) {
      r.trang_thai = 'Không khả dụng';
      r.ly_do = 'Google Flights báo hành trình không còn (hết chỗ, hết bán, hoặc sai số hiệu)';
      ket_qua.push(r); continue;
    }
    const iSel = t.indexOf('Các chuyến bay bạn đã chọn');
    const iOpt = t.indexOf('Tùy chọn đặt vé');
    const iEnd = t.indexOf(OK_MARK, iOpt);
    if (iSel < 0 || iOpt < 0 || iEnd < 0) {
      r.ly_do = 'Trang đặt vé không nạp xong trong ' + WAIT_MS / 1000 + 's: '
              + t.slice(0, 160).replace(/\n+/g, ' | ');
      ket_qua.push(r); continue;
    }

    // Khối chuyến đã chọn: dùng để kiểm đúng chuyến + đọc hành lý.
    const sel = t.slice(iSel, iOpt).split('\n').map(s => s.trim()).filter(Boolean);
    r.chuyen = sel.slice(2, 9).join(' | ');
    r.hanh_ly = sel.filter(s => /hành lý/i.test(s) && /^(Miễn phí|Có tính phí|Không|Bao gồm)/.test(s));

    // Khối người bán. Mẫu đã gặp (mỗi mục một dòng):
    //   "Đặt vé của VietjetHãng hàng không" / "Bao gồm phí tiện lợi 100.000 ₫" / "742.061 ₫" / "Tiếp tục"
    //   "Đặt vé của Jettzy" / "679.301 ₫" / "Tiếp tục"
    let cur = null;
    for (const line of t.slice(iOpt, iEnd).split('\n').map(s => s.trim()).filter(Boolean)) {
      const m = line.match(/^Đặt vé (?:của|với|qua) (.+)$/);
      if (m) {
        const hang = /Hãng hàng không$/.test(m[1]);
        cur = { nguoi_ban: m[1].replace(/\s*Hãng hàng không$/, '').trim(),
                loai: hang ? 'Hãng hàng không' : 'Đại lý', gia: null, ghi_chu: [] };
        r.ban.push(cur);
        continue;
      }
      if (!cur) continue;
      if (/^[\d.]+\s*₫$/.test(line)) { if (cur.gia === null) cur.gia = vnd(line); continue; }
      if (/^(Tiếp tục|Tùy chọn xem|Cách xếp hạng|Tìm hiểu thêm)/.test(line)) continue;
      cur.ghi_chu.push(line);
    }
    r.ban.forEach(b => { b.ghi_chu = b.ghi_chu.join('; '); });

    // SANITY CHECK: thiếu cái này thì trang đổi giao diện sẽ cho ra 0 người bán mà không ai biết.
    const warn = [];
    if (f.dep && !sel.includes(f.dep)) warn.push(`giờ đi ${f.dep} không thấy trong khối chuyến đã chọn`);
    if (!r.ban.length) warn.push('không đọc được người bán nào, nghi trang đổi giao diện');
    if (r.ban.some(b => b.gia === null)) warn.push('có người bán thiếu giá');
    if (warn.length) { r.ly_do = warn.join('; '); }
    else { r.trang_thai = 'OK'; }
    ket_qua.push(r);
  }

  return JSON.stringify({ ket_qua, con_lai, dung }, null, 0);
}
