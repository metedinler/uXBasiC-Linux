# -*- coding: utf-8 -*-
"""uXBasic programlama kuralları belgesini üretir: docs/kitaplar/UXBASIC_PROGRAMLAMA_KURALLARI.md

Amaç: yerel kodlayıcı model (uxcoder / qwen2.5-coder) ve insanlar için, dilin KURALLARINI ve her yapının çalışan yazımını tek yerde
vermek. Belge uydurma içermez: her {{ORNEK:grup/ad}} yer tutucusu, örneğin AST, MIR ve native x64'te GEÇTİĞİ kayıtlı sonuçlardan
(ornek_sonuclari*.json) doğrulanmışsa kod + çıktı ile, doğrulanmamışsa "DOĞRULANMADI + motor durumları" ile doldurulur.

Kullanım: python tools/kitap/kural_belgesi_uret.py            (önce ornek_dogrula.py ile sonuçlar güncel olmalı)
Girdi:  docs/kitaplar/_ortak/ornekler/**.uxb ve ornek_sonuclari_20261007.json + ornek_sonuclari_22.json (son çalıştırmalar)
Çıktı:  docs/kitaplar/UXBASIC_PROGRAMLAMA_KURALLARI.md  +  docs/kitaplar/_ortak/kural_dogrulama_ozeti.json
"""
import json
import os
import re

KOK = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ORTAK = os.path.join(KOK, "docs", "kitaplar", "_ortak")
CIKTI = os.path.join(KOK, "docs", "kitaplar", "UXBASIC_PROGRAMLAMA_KURALLARI.md")
SONUC_DOSYALARI = ["ornek_sonuclari_20261007.json", "ornek_sonuclari_22.json", "ornek_sonuclari_23.json",
                   "ornek_sonuclari_20261007b.json",
                   "ornek_sonuclari_codex_20261007_final.json"]  # sonrakiler öncekini ezer; Codex kaydı gerçek son kabul kanıtıdır


def sonuclari_oku():
    s = {}
    for ad in SONUC_DOSYALARI:
        p = os.path.join(ORTAK, ad)
        if os.path.exists(p):
            for e in json.load(open(p, encoding="utf-8")):
                s[e["dosya"].split("ornekler/")[-1]] = e
    return s


SONUC = sonuclari_oku()
DURUM = {"ornek": 0, "dogrulandi": 0, "dogrulanmadi": []}


def ornek(anahtar):
    """{{ORNEK:grup/ad}} -> markdown. Doğrulanmışsa kod+çıktı, değilse durum satırı."""
    DURUM["ornek"] += 1
    yol = os.path.join(ORTAK, "ornekler", anahtar + ".uxb")
    if not os.path.exists(yol):
        DURUM["dogrulanmadi"].append(anahtar)
        return f"> _Örnek dosyası yok: {anahtar}_"
    satirlar = open(yol, encoding="utf-8").read().splitlines()
    kod = "\n".join(l for l in satirlar if not l.startswith(("' KONU", "' KOMUTLAR", "' ACIKLAMA", "'=")))
    beklenen = [l[2:].strip() for l in satirlar if l.startswith("'=")]
    r = SONUC.get(anahtar + ".uxb")
    if r and r.get("hepsi") and beklenen:
        DURUM["dogrulandi"] += 1
        return (f"```basic\n{kod.strip()}\n```\nÇıktı **[DOĞRULANDI: AST, MIR, native x64]**:\n```text\n" + "\n".join(beklenen) + "\n```")
    durum = ", ".join(f"{m}={v['durum']}" for m, v in (r or {"motor": {}})["motor"].items()) or "sonuç kaydı yok"
    DURUM["dogrulanmadi"].append(anahtar)
    return (f"> **DOĞRULANMADI** ({durum}). Tasarıma göre yazılmış örnek aşağıdadır; çalışır sayma.\n```basic\n{kod.strip()}\n```")


ŞABLON = r'''# uXBasic Programlama Kuralları

_Bu belge otomatik üretilir (`tools/kitap/kural_belgesi_uret.py`). Amaç: uXBasic kodu yazan kişinin ve yerel kodlayıcı modelin (uxcoder)
dilin kurallarını, her yapının **çalışan** yazımını ve bilinen sınırları tek yerde görmesi._

## 0. Okuma kuralları (kanıt işaretleri)

- **[DOĞRULANDI]** — örnek AST yorumlayıcı, MIR yorumlayıcı ve native x64'te çalıştırıldı, çıktısı beklenenle birebir aynı.
- **[HEDEF]** — tasarım belgesinde var, ama çalıştırılarak doğrulanmadı. Yeni kodda güvenme.
- **[YOK / SINIR]** — denendi, çalışmıyor ya da motorlar arasında farklı. Bölüm 17'de listelidir.
- Bu belge ile `docs/tasarim/uXBasic_Hedeflenen_Sistem_ve_Kullanma_Kilavuzu_TR_2026-09-24 (1).md` arasında fark varsa **bu belge doğrudur**
  (kılavuz hedef tasarımdır; farklar Bölüm 16'dadır).

## 1. Temel kurallar (Mete'nin kesin kuralları)

1. **Tip adları:** `I8 U8 I16 U16 I32 U32 I64 U64 F32 F64 F80 F128 BIGINT BIGF BIGD BALL BOOLEAN STRING WSTRING`.
   **`LONG`, `INTEGER`, `DOUBLE`, `SINGLE`, `BYTE` adları ve `$ # % ! &` tip son ekleri uXBasic'te YOKTUR.** (`LEFT$` değil `LEFT`, `CHR$` değil `CHR`.)
2. **Tip dönüştürme tip adıyla yapılır:** `I8(x)`, `U8(x)`, `I32(x)`, `F32(x)`. Klasik `CINT CLNG CDBL CSNG FIX INT` de vardır.
3. **Büyük/küçük harf ayrımı yok.** Tip adları ve değişken adları aynı ad alanındadır (`CLASS K` varken `DIM k` hata).
4. **`TRUE = -1`, `FALSE = 0`.** Karşılaştırma sonucu doğruysa `-1` yazdırılır.
5. **`^` üs değil XOR'dur;** üs alma `**`'dır.
6. **Satır sonu deyim ayırıcıdır;** `:` ile aynı satıra birden çok deyim yazılabilir.
7. **Aynı program her motorda aynı sonucu vermelidir** (AST yorumlayıcı, MIR yorumlayıcı, native x64; ayrıca JS/WASM hedefleri).
8. Yorum satırı `'` ile başlar.

## 2. Program yapısı

Üst düzey deyimler doğrudan çalışır; istenirse giriş noktası `MAIN ... END MAIN` bloğudur:

{{ORNEK:22_kurallar/main_end}}

Yordamlar:

{{ORNEK:06_rutin/sub_function}}

- `BYVAL` kopya verir, `BYREF` asıl değişkeni verir:

{{ORNEK:06_rutin/byref_byval}}

- `CALL` ile yordam çağrısı, `DECLARE` ile ileri bildirim, özyineleme desteklenir, `STATIC` yerel değişken çağrılar arasında değerini korur:

{{ORNEK:06_rutin/call}}

{{ORNEK:06_rutin/declare_ileri}}

{{ORNEK:06_rutin/ozyineleme}}

{{ORNEK:06_rutin/static_yerel}}

- Dizi parametresi:

{{ORNEK:06_rutin/dizi_parametre}}

## 3. Değişken, sabit, dizi

{{ORNEK:15_tipler/const_dim_redim}}

{{ORNEK:15_tipler/dizi_cok_boyut}}

Üst düzeyde bildirilen değişken aynı dosyadaki rutinlerden okunup yazılabilir (**`DIM SHARED` sözdizimi yoktur**):

{{ORNEK:22_kurallar/ust_duzey_degisken}}

Tipler:

{{ORNEK:15_tipler/tamsayi_tipleri}}

{{ORNEK:15_tipler/dar_tamsayi}}

{{ORNEK:15_tipler/ondalik_tipleri}}

{{ORNEK:15_tipler/u64}}

{{ORNEK:15_tipler/f80}}

{{ORNEK:15_tipler/string_boolean}}

`DEFINT/DEFLNG/DEFSNG/DEFDBL/DEFSTR` harf aralığına göre örtük tip verir; bildirimsiz değişken de kullanılabilir:

{{ORNEK:10_deftype/defint}}

{{ORNEK:10_deftype/bildirimsiz}}

## 4. Operatörler

{{ORNEK:13_operator/aritmetik}}

{{ORNEK:13_operator/karsilastirma}}

{{ORNEK:13_operator/mantik}}

{{ORNEK:13_operator/genis_mantik}}

{{ORNEK:13_operator/kisa_devre}}

{{ORNEK:13_operator/kaydirma}}

{{ORNEK:13_operator/bilesik_atama}}

{{ORNEK:13_operator/sayi_tabanlari}}

{{ORNEK:13_operator/negatif_bolme}}

{{ORNEK:13_operator/metin_karsilastirma}}

## 5. Akış denetimi

{{ORNEK:01_akis/if_elseif}}

Tek satırlık `IF ... THEN a ELSE b` (S-083 düzeltmesinden sonra yalnız seçilen dal çalışır; düzeltmeden önceki derleyicilerde iki dal da çalışırdı):

{{ORNEK:01_akis/if_tek_satir}}

{{ORNEK:01_akis/select_case}}

{{ORNEK:22_kurallar/select_case_is}}

{{ORNEK:01_akis/select_case_to}}

{{ORNEK:01_akis/select_case_metin}}

Döngüler:

{{ORNEK:05_dongu/for_step}}

{{ORNEK:05_dongu/while_wend}}

{{ORNEK:05_dongu/do_while_until}}

{{ORNEK:05_dongu/for_each}}

**FOR EACH ile DO EACH aynı şey değildir** (docs/tasarim, 23.09 sistem kararları §13):

- `FOR EACH` **anlık görüntü** (snapshot) alır: virgüllü listedeki bütün ifadeler gövde çalışmadan ÖNCE değerlendirilir.
- `DO EACH` **canlıdır** (JIT): her ifade sırası gelince değerlendirilir; önceki turda yapılan değişiklik sonraki ifadede görünür.

{{ORNEK:23_tasarim/each_snapshot}}

{{ORNEK:23_tasarim/each_canli}}

Metin üzerinde `FOR EACH c, i IN s` kod noktası kod noktası gezer, `i` 0 tabanlı sıradır (bayt ya da JS UTF-16 birimi değil):

{{ORNEK:23_tasarim/each_metin_kodnoktasi}}

**Kural [KARARLI]:** virgüllü `IN` listesi yalnız **skaler değer listesidir** (`IN 10, 20, 30` ya da `IN a, a + 5`). Dizi/koleksiyon/metin
kaynağı adlarını virgülle birleştirmek (`FOR EACH x IN a, b`, burada a ve b dizi) derleme hatasıdır:
`FOR EACH: a is a array; a comma-separated EACH list holds scalar values only` (test: `tests/iterators/neg_each_two_arrays.uxb`).
Çok kaynaklı gezinti gelecekte açık iterator işlevleriyle gelecektir: `CHAIN(a, b)` ve `ZIP(a, b)` **[HEDEF, S-135 — henüz yok]**.
Tek kaynak: `FOR EACH v IN a` dizi, STRING/WSTRING, LIST, DICT, SET üzerinde çalışır.

{{ORNEK:05_dongu/exit_for_do}}

{{ORNEK:05_dongu/continue}}

{{ORNEK:01_akis/exit_if}}

{{ORNEK:01_akis/goto_etiket}}

{{ORNEK:01_akis/gosub_return}}

## 6. Metin ve matematik işlevleri

{{ORNEK:17_metin/len_mid_instr}}

{{ORNEK:17_metin/left_right_case}}

{{ORNEK:17_metin/str_val_chr_asc}}

{{ORNEK:17_metin/hex_oct_bin}}

{{ORNEK:17_metin/trim_space}}

{{ORNEK:17_metin/birlestirme}}

{{ORNEK:17_metin/string_tekrar}}

{{ORNEK:18_matematik/temel}}

{{ORNEK:18_matematik/trig_log}}

{{ORNEK:18_matematik/donusum}}

{{ORNEK:18_matematik/iff}}

{{ORNEK:18_matematik/rnd_randomize}}

## 7. Kayıtlar, yapılar, sayımlar, koleksiyonlar

{{ORNEK:07_yapi/type}}

{{ORNEK:22_kurallar/type_ic_ice}}

{{ORNEK:07_yapi/struct_union}}

{{ORNEK:07_yapi/enum}}

{{ORNEK:16_koleksiyon/list}}

{{ORNEK:16_koleksiyon/dict}}

{{ORNEK:16_koleksiyon/set}}

## 8. Sınıflar ve nesneler

{{ORNEK:07_yapi/class_new}}

{{ORNEK:07_yapi/constructor_destructor}}

{{ORNEK:07_yapi/class_miras}}

{{ORNEK:07_yapi/interface}}

{{ORNEK:07_yapi/property}}

{{ORNEK:08_erisim/public_private}}

**MAGIC metotları** `MAGIC ADI(...) ... END MAGIC` biçimindedir (`END METHOD` ile kapanmaz). Operatör aşırı yükleme `OPERATOR +` ile değil `MAGIC ADD(other)` ile yapılır:

{{ORNEK:22_kurallar/operator_magic_add}}

{{ORNEK:22_kurallar/magic_tostring}}

## 9. Modül, ad alanı, ALIAS, kütüphane

{{ORNEK:09_kapsam/module_using_main}}

{{ORNEK:09_kapsam/namespace}}

{{ORNEK:22_kurallar/alias_kutuphane_adi}}

**Kütüphane kullanımı:** kütüphane `INCLUDE "include/modules/<ad>.uxmh"` ile eklenir, işlevleri kütüphane adıyla (ad alanı) çağrılır:

{{ORNEK:22_kurallar/kutuphane_include}}

### Birinci sınıf kütüphane tipleri [KARARLI tasarım, kısmen uygulandı]

uXBasic çekirdeği küçük kalır; `RATIONAL`, `COMPLEX`, `POLYNOMIAL`, `MATRIX`, `TENSOR`, `DATAFRAME` gibi tipler çekirdeğe gömülmez, **manifest/registry
sözleşmesiyle** gelir: yerleşim, operatörler (`ADD SUB MUL DIV EQ NE LT LE GT GE`), MAGIC davranışları (`TOSTRING CLONE HASH ITER`), dönüşümler, yaşam
döngüsü (`storage_model / copy_model / clone_model / drop_model`), ABI ve hedef sağlayıcıları (MIR, JS, WASM, native). `c = a + b` iki `RATIONAL` için
tamsayı toplama değil `CALL RATIONAL.ADD(a, b)` olarak indirilir. Kaynakta `LIBTYPE "ad.library_type.json"` ile manifest yüklenir. Durum: referans `RATIONAL`
**yalnız MIR yorumlayıcıda** çalışır (`tests/library_type_contract`); JS/WASM/native sağlayıcıları ve genel CLONE/RETAIN/DROP **[HEDEF]**. `r = 1 / 3`
`RATIONAL` oluşturmaz (sayısal bölme olur); güvenli yazım `RATIONAL(1, 3)` biçimidir. Bir görev sınırından geçiş `taskTransfer / threadSafety /
sharedPolicy` alanlarına bağlıdır (varsayılan FORBID).

## 10. Dış kütüphane çağrıları: CALL(DLL, ...) ve CALL(API, ...)

Gerçek yazım (kılavuzdaki kısa biçim DEĞİL):

`CALL(DLL, "dosya.dll", "işlev", DÖNÜŞ_TİPİ, ÇAĞRI_KURALI, "ARGÜMAN_TİPLERİ", argüman1, argüman2, ...)`

- `DÖNÜŞ_TİPİ`: `I32`, `I64`, `U64`, `F64`, `PTR` gibi bir tip adı. `ÇAĞRI_KURALI`: `CDECL` ya da `STDCALL`.
- `"ARGÜMAN_TİPLERİ"`: tek metin içinde virgülle (`"STRPTR,PTR"`, `"STRPTR,U64"`); `STRPTR` metin göstericisi, `PTR` gösterici.

{{ORNEK:22_kurallar/call_dll_strlen}}

{{ORNEK:22_kurallar/call_dll_strtod}}

{{ORNEK:22_kurallar/call_dll_stdcall}}

`CALL(API, "kütüphane", "işlev", DÖNÜŞ_TİPİ)` biçimi API sağlayıcı yoluyla çağırır:

{{ORNEK:22_kurallar/call_api}}

## 11. Hata yönetimi

{{ORNEK:02_hata/try_catch_finally}}

{{ORNEK:02_hata/throw_rutinden}}

{{ORNEK:02_hata/assert}}

## 12. Olay, boru, iş parçacığı, görev, eşzamanlılık

{{ORNEK:03_olay/event_slot_trigger}}

{{ORNEK:03_olay/event_parametre}}

{{ORNEK:03_olay/pipe}}

{{ORNEK:03_olay/thread_trigger}}

{{ORNEK:22_kurallar/trigger_thread_arg}}

`SPAWN` bir THREAD/PARALEL'i görev olarak başlatır; `TASK OF tip` sonuç tipini bildirir; `JOIN()` sonucu alır:

{{ORNEK:04_gorev/spawn_join}}

{{ORNEK:22_kurallar/paralel_spawn}}

{{ORNEK:04_gorev/taskgroup}}

**SLOT ile TASK aynı şey değildir [KARARLI]:** `SLOT` 0..255 arası **256 sabit bağlama noktasıdır** (adı, türü, hedefi, ON/OFF durumu); çalışan
görev değildir. Her `SPAWN`/`TRIGGER` ayrı bir **çalışma örneği (TaskRun)** üretir ve `TASK` bu örneğin opak tutamacıdır (sayı ya da PTR
değildir: `t = t + 1` yasak). 10.000 SPAWN 10.000 işletim sistemi iş parçacığı demek değildir; çalışma zamanı sınırlı bir işçi havuzu kullanır.
Her çalışmanın kendi sonucu ve hatası vardır; `TASK OF T` sonucun statik tipini bildirir (tipsiz `TASK` sonucu `OBJECT` olur).
`EVENT / PIPE / THREAD / PARALEL / SLOT / TRIGGER` aynen korunur; `SPAWN / TASK / TASKGROUP` bunların üstüne çalışma örneği katmanı ekler.

**Ortak veri — Model D (Mete'nin kesin kararı, 2026-09-26) [KARARLI]:** normal global/modül/STATIC değişkenler görevlerde **kullanılabilir**;
tek deyimlik ortak erişim **otomatik senkronizedir** (kullanıcı LOCK yazmaz). İki görev `toplam += x` yaparsa sonuç her motorda kesindir:

{{ORNEK:23_tasarim/gorev_otomatik_senkron}}

`LOCK a, b ... END LOCK` yalnız **birden çok deyimin birlikte bölünmez olması** içindir ve **transaction değildir** (hata olursa yapılan yazmalar geri
alınmaz). Kilitler `lockOrderId` sırasıyla alınır, ters sırada bırakılır; aynı kilidi ikinci kez açıkça LOCK etmek `SELF_DEADLOCK` hatasıdır:

{{ORNEK:23_tasarim/lock_coklu_deyim}}

Diğer kurallar: `MUTEX` yalnız dış kaynak/programcı tanımlı kritik bölge içindir; `UNSAFE ... END UNSAFE` yalnız ham adres ve sözleşmesiz FFI
güvencelerini o bölgede kaldırır; görev zincirinde **`END` yasaktır** (RETURN/THROW/sonuç kullanılır); bekleme çevrimi `TASK_WAIT_CYCLE` hatasıdır;
LOCK içinde `JOIN/WAIT` bloklaması yasaktır. Yorumlayıcılarda görevler SPAWN anında çalıştırılabilir: **görevler arası çıktı sırası dil garantisi
değildir**, sıra gerekiyorsa `JOIN` kullan. Legacy AST-x64 bu yapıları açık tanıyla reddeder. Henüz uygulanmayanlar (yerel `SHARED`, `BYSHARED`,
`MOVE/CLONE`, JOINALL LIST) **[HEDEF]**: "henuz uygulanmadi: S-146 adim N" tanısı verir.

Paylaşılan veri **`LOCK`**, **`MUTEX`**, **`DIM ATOMIC`** ile korunur (`DIM SHARED` sözdizimi henüz yoktur):

{{ORNEK:20_esz/lock}}

{{ORNEK:20_esz/mutex}}

{{ORNEK:20_esz/atomic}}

## 13. Bellek ve işaretçiler

{{ORNEK:19_bellek/inc_dec_sizeof}}

{{ORNEK:19_bellek/varptr}}

{{ORNEK:19_bellek/peek_poke}}

**Ham `PTR` aritmetiği bayt tabanlıdır [KARARLI, S-071]:** `PTR + n` n bayt ilerler (`PTR + PTR` hata, `PTR - PTR` bayt farkı = I64). Dizi elemanının adresi
`taban + (indeks - LBOUND) * adım`tır; I32 dizisinde sonraki eleman `p + 4`'tür:

{{ORNEK:23_tasarim/ptr_bayt_aritmetigi}}

Tasarım kararları: `PTR TO T` (tipli işaretçi, `p + 1` bir eleman ilerler) **[HEDEF, S-113 — henüz yok]**; F80'in gerçek veri boyutu 10 bayt, depolama adımı 16
(`SIZEOF(F80)` 10; ham PTR +1 bayt, tipli PTR +16); bellek çeşidi yalnız `VIRTUAL` ve `NATIVE`'dir, `EXTERNAL` bir bellek türü değil adresin
**kökenidir**; mod yazılmazsa PEEK/POKE için `PTR` kaynağı → NATIVE, düz sayısal adres → VIRTUAL.

## 14. Girdi/çıktı, dosya, ekran, süreç

{{ORNEK:11_io/print_virgul}}

{{ORNEK:11_io/dosya_yaz_oku}}

{{ORNEK:11_io/eof_lof}}

{{ORNEK:12_ekran/cls_color_locate}}

{{ORNEK:14_shell/shell}}

## 15. Önişlemci (derleme zamanı)

Önişlemci yönergeleri `%%` ile başlar; kaynak derlemeden önce genişletilir:

{{ORNEK:21_onislemci/define_if}}

{{ORNEK:21_onislemci/macro}}

{{ORNEK:22_kurallar/onislemci_for}}

**Tek önişlemci [KARARLI, docs/tasarim 24.09]:** eski A/B önişlemci ayrımı kalktı; bütün `%%` komutları tek komut uzayındadır. `%%PP A` / `%%PP B`
eski kaynak uyumluluğu için kabul edilir ama etkisizdir (`PREPROCESSOR_PP_DEPRECATED_NO_EFFECT`); yeni kodda yazma. Önişlemci kaynağı genişletir ve normal
derleyici kapılarından geçecek **normal uXBasic kaynağı** üretir. `%%FOREACH` listesi parantez içinde tırnaklı değerlerle yazılır (tek metin
`"A,B"` biçimi [HEDEF]):

{{ORNEK:23_tasarim/onislemci_foreach}}

{{ORNEK:23_tasarim/onislemci_foreach_islev}}

**`REM %%` meta komutları [KARARLI tasarım; ilk halka çalışıyor]:** ham `%%` komutlarından sonra, **önişlemci genişlemesinden sonra** toplanır ve AST/MIR
bildirimine bağlanır. Programın çalışma sonucunu değiştirmez. İki aile vardır: `REM %%ATTR <ad> [arg]` (programın ne olduğunu tanımlar: `TEST`, `DEPRECATED
"neden"`, `REFLECT`, `SERIALIZABLE`, `EXPORT JS`, `EXPORT WASM`, `ROUTE GET "/yol"`, `AUTHOR "ad"`) ve `REM %%MIR <politika> [değer]` (yalnız gerçekten tüketicisi
olan MIR/arka uç politikaları; tanınan ama uygulanmayan politika `META_MIR_POLICY_NOT_IMPLEMENTED` ile reddedilir). Sınır: `REM %%` geçmişi değiştirmez —
ham `%%` = kaynağı üretir, `REM %%ATTR` = oluşan programı tanımlar, `REM %%MIR` = arka uç politikasını verir.

{{ORNEK:23_tasarim/meta_rem_attr}}

## 16. Tasarım kılavuzu ile gerçek arasındaki farklar

| Kılavuzda | Gerçekte (doğrulanmış) |
|---|---|
| `CALL(DLL, "mylib.dll", "f", a, b)` | `CALL(DLL, "mylib.dll", "f", DÖNÜŞ_TİPİ, ÇAĞRI_KURALI, "ARG_TİPLERİ", a, b)` (Bölüm 10) |
| `DIM SHARED x AS T` | Parser reddeder (`DIM: AS expected`); paylaşım `LOCK/MUTEX/ATOMIC` ile |
| `OPERATOR +(other) ... END OPERATOR` | `MAGIC ADD(other) ... END MAGIC` |
| `MAGIC ... END MAGIC` (kılavuzda doğru) / eski testlerde `END METHOD` | Yalnız `END MAGIC` geçerli; `END METHOD` parse hatası |
| `DIM t AS TASK` | `DIM t AS TASK OF I32 = SPAWN F(...)` (sonuç tipiyle); tipsiz `TASK` sonucu `OBJECT`tir |
| `PUBLIC:` (iki nokta) | Hem `PUBLIC` hem `PUBLIC:` kabul edilir |
| `%%FOREACH T IN "I32,F64"` (tek metin) | `%%FOREACH T IN ("I32", "F64")` (parantezli tırnaklı liste) |
| `DIM SHARED`, `LOCK x` ile `GUARDED BY` | Model D: global değişkenler zaten otomatik senkron; `LOCK a, b ... END LOCK` çok deyimli bölge için |

## 17. Bilinen sınırlar ve açık hatalar (uygulanmışmış gibi yazma)

{{SINIRLAR}}

## 18. Kod yazarken kontrol listesi

1. Tip adı listesi dışında tip kullandın mı? (`LONG/INTEGER/DOUBLE` yok.)
2. Sınıf değişkenini `DIM x AS Sinif = NEW Sinif()` biçiminde mi başlattın? (`DIM c AS Sinif = a + b` geçersiz: başlatıcı `NEW` olmalı.)
3. MAGIC bloğunu `END MAGIC` ile mi kapattın?
4. `CALL(DLL, ...)` içinde dönüş tipi, çağrı kuralı ve argüman tipleri metni var mı?
5. Kütüphane için `INCLUDE "include/modules/<ad>.uxmh"` ve `ad.İşlev(...)` biçimini kullandın mı?
6. Paylaşılan veriyi `LOCK`/`MUTEX`/`ATOMIC` ile mi koruyorsun?
7. `^` XOR'dur; üs için `**`.
8. Bir yapıyı bu belgede [DOĞRULANDI] işareti yoksa yeni kodda kullanmadan önce küçük bir örnekle sına.
'''


def sinirlar():
    satir = ["| Örnek | Motor durumları | Not |", "|---|---|---|"]
    notlar = {
        "22_kurallar/call_api": "`CALL(API)` AST ve MIR'de çalışır; native x64 'MIR x64 FFI: invalid runtime argument start' ile BUILDFAIL verir.",
        "22_kurallar/operator_magic_add": "`c = a + b` ifadesi, MAGIC ADD dönüşünü Sayi yerine I32 sayıp 'cannot convert TYPE_I32 to SAYI' veriyor.",
        "22_kurallar/magic_tostring": "`STR(nesne)` MAGIC TOSTRING'i kullanmıyor: AST/MIR/native üç farklı değer yazdırıyor (SORUN_TAKIP S-198).",
    }
    for anahtar in sorted(set(DURUM["dogrulanmadi"])):
        r = SONUC.get(anahtar + ".uxb")
        durum = ", ".join(f"{m}={v['durum']}" for m, v in (r or {"motor": {}})["motor"].items()) or "kayıt yok"
        satir.append(f"| `{anahtar}` | {durum} | {notlar.get(anahtar, '')} |")
    if len(satir) == 2:
        return "Doğrulanamayan örnek yok."
    return "\n".join(satir)


def main():
    metin = ŞABLON
    metin = re.sub(r"\{\{ORNEK:([^}]+)\}\}", lambda m: ornek(m.group(1)), metin)
    metin = metin.replace("{{SINIRLAR}}", sinirlar())
    os.makedirs(os.path.dirname(CIKTI), exist_ok=True)
    open(CIKTI, "w", encoding="utf-8", newline="\n").write(metin)
    ozet = {"ornek_yer_tutucusu": DURUM["ornek"], "dogrulandi": DURUM["dogrulandi"], "dogrulanmadi": sorted(set(DURUM["dogrulanmadi"]))}
    json.dump(ozet, open(os.path.join(ORTAK, "kural_dogrulama_ozeti.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"Yazıldı: {CIKTI}")
    print(f"örnek: {ozet['ornek_yer_tutucusu']}  doğrulandı: {ozet['dogrulandi']}  doğrulanmadı/eksik: {len(ozet['dogrulanmadi'])}")
    for a in ozet["dogrulanmadi"]:
        print("  -", a)


if __name__ == "__main__":
    main()
