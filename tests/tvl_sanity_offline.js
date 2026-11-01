// Offline checks for skill/.../scripts/tvl_playwright.js, no network to Traveloka:
// the cross-leg comparison must flag a truncated body on a THIN route (where the absolute
// MIN_RAW threshold is useless) and must stay quiet when a thin route is simply thin.
//   node tests/tvl_sanity_offline.js skill/ve-may-bay-noi-dia/scripts/tvl_playwright.js
// Run by tests/test_scripts.py when node + the playwright package are available.
// PW_CHROMIUM=/path/to/chromium reuses a browser that is already on disk, for when the
// installed playwright package and the cached browser build do not match.
const fs = require('fs');
const { chromium } = require('playwright');
const SRC = fs.readFileSync(process.argv[2], 'utf8');

// One searchResults entry in the shape the script reads.
const leg = (i, code, name) => ({
  flightMetadata: {
    totalNumStop: 0,
    tripDuration: 55,
    totalCombinedPrice: { currencyValue: { amount: 1000000 + i * 1000 } }
  },
  connectingFlightRoutes: [{
    segments: [{
      seatClass: 'ECONOMY',
      flightNumber: code + ' ' + (100 + i),
      airlineCode: code,
      departureTime: { hour: 6, minute: (i % 6) * 10 },
      arrivalTime: { hour: 7, minute: (i % 6) * 10 }
    }]
  }]
});

const payload = (n, codes) => ({
  data: {
    searchResults: Array.from({ length: n }, (_, i) => leg(i, codes[i % codes.length])),
    airlineDataMap: Object.fromEntries(codes.map(c => [c, { name: c === 'VN' ? 'Vietnam Airlines' : 'Vietjet' }]))
  }
});

async function run(page, perLeg, { minRaw, minHang }) {
  // perLeg: { 'DD-MM-YYYY': { n, codes } }
  const days = Object.keys(perLeg);
  await page.unrouteAll().catch(() => {});
  await page.route('**/flight/fullsearch**', async route => {
    await route.fulfill({
      contentType: 'text/html',
      body: '<html><body><script>fetch("/api/v2/flight/search/initial",{method:"POST"})'
          + '.then(r=>r.json())</script>cho nap</body></html>'
    });
  });
  await page.route('**/flight/search/initial', async route => {
    const d = new URL(route.request().frame().url()).searchParams.get('dt').split('.')[0];
    await route.fulfill({ contentType: 'application/json',
                          body: JSON.stringify(payload(perLeg[d].n, perLeg[d].codes)) });
  });
  let s = SRC
    .replace(/const ROUTE = '[^']*';/, "const ROUTE = 'SGN.DLI';")
    .replace(/const LEGS  = \[[^\]]*\];/, 'const LEGS  = ' + JSON.stringify(days) + ';')
    .replace(/const WIN   = \[[^\]]*\];/, 'const WIN   = [0, 1440];')
    .replace(/const DELAY = \d+;/, 'const DELAY = 0;')
    .replace(/const MIN_RAW  = [^;]+;/, `const MIN_RAW  = ${minRaw};`)
    .replace(/const MIN_HANG = [^;]+;/, `const MIN_HANG = ${minHang};`);
  return await eval(s.replace(/^\/\*[\s\S]*?\*\//, ''))(page);
}

(async () => {
  const browser = await chromium.launch(
    process.env.PW_CHROMIUM ? { executablePath: process.env.PW_CHROMIUM } : {});
  const page = await browser.newPage();
  let failed = 0;
  const ok = (c, m) => { if (!c) failed++; console.log((c ? 'PASS ' : 'FAIL ') + m); };

  // 1. Thin route, consistent across legs: this is the real SGN-DLI shape (2 airlines,
  //    ~6 flights/day). Must NOT be reported as data loss.
  let o = await run(page, {
    '03-12-2026': { n: 6, codes: ['VN', 'VJ'] },
    '04-12-2026': { n: 6, codes: ['VN', 'VJ'] },
    '05-12-2026': { n: 5, codes: ['VN', 'VJ'] }
  }, { minRaw: null, minHang: null });
  ok(/khong co dau hieu body bi cat/.test(o), 'thin but consistent route: no truncation flag');
  ok(!/!!!/.test(o), 'thin route with thresholds off raises no warning at all');

  // 2. Truncated body on a thin route: one leg far below the others. The absolute
  //    threshold cannot catch this (every leg is under 110); the cross-leg check must.
  o = await run(page, {
    '03-12-2026': { n: 6, codes: ['VN', 'VJ'] },
    '04-12-2026': { n: 2, codes: ['VN'] },
    '05-12-2026': { n: 6, codes: ['VN', 'VJ'] }
  }, { minRaw: null, minHang: null });
  ok(/!!! 04-12-2026=2 duoi 50% cua max \(6\)/.test(o),
     'truncated leg on a thin route is flagged by the cross-leg check');

  // 3. Trunk route, the 09/08/2026 failure shape (120/51/77/57/18) must flag the low legs.
  o = await run(page, {
    '25-08-2026': { n: 120, codes: ['VN', 'VJ'] },
    '26-08-2026': { n: 18, codes: ['VN'] }
  }, { minRaw: 110, minHang: 3 });
  ok(/raw=18 < nguong 110/.test(o), 'absolute threshold still fires on a trunk route');
  ok(/duoi 50% cua max \(120\)/.test(o), 'cross-leg check also flags it');

  // 4. A single leg cannot be cross-checked: say nothing rather than a false OK.
  o = await run(page, { '03-12-2026': { n: 6, codes: ['VN', 'VJ'] } }, { minRaw: null, minHang: null });
  ok(!/doi chieu giua/.test(o), 'one leg only: no cross-leg verdict claimed');

  await browser.close();
  process.exit(failed ? 1 : 0);
})();
