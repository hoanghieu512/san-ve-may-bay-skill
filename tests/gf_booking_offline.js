// Offline checks for skill/.../scripts/gf_booking.js, no network to Google:
// captcha -> con_lai, stale DOM after a failed goto, recovery after a failed goto, budget cap.
//   node tests/gf_booking_offline.js skill/ve-may-bay-noi-dia/scripts/gf_booking.js
// Run by tests/test_scripts.py when node + the playwright package are available.
// PW_CHROMIUM=/path/to/chromium reuses a browser that is already on disk, for when the
// installed playwright package and the cached browser build do not match.
const fs = require('fs');
const { chromium } = require('playwright');
const SRC = fs.readFileSync(process.argv[2], 'utf8');
const OUT_DIR = process.argv[3] || '';
const page_ok = (dep) => 'data:text/html;charset=utf-8,' + encodeURIComponent(
  `<pre>Các chuyến bay bạn đã chọn\nTheo dõi giá\nThứ 7, 14 thg 11\n${dep}\n – \n07:20\nVietjet\n` +
  `Tùy chọn đặt vé\nĐặt vé của VietjetHãng hàng không\n1.000.000 ₫\nTiếp tục\n` +
  `Giá bao gồm các loại phí và thuế bắt buộc cho 1 người lớn.</pre>`);
const captcha = 'data:text/html;charset=utf-8,' + encodeURIComponent('<p>lưu lượng truy cập bất thường</p>');
const blank = 'data:text/html,<p>loading</p>';
// Trang có dòng hành lý + hai người bán (một hãng có ghi chú phí, một đại lý): dùng cho
// ca đối chiếu gọn/JSON, nơi cần đủ cả `hanh_ly` lẫn `ghi_chu`.
const page_bag = (dep) => 'data:text/html;charset=utf-8,' + encodeURIComponent(
  `<pre>Các chuyến bay bạn đã chọn\nTheo dõi giá\nThứ 7, 14 thg 11\n${dep}\n – \n07:20\nVietjet\n` +
  `Miễn phí 1 kiện hành lý xách tay\nCó tính phí kiện hành lý ký gửi đầu tiên\n` +
  `Tùy chọn đặt vé\nĐặt vé của VietjetHãng hàng không\nBao gồm phí tiện lợi 100.000 ₫\n` +
  `742.061 ₫\nTiếp tục\nĐặt vé của Jettzy\n679.301 ₫\nTiếp tục\n` +
  `Giá bao gồm các loại phí và thuế bắt buộc cho 1 người lớn.</pre>`);
const gone = 'data:text/html;charset=utf-8,' + encodeURIComponent(
  '<pre>hành trình trước đây bạn chọn bây giờ không còn nữa</pre>');
const F = (url, sh, dep) => ({ url, sh, dep, ngay: '2026-11-14', tu: 'SGN', den: 'DAD' });
function src(flights, budget, gon) {
  let s = SRC.replace(/const FLIGHTS = \[[\s\S]*?\n  \];/, 'const FLIGHTS = ' + JSON.stringify(flights) + ';')
             .replace(/const GON\s*=\s*\w+;/, `const GON       = ${gon};`);
  if (budget) s = s.replace(/const BUDGET_MS = \d+;/, `const BUDGET_MS = ${budget};`);
  // Đổi khối tham số mà regex không khớp nữa thì ca test chạy với giá trị mặc định và
  // "pass" vì lý do sai. Chặn ở đây, đừng để nó im lặng.
  for (const [re, ten] of [[/const FLIGHTS = \[\{|const FLIGHTS = \[\];/, 'FLIGHTS'],
                           [new RegExp('const GON {7}= ' + gon + ';'), 'GON']])
    if (!re.test(s)) throw new Error('khong thay the duoc ' + ten + ' trong gf_booking.js');
  return s;
}
// Mọi ca cũ đọc JSON, nên phải tắt GON (mặc định của script giờ là bật).
async function run(page, flights, budget) {
  const t0 = Date.now(); const out = JSON.parse(await eval(src(flights, budget, false))(page));
  out.ms = Date.now() - t0; return out;
}
const runGon = (page, flights, budget) => eval(src(flights, budget, true))(page);
(async () => {
  const browser = await chromium.launch(
    process.env.PW_CHROMIUM ? { executablePath: process.env.PW_CHROMIUM } : {});
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
  // Chế độ gọn không được mất gì so với JSON. Chạy cùng một bộ chuyến hai lần rồi dump cả
  // hai ra OUT_DIR; tests/test_scripts.py dựng lại bằng gf_booking_gon.py và so từng khoá.
  const RT = [F(page_bag('06:00'), 'VJ 1', '06:00'), F(gone, 'VN 2', '08:00')];
  const full = await run(page, RT);
  const text = await runGon(page, RT);
  ok(text.startsWith('# GON\t1\t2 chuyen'), 'gon header: ' + text.split('\n')[0]);
  ok(text.split('\n').filter(l => l.startsWith('B\t')).length === 2,
     'gon has 2 seller lines: ' + text.split('\n').filter(l => l.startsWith('B\t')).length);
  ok(/^H\tMiễn phí 1 kiện hành lý xách tay ;; Có tính phí/m.test(text), 'gon H line joins hanh_ly');
  ok(!text.includes('data:text/html'), 'gon drops url');
  ok(/^# CON_LAI\t\(het\)$/m.test(text) && /^# DUNG\t\(khong\)$/m.test(text), 'gon footer');
  // Hết ngân sách: con_lai trả về CHỈ SỐ trong FLIGHTS, không trả url.
  const cut = await runGon(page, [F(blank, 'VJ 9', '06:00'), F(page_bag('07:00'), 'VJ 8', '07:00')], 6000);
  ok(/^# CON_LAI\t0,1$/m.test(cut) && !cut.includes('data:text/html'),
     'gon con_lai is indices: ' + (cut.match(/^# CON_LAI.*$/m) || [''])[0]);
  if (OUT_DIR) {
    fs.writeFileSync(OUT_DIR + '/gon.txt', text);
    delete full.ms;
    fs.writeFileSync(OUT_DIR + '/full.json', JSON.stringify(full));
    fs.writeFileSync(OUT_DIR + '/flights.json', JSON.stringify(RT));
  }
  await browser.close();
  process.exit(failed ? 1 : 0);
})();
