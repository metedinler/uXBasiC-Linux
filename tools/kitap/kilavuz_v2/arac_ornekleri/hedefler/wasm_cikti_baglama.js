// KONU: uXBasic programını WASM'a derleyip ana bilgisayar (host) içe aktarmalarıyla çalıştırmak ve PRINT çıktısını yakalamak
// KOMUTLAR: uxb wat --emit-wasm --wasm-out --wat-out --wat2wasm · ux_wasm_runtime.js · globalThis.uxbWasmImports · WebAssembly.instantiate · MAIN dışa aktarımı
// ACIKLAMA: uXBasic'in WASM çıktısı kendi başına çalışmaz: modül dört "ux" içe aktarması bekler (host_call4, host_call16, print_i32, print_f64); bunları üretilen ux_wasm_runtime.js sağlar (globalThis.uxbWasmImports). Program, dışa aktarılan MAIN işlevidir; her FUNCTION de büyük harfli adla dışa aktarılır (FAKT). Sayı yazdırma print_i32 içe aktarması üzerinden gider: çalışma zamanı sayıyı globalThis.ux.print(metin) ile, satır sonunu globalThis.ux.println() ile bildirir; bu iki işlev tanımlanırsa çıktı konsola değil sizin işlevlerinize gelir. Dikkat: bu yönlendirme yalnız `process` olmayan ortamda (tarayıcıda) uygulanır; node'da çalışma zamanı sayıyı doğrudan standart çıktıya yazar. Bu betik tarayıcıyı, `process` tanımsız bir vm bağlamında çalışma zamanını yükleyerek taklit eder. Aşağıdaki kalıp bir tarayıcı sayfasında da aynen çalışır (WebAssembly.instantiate'e fetch ile alınan bayt dizisi verilir); yerleşik tarayıcıda da sınanmıştır (bkz. Bölüm 21.5). Yalnız tamsayı yazdırılabilir: metin ve ondalık WASM'da henüz yoktur (G-WASM-7, G-WASM-8).
//= dis aktarilan islevler: FAKT, MAIN
//= ice aktarmalar: host_call16, host_call4, print_f64, print_i32 (hepsi ux.* modulunden)
//= yakalanan satirlar: 1 4 9 16 25 55 720
//= FAKT(5) dogrudan cagri: 120
const { spawnSync } = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");
const vm = require("vm");

const UXB = path.resolve(process.env.UXB_EXE || path.join("bin", "uxb.exe"));
const KOK = path.dirname(path.dirname(UXB));
const WAT2WASM = path.join(KOK, "tools", "wabt", "bin", "wat2wasm.exe");
const KAYNAK = [
  "FUNCTION Fakt(n AS I32) AS I32",
  "    IF n <= 1 THEN RETURN 1",
  "    RETURN n * Fakt(n - 1)",
  "END FUNCTION",
  "DIM i AS I32",
  "DIM toplam AS I32 = 0",
  "FOR i = 1 TO 5",
  "    toplam += i * i",
  "    PRINT i * i",
  "NEXT",
  "PRINT toplam",
  "PRINT Fakt(6)",
  "",
].join("\n");

const klasor = fs.mkdtempSync(path.join(os.tmpdir(), "uxb_wasm_"));
fs.writeFileSync(path.join(klasor, "kare.uxb"), KAYNAK);
spawnSync(UXB, ["wat", path.join(klasor, "kare.uxb"), "--emit-wasm", "--wasm-out", path.join(klasor, "kare.wasm"),
  "--wat-out", path.join(klasor, "kare.wat"), "--wat2wasm=" + WAT2WASM, "--out-root", path.join(klasor, "o")], { cwd: KOK, encoding: "utf8" });
for (const dosya of ["kare.wasm", "ux_wasm_runtime.js"]) {
  if (!fs.existsSync(path.join(klasor, dosya))) {
    console.log("URETILEMEDI: " + dosya);
    process.exit(4);
  }
}

const bytes = fs.readFileSync(path.join(klasor, "kare.wasm"));
const modul = new WebAssembly.Module(bytes);
const disAktarilan = WebAssembly.Module.exports(modul).filter((e) => e.kind === "function").map((e) => e.name).sort();
const iceAktarilan = WebAssembly.Module.imports(modul).map((e) => e.name).sort();
console.log("dis aktarilan islevler: " + disAktarilan.join(", "));
console.log("ice aktarmalar: " + iceAktarilan.join(", ") + " (hepsi " + [...new Set(WebAssembly.Module.imports(modul).map((e) => e.module))].join(",") + ".* modulunden)");

// Çalışma zamanı, `process` tanımlıysa (node) sayıyı doğrudan standart çıktıya yazar; `process` yoksa (tarayıcı)
// globalThis.ux.print/println'i çağırır. Tarayıcıyı taklit etmek için `process` tanımsız bir vm bağlamı kullanılır.
const satirlar = [];
let satir = "";
const kumanda = vm.createContext({
  bytes: new Uint8Array(bytes),
  console: { log() {}, error() {} },
  ux: {
    print: (metin) => { satir += metin; },
    println: () => { satirlar.push(satir); satir = ""; },
  },
});
vm.runInContext(fs.readFileSync(path.join(klasor, "ux_wasm_runtime.js"), "utf8"), kumanda);  // globalThis.uxbWasmImports
vm.runInContext(
  "WebAssembly.instantiate(bytes, globalThis.uxbWasmImports).then(function (r) { globalThis.uxbWasmInstance = r.instance; r.instance.exports.MAIN(); globalThis.fakt5 = r.instance.exports.FAKT(5); })",
  kumanda
).then(() => {
  console.log("yakalanan satirlar: " + satirlar.join(" "));
  console.log("FAKT(5) dogrudan cagri: " + kumanda.fakt5);
  fs.rmSync(klasor, { recursive: true, force: true });
});
