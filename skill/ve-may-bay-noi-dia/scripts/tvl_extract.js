/* Traveloka — trích chuyến bay thẳng, GIÁ RẺ NHẤT mỗi chuyến, trong một khung giờ.
 *
 * Traveloka virtualize danh sách: scroll bằng JS KHÔNG nạp thêm dòng.
 * Vì vậy script này tách làm 2 phần và phải xen kẽ với scroll THẬT.
 *
 * QUY TRÌNH (một browser_batch):
 *   1. navigate tới URL fullsearch
 *   2. computer wait 10s
 *   3. javascript_tool: dán file này  →  init + bấm bộ lọc + __cap() lần đầu
 *   4. computer scroll (amount 8)
 *   5. javascript_tool: "await new Promise(r=>setTimeout(r,2500)); window.__cap(LO,HI); 'ok '+Object.keys(window.__acc).length"
 *   6. lặp bước 4-5 thêm 1-2 lần
 *   7. javascript_tool cuối: "window.__cap(LO,HI); window.__out()"
 *
 * Sửa 2 chỗ ở cuối file: danh sách bộ lọc và (LO,HI).
 *   Sáng 06:00-12:00 → ['Buổi sáng'], LO=360 HI=600
 *   Chiều tối 17:00-22:00 → ['Buổi tối','Buổi chiều'], LO=1020 HI=1320
 *
 * URL: https://www.traveloka.com/vi-vn/flight/fullsearch?ap=SGN.DAD&dt=06-08-2026.NA&ps=1.0.0&sc=ECONOMY
 */
window.__acc = {};

window.__cap = function (lo, hi) {
  const all = [...document.querySelectorAll('div')].filter(d => {
    const t = d.innerText || '';
    return /VND\/khách/.test(t) && /Bay thẳng/.test(t) && t.length < 600;   // "Bay thẳng" loại nối chuyến
  });
  const top = all.filter(r => !all.some(o => o !== r && r.contains(o)));
  for (const r of top) {
    const t   = r.innerText.replace(/\n+/g, '|');
    const air = (t.match(/(VietJet Air|Vietnam Airlines|Vietravel Airlines|Bamboo Airways|Pacific Airlines|SUN PhuQuoc AIRWAYS)/) || [])[1];
    if (!air) continue;
    const tt = t.match(/\d{2}:\d{2}/g);
    if (!tt || tt.length < 2) continue;
    const mi = +tt[0].slice(0, 2) * 60 + +tt[0].slice(3);
    if (mi < lo || mi > hi) continue;
    const p = [...t.matchAll(/([\d.]{7,})\s*VND/g)].map(m => +m[1].replace(/\./g, ''));
    if (!p.length) continue;
    const v = Math.min(...p);
    const k = tt[0] + '|' + air;
    // MIN: một chuyến có nhiều hạng vé nằm rời nhau trong danh sách
    if (!window.__acc[k] || v < window.__acc[k].gia)
      window.__acc[k] = { dep: tt[0], arr: tt[1], hang: air, gia: v,
                          bag: (t.match(/\d+\s?x?\s?\d*kg/) || [])[0] || '' };
  }
};

window.__out = function () {
  return Object.values(window.__acc)
    .sort((a, b) => a.dep.localeCompare(b.dep))
    .map(o => [o.dep, o.arr, o.hang, o.gia, o.bag].join(' ; '))
    .join('\n');
};

window.__filter = function (name) {
  // [0] = khối "Giờ khởi hành"; [1] = khối "Giờ đến nơi" — luôn lấy [0]
  const e = [...document.querySelectorAll('div,label,span')]
    .filter(x => (x.innerText || '').trim() === name)[0];
  if (!e) return false;
  let n = e;
  for (let i = 0; i < 3; i++) n = n.parentElement;
  n.click();
  return true;
};

/* --- init --- */
for (let i = 0; i < 25; i++) {
  if (!/Đang tìm kiếm/.test(document.body.innerText)) break;
  await new Promise(r => setTimeout(r, 2000));
}
for (const f of ['Buổi sáng']) {                 // ← sửa danh sách bộ lọc
  window.__filter(f);
  await new Promise(r => setTimeout(r, 4000));
}
window.__cap(360, 600);                          // ← sửa khung giờ
'ok ' + Object.keys(window.__acc).length;
