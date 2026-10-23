/* Google Flights: trích danh sách chuyến bay thẳng trong một khung giờ.
 *
 * DÙNG: dán toàn bộ file này vào mcp__claude-in-chrome__javascript_tool,
 *       thay LO/HI ở dòng cuối bằng phút-kể-từ-nửa-đêm.
 *       06:00 = 360 · 10:00 = 600 · 17:00 = 1020 · 22:00 = 1320
 *
 * TRẢ VỀ: dòng đầu "# luc DD/MM/YYYY HH:MM (giờ VN) | trang co N dong, trong khung gio M":
 *         chép phần thời điểm vào `_thu_thap` của file thô (references/merge-sources.md).
 *         "# CHAN: ..." = captcha, "# CANH BAO: 0 dong ..." = trang trống: KHÔNG phải
 *         "không có chuyến", dừng và báo người dùng. Sau dòng đầu là mỗi dòng
 *         "giờ đi ; giờ đến ; hãng ; số hiệu ; giá" -> cot ["dep","arr","hang","sh","gia"].
 *         Giá là chuỗi có dấu chấm ngăn nghìn: bỏ dấu chấm trước khi lưu số.
 *
 * Trang phải nạp xong (chờ ~8s sau navigate). URL one-way:
 *   https://www.google.com/travel/flights?q=Oneway%20flights%20from%20SGN%20to%20DAD%20on%202026-08-06&curr=VND&hl=vi&gl=VN
 */
window.GF = async function (lo, hi) {
  // Trang captcha "lưu lượng truy cập bất thường" không có dòng chuyến bay nào: nếu không
  // chặn ở đây, kết quả trông y như "khung giờ này không có chuyến" (đã xảy ra 23/10/2026).
  if (/lưu lượng truy cập bất thường|unusual traffic/i.test(document.body.innerText) ||
      /\/sorry\//.test(location.pathname))
    return '# CHAN: Google bao luu luong bat thuong (captcha). DUNG, bao nguoi dung (SKILL.md §1.5)';
  // Nhận diện dòng chuyến bay bằng aria-label "Thời gian khởi hành", KHÔNG bằng chuỗi
  // "SGN–DAD": sau khi bung chi tiết, Google Flights đổi sang dạng "(DAD)" và mọi
  // regex dựa trên mã sân bay sẽ loại sạch dòng ở lượt đọc thứ hai.
  const depLabel = x => [...x.querySelectorAll('[aria-label]')]
      .map(e => e.getAttribute('aria-label'))
      .find(s => /^Thời gian khởi hành/.test(s));
  const rows = () => {
    let r = [...document.querySelectorAll('li')].filter(
      l => l.innerText && /₫/.test(l.innerText) && depLabel(l));
    return r.filter(x => !r.some(o => o !== x && x.contains(o)));   // bỏ li lồng nhau
  };
  const depOf = x => {
    const a = depLabel(x);
    if (!a) return null;
    const m = a.match(/(\d{2}):(\d{2})/);
    if (!m) return null;
    const mins = +m[1] * 60 + +m[2];
    return (mins >= lo && mins <= hi) ? m[0] : null;
  };

  // Bung chi tiết CHỈ những dòng trong khung giờ: số hiệu chuyến chỉ hiện sau khi bung.
  for (const x of rows()) {
    if (!depOf(x)) continue;
    const b = [...x.querySelectorAll('button')]
      .find(y => (y.getAttribute('aria-label') || '').startsWith('Thông tin'));
    if (b) b.click();
  }
  await new Promise(r => setTimeout(r, 4500));

  const map = {};
  for (const x of rows()) {
    const dep = depOf(x);
    if (!dep) continue;
    const t   = x.innerText.replace(/\u00a0/g, ' ').replace(/\n+/g, ' | ');   // số hiệu dùng NBSP: "VJ\u00a0636"
    // 9G = Sun PhuQuoc Airways (trên trang hiện "A321neo9G 954"), KHÔNG phải SP.
    const fn  = [...new Set((t.match(/(VN|VJ|QH|VU|BL|9G)\s?\d{2,4}/g) || []))].join(',');
    const p   = (t.match(/([\d.]{7,})\s*₫/) || [])[1] || '';
    const tt  = t.match(/\d{2}:\d{2}/g) || [];
    const air = (t.match(/(Vietjet|Vietnam Airlines|Vietravel Airlines|Bamboo Airways|Pacific Airlines|Sun PhuQuoc Airways)/) || [])[1] || '';
    const k   = dep + '|' + air;
    const arr = (tt[1] && tt[1] !== dep) ? tt[1] : '';
    const o   = map[k] || {};
    map[k] = { dep, air, arr: arr || o.arr || '', fn: fn || o.fn || '', p: p || o.p || '' };
  }
  const luc = new Date().toLocaleString('sv-SE', { timeZone: 'Asia/Ho_Chi_Minh' }).replace(/^(\d{4})-(\d{2})-(\d{2}) (\d{2}:\d{2}).*$/, '$3/$2/$1 $4') + ' (giờ VN)';
  // 0 dòng trên cả trang = trang chưa nạp xong hoặc bị chặn, KHÔNG phải "không có chuyến".
  const tong = rows().length;
  if (!tong) return '# CANH BAO: 0 dong chuyen bay tren ca trang (chua nap xong?). Khong dung ket qua nay, quet lai';
  return ['# luc ' + luc + ' | trang co ' + tong + ' dong, trong khung gio ' + Object.keys(map).length].concat(Object.values(map)
    .sort((a, b) => a.dep.localeCompare(b.dep))
    .map(o => [o.dep, o.arr, o.air, o.fn, o.p].join(' ; ')))
    .join('\n');
};
await window.GF(360, 600);
