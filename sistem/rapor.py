#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rapor.py — F8 Dönüşüm Raporu (COORDINATION.md F8 satırı).

Bir dönüşümde "kaynakta kaç soru vardı, çıktıya kaç soru aktarıldı, kaçı
metin kaçı görsel formatında, kaçı düzgün aktarıldı" sorularına kaba ama
DÜRÜST bir cevap üretir. `qa/dogrula.py`'nin (anahtar ifade sayımı) YERİNE
geçmez, onu TAMAMLAR — dogrula.py'ye dokunulmadı.

Kullanım:
    python3 sistem/rapor.py --kaynak <kaynak.pdf> --tema-dir temalar/NN-ad [--cikti <cikti.pdf>]

Çıktılar (tema-dir/log/ altına):
    donusum_raporu.md   İnsan okur, Türkçe, tarih damgalı. Üzerine YAZILIR
                         (eski rapor arşivlenmez — ama runs.jsonl'e her koşu
                         bir satır olarak eklenir, geçmiş orada kalır).
    rapor.json           Makine: sayısal özet + eşleşmeyen/kayıp id-numara
                         listeleri.

Yöntem — 4 metrik (kısa özet, ayrıntı fonksiyon docstring'lerinde):
  1) Kaynak soru sayısı TAHMİNİ: kaynak PDF'in metin katmanında satır BAŞINDA
     "12." / "12)" gibi 1-3 haneli bir sayı + noktalama + devamında metin
     arayan kaba bir regex sayımı — cevap anahtarı satırları (aynı satırda
     birden çok "N.HARF" deseni) ve salt sayfa numarası satırları (noktalama
     yok) elenir. Bu TAHMİNDİR, kesin soru sayısı değildir.
  2) Çıktı soru sayısı: sorular.html içindeki, manifest.json'un AKTİF akışında
     yer alan (silinmemiş) class="question" blok sayısı.
  3) Format dağılımı: her aktif sorunun içinde <img> var mı (gorsel) yok mu
     (metin) + bunların içinde "anlamlı metni" (soru no hariç, yalnızca
     harf/rakam) kısa/boş olanlar ayrıca "salt görsel" olarak işaretlenir.
  4) Aktarım kontrolü: her aktif sorunun HTML etiketleri temizlenmiş (br->boşluk,
     .rt/.frac/.sup içeriği düz metne çevrilmiş, Türkçe'ye duyarlı küçük harfe
     çevrilmiş, boşluk sıkıştırılmış) ilk ~40 karakteri, aynı şekilde
     normalize edilmiş kaynak PDF metninde ARANIR (alt-dize testi). Anlamlı
     metni MEANINGFUL_MIN karakterden kısa olan (ör. salt görsel) sorular bu
     karşılaştırmadan MUAF tutulur ve "görsel içerikli — metin karşılaştırması
     yapılamadı" kategorisine düşer (bunlar "eşleşmedi" ile KARIŞTIRILMAZ).

Bağımlılık: yalnızca PyMuPDF (fitz) + stdlib — poppler/pdftotext GEREKMEZ,
script bağımsız çalışabilir.
"""
from __future__ import annotations

import argparse
import html as html_module
import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta

try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover
    sys.stderr.write("HATA: PyMuPDF (fitz) bulunamadı. `pip install pymupdf` ile kurun.\n")
    raise

TR_TZ = timezone(timedelta(hours=3))

MEANINGFUL_MIN = 20  # bu kadar harf/rakamdan azsa "görsel içerikli" say (elle kontrol gerekmez)
PREFIX_LEN = 40  # aktarım kontrolünde karşılaştırılan ilk karakter sayısı


def simdi_iso() -> str:
    return datetime.now(TR_TZ).strftime("%Y-%m-%dT%H:%M:%S+03:00")


# ------------------------------------------------------------------ normalize

def tr_casefold(s: str) -> str:
    """Türkçe'ye duyarlı küçük harfe çevirme (İ->i, I->ı), sonra genel .lower()."""
    return s.replace("İ", "i").replace("I", "ı").lower()


def normalize_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def html_to_text(ic_html: str) -> str:
    """<br> -> boşluk, tüm etiketler SESSİZCE (boşluksuz) kaldırılır (.rt/.sup/.sub
    inline olduğu için aralarında kaynak metinde de boşluk yoktur — ör.
    '7<span class="sup">x+2</span>' -> '7x+2', kaynak pdftotext çıktısıyla
    aynı). TEK istisna: '.frac'ın num/den çocukları kaynak PDF'te ayrı SATIR
    olduğundan (pay üstte, payda altta), aralarına kaybolmasın diye bir
    boşluk eklenir."""
    s = re.sub(r"<br\s*/?>", " ", ic_html, flags=re.IGNORECASE)
    s = re.sub(r'(</span>)(\s*<span class="den">)', r"\1 \2", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = html_module.unescape(s)
    return normalize_ws(s)


def sadece_alnum(s: str) -> str:
    return re.sub(r"[^\w]+", "", s, flags=re.UNICODE)


# ------------------------------------------------------------------ kaynak PDF

def kaynak_metni_satirlar(pdf_path: str) -> list[str]:
    """Geriye uyumluluk için korunuyor (yalnızca satır metinleri). Yeni kod
    `kaynak_pdf_oku`'yu kullanır — o da bu satırları döndürür, ek olarak span
    bazlı satır verisini ve sayfa başına görsel-bölge sayımını tek geçişte üretir."""
    doc = fitz.open(pdf_path)
    try:
        satirlar: list[str] = []
        for sayfa in doc:
            metin = sayfa.get_text("text")
            satirlar.extend(metin.split("\n"))
        return satirlar
    finally:
        doc.close()


ANSWER_LETTER_RE = re.compile(r"\d{1,3}[.)]\s*[A-EÇĞİÖŞÜ]\b")
QNUM_LINE_RE = re.compile(r"^(\d{1,3})[.)]\s+\S")
QNUM_SPAN_RE = re.compile(r"^(\d{1,3})[.)]$")


def kaynak_pdf_oku(pdf_path: str) -> dict:
    """Kaynak PDF'i TEK geçişte okuyup üç şeyi birden döndürür:
      - satirlar: get_text("text") satırları (yöntem 1 — satır bazlı tahmin ve
        aktarım kontrolü normalize metni için)
      - span_satirlar: get_text("dict") ile her SATIRIN ilk span'ının metni +
        satırın tüm span'ları birleşik metni, (ilk, tam) çiftleri halinde
        (yöntem 2 — span bazlı tahmin için)
      - sayfa_gorsel: {sayfa_no(1-bazlı): göz. bölge sayısı} — F10 sayfa bazlı
        görsel karşılaştırması için (bkz. `_basit_figur_bolgeleri`).
    """
    doc = fitz.open(pdf_path)
    try:
        satirlar: list[str] = []
        span_satirlar: list[tuple[str, str]] = []
        sayfa_gorsel: dict[int, int] = {}
        for idx, sayfa in enumerate(doc):
            pno = idx + 1
            metin = sayfa.get_text("text")
            satirlar.extend(metin.split("\n"))

            metin_dict = sayfa.get_text("dict")
            for blok in metin_dict.get("blocks", []):
                for satir in blok.get("lines", []):
                    spans = satir.get("spans", [])
                    if not spans:
                        continue
                    ilk = (spans[0].get("text") or "")
                    tam = "".join(s.get("text") or "" for s in spans)
                    span_satirlar.append((ilk, tam))

            adet = 0
            try:
                image_list = sayfa.get_image_info(xrefs=True)
            except Exception:
                image_list = []
            for img in image_list:
                x0, y0, x1, y1 = img["bbox"]
                if y0 < 70 and x0 < 100:
                    continue  # header logosu (extract.py extract_page_images ile aynı eşik)
                adet += 1
            try:
                drawings = sayfa.get_drawings()
            except Exception:
                drawings = []
            adet += len(_basit_figur_bolgeleri(drawings))
            sayfa_gorsel[pno] = adet
        return {
            "satirlar": satirlar,
            "span_satirlar": span_satirlar,
            "sayfa_gorsel": sayfa_gorsel,
        }
    finally:
        doc.close()


def _rects_yakin(a: tuple, b: tuple, pad: float = 8.0) -> bool:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    return not (ax1 + pad < bx0 or bx1 + pad < ax0 or ay1 + pad < by0 or by1 + pad < ay0)


def _basit_figur_bolgeleri(drawings) -> list[tuple]:
    """`sistem/extract.py`'deki collect_thin_bars + collect_theory_boxes +
    collect_figure_regions üçlüsünün BASİTLEŞTİRİLMİŞ hali (COORDINATION.md F10):
    ince çizgileri (kök/kesir/ayraç vinculum'ları, h<2.6) ve açık renkli dolgu
    dikdörtgenlerini (muhtemelen teori-kutusu arka planı) eleyip kalan çizimleri
    yakınlık bazlı kümeler; yeterince büyük (w>14, h>9) kümeleri 'görsel bölge'
    sayar. extract.py'deki header/kurgu-metni-üstü rozet ayıklaması ve tekil-dolgu
    metin-örtüşme istisnası burada UYGULANMAZ — bu yalnızca bir rapor tahminidir,
    extract.py'nin kendisi DEĞİŞTİRİLMEDİ ve tekrar ÇALIŞTIRILMADI."""
    adaylar = []
    for d in drawings:
        try:
            x0, y0, x1, y1 = d["rect"]
        except Exception:
            continue
        w, h = x1 - x0, y1 - y0
        if h < 2.6 and w > 0.8:
            continue  # ince çizgi (kök/kesir/ayraç ailesi)
        if d.get("type") == "fs":
            fill = d.get("fill")
            if fill and all(0.85 <= c <= 1.0 for c in fill[:3]):
                continue  # açık renkli dolgu -> muhtemelen teori kutusu arka planı
        if w < 3.0 or h < 3.0:
            continue
        adaylar.append((x0, y0, x1, y1))

    kumeler: list[list[float]] = []
    for rect in adaylar:
        birlesti = False
        for k in kumeler:
            if _rects_yakin(tuple(k[:4]), rect):
                k[0] = min(k[0], rect[0])
                k[1] = min(k[1], rect[1])
                k[2] = max(k[2], rect[2])
                k[3] = max(k[3], rect[3])
                birlesti = True
                break
        if not birlesti:
            kumeler.append([rect[0], rect[1], rect[2], rect[3]])

    degisti = True
    while degisti:
        degisti = False
        for i in range(len(kumeler)):
            for j in range(i + 1, len(kumeler)):
                if kumeler[i] is None or kumeler[j] is None:
                    continue
                if _rects_yakin(tuple(kumeler[i]), tuple(kumeler[j])):
                    kumeler[i][0] = min(kumeler[i][0], kumeler[j][0])
                    kumeler[i][1] = min(kumeler[i][1], kumeler[j][1])
                    kumeler[i][2] = max(kumeler[i][2], kumeler[j][2])
                    kumeler[i][3] = max(kumeler[i][3], kumeler[j][3])
                    kumeler[j] = None
                    degisti = True
        kumeler = [k for k in kumeler if k is not None]

    return [tuple(k) for k in kumeler if (k[2] - k[0]) > 14 and (k[3] - k[1]) > 9]


def kaynak_soru_tahmini_satir(satirlar: list[str]) -> tuple[int, list[int]]:
    """YÖNTEM 1 (satır bazlı): satır başında '12.'/'12)' + AYNI SATIRDA devamında
    metin arar; aynı satırda >=2 tane 'N.HARF' deseni varsa (cevap anahtarı satırı,
    örn. '1.B 2.A 3.C') o satırı SAYMAZ. Salt sayfa numarası satırları ('53' tek
    başına) zaten regex'e (noktalama + devam metni şartı) takılmadığı için otomatik
    elenir.

    SINIRI (F10 teşhisi — 08 teması): taranmış/görsel ağırlıklı kaynaklarda soru
    numarası kendi satırında YALNIZ BAŞINA durur ("1.\\n" gibi) — asıl soru metni
    resim olduğu için aynı satırda devam metni YOKTUR. Bu durumda bu yöntem 0
    döner; `kaynak_soru_tahmini_span` bu durumu yakalamak için eklendi."""
    adaylar: list[int] = []
    for satir in satirlar:
        s = satir.strip()
        if not s:
            continue
        if len(ANSWER_LETTER_RE.findall(s)) >= 2:
            continue  # cevap anahtarı satırı
        m = QNUM_LINE_RE.match(s)
        if m:
            adaylar.append(int(m.group(1)))
    return len(adaylar), adaylar


def kaynak_soru_tahmini_span(span_satirlar: list[tuple[str, str]]) -> tuple[int, list[int]]:
    """YÖNTEM 2 (span bazlı, F10): `get_text('dict')`'te her SATIRIN İLK span'ı
    TAM OLARAK '12.' / '12)' ise (satırın geri kalanında başka metin olsun ya da
    olmasın) bunu bir soru-numarası adayı sayar. Taranmış sayfalarda soru numarası
    genelde kendi satırında tek span olarak durur (devamı görsel olduğu için aynı
    satırda metin yoktur) — yöntem 1'in kaçırdığı bu durumu yakalar.

    Cevap anahtarı satırları burada da elenir: ANSWER_LETTER_RE satırın TÜM
    span'larının birleşik metninde (`tam`) >=2 eşleşme ararsa eleme yapılır; ayrıca
    '1.B' gibi numara+harf TEK bir span'da birleşikse zaten `QNUM_SPAN_RE` ile tam
    eşleşmeyeceği için kendiliğinden elenir."""
    adaylar: list[int] = []
    for ilk, tam in span_satirlar:
        ilk_s = ilk.strip()
        m = QNUM_SPAN_RE.match(ilk_s)
        if not m:
            continue
        if len(ANSWER_LETTER_RE.findall(tam)) >= 2:
            continue  # cevap anahtarı satırı
        adaylar.append(int(m.group(1)))
    return len(adaylar), adaylar


# ------------------------------------------------------------------ çıktı (sorular.html + manifest.json)

BLOK_PATTERN = re.compile(
    r'<(section|div)\s+class="([^"]+)"\s+id="([^"]+)"\s+data-kaynak-sayfa="([^"]+)"[^>]*>(.*?)</\1>',
    re.DOTALL,
)


def sorular_html_oku(tema_dir: str) -> str:
    yol = os.path.join(tema_dir, "sorular.html")
    if not os.path.exists(yol):
        raise FileNotFoundError(f"sorular.html bulunamadı: {yol}")
    with open(yol, "r", encoding="utf-8") as f:
        return f.read()


def manifest_oku(tema_dir: str) -> dict:
    yol = os.path.join(tema_dir, "manifest.json")
    if not os.path.exists(yol):
        raise FileNotFoundError(f"manifest.json bulunamadı: {yol}")
    with open(yol, "r", encoding="utf-8") as f:
        return json.load(f)


def bloklari_ayristir(html_metin: str) -> dict[str, dict]:
    bloklar: dict[str, dict] = {}
    for tag, sinif, b_id, sayfa, ic in BLOK_PATTERN.findall(html_metin):
        bloklar[b_id] = {"sinif": sinif, "kaynak_sayfa": sayfa, "ic": ic}
    return bloklar


def aktif_id_sirasi(manifest: dict) -> list[str]:
    sira: list[str] = []
    for grup in manifest.get("akis", []):
        sira.extend(grup.get("bloklar", []))
    return sira


def cikti_sorulari_analiz_et(tema_dir: str) -> list[dict]:
    html_metin = sorular_html_oku(tema_dir)
    manifest = manifest_oku(tema_dir)
    bloklar = bloklari_ayristir(html_metin)

    sonuc = []
    for b_id in aktif_id_sirasi(manifest):
        b = bloklar.get(b_id)
        if not b or b["sinif"] != "question":
            continue
        ic = b["ic"]
        has_img = bool(re.search(r"<img\b", ic))
        norm_full = tr_casefold(html_to_text(ic))
        anlamli = re.sub(r"^\d{1,3}[.)]\s*", "", norm_full)
        anlamli_uzunluk = len(sadece_alnum(anlamli))
        sonuc.append(
            {
                "id": b_id,
                "kaynak_sayfa": b["kaynak_sayfa"],
                "has_img": has_img,
                "norm_full": norm_full,
                "anlamli_uzunluk": anlamli_uzunluk,
            }
        )
    return sonuc


def cikti_sayfa_gorsel_sayilari(tema_dir: str) -> dict[int, int]:
    """F10 — sorular.html'deki AKTİF (manifest akışında, silinmemiş) bloklarda,
    her `data-kaynak-sayfa`'ya bağlı toplam `<img>` sayısını döner
    ({sayfa_no(1-bazlı): adet}). Sınıf (question/theory/para…) AYRIMI YAPILMAZ —
    amaç kaynak sayfadaki toplam görsel-bölge sayısıyla karşılaştırmak, yalnızca
    soru görsellerini değil. Silinmiş/aktif-olmayan bloklar (manifest akışında
    yer almayanlar) SAYILMAZ — onlar zaten çıktıya basılmıyor."""
    html_metin = sorular_html_oku(tema_dir)
    manifest = manifest_oku(tema_dir)
    bloklar = bloklari_ayristir(html_metin)
    aktif = set(aktif_id_sirasi(manifest))

    sonuc: dict[int, int] = {}
    for b_id, b in bloklar.items():
        if b_id not in aktif:
            continue
        try:
            sayfa = int(b["kaynak_sayfa"])
        except (TypeError, ValueError):
            continue
        adet = len(re.findall(r"<img\b", b["ic"]))
        sonuc[sayfa] = sonuc.get(sayfa, 0) + adet
    return sonuc


# ------------------------------------------------------------------ ana hesap


def rapor_hesapla(kaynak_pdf: str, tema_dir: str, cikti_pdf: str | None) -> dict:
    kaynak_veri = kaynak_pdf_oku(kaynak_pdf)
    kaynak_satirlar = kaynak_veri["satirlar"]

    # F10: iki bağımsız tahmin yöntemi, nihai tahmin ikisinin BÜYÜĞÜ (bkz.
    # kaynak_soru_tahmini_satir / kaynak_soru_tahmini_span docstring'leri).
    tahmin_satir, numaralar_satir = kaynak_soru_tahmini_satir(kaynak_satirlar)
    tahmin_span, numaralar_span = kaynak_soru_tahmini_span(kaynak_veri["span_satirlar"])
    if tahmin_span > tahmin_satir:
        kaynak_tahmini, kaynak_numaralari, tahmin_yontemi = tahmin_span, numaralar_span, "span_bazli"
    else:
        kaynak_tahmini, kaynak_numaralari, tahmin_yontemi = tahmin_satir, numaralar_satir, "satir_bazli"

    kaynak_norm = tr_casefold(normalize_ws(" ".join(kaynak_satirlar)))
    # Çıktıda kök '.rt' sınıfı √ glifini KULLANMAZ (SISTEM.md §3 — SVG çengel
    # ile çizilir, radikand düz metin kalır); kaynağın metin katmanında ise √
    # karakteri GERÇEKTEN vardır. Bu, kökü olan HER sorunun aktarım kontrolünde
    # yanlış "eşleşmedi" çıkmasına yol açar — SISTEM.md §6.1'in de kabul ettiği
    # tek beklenen fark budur, o yüzden karşılaştırmadan ÖNCE iki taraftan da elenir.
    kaynak_norm = normalize_ws(kaynak_norm.replace("√", ""))

    sorular = cikti_sorulari_analiz_et(tema_dir)

    metin_sayisi = sum(1 for s in sorular if not s["has_img"])
    gorsel_sayisi = sum(1 for s in sorular if s["has_img"])
    salt_gorsel_sayisi = sum(
        1 for s in sorular if s["has_img"] and s["anlamli_uzunluk"] < MEANINGFUL_MIN
    )

    eslesen: list[str] = []
    eslesmeyen: list[str] = []
    gorsel_icerik: list[str] = []
    eslesen_numaralari: set[int] = set()

    for s in sorular:
        if s["anlamli_uzunluk"] < MEANINGFUL_MIN:
            gorsel_icerik.append(s["id"])
            continue
        prefix = s["norm_full"][:PREFIX_LEN]
        if prefix and prefix in kaynak_norm:
            eslesen.append(s["id"])
            m = re.match(r"^(\d{1,3})[.)]", s["norm_full"])
            if m:
                eslesen_numaralari.add(int(m.group(1)))
        else:
            eslesmeyen.append(s["id"])

    # Yaklaşık/kaba: kaynakta aday olarak görülen ama hiçbir çıktı sorusunun
    # eşleşmesinde "yakalanmayan" numaralar. Bölüm bazlı numara sıfırlanması
    # (her yeni KUR/bölüm 1'den başlar) yüzünden bu liste GLOBAL bir kümedir,
    # kesin bir kayıp kanıtı değil, yalnızca elle kontrol için bir ipucudur.
    kaynak_numaralari_kume = set(kaynak_numaralari)
    olasi_kayip_numaralar = sorted(kaynak_numaralari_kume - eslesen_numaralari)

    # Kaynak neredeyse hiç satır-başı soru adayı vermiyor ama çıktıda onlarca
    # soru varsa (bu temada tipik durum: taranmış/vektör-görsel ağırlıklı
    # kaynak, extract.py soruları img-block'a çevirmiş) tahmin sayısı 0'a
    # yakın kalır — bunu SESSİZCE 0 göstermek yanıltıcı olur, açıkça uyar.
    kaynak_metin_kisitli = kaynak_tahmini < max(3, len(sorular) // 20) and len(sorular) >= 5

    # F10 — sayfa bazlı görsel karşılaştırma: kaynak sayfadaki (basitleştirilmiş)
    # görsel-bölge sayısı ile çıktıda o sayfaya bağlı aktif <img> sayısı
    # karşılaştırılır. kaynak > cikti olan sayfalar "muhtemelen kayıp görsel"
    # ipucu sayılır — extract.py'nin kendi eşikleri daha zengin (header/kurgu
    # metni ayıklaması, tek-dolgu istisnası) olduğundan burada bir miktar
    # ABARTILI SAYIM (yanlış pozitif) beklenir, bu yüzden "olası" deniyor.
    kaynak_sayfa_gorsel = kaynak_veri["sayfa_gorsel"]
    cikti_sayfa_gorsel = cikti_sayfa_gorsel_sayilari(tema_dir)
    sayfa_gorsel_karsilastirma: list[dict] = []
    olasi_eksik_gorsel_sayfalar: list[int] = []
    for sayfa_no in sorted(set(kaynak_sayfa_gorsel) | set(cikti_sayfa_gorsel)):
        k = kaynak_sayfa_gorsel.get(sayfa_no, 0)
        c = cikti_sayfa_gorsel.get(sayfa_no, 0)
        if k == 0 and c == 0:
            continue  # görselsiz sayfaları listede boğmayalım
        sayfa_gorsel_karsilastirma.append({"sayfa": sayfa_no, "kaynak": k, "cikti": c})
        if k > c:
            olasi_eksik_gorsel_sayfalar.append(sayfa_no)

    cikti_sayfa = None
    if cikti_pdf and os.path.exists(cikti_pdf):
        try:
            doc = fitz.open(cikti_pdf)
            cikti_sayfa = doc.page_count
            doc.close()
        except Exception:
            cikti_sayfa = None

    tema_bilgi = {"tema": None, "baslik": None, "surum": None}
    try:
        manifest = manifest_oku(tema_dir)
        tema_bilgi = {
            "tema": manifest.get("tema"),
            "baslik": manifest.get("baslik"),
            "surum": manifest.get("surum"),
        }
    except Exception:
        pass

    return {
        "olusturuldu": simdi_iso(),
        "tema_dir": os.path.abspath(tema_dir),
        "tema": tema_bilgi["tema"],
        "baslik": tema_bilgi["baslik"],
        "surum": tema_bilgi["surum"],
        "kaynak_pdf": os.path.abspath(kaynak_pdf),
        "cikti_pdf": os.path.abspath(cikti_pdf) if cikti_pdf else None,
        "cikti_sayfa": cikti_sayfa,
        "kaynak_soru_tahmini": kaynak_tahmini,
        "cikti_soru_sayisi": len(sorular),
        "metin_sayisi": metin_sayisi,
        "gorsel_sayisi": gorsel_sayisi,
        "salt_gorsel_sayisi": salt_gorsel_sayisi,
        "eslesen_sayisi": len(eslesen),
        "eslesmeyen_sayisi": len(eslesmeyen),
        "gorsel_icerik_sayisi": len(gorsel_icerik),
        "eslesmeyen_idler": eslesmeyen,
        "gorsel_icerik_idler": gorsel_icerik,
        "olasi_kayip_numaralar": olasi_kayip_numaralar,
        "kaynak_metin_kisitli": kaynak_metin_kisitli,
        "kaynak_soru_tahmini_satir_bazli": tahmin_satir,
        "kaynak_soru_tahmini_span_bazli": tahmin_span,
        "kaynak_soru_tahmini_yontemi": tahmin_yontemi,
        "sayfa_gorsel_karsilastirma": sayfa_gorsel_karsilastirma,
        "olasi_eksik_gorsel_sayfalar": olasi_eksik_gorsel_sayfalar,
        "yontem_notu": (
            "Kaynak soru sayısı için İKİ bağımsız TAHMİN hesaplanır — (1) satır bazlı: satır "
            "başında '12.'/'12)' + AYNI SATIRDA devam metni arar; (2) span bazlı (F10): "
            "get_text('dict')'te satırın İLK span'ı tam olarak '12.'/'12)' ise sayar (taranmış/"
            "görsel ağırlıklı kaynaklarda soru numarası kendi satırında yalnız durur, devam metni "
            "resim olduğu için satırda YOKTUR — yöntem 1 bunu kaçırır). Nihai tahmin ikisinin "
            f"BÜYÜĞÜdür (bu koşuda: {tahmin_yontemi}); her iki ham değer de "
            "kaynak_soru_tahmini_satir_bazli / kaynak_soru_tahmini_span_bazli alanlarında saklanır. "
            "Cevap anahtarı satırları (örn. '1.B 2.A 3.C') her iki yöntemde de elenir. Aktarım "
            "kontrolü her çıktı sorusunun ilk ~40 normalize karakterini kaynak metninde arar, kısa/"
            "salt-görsel sorular karşılaştırma dışı tutulur. Sayfa bazlı görsel karşılaştırması "
            "(sayfa_gorsel_karsilastirma / olasi_eksik_gorsel_sayfalar) kaynaktaki basitleştirilmiş "
            "görsel-bölge sayımını (extract.py'nin gömülü görüntü + büyük vektör çizim kümesi "
            "mantığının basit bir kopyası, extract.py'nin kendisi ÇALIŞTIRILMADI) çıktıdaki aynı "
            "kaynak sayfaya bağlı <img> sayısıyla karşılaştırır — extract.py'nin banner/tekil-dolgu "
            "istisnaları burada yok, bu yüzden bir miktar yanlış pozitif (abartılı 'olası eksik') "
            "beklenir; kesin/otomatik doğrulama için qa/dogrula.py'ye bakın."
        ),
    }


# ------------------------------------------------------------------ md üretimi


def _liste_blok(baslik: str, idler: list[str], sinir: int = 60) -> str:
    if not idler:
        return f"**{baslik}:** yok\n"
    gosterilen = idler[:sinir]
    satir = f"**{baslik}** ({len(idler)} adet):\n\n" + ", ".join(gosterilen)
    if len(idler) > sinir:
        satir += f", … (+{len(idler) - sinir} tane daha, tam liste rapor.json'da)"
    return satir + "\n"


def md_uret(ozet: dict) -> str:
    baslik = ozet.get("baslik") or ozet.get("tema") or os.path.basename(ozet["tema_dir"])
    satirlar = []
    satirlar.append(f"# Dönüşüm Raporu — {baslik}")
    satirlar.append("")
    satirlar.append(f"Oluşturulma: {ozet['olusturuldu']}")
    if ozet.get("surum") is not None:
        satirlar.append(f"Sürüm: {ozet['surum']}")
    satirlar.append(f"Kaynak: `{ozet['kaynak_pdf']}`")
    if ozet.get("cikti_pdf"):
        sayfa_notu = f" ({ozet['cikti_sayfa']} sayfa)" if ozet.get("cikti_sayfa") else ""
        satirlar.append(f"Çıktı: `{ozet['cikti_pdf']}`{sayfa_notu}")
    satirlar.append("")
    satirlar.append(f"> Yöntem: {ozet['yontem_notu']}")
    if ozet.get("kaynak_metin_kisitli"):
        satirlar.append("")
        satirlar.append(
            "> **UYARI**: kaynak PDF'in metin katmanı çok sınırlı görünüyor (muhtemelen "
            "taranmış/vektör-görsel ağırlıklı bir belge — soru numaraları dışında satır başına "
            "metin bulunamadı). Bu yüzden **\"kaynaktaki soru sayısı\" tahmini güvenilir "
            "DEĞİLDİR** ve aktarım kontrolü neredeyse tüm soruları \"görsel içerikli\" kategorisine "
            "düşürecektir — bu bir hata değil, kaynağın doğasından kaynaklanıyor; elle örneklem "
            "kontrolüne güvenin."
        )
    satirlar.append("")
    satirlar.append("## Özet Tablo")
    satirlar.append("")
    satirlar.append("| Metrik | Sayı |")
    satirlar.append("|---|---|")
    satirlar.append(f"| Kaynaktaki soru sayısı (TAHMİN) | {ozet['kaynak_soru_tahmini']} |")
    satirlar.append(
        f"|    — satır bazlı yöntem | {ozet.get('kaynak_soru_tahmini_satir_bazli', '—')} |"
    )
    satirlar.append(
        f"|    — span bazlı yöntem (F10) | {ozet.get('kaynak_soru_tahmini_span_bazli', '—')} |"
    )
    satirlar.append(
        f"|    — kazanan yöntem | {ozet.get('kaynak_soru_tahmini_yontemi', '—')} |"
    )
    satirlar.append(f"| Çıktıya aktarılan soru sayısı | {ozet['cikti_soru_sayisi']} |")
    satirlar.append(f"| — metin formatında | {ozet['metin_sayisi']} |")
    satirlar.append(f"| — görsel içeren | {ozet['gorsel_sayisi']} |")
    satirlar.append(f"|    (bunların salt görsel/metinsiz olanı) | {ozet['salt_gorsel_sayisi']} |")
    satirlar.append(f"| Düzgün aktarıldığı doğrulanan (eşleşti) | {ozet['eslesen_sayisi']} |")
    satirlar.append(f"| Eşleşmedi — elle kontrol önerilir | {ozet['eslesmeyen_sayisi']} |")
    satirlar.append(
        f"| Görsel içerikli — metin karşılaştırması yapılamadı | {ozet['gorsel_icerik_sayisi']} |"
    )
    satirlar.append("")
    satirlar.append("## Elle Kontrol Önerilen Sorular")
    satirlar.append("")
    satirlar.append(_liste_blok("Eşleşmedi", ozet["eslesmeyen_idler"]))
    satirlar.append("")
    satirlar.append("## Kayıp Olabilecek Kaynak Soru Numaraları (yaklaşık)")
    satirlar.append("")
    satirlar.append(
        "> Not: kaynak PDF'te her yeni bölüm (KUR) numaralamayı 1'den yeniden başlattığı için "
        "bu liste GLOBAL bir küme farkıdır, kesin kayıp kanıtı DEĞİLDİR — yalnızca hangi "
        "numaraların gözle kontrol edilmesi gerektiğine dair bir ipucudur."
    )
    satirlar.append("")
    if ozet["olasi_kayip_numaralar"]:
        satirlar.append(", ".join(str(n) for n in ozet["olasi_kayip_numaralar"][:80]))
        if len(ozet["olasi_kayip_numaralar"]) > 80:
            satirlar.append(f"\n… (+{len(ozet['olasi_kayip_numaralar']) - 80} tane daha, tam liste rapor.json'da)")
    else:
        satirlar.append("yok")
    satirlar.append("")

    satirlar.append("## Sayfa Bazlı Görsel Karşılaştırması (F10)")
    satirlar.append("")
    satirlar.append(
        "> Not: kaynak sütunu, extract.py'nin gömülü görüntü + büyük vektör çizim kümesi "
        "mantığının BASİTLEŞTİRİLMİŞ bir kopyasıyla sayılır (extract.py'nin kendisi "
        "ÇALIŞTIRILMADI); banner/tekil-dolgu istisnaları burada yok, bu yüzden kaynak sayısı "
        "gerçek görsel-bölge sayısından biraz FAZLA çıkabilir (yanlış pozitif). cikti sütunu "
        "yalnızca AKTİF (silinmemiş) bloklardaki `<img>` sayısıdır."
    )
    satirlar.append("")
    eksik_sayfalar = ozet.get("olasi_eksik_gorsel_sayfalar") or []
    if eksik_sayfalar:
        satirlar.append(
            f"> **DİKKAT**: aşağıdaki sayfalarda kaynaktaki görsel-bölge sayısı çıktıdaki "
            f"`<img>` sayısından FAZLA — olası eksik görsel, elle kontrol edin: "
            + ", ".join(str(n) for n in eksik_sayfalar[:80])
            + (f", … (+{len(eksik_sayfalar) - 80} tane daha)" if len(eksik_sayfalar) > 80 else "")
        )
        satirlar.append("")
    karsilastirma = ozet.get("sayfa_gorsel_karsilastirma") or []
    if karsilastirma:
        satirlar.append("| Kaynak sayfa | Kaynak (tahmini) | Çıktı |")
        satirlar.append("|---|---|---|")
        for satir in karsilastirma[:120]:
            isaret = " ⚠️" if satir["kaynak"] > satir["cikti"] else ""
            satirlar.append(f"| {satir['sayfa']} | {satir['kaynak']} | {satir['cikti']}{isaret} |")
        if len(karsilastirma) > 120:
            satirlar.append(f"\n… (+{len(karsilastirma) - 120} sayfa daha, tam liste rapor.json'da)")
    else:
        satirlar.append("Görsel içeren sayfa bulunamadı (ne kaynakta ne çıktıda).")
    satirlar.append("")
    return "\n".join(satirlar) + "\n"


# ------------------------------------------------------------------ runs.jsonl


def runs_jsonl_yaz(tema_dir: str, kayit: dict) -> None:
    log_dir = os.path.join(tema_dir, "log")
    os.makedirs(log_dir, exist_ok=True)
    yol = os.path.join(log_dir, "runs.jsonl")
    kayit = {"ts": simdi_iso(), **kayit}
    with open(yol, "a", encoding="utf-8") as f:
        f.write(json.dumps(kayit, ensure_ascii=False) + "\n")


# ------------------------------------------------------------------ main


def main() -> int:
    parser = argparse.ArgumentParser(description="F8 — Dönüşüm Raporu üretici")
    parser.add_argument("--kaynak", required=True, help="Kaynak PDF yolu")
    parser.add_argument("--tema-dir", required=True, dest="tema_dir", help="temalar/NN-ad klasörü")
    parser.add_argument("--cikti", default=None, help="Üretilen çıktı PDF yolu (opsiyonel, bilgi amaçlı)")
    args = parser.parse_args()

    if not os.path.exists(args.kaynak):
        sys.stderr.write(f"HATA: kaynak PDF bulunamadı: {args.kaynak}\n")
        return 1
    if not os.path.isdir(args.tema_dir):
        sys.stderr.write(f"HATA: tema dizini bulunamadı: {args.tema_dir}\n")
        return 1

    try:
        ozet = rapor_hesapla(args.kaynak, args.tema_dir, args.cikti)
    except Exception as exc:
        sys.stderr.write(f"HATA: rapor hesaplanamadı: {exc}\n")
        return 1

    log_dir = os.path.join(args.tema_dir, "log")
    os.makedirs(log_dir, exist_ok=True)

    md_yol = os.path.join(log_dir, "donusum_raporu.md")
    json_yol = os.path.join(log_dir, "rapor.json")

    with open(md_yol, "w", encoding="utf-8") as f:
        f.write(md_uret(ozet))
    with open(json_yol, "w", encoding="utf-8") as f:
        json.dump(ozet, f, ensure_ascii=False, indent=2)

    runs_jsonl_yaz(
        args.tema_dir,
        {
            "islem": "rapor",
            "girdi": os.path.abspath(args.kaynak),
            "cikti": md_yol,
            "sayfa": ozet.get("cikti_sayfa"),
            "soru": ozet.get("cikti_soru_sayisi"),
            "kok": None,
            "gorsel": ozet.get("gorsel_sayisi"),
            "dogrulama": (
                f"kaynak_tahmin={ozet['kaynak_soru_tahmini']} "
                f"eslesen={ozet['eslesen_sayisi']} "
                f"eslesmeyen={ozet['eslesmeyen_sayisi']} "
                f"gorsel_icerik={ozet['gorsel_icerik_sayisi']}"
            ),
            "sha256": "",
            "ajan": "rapor.py",
        },
    )

    print(f"Rapor üretildi: {md_yol}")
    print(f"          json: {json_yol}")
    print(
        f"kaynak~={ozet['kaynak_soru_tahmini']} cikti={ozet['cikti_soru_sayisi']} "
        f"metin={ozet['metin_sayisi']} gorsel={ozet['gorsel_sayisi']} "
        f"eslesen={ozet['eslesen_sayisi']} eslesmeyen={ozet['eslesmeyen_sayisi']} "
        f"gorsel_icerik={ozet['gorsel_icerik_sayisi']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
