/* Traveloka qua Playwright MCP — quét nhiều chặng trong MỘT tool call.
 *
 * DÙNG: dán vào mcp__playwright__browser_run_code_unsafe, sửa LEGS + WINDOW ở đầu.
 * Trả về text gọn (~40 dòng/chặng), không screenshot, không file.
 *
 * ĐỌC references/playwright-path.md TRƯỚC — có một bẫy làm mất dữ liệu im lặng.
 */
async (page) => {
  // ---- sửa 3 dòng này ----
  const ROUTE = 'SGN.DAD';
  const LEGS  = ['25-08-2026', '26-08-2026'];     // DD-MM-YYYY
  const WIN   = [345, 630];                        // phút từ nửa đêm; [0,1440] = không lọc
  const DELAY = 2000;                               // ms giữa các chặng
  // ------------------------

  const pad  = t => String(t.hour).padStart(2, '0') + ':' + String(t.minute).padStart(2, '0');
  const mins = s => +s.slice(0, 2) * 60 + +s.slice(3);
  const out  = [];

  for (const d of LEGS) {
    let raw = null;
    // BẪY: giữ PROMISE, chưa await. Await sau, trước khi sang chặng kế.
    const handler = (resp) => {
      if (resp.url().includes('/flight/search/initial') && resp.status() === 200)
        raw = resp.json().catch(() => null);
    };
    page.on('response', handler);

    const url = `https://www.traveloka.com/vi-vn/flight/fullsearch?ap=${ROUTE}&dt=${d}.NA&ps=1.0.0&sc=ECONOMY`;
    try { await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 }); } catch (e) {}
    for (let i = 0; i < 50 && !raw; i++) await page.waitForTimeout(400);

    const payload = raw ? await raw : null;   // <-- BẮT BUỘC await ở đây
    page.off('response', handler);

    if (!payload) { out.push(`=== ${d} :: FAIL — khong bat duoc payload`); continue; }

    const data = payload.data || {};
    const res  = data.searchResults || [];
    const al   = data.airlineDataMap || {};
    const best = {};

    for (const r of res) {
      const m = r.flightMetadata, s = r.connectingFlightRoutes[0].segments;
      if (+m.totalNumStop !== 0) continue;            // chi bay thang
      if (s[0].seatClass !== 'ECONOMY') continue;     // seatClassInventory LUON 'ECONOMY' -> vo dung
      const dep = pad(s[0].departureTime);
      if (mins(dep) < WIN[0] || mins(dep) > WIN[1]) continue;
      const p = +m.totalCombinedPrice.currencyValue.amount;   // da gom thue + phi
      const k = s[0].flightNumber + '|' + dep;               // cung chuyen co nhieu fare family
      if (!best[k] || p < best[k].p)
        best[k] = { f: s[0].flightNumber, a: (al[s[0].airlineCode] || {}).name || s[0].airlineCode,
                    dep, arr: pad(s[s.length - 1].arrivalTime), p,
                    dur: +m.tripDuration };                   // route.durationInMinutes = 0, dung cai nay
    }

    const rows  = Object.values(best).sort((x, y) => x.dep.localeCompare(y.dep));
    const hangs = [...new Set(rows.map(r => r.a))];

    // SANITY CHECK — thieu cai nay thi loi mat du lieu tai dien ma khong ai biet
    const warn = [];
    if (res.length < 110) warn.push(`raw=${res.length} THAP BAT THUONG — nghi body bi cat, QUET LAI`);
    if (hangs.length < 3) warn.push(`chi ${hangs.length} hang — nghi thieu du lieu`);

    out.push(`=== ${d} :: raw=${res.length} -> ${rows.length} chuyen | hang: ${hangs.join('/')}`
             + (warn.length ? '\n!!! ' + warn.join(' ; ') : ''));
    out.push(rows.map(r => [r.dep, r.arr, r.f, r.a, r.p].join(' ; ')).join('\n'));

    if (DELAY) await page.waitForTimeout(DELAY);
  }
  return out.join('\n');
}
