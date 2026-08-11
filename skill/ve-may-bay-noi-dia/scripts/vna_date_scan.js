/* Quét giá thấp nhất TỪNG NGÀY của Vietnam Airlines, cả hai chiều, trong MỘT tool call.
 *
 * DÙNG: dán vào mcp__playwright__browser_run_code_unsafe, sửa khối tham số ở đầu.
 * MỤC ĐÍCH: chọn cặp ngày đáng quét. KHÔNG phải nguồn giá — xem references/vna-date-scan.md.
 *
 * Không cần navigate, không cookie, không captcha. Chỉ 2 request HTTP.
 */
async (page) => {
  // ---- sửa khối này ----
  const ORIG  = 'SGN';
  const DEST  = 'DAD';
  const START = '2026-08-09';        // YYYY-MM-DD, ngày đi sớm nhất cần xét
  const RANGE = 60;                  // số ngày quét tới; trần <= 180.
                                     // Bám sát khoảng người dùng thực sự quan tâm —
                                     // quét 180 ngày ra cặp rẻ nhất ở tận Tết, vô nghĩa
                                     // nếu họ định đi tháng sau.
  const STAYS = [3, 4];              // các độ dài lưu trú cần ghép (đêm)
  const TOP   = 12;                  // số cặp rẻ nhất in ra
  // ----------------------

  const API = 'https://integration-middleware-website.vietnamairlines.com'
            + '/api/v1/public/booking/air-best-price';

  const ctx = await page.context().browser().newContext({ ignoreHTTPSErrors: true });
  const out = [];

  const fetchLeg = async (o, d) => {
    const r = await ctx.request.post(API, {
      headers: { 'content-type': 'application/json' },
      data: { route: { originLocationCode: o, destinationLocationCode: d,
                       departureDateTime: START },
              tripDetails: { rangeOfDeparture: RANGE }, location: 'VN' }
    });
    if (r.status() !== 200) return { err: `HTTP ${r.status()} ${(await r.text()).slice(0, 200)}` };
    const j = await r.json();
    if (!j.success || !j.data || !j.data.prices) return { err: 'payload la: ' + JSON.stringify(j).slice(0, 200) };
    const m = {};
    for (const p of j.data.prices) m[p.departureDate] = +p.price[0].total;
    return { m, n: j.data.prices.length };
  };

  const go = await fetchLeg(ORIG, DEST);
  const ve = await fetchLeg(DEST, ORIG);
  await ctx.close();

  // SANITY CHECK — thieu cai nay thi so lieu thieu troi qua ma khong ai biet
  for (const [ten, r] of [[`${ORIG}-${DEST}`, go], [`${DEST}-${ORIG}`, ve]]) {
    if (r.err) { out.push(`=== ${ten} :: FAIL — ${r.err}`); continue; }
    const ok = r.n >= RANGE * 0.8;
    out.push(`=== ${ten} :: ${ok ? 'OK' : 'NGHI NGO'} — ${r.n}/${RANGE + 1} ngay co gia`);
  }
  if (go.err || ve.err) return out.join('\n');

  const dayName = ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7'];
  const Y0 = START.slice(0, 4);
  // RANGE lon co the tran sang nam sau -> phai hien nam, neu khong 04/01 la mo ho
  const fmt = d => { const [y, m, dd] = d.split('-'); return y === Y0 ? `${dd}/${m}` : `${dd}/${m}/${y.slice(2)}`; };
  const dow = d => dayName[new Date(d + 'T00:00:00Z').getUTCDay()];
  const vnd = n => n.toLocaleString('vi-VN');

  // ---- bang gia tung ngay, chieu di ----
  const diDays = Object.keys(go.m).sort();
  out.push('', `--- ${ORIG}->${DEST} theo ngay (VND, da gom thue phi) ---`);
  out.push(diDays.map(d => `${fmt(d)} ${dow(d)} ${vnd(go.m[d])}`).join('  |  '));

  // ---- ghep cap ----
  const caps = [];
  for (const d of diDays) {
    for (const s of STAYS) {
      const back = new Date(d + 'T00:00:00Z');
      back.setUTCDate(back.getUTCDate() + s);
      const r = back.toISOString().slice(0, 10);
      if (ve.m[r] === undefined) continue;
      caps.push({ d, r, s, tong: go.m[d] + ve.m[r] });
    }
  }
  caps.sort((a, b) => a.tong - b.tong);

  if (!caps.length) {
    out.push('', `KHONG ghep duoc cap nao — RANGE (${RANGE}) qua nho so voi STAYS (${STAYS.join('/')}).`);
    return out.join('\n');
  }

  out.push('', `--- ${TOP} cap re nhat (luu tru ${STAYS.join('/')} dem) ---`);
  for (const c of caps.slice(0, TOP))
    out.push(`${fmt(c.d)} ${dow(c.d)} -> ${fmt(c.r)} ${dow(c.r)}  (${c.s}d)  `
           + `di ${vnd(go.m[c.d])} + ve ${vnd(ve.m[c.r])} = ${vnd(c.tong)}`);

  const re = caps[0], dat = caps[caps.length - 1];
  out.push('', `Bien do: re nhat ${vnd(re.tong)} (${fmt(re.d)}) — dat nhat ${vnd(dat.tong)} `
             + `(${fmt(dat.d)}) — chenh ${((dat.tong / re.tong - 1) * 100).toFixed(0)}%`);
  out.push('LUU Y: gia min-cua-ngay, chi Vietnam Airlines, KHONG gan voi chuyen/khung gio.');

  return out.join('\n');
}
