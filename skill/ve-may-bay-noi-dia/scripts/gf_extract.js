/* Google Flights — trích danh sách chuyến bay thẳng trong một khung giờ.
 *
 * DÙNG: dán toàn bộ file này vào mcp__claude-in-chrome__javascript_tool,
 *       thay LO/HI ở dòng cuối bằng phút-kể-từ-nửa-đêm.
 *       06:00 = 360 · 10:00 = 600 · 17:00 = 1020 · 22:00 = 1320
 *
 * TRẢ VỀ: mỗi dòng "giờ đi ; giờ đến ; hãng ; số hiệu ; giá"
 *         Giá là chuỗi có dấu chấm ngăn nghìn — bỏ dấu chấm trước khi lưu số.
 *
 * Trang phải nạp xong (chờ ~8s sau navigate). URL one-way:
 *   https://www.google.com/travel/flights?q=Oneway%20flights%20from%20SGN%20to%20DAD%20on%202026-08-06&curr=VND&hl=vi&gl=VN
 */
window.GF = async function (lo, hi) {
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

  // Bung chi tiết CHỈ những dòng trong khung giờ — số hiệu chuyến chỉ hiện sau khi bung.
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
    const t   = x.innerText.replace(/\n+/g, ' | ');
    const fn  = [...new Set((t.match(/(VN|VJ|QH|VU|BL|SP)\s?\d{2,4}/g) || []))].join(',');
    const p   = (t.match(/([\d.]{7,})\s*₫/) || [])[1] || '';
    const tt  = t.match(/\d{2}:\d{2}/g) || [];
    const air = (t.match(/(Vietjet|Vietnam Airlines|Vietravel Airlines|Bamboo Airways|Pacific Airlines|Sun PhuQuoc Airways)/) || [])[1] || '';
    const k   = dep + '|' + air;
    const arr = (tt[1] && tt[1] !== dep) ? tt[1] : '';
    const o   = map[k] || {};
    map[k] = { dep, air, arr: arr || o.arr || '', fn: fn || o.fn || '', p: p || o.p || '' };
  }
  return Object.values(map)
    .sort((a, b) => a.dep.localeCompare(b.dep))
    .map(o => [o.dep, o.arr, o.air, o.fn, o.p].join(' ; '))
    .join('\n');
};
await window.GF(360, 600);
