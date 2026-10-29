# -*- coding: utf-8 -*-
"""Dış yapay zekâ (Kimi / Gemini / ChatGPT) ile belge denetimi.

Bir denetim isteğini (Markdown) ve ek dosyaları (satır numaralı TAM metin) sırayla verilen sağlayıcılara sorar;
ilk başarılı cevabı yapılandırılmış JSON olarak kaydeder. Harita doldurucunun istemcisini, kotasını ve anahtar
dosyasını kullanır (UxbRAG\\UXB_HYBRID_RAG_V4_YORUMLU_JSON\\tools\\uxb_harita_doldur.py) — günlük sınırlar ortaktır
ve aşılmaz. Diskteki hiçbir kaynağı değiştirmez.

  python tools/kitap/dis_danis.py --istek istek.md --ek docs/kitaplar/_ortak/dil_tanimi/alanlar/05_ifadeler/bolum.md \
         --ek src/parser/parser/parser_expr.fbs --saglayici kimi,gemini2,gemini --cikti cevap.json

Çıkış kodu: 0 cevap alındı, 1 hiçbir sağlayıcı cevap vermedi (sebep cikti dosyasında ve ekranda).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

KOK = Path(__file__).resolve().parents[2]                       # ...\uxb
V4_TOOLS = KOK.parent / "UxbRAG" / "UXB_HYBRID_RAG_V4_YORUMLU_JSON" / "tools"
sys.path.insert(0, str(V4_TOOLS))
import uxb_harita_doldur as hd  # noqa: E402

SEMA = {
    "type": "object",
    "properties": {
        "ozet": {"type": "string"},
        "bulgular": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "tur": {"type": "string", "description": "YANLIŞ | KANITSIZ | EKSİK | ÇELİŞKİ | TUTARSIZ"},
                    "iddia": {"type": "string"},
                    "neden": {"type": "string"},
                    "kanit": {"type": "string", "description": "dosya:satır ya da belge#başlık"},
                    "oneri": {"type": "string"},
                },
                "required": ["tur", "iddia", "neden", "kanit", "oneri"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["ozet", "bulgular"],
    "additionalProperties": False,
}

SISTEM = (hd.GENEL_BAGLAM + "\nGörevin: sana verilen uXBasic Dil Tanımı metnini, yine sana verilen kaynak kod ve tasarım "
          "belgelerine karşı DENETLEMEK. Yalnız verilen metinlerden kanıtlayabildiğin bulguyu yaz; her bulguda kanıt "
          "olarak 'dosya:satır' (L öneklerindeki numara) ya da 'belge#başlık' ver. Emin olmadığın şeyi yazma. "
          "Bulgu yoksa boş liste döndür. Çıktı: {\"ozet\": kısa Türkçe özet, \"bulgular\": [...]}.")

SINIR = 600_000   # karakter; daha büyük istekler bölünmeli


def numarali(yol: Path) -> str:
    satirlar = yol.read_text(encoding="utf-8", errors="replace").splitlines()
    rel = yol.resolve().relative_to(KOK) if yol.resolve().is_relative_to(KOK) else yol
    return f"\n===== DOSYA: {rel} ({len(satirlar)} satır) =====\n" + "\n".join(
        f"L{i}| {s}" for i, s in enumerate(satirlar, 1))


def main() -> int:
    ap = argparse.ArgumentParser(description="Belge bölümünü dış modele denetletir.")
    ap.add_argument("--istek", required=True, help="Denetim görevini anlatan Markdown dosyası")
    ap.add_argument("--ek", action="append", default=[], help="İsteğe eklenecek dosya (birden çok)")
    ap.add_argument("--saglayici", default="kimi,gemini2,gemini", help="Sırayla denenecek sağlayıcılar")
    ap.add_argument("--cikti", required=True, help="Cevabın yazılacağı JSON dosyası")
    ap.add_argument("--max-token", type=int, default=16000)
    a = ap.parse_args()

    istek = Path(a.istek).read_text(encoding="utf-8")
    ekler = []
    for e in a.ek:
        p = Path(e) if Path(e).is_absolute() else KOK / e
        if not p.is_file():
            raise SystemExit(f"Ek dosya yok: {e}")
        ekler.append(numarali(p))
    kullanici = istek + "\n\n" + "".join(ekler)
    if len(kullanici) > SINIR:
        raise SystemExit(f"İstek çok büyük ({len(kullanici)} karakter > {SINIR}); daha az/küçük ek verin.")

    cfg = hd.ayarlari_oku()
    kayit = {"istek": str(Path(a.istek).resolve()), "ekler": a.ek, "denemeler": [], "durum": "CEVAP_YOK"}
    for sag in [s.strip().lower() for s in a.saglayici.split(",") if s.strip()]:
        if sag not in hd.SAGLAYICILAR:
            kayit["denemeler"].append({"saglayici": sag, "hata": "bilinmeyen sağlayıcı"})
            continue
        ist = hd.istemci_kur(sag, cfg, argparse.Namespace(model="", rpm=0, rpd=-1, max_istek=0))
        if ist is None:
            kayit["denemeler"].append({"saglayici": sag, "hata": "anahtar yok"})
            continue
        t0 = time.time()
        try:
            cevap = ist.sor(SISTEM, kullanici, SEMA, a.max_token)
        except hd.ModelHata as e:
            kayit["denemeler"].append({"saglayici": sag, "model": ist.model, "hata": f"{e.kind}: {str(e)[:300]}"})
            print(f"[{sag}] {e.kind}: {str(e)[:200]}", flush=True)
            continue
        if not isinstance(cevap, dict) or "bulgular" not in cevap:
            kayit["denemeler"].append({"saglayici": sag, "model": ist.model, "hata": "şemaya uymayan cevap"})
            continue
        kayit.update({"durum": "CEVAP_VAR", "saglayici": sag, "model": ist.model,
                      "sure_sn": round(time.time() - t0, 1), "cevap": cevap})
        break
    Path(a.cikti).parent.mkdir(parents=True, exist_ok=True)
    Path(a.cikti).write_text(json.dumps(kayit, ensure_ascii=False, indent=2), encoding="utf-8")
    if kayit["durum"] == "CEVAP_VAR":
        print(f"{kayit['saglayici']} ({kayit['model']}): {len(kayit['cevap']['bulgular'])} bulgu, {kayit['sure_sn']} sn -> {a.cikti}")
        return 0
    print("Hiçbir sağlayıcı cevap vermedi:", "; ".join(f"{d['saglayici']}: {d.get('hata', '')}" for d in kayit["denemeler"]))
    return 1


if __name__ == "__main__":
    sys.exit(main())
