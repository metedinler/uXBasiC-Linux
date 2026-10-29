# KONU: uxhttp ile bir HTTP hizmetini kullanmak: GET, POST+JSON, yönlendirme, zaman aşımı ve yeniden deneme (üç yerel motorda aynı sonuç)
# KOMUTLAR: uxhttp.Open · SetUrl · SetMethod · AddHeader · SetBody · SetTimeout · FollowRedirects · Perform · Status · ResponseText · ErrorText · uxjson.Parse · uxdatetime.SleepMilliseconds · uxb run · uxb bld
# ACIKLAMA: Python ile yerel bir HTTP hizmeti açılır (dış ağ gerekmez); uXBasic programı onu uxhttp (libcurl) ile çağırır. HTTP durum kodu (404, 500) ile ağ kodu (Perform'un döndürdüğü libcurl kodu: 0 tamam, 3 geçersiz adres, 28 zaman aşımı) ayrı şeylerdir; program ikisini ayrı denetler. Yanıt gövdesi uxjson ile çözülür. Kararsız bir uç noktaya artan beklemeyle yeniden deneme yapılır. Aynı program AST, MIR ve x64 motorlarında çalıştırılıp çıktılar karşılaştırılır. x64 çalıştırılabilir dosyası uxhttp.dll ve bağımlılıklarını bulmak için derleyicinin bin klasörünün PATH'te olmasını ister.
#= GET /merhaba: durum 200, govde merhaba dunya
#= GET /yok: ag kodu 0, durum 404
#= POST /api/topla: adet 4, toplam 10.5, anahtar abc
#= yonlendirme izlendi: 200
#= yonlendirme kapali: 302
#= zaman asimi: kod 28, durum 0
#= gecersiz adres: kod 3
#= yeniden deneme: 3. denemede durum 200
#= motorlar ayni: evet (AST, MIR, x64)
import json, os, shutil, subprocess, sys, tempfile, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

UXB = os.path.abspath(os.environ.get("UXB_EXE", os.path.join("bin", "uxb.exe")))
BIN = os.path.dirname(UXB)
KOK = os.path.dirname(BIN)  # include/modules/... yolları proje kökünden çözülür
RUNTIME_DLL = os.path.join(BIN, "uxb_runtime.dll")


class Isleyici(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def yanit(self, kod, govde, tur="text/plain; charset=utf-8", ek=None):
        b = govde.encode("utf-8")
        try:
            self.send_response(kod)
            self.send_header("Content-Type", tur)
            self.send_header("Content-Length", str(len(b)))
            for k, v in (ek or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(b)
        except OSError:
            pass  # istemci zaman aşımıyla bağlantıyı kapatmış olabilir

    def do_GET(self):
        if self.path == "/merhaba":
            self.yanit(200, "merhaba dunya")
        elif self.path == "/yonlendir":
            self.yanit(302, "", ek={"Location": "/merhaba"})
        elif self.path == "/yavas":
            time.sleep(1.5)
            self.yanit(200, "gec geldim")
        elif self.path == "/kararsiz":
            self.server.kararsiz += 1  # ilk iki çağrı 500, sonrası 200
            if self.server.kararsiz <= 2:
                self.yanit(500, "gecici hata")
            else:
                self.yanit(200, "tamam")
        else:
            self.yanit(404, "bulunamadi")

    def do_POST(self):
        n = int(self.headers.get("Content-Length", "0"))
        veri = self.rfile.read(n).decode("utf-8")
        if self.path == "/api/topla":
            d = json.loads(veri)
            self.yanit(200, json.dumps({"adet": len(d["sayilar"]), "toplam": sum(d["sayilar"]), "anahtar": self.headers.get("X-Anahtar")}), "application/json")
        else:
            self.yanit(404, "bulunamadi")


class Sunucu(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self):
        super().__init__(("127.0.0.1", 0), Isleyici)
        self.kararsiz = 0

    def handle_error(self, request, client_address):
        pass


UXB_KAYNAK = '''INCLUDE "include/modules/uxhttp.uxmh"
INCLUDE "include/modules/uxjson.uxmh"
INCLUDE "include/modules/uxdatetime.uxmh"

DIM sonKod AS I32 = 0
DIM sonDurum AS I64 = 0
DIM sonGovde AS STRING = ""
DIM sonHata AS STRING = ""

' Tek bir HTTP istegi yapar; sonucu sonKod (ag kodu), sonDurum (HTTP durumu), sonGovde, sonHata degiskenlerine yazar
SUB Istek(yontem AS STRING, url AS STRING, govde AS STRING, baslik1 AS STRING, baslik2 AS STRING, zamanAsimi AS I64, izle AS I32)
    DIM h AS U64 = uxhttp.Open()
    DIM rc AS I32
    rc = uxhttp.SetUrl(h, url)
    rc = uxhttp.SetMethod(h, yontem)
    IF LEN(baslik1) > 0 THEN rc = uxhttp.AddHeader(h, baslik1)
    IF LEN(baslik2) > 0 THEN rc = uxhttp.AddHeader(h, baslik2)
    IF LEN(govde) > 0 THEN rc = uxhttp.SetBody(h, govde)
    rc = uxhttp.SetTimeout(h, zamanAsimi)
    rc = uxhttp.FollowRedirects(h, izle)
    sonKod = uxhttp.Perform(h)
    sonDurum = uxhttp.Status(h)
    sonGovde = uxhttp.ResponseText(h)
    sonHata = uxhttp.ErrorText(h)
    uxhttp.Close(h)
END SUB

' Ag hatasi ya da 5xx durumunda artan beklemeyle yeniden dener; kac denemede bittigini verir
FUNCTION GetYenidenDene(url AS STRING, enFazla AS I32) AS I32
    DIM deneme AS I32 = 0
    DIM bekle AS U32 = 50
    DO
        deneme += 1
        Istek("GET", url, "", "", "", 2000, 1)
        IF sonKod = 0 THEN
            IF sonDurum < 500 THEN EXIT DO
        END IF
        IF deneme >= enFazla THEN EXIT DO
        uxdatetime.SleepMilliseconds(bekle)
        bekle = bekle * 2
    LOOP
    RETURN deneme
END FUNCTION

MAIN
    DIM adres AS STRING = "http://127.0.0.1:@PORT@"
    DIM belge AS U64
    DIM kok AS U64
    DIM adet AS I64
    DIM toplam AS F64
    DIM anahtar AS STRING
    DIM n AS I32

    Istek("GET", adres + "/merhaba", "", "", "", 2000, 1)
    PRINT "GET /merhaba: durum "; sonDurum; ", govde "; sonGovde

    Istek("GET", adres + "/yok", "", "", "", 2000, 1)
    PRINT "GET /yok: ag kodu "; sonKod; ", durum "; sonDurum

    Istek("POST", adres + "/api/topla", "{""sayilar"":[1,2,3,4.5]}", "Content-Type: application/json", "X-Anahtar: abc", 2000, 1)
    belge = uxjson.Parse(sonGovde)
    ASSERT belge <> 0, "yanit JSON degil"
    kok = uxjson.Root(belge)
    adet = uxjson.GetI64(uxjson.ObjectGet(kok, "adet"))
    toplam = uxjson.GetF64(uxjson.ObjectGet(kok, "toplam"))
    anahtar = uxjson.GetString(uxjson.ObjectGet(kok, "anahtar"))
    PRINT "POST /api/topla: adet "; adet; ", toplam "; toplam; ", anahtar "; anahtar
    uxjson.Free(belge)

    Istek("GET", adres + "/yonlendir", "", "", "", 2000, 1)
    PRINT "yonlendirme izlendi: "; sonDurum
    Istek("GET", adres + "/yonlendir", "", "", "", 2000, 0)
    PRINT "yonlendirme kapali: "; sonDurum

    Istek("GET", adres + "/yavas", "", "", "", 300, 1)
    PRINT "zaman asimi: kod "; sonKod; ", durum "; sonDurum

    Istek("GET", "bu bir adres degil", "", "", "", 2000, 1)
    PRINT "gecersiz adres: kod "; sonKod

    n = GetYenidenDene(adres + "/kararsiz", 5)
    PRINT "yeniden deneme: "; n; ". denemede durum "; sonDurum
END MAIN
'''


def calistir(komut, cwd):
    ortam = dict(os.environ)
    ortam["PATH"] = BIN + os.pathsep + ortam["PATH"]  # uxhttp.dll ve bagimliliklari icin
    p = subprocess.run(komut, cwd=cwd, capture_output=True, env=ortam, timeout=120)
    return p.returncode, (p.stdout + p.stderr).decode("utf-8", "replace")


def sonuc_satirlari(metin):
    return [s.strip() for s in metin.splitlines() if s.strip() and not s.startswith(("INFO", "WARN"))]


def motor_calistir(motor, klasor):
    sunucu = Sunucu()  # her motor kendi sunucusunu ve sayacini kullanir
    port = sunucu.server_address[1]
    threading.Thread(target=sunucu.serve_forever, daemon=True).start()
    try:
        yol = os.path.join(klasor, "istemci_" + motor + ".uxb")
        open(yol, "w", encoding="utf-8").write(UXB_KAYNAK.replace("@PORT@", str(port)))
        if motor == "AST":
            rc, cikti = calistir([UXB, "run", yol, "--out-root", os.path.join(klasor, "a")], KOK)
        elif motor == "MIR":
            rc, cikti = calistir([UXB, "run", yol, "--interpreter-backend", "MIR", "--out-root", os.path.join(klasor, "m")], KOK)
        else:
            exe = os.path.join(klasor, "istemci.exe")
            calistir([UXB, "bld", yol, "--build-x64", "--build-x64-out", exe, "--out-root", os.path.join(klasor, "x")], KOK)
            if not os.path.exists(exe):
                return ["x64 derlenemedi"]
            if os.path.exists(RUNTIME_DLL):
                shutil.copy(RUNTIME_DLL, klasor)
            rc, cikti = calistir([exe], klasor)
        return sonuc_satirlari(cikti)
    finally:
        sunucu.shutdown()
        sunucu.server_close()


with tempfile.TemporaryDirectory() as klasor:
    sonuclar = {m: motor_calistir(m, klasor) for m in ("AST", "MIR", "x64")}

for satir in sonuclar["AST"]:
    print(satir)
ayni = sonuclar["AST"] == sonuclar["MIR"] == sonuclar["x64"] and len(sonuclar["AST"]) == 8
print("motorlar ayni: " + ("evet (AST, MIR, x64)" if ayni else "HAYIR " + str(sonuclar)))
