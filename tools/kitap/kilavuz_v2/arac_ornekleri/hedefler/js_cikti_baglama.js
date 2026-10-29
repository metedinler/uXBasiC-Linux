// KONU: Tarayıcı çıktısı (uxb jsw --emit-browser) ve PRINT çıktısını sayfaya ya da başka bir yere bağlamak (uxb.console.setSink)
// KOMUTLAR: uxb jsw --emit-browser --html-out --js-out · ux_runtime.js · uxb.console.setSink · node
// ACIKLAMA: `uxb jsw --emit-browser` üç dosya üretir: HTML kabuğu, ux_runtime.js (çalışma zamanı) ve program.js. Varsayılan olarak PRINT satırları tarayıcının konsoluna (console.log) gider; HTML kabuğundaki <pre id="uxb-console"> öğesi boş kalır. Çıktıyı sayfaya yazmak için program.js yüklenmeden ÖNCE uxb.console.setSink({ writeLine: ... }) çağrılır; çalışma zamanı sink varsa konsola yazmaz. Üretilen giriş noktası (uxbMain) asenkrondur: program.js yüklenince kendiliğinden başlar ama bir Promise döndürür; bitişini beklemek isteyen kod, program.js'ten önce uxb.autoRun = false yazıp uxbMain()'i kendisi çağırır ve Promise'i bekler. Bu betik üretilen dosyaları node ile iki kipte çalıştırır (sink'siz ve sink'li) ve kalıbı doğrular; aynı kalıp yerleşik bir tarayıcıda da sınanmıştır (bkz. Bölüm 21.4).
//= html: ux_runtime.js ve program.js baglantili, <pre id="uxb-console"> var
//= sink'siz: 8 satir konsola yazildi
//= sink'li: 8 satir sayfaya yonlendirildi, konsola yazilan satir: 0
//= ilk satir: merhaba tarayici, son satir: 6! = 720
const { spawnSync } = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");

const UXB = path.resolve(process.env.UXB_EXE || path.join("bin", "uxb.exe"));
const KOK = path.dirname(path.dirname(UXB));
const KAYNAK = [
  "FUNCTION Fakt(n AS I32) AS I32",
  "    IF n <= 1 THEN RETURN 1",
  "    RETURN n * Fakt(n - 1)",
  "END FUNCTION",
  "DIM i AS I32",
  "DIM toplam AS I32 = 0",
  'PRINT "merhaba tarayici"',
  "FOR i = 1 TO 5",
  "    toplam += i * i",
  '    PRINT i; " karesi = "; i * i',
  "NEXT",
  'PRINT "kareler toplami = "; toplam',
  'PRINT "6! = "; Fakt(6)',
  "",
].join("\n");

const klasor = fs.mkdtempSync(path.join(os.tmpdir(), "uxb_web_"));
fs.writeFileSync(path.join(klasor, "kare.uxb"), KAYNAK);
const derle = spawnSync(UXB, ["jsw", path.join(klasor, "kare.uxb"), "--emit-browser", "--html-out", path.join(klasor, "kare.html"),
  "--js-out", path.join(klasor, "kare.js"), "--out-root", path.join(klasor, "o")], { cwd: KOK, encoding: "utf8" });
for (const dosya of ["kare.html", "kare.js", "ux_runtime.js"]) {
  if (!fs.existsSync(path.join(klasor, dosya))) {
    console.log("URETILEMEDI: " + dosya + " " + (derle.stderr || "").slice(-200));
    process.exit(4);
  }
}

const html = fs.readFileSync(path.join(klasor, "kare.html"), "utf8");
if (html.includes('src="ux_runtime.js"') && html.includes('src="kare.js"') && html.includes('id="uxb-console"')) {
  console.log("html: ux_runtime.js ve program.js baglantili, <pre id=\"uxb-console\"> var");
}

// 1) sink'siz: PRINT satırları console.log'a gider (node'da standart çıktı)
const sinksiz = spawnSync("node", [path.join(klasor, "kare.js")], { encoding: "utf8" });
const satirlar1 = sinksiz.stdout.split(/\r?\n/).filter((s) => s.length > 0);
console.log("sink'siz: " + satirlar1.length + " satir konsola yazildi");

// 2) sink'li: çalışma zamanı program.js'ten önce yüklenir, otomatik başlatma kapatılır, sink bağlanır;
//    üretilen giriş noktası (uxbMain) asenkrondur ve bir Promise döndürür, bitişi beklenir
fs.writeFileSync(path.join(klasor, "calistir.js"), [
  'require("./ux_runtime.js");',
  "uxb.autoRun = false;",
  "const toplanan = [];",
  "uxb.console.setSink({ writeLine: (satir) => toplanan.push(satir) });",
  'require("./kare.js");',
  "globalThis.uxbMain().then(() => console.log(JSON.stringify(toplanan)));",
].join("\n"));
const sinkli = spawnSync("node", [path.join(klasor, "calistir.js")], { cwd: klasor, encoding: "utf8" });
const cikti = sinkli.stdout.split(/\r?\n/).filter((s) => s.length > 0);
const toplanan = JSON.parse(cikti[cikti.length - 1]);
console.log("sink'li: " + toplanan.length + " satir sayfaya yonlendirildi, konsola yazilan satir: " + (cikti.length - 1));
console.log("ilk satir: " + toplanan[0] + ", son satir: " + toplanan[toplanan.length - 1]);
fs.rmSync(klasor, { recursive: true, force: true });
