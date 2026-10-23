// Offline checks for skill/.../scripts/gf_booking.js, no network to Google:
// captcha -> con_lai, stale DOM after a failed goto, recovery after a failed goto, budget cap.
//   node tests/gf_booking_offline.js skill/ve-may-bay-noi-dia/scripts/gf_booking.js
// Run by tests/test_scripts.py when node + the playwright package are available.
const fs = require('fs');
const { chromium } = require('playwright');
const SRC = fs.readFileSync(process.argv[2], 'utf8');
const page_ok = (dep) => 'data:text/html;charset=utf-8,' + encodeURIComponent(
  `<pre>Các chuyến bay bạn đã chọn\nTheo dõi giá\nThứ 7, 14 thg 11\n${dep}\n – \n07:20\nVietjet\n` +
  `Tùy chọn đặt vé\nĐặt vé của VietjetHãng hàng không\n1.000.000 ₫\nTiếp tục\n` +
  `Giá bao gồm các loại phí và thuế bắt buộc cho 1 người lớn.</pre>`);
const captcha = 'data:text/html;charset=utf-8,' + encodeURIComponent('<p>lưu lượng truy cập bất thường</p>');
const blank = 'data:text/html,<p>loading</p>';
const F = (url, sh, dep) => ({ url, sh, dep, ngay: '2026-11-14', tu: 'SGN', den: 'DAD' });
async function run(page, flights, budget) {
  let s = SRC.replace(/const FLIGHTS = \[[\s\S]*?\n  \];/, 'const FLIGHTS = ' + JSON.stringify(flights) + ';');
  if (budget) s = s.replace(/const BUDGET_MS = \d+;/, `const BUDGET_MS = ${budget};`);
  const t0 = Date.now(); const out = JSON.parse(await eval(s)(page)); out.ms = Date.now() - t0; return out;
}
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  let failed = 0;
  const ok = (c, m) => { if (!c) failed++; console.log((c ? 'PASS ' : 'FAIL ') + m); };
  let o = await run(page, [F(page_ok('06:00'), 'VJ 1', '06:00'), F(captcha, 'VJ 2', '07:00'), F(page_ok('08:00'), 'VJ 3', '08:00')]);
  ok(o.ket_qua.length === 1 && o.ket_qua[0].trang_thai === 'OK', 'first flight read OK before captcha');
  ok(o.dung && o.con_lai.map(x => x.sh).join() === 'VJ 2,VJ 3', 'captcha flight + rest go to con_lai: ' + o.con_lai.map(x => x.sh));
  o = await run(page, [F(page_ok('06:00'), 'VJ 1', '06:00'), F('http://127.0.0.1:9/', 'VN 2', '06:00')]);
  ok(o.ket_qua[1] && o.ket_qua[1].trang_thai !== 'OK' && !o.ket_qua[1].ban.length,
     'failed goto does not reuse previous page: ' + (o.ket_qua[1] && o.ket_qua[1].trang_thai + ' / ' + o.ket_qua[1].ly_do.slice(0, 50)));
  o = await run(page, [F(page_ok('06:00'), 'VJ 1', '06:00'), F('http://127.0.0.1:9/', 'VN 2', '06:00'), F(page_ok('08:00'), 'VJ 3', '08:00')]);
  ok(o.ket_qua[2] && o.ket_qua[2].trang_thai === 'OK', 'valid flight right after a failed one is still read: ' + (o.ket_qua[2] && o.ket_qua[2].trang_thai));
  o = await run(page, [F(blank, 'VJ 1', '06:00'), F(page_ok('07:00'), 'VJ 2', '07:00')], 6000);
  ok(o.ms < 8000, 'budget 6000ms respected, took ' + o.ms + 'ms');
  ok(o.con_lai.map(x => x.sh).join() === 'VJ 1,VJ 2' && !o.ket_qua.length, 'budget-cut flight goes to con_lai: ' + o.con_lai.map(x => x.sh));
  await browser.close();
  process.exit(failed ? 1 : 0);
})();
