#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract.py — v2 PDF -> sorular.html + manifest.json + assets/ (build_linux)

FAZ 3 / Görev A4a (Claude-Sonnet #5) — YAPISAL DÜZELTME sürümü.

Önceki sürüm (AGY / Görev A1) v3_taslak.pdf'te doğrulanan yapısal bozukluklara
yol açıyordu (bkz. COORDINATION.md "## FAZ 3 QA Bulguları" — X1, Q3a, Q3b).
Bulunan kök nedenler ve bu sürümdeki düzeltmeler:

  1. KÖK TAŞMASI (en kritik): `.rt` radikand sınırı eskiden metin içi "boundary
     token" tahminiyle (örn. " + ", " = " gibi tam eşleşen ayraç arayarak)
     belirleniyordu; bu ayraçlar tam o şekilde bulunamazsa radikand cümlenin
     kalanının TAMAMINI yutuyordu (`.rt` CSS'i `white-space:nowrap` olduğu
     için bu durum kök çizgisinin sayfa/sütun genişliğine taşmasına ve
     metinlerin üst üste binmesine yol açıyordu). DÜZELTME: PDF'te √
     glifinin hemen ardından çizilen GERÇEK üst-çizgi (vinculum) vektör
     çizimi bulunup radikand SADECE bu çizginin x-aralığına giren token'larla
     sınırlandırılıyor (page.get_drawings() + span geometrisi, karakter
     seviyesinde doğrulandı — bkz. bu görev için yapılan analiz).
  2. KESİR DÜZLEŞMESİ / YANLIŞ ŞIK YUTMA: pay/payda gruplama dikey toleransı
     ±10pt (neredeyse tam satır yüksekliği) idi ve yatay eşleşme "herhangi
     bir örtüşme" ile yapılıyordu — bu, komşu şıkların/ifadelerin yanlışlıkla
     bir kesirin payı/paydası sanılmasına yol açıyordu (örn. "a<2/3" ve
     "b<4/5" nin "a<2/34" ve "b<5" olarak birleşmesi). DÜZELTME: dikey
     tolerans ~5pt'e indirildi, yatay kontrol "span bar aralığının içinde"
     (containment) olacak şekilde sıkılaştırıldı.
  3. SATIR/ŞIK ARASI BOŞLUK KAYBI: PyMuPDF aynı GÖRSEL satırı bile büyük
     yatay boşluklarda ayrı "line" nesnelerine bölüyor (örn. beş şık A)..E)
     hepsi aynı y-aralığında ama 5 ayrı "line"). Eski kod satırlar arasına
     HİÇBİR ayraç koymadan birleştiriyordu ("A) a6C) a-6D) a5E) a-4" gibi
     okunaksız birleşmeler). DÜZELTME: iki ardışık "line" dikey olarak
     örtüşüyorsa (aynı satır, sadece yatay boşluklu) araya boşluk konur;
     örtüşmüyorsa (gerçek yeni satır) madde işaretiyle (a),b),I,II...)
     başlıyorsa veya büyük dikey boşluk varsa <br>, aksi halde boşluk konur.
  4. SINIFLANDIRILAMAYAN METNİN PARÇALANMASI: eskiden her "fallback" (kur-tag/
     theory-box/question/answer-key olmayan) blok kendi başına ayrı bir
     `.theory-box`'a sarılıyordu — bu yüzden 3 satırlık basit bir paragraf
     veya tablo 3-6 ayrı yuvarlak kutuya bölünüyordu. DÜZELTME: ardışık
     fallback bloklar TEK bir `.para` bloğunda (kutu/arka plan YOK, sadece
     satır yapısı korunmuş) birleştiriliyor.
  5. CEVAP ANAHTARI YANLIŞ SINIFLANDIRMA: eskiden yalnız "ilk satırın ilk
     span'ı" birleştirilip "1. VE 2. VE 3. VE (A veya B veya C)" alt-dizesi
     aranıyordu — hem yanlış pozitif (sıradan metin) hem yanlış negatif
     (yerel cevap anahtarı 1'den başlamıyorsa, örn. "3. a)...") üretiyordu.
     DÜZELTME: TÜM span'ların birleşik metni + yazı boyutu (cevap anahtarı
     satırları belirgin şekilde küçük punto) + regex kombinasyonu kullanılıyor.
  6. SAYFA ALTI NUMARA SIZINTISI: v2'nin kendi sayfa numarası (footer) bir
     SONRAKİ v3 sayfasında öksüz bir kutu olarak beliriyordu. DÜZELTME: sayfa
     altı bandındaki (y > sayfa_yüksekliği-40) yalnızca-rakam kısa bloklar
     süzülüyor.
  7. VEKTÖR ÇİZİM ŞEKİLLERİNİN KAYBI: yalnızca gömülü raster <image>'lar
     yakalanıyordu; salt vektör çizimlerden oluşan şekiller (renkli sayı
     doğrusu/lejant, sembol tabloları, ızgara çizgileri) hiç yakalanmıyor,
     içeriği sadece harfler/parça metin olarak kalıyordu. DÜZELTME: "bar"
     olmayan (ince çizgi/kesir/kök değil) anlamlı çizim kümeleri tespit
     edilip görüntü olarak kırpılıyor; bu bölgelerin İÇİNDEKİ metin blokları
     çift baskıyı önlemek için akan metne AYRICA eklenmiyor (raster
     görüntülerin içindeki gömülü metin katmanları için de aynı bastırma
     uygulanıyor — bkz. sf.119/123/127-130 QA bulguları).

  KAPSAM DIŞI / BİLİNEN SINIRLAMALAR (bkz. final rapor "kalan riskler"):
   - Bant (tam-genişlik / sütun) sıralama mimarisi DEĞİŞTİRİLMEDİ; bu yüzden
     nadir durumlarda (bir sorunun öncülleri sayfa içinde farklı bir "band"a
     düşerse) sıra karışması hâlâ teorik olarak mümkün.
   - Karmaşık çok-satır/çok-sütun tabloların TAM hücre-hizalı HTML <table>
     olarak yeniden inşası yapılmıyor (ya vektör-çizim varsa görüntü olarak
     kırpılıyor, ya da satır yapısı korunarak akan metin olarak basılıyor).
"""
import os
import re
import json
import shutil
import argparse
import subprocess
import tempfile
from datetime import datetime
import fitz  # PyMuPDF

# ---------------------------------------------------------------------------
# Sabitler
# ---------------------------------------------------------------------------
QNUM_RE = re.compile(r"^(\d+)\.(?:\s+|$)(.*)$", re.DOTALL)
MARKER_RE = re.compile(r"^([a-hA-H]\)|[IVX]{1,4}[.)])\s?")
ANSKEY_PATTERN_RE = re.compile(r"\d{1,3}[.)]\s*[a-eA-E][.)]?")
ANSKEY_LETTER_RE = re.compile(r"[a-h]\)")
SAME_ROW_Y_OVERLAP_TOL = 3.0     # pt — bu kadar dikey örtüşme varsa "aynı satır"
ROOT_BAR_TOL = 1.8               # pt — radikand x-sınırı toleransı
ROOT_BAR_Y_TOL = 16.0            # pt — radikandın bar ile aynı satırda sayılması için
FRAC_Y_OVERLAP = 6.0             # pt — pay/payda karakterinin çizgiyi ne kadar
                                  #   dikey olarak "geçebileceği" (üst/alt indis
                                  #   yüzünden çizgiye taşan glifler için)
FRAC_Y_GAP = 6.0                 # pt — pay/payda ile çizgi arası izin verilen boşluk
FRAC_X_PAD = 2.2                 # pt — pay/payda yatay taşma toleransı
FOOTER_Y_MARGIN = 42.0           # pt — sayfa altından bu kadarı footer bandı sayılır
PROSE_WORD_RE = re.compile(r"[a-zA-ZçğıöşüÇĞİÖŞÜ]{4,}\s+[a-zA-ZçğıöşüÇĞİÖŞÜ]{3,}")


_TR_UPPER_MAP = str.maketrans({"i": "İ", "ı": "I"})


def turkish_upper(s):
    """Python'un yerleşik str.upper()'ı Türkçe'ye duyarlı DEĞİL: küçük
    noktalı 'i'yi noktasız 'I'ya çeviriyor (doğrusu noktalı 'İ'). Bu yüzden
    örn. "Klasikleşmiş Uygulamalar".upper() → "KLASIKLEŞMIŞ..." olur ve
    known_sections listesindeki "KLASİKLEŞMİŞ UYGULAMALAR" (doğru noktalı
    İ) ile HİÇ eşleşmez — bölüm başlığı tamamen kayboluyordu (bkz.
    COORDINATION.md A4a notu, "Klasikleşmiş Uygulamalar" sayımı 16≠12).
    Bu fonksiyon önce Türkçe'ye özgü i/ı harflerini doğru büyük harflerine
    çevirip SONRA genel .upper()'ı uyguluyor (ş/ğ/ü/ö/ç zaten doğru eşleşir)."""
    return s.translate(_TR_UPPER_MAP).upper()


def get_qnum(text):
    m = QNUM_RE.match(text.strip())
    if m:
        return int(m.group(1)), m.group(2).strip()
    return None, None


def span_key(s):
    b = s["bbox"]
    return (round(b[0], 1), round(b[1], 1), round(b[2], 1), round(b[3], 1), s.get("text"))


def rect_key(r):
    return tuple(round(v, 1) for v in r)


def block_full_text(block):
    """Bir bloktaki TÜM span'ların birleşik metni (sınıflandırma için)."""
    if "lines" not in block:
        return ""
    parts = []
    for line in block["lines"]:
        for s in line["spans"]:
            parts.append(s["text"])
    return "".join(parts)


def block_spans_flat(block):
    out = []
    if "lines" not in block:
        return out
    for line in block["lines"]:
        for s in line["spans"]:
            out.append(s)
    return out


def classify_answer_key(full_text, spans):
    """Cevap anahtarı satırı mı? (küçük punto + tekrarlayan 'N) harf' deseni).

    Eskiden yalnız "1. VE 2. VE 3. VE (A veya B veya C)" alt-dize testi vardı —
    hem yanlış pozitif hem yanlış negatif üretiyordu (yerel cevap anahtarı
    1'den başlamayabilir, örn. "3. a) 4 b) 2√3..."). Artık TÜM span metni +
    tekrarlayan "N) harf" deseni sayısı + yazı boyutu birlikte kullanılıyor.
    """
    if not full_text.strip():
        return False
    sizes = [s["size"] for s in spans if s.get("size")]
    med_size = sorted(sizes)[len(sizes) // 2] if sizes else 10.0

    hits = len(ANSKEY_PATTERN_RE.findall(full_text))
    if hits >= 4:
        return True
    if hits >= 2 and med_size <= 8.9:
        return True

    # İkinci biçim: "3. a) 4  b) 2√3  c) 3 ..." — tek baştaki soru numarasından
    # sonra harf-parantez tekrarı (çok maddeli sorunun cevap anahtarı). Gerçek
    # çok maddeli SORULARLA (aynı desen ama gövde punto ~9.6-10pt) karışmaması
    # için yazı boyutu şartı ZORUNLU.
    letter_hits = len(ANSKEY_LETTER_RE.findall(full_text))
    if letter_hits >= 3 and med_size <= 8.9:
        return True
    return False


def _enrich_rawdict_text(text_dict):
    """rawdict modunun span'larında toplu 'text' alanı YOK (sadece karakter
    başına 'chars') — geri kalan boru hattı (block_full_text, is_header,
    classify_answer_key vb.) dict modunun span['text']'ini beklediği için
    burada yeniden kuruyoruz. 'chars' span üzerinde SAKLANIYOR ki kesir/kök
    sınır tespiti karakter düzeyinde bölme yapabilsin (bkz. split_span_at_bars
    — A4a/#6 düzeltmesi: '8√6/4√2' → 8 dışarıda, '√(1−11/36)' → '√(1−11) 36',
    cevap anahtarı '5/6' → '5 6' gibi "span bütünlüğü kesir/kök sınırını
    atlatıyor" bug ailesini çözer)."""
    for block in text_dict.get("blocks", []):
        if "lines" not in block:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                span["text"] = "".join(ch["c"] for ch in span.get("chars", ()))


def split_mixed_blocks(blocks):
    new_blocks = []
    for b in blocks:
        if "lines" not in b or not b["lines"]:
            new_blocks.append(b)
            continue
        
        current_sub_lines = [b["lines"][0]]
        for idx in range(1, len(b["lines"])):
            prev_line = b["lines"][idx-1]
            curr_line = b["lines"][idx]
            
            prev_text = "".join(sp["text"] for sp in prev_line["spans"]).strip()
            curr_text = "".join(sp["text"] for sp in curr_line["spans"]).strip()
            
            prev_sizes = [sp["size"] for sp in prev_line["spans"] if sp.get("size")]
            curr_sizes = [sp["size"] for sp in curr_line["spans"] if sp.get("size")]
            
            prev_med = sorted(prev_sizes)[len(prev_sizes) // 2] if prev_sizes else 10.0
            curr_med = sorted(curr_sizes)[len(curr_sizes) // 2] if curr_sizes else 10.0
            
            prev_hits = len(ANSKEY_PATTERN_RE.findall(prev_text))
            prev_letter_hits = len(ANSKEY_LETTER_RE.findall(prev_text))
            prev_is_ans = (prev_hits >= 4) or (prev_hits >= 2 and prev_med <= 8.9) or (prev_letter_hits >= 3 and prev_med <= 8.9)
            
            curr_hits = len(ANSKEY_PATTERN_RE.findall(curr_text))
            curr_letter_hits = len(ANSKEY_LETTER_RE.findall(curr_text))
            curr_is_ans = (curr_hits >= 4) or (curr_hits >= 2 and curr_med <= 8.9) or (curr_letter_hits >= 3 and curr_med <= 8.9)
            
            curr_is_qstart = bool(QNUM_RE.match(curr_text))
            
            should_split = False
            if prev_is_ans != curr_is_ans:
                should_split = True
            elif abs(prev_med - curr_med) > 2.0:
                should_split = True
            elif curr_is_qstart:
                should_split = True
            
            if should_split:
                new_blocks.append(create_sub_block(b, current_sub_lines))
                current_sub_lines = [curr_line]
            else:
                current_sub_lines.append(curr_line)
        
        if current_sub_lines:
            new_blocks.append(create_sub_block(b, current_sub_lines))
            
    return new_blocks

def create_sub_block(orig_block, lines):
    x0 = min(line["bbox"][0] for line in lines)
    y0 = min(line["bbox"][1] for line in lines)
    x1 = max(line["bbox"][2] for line in lines)
    y1 = max(line["bbox"][3] for line in lines)
    
    new_b = dict(orig_block)
    new_b["bbox"] = (x0, y0, x1, y1)
    new_b["lines"] = lines
    return new_b



def split_span_at_bars(span, thin_bars, y_tol=2.0, min_gap=1.0):
    """Bir PDF span'ı, kendi dikey aralığına yakın ince çizgilerin (kesir
    çizgisi / kök vinculum'u) YATAY sınırlarına göre karakter düzeyinde
    böler. Kaynak PDF sık sık bir kesrin payını/kökün radikandının bir
    parçasını önündeki düz metinle AYNI span'a kaynaştırır (font çalışması
    kırılmıyor) — bu da sonraki kesir/kök gruplama adımlarının span
    BÜTÜNLÜĞÜ üzerinden çalışan sınır kontrolünü atlatır. Bar bu span'ın
    aralığına yakın değilse ya da span zaten tek karakterse dokunmadan
    döner (davranış DEĞİŞMEZ — bu yüzden geniş uygulanması güvenli: yanlış
    pozitif bir "kesim" sadece parçaları tekrar bitişik yazıya döndürür,
    görünür bir fark yaratmaz)."""
    chars = span.get("chars")
    if not chars or len(chars) < 2:
        return [span]
    # Güvenlik ağı: SADECE en az bir RAKAM içeren span'lar bölünmeye adaydır.
    # Gerçek "kaynaşmış" durumların HEPSİ (kesir payı, kök radikandı) rakam
    # içerir; salt düz yazı (harf) satırları rakam içermez. Bu koruma
    # olmadan, sayfadaki TAMAMEN İLGİSİZ bir kesir/kök çizgisi (aynı satır
    # yüksekliğine denk gelen) düz metni yanlışlıkla parçalayıp sahte bir
    # kesir oluşturabiliyordu (bkz. QA: "Kare biçimindeki ... orta" +
    # "noktasından ... A ve B ... iki çiviye" → sahte "orta / a iki" kesri,
    # A4a/#6 sırasında bu split fonksiyonu eklenirken ortaya çıkan regresyon).
    if not any(ch.isdigit() for ch in span["text"]):
        return [span]
    sx0, sy0, sx1, sy1 = span["bbox"]
    cuts = set()
    for (bx0, by0, bx1, by1) in thin_bars:
        if by1 < sy0 - y_tol or by0 > sy1 + y_tol:
            continue
        for bx in (bx0, bx1):
            if sx0 + min_gap < bx < sx1 - min_gap:
                cuts.add(bx)
    if not cuts:
        return [span]
    cuts = sorted(cuts)
    groups = [[] for _ in range(len(cuts) + 1)]
    for ch in chars:
        ccx = (ch["bbox"][0] + ch["bbox"][2]) / 2.0
        idx = 0
        for i, cut in enumerate(cuts):
            if ccx >= cut:
                idx = i + 1
        groups[idx].append(ch)
    pieces = []
    for g in groups:
        if not g:
            continue
        text = "".join(c["c"] for c in g)
        if not text:
            continue
        pieces.append({
            "text": text,
            "font": span["font"],
            "size": span["size"],
            "bbox": (
                min(c["bbox"][0] for c in g),
                min(c["bbox"][1] for c in g),
                max(c["bbox"][2] for c in g),
                max(c["bbox"][3] for c in g),
            ),
        })
    return pieces if pieces else [span]


def rects_close(a, b, pad=6.0):
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    return not (ax1 + pad < bx0 or bx1 + pad < ax0 or ay1 + pad < by0 or by1 + pad < ay0)


def union_rect(a, b):
    return (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]))


def overlap_ratio(inner, outer, pad=2.0):
    ix0, iy0, ix1, iy1 = inner
    ox0, oy0, ox1, oy1 = outer[0] - pad, outer[1] - pad, outer[2] + pad, outer[3] + pad
    dx0, dy0 = max(ix0, ox0), max(iy0, oy0)
    dx1, dy1 = min(ix1, ox1), min(iy1, oy1)
    if dx1 <= dx0 or dy1 <= dy0:
        return 0.0
    inter = (dx1 - dx0) * (dy1 - dy0)
    area = max(0.0, ix1 - ix0) * max(0.0, iy1 - iy0)
    return inter / area if area > 0 else 0.0


def shrink_rect_to_exclude(rect, bboxes):
    rx0, ry0, rx1, ry1 = rect
    for bx0, by0, bx1, by1 in bboxes:
        ix0, iy0 = max(rx0, bx0), max(ry0, by0)
        ix1, iy1 = min(rx1, bx1), min(ry1, by1)
        if ix1 <= ix0 or iy1 <= iy0:
            continue
        options = []
        if by0 > ry0:
            options.append(((rx0, ry0, rx1, by0), (rx1 - rx0) * (by0 - ry0)))
        if by1 < ry1:
            options.append(((rx0, by1, rx1, ry1), (rx1 - rx0) * (ry1 - by1)))
        if bx0 > rx0:
            options.append(((rx0, ry0, bx0, ry1), (bx0 - rx0) * (ry1 - ry0)))
        if bx1 < rx1:
            options.append(((bx1, ry0, rx1, ry1), (rx1 - bx1) * (ry1 - ry0)))
        if options:
            options.sort(key=lambda x: x[1], reverse=True)
            rx0, ry0, rx1, ry1 = options[0][0]
    return (rx0, ry0, rx1, ry1)



# ---------------------------------------------------------------------------
# Sayfa geometrisi: kök çizgileri (vinculum), kesir çizgileri, ayraçlar
# ---------------------------------------------------------------------------
def collect_thin_bars(drawings):
    """height<2.6 olan tüm ince çizim dikdörtgenlerini döndürür (rect listesi)."""
    bars = []
    for d in drawings:
        x0, y0, x1, y1 = d["rect"]
        w, h = x1 - x0, y1 - y0
        if h < 2.6 and w > 0.8:
            bars.append((x0, y0, x1, y1))
    return bars


def match_root_bars(page_spans, thin_bars):
    """Her '√' span'ını, hemen ardından çizilen üst-çizgiye (vinculum) eşler.

    Dönüş: dict[span_key] -> bar_rect, ve kullanılan bar indekslerinin seti
    (kesir tespitinden hariç tutulmaları için).
    """
    root_spans = [s for s in page_spans if s["text"] == "√"]
    used = set()
    root_bar_for = {}
    for s in sorted(root_spans, key=lambda s: (s["bbox"][1], s["bbox"][0])):
        sx0, sy0, sx1, sy1 = s["bbox"]
        best, best_d = None, 1e9
        for bi, (x0, y0, x1, y1) in enumerate(thin_bars):
            if bi in used:
                continue
            if x1 - x0 > 180.0:
                continue  # geniş ayraç/soru-arası çizgi, kök çizgisi olamaz
            cond = (abs(x0 - sx1) < 4.0 and abs(y0 - sy0) < 12.0) or \
                   (sx0 - 2 <= x0 <= sx1 + 2 and abs(y0 - sy0) < 12.0)
            if cond:
                dist = abs(y0 - sy0) + abs(x0 - sx1)
                if dist < best_d:
                    best_d, best = dist, bi
        if best is not None:
            used.add(best)
            root_bar_for[span_key(s)] = thin_bars[best]
    return root_bar_for, used


def collect_theory_boxes(drawings, profile=None):
    boxes = []
    r_min, r_max = 0.9, 0.95
    g_min, g_max = 0.95, 0.98
    b_min, b_max = 0.97, 0.99
    
    if profile and "theory_box_color" in profile:
        color_conf = profile["theory_box_color"]
        r_min, r_max = color_conf.get("r_range", [r_min, r_max])
        g_min, g_max = color_conf.get("g_range", [g_min, g_max])
        b_min, b_max = color_conf.get("b_range", [b_min, b_max])
        
    for d in drawings:
        if d["type"] == "fs":
            rect = d["rect"]
            fill = d.get("fill")
            if fill and r_min <= fill[0] <= r_max and g_min <= fill[1] <= g_max and b_min <= fill[2] <= b_max:
                boxes.append(rect)
    return boxes


def collect_figure_regions(drawings, theory_boxes, excluded_bar_keys, text_blocks=()):
    """Salt vektör çizimlerden oluşan (bar/tema-kutusu olmayan) şekil
    kümelerini bulur — renkli sayı doğrusu, lejant, sembol tablosu vb.
    Bunlar 'bar' (ince çizgi, kök/kesir/ayraç) ya da theory-box arka planı
    DEĞİLSE, birbirine yakın çizimler tek bir bölgede kümelenip görüntü
    olarak kırpılmaya aday olur.

    A4a/#6 REGRESYON DÜZELTMESİ: Tek bir dolgu (fill) dikdörtgeninden oluşan
    kümeler — bölüm başlığı ("GÜNLÜK HAYAT UYGULAMALARI" vb.) veya "2020 MSÜ
    Kurgusu" etiketi gibi metinlerin ARKASINDAKİ salt dekoratif rozet/banner
    dolgusu — gerçek bir diyagram DEĞİLDİR. Bunlar eskiden figür sayılıp
    görüntü olarak kırpılıyor, ÜZERLERİNDEKİ gerçek metin de "çift baskı
    önleme" adımıyla TAMAMEN siliniyordu (regresyon: .kur-tag/.tag-kurgusu
    içeriği kayboluyordu, bkz. COORDINATION.md FAZ 3 A4a notu). Bu yüzden:
    kümede TEK bir çizim varsa VE bu çizim dolgulu (fill) bir dikdörtgense
    VE üzerinde/içinde GERÇEK bir metin bloğu oturuyorsa (overlap>0.6) —
    bunu dekoratif banner say, figür listesine EKLEME (metin normal akışta
    kalsın). Gerçek tek-çizimli notasyon sembolleri (○, □ vb.) genelde
    stroke'tur (fill=None) ya da altlarında örtüşen metin YOKTUR — ikisi de
    bu kuralın dışında kalır, eskisi gibi görüntü olarak kırpılmaya devam eder.
    """
    candidates = []
    for d in drawings:
        x0, y0, x1, y1 = d["rect"]
        w, h = x1 - x0, y1 - y0
        key = rect_key(d["rect"])
        if key in excluded_bar_keys:
            continue
        if h < 2.6 and w > 0.8:
            continue  # herhangi bir ince çizgi (bar ailesi) — atla
        is_theory_bg = any(
            abs(x0 - tb[0]) < 2 and abs(y0 - tb[1]) < 2 and abs(x1 - tb[2]) < 2 and abs(y1 - tb[3]) < 2
            for tb in theory_boxes
        )
        if is_theory_bg:
            continue
        if w < 3.0 or h < 3.0:
            continue
        candidates.append(d)

    clusters = []  # [x0,y0,x1,y1, [members]]
    for d in candidates:
        rect = d["rect"]
        merged = False
        for c in clusters:
            if rects_close(tuple(c[:4]), rect, pad=8.0):
                c[0], c[1], c[2], c[3] = union_rect(tuple(c[:4]), rect)
                c[4].append(d)
                merged = True
                break
        if not merged:
            clusters.append([rect[0], rect[1], rect[2], rect[3], [d]])

    # birleşme sonrası tekrar geçiş (transitive merge) — basit iki-pas yaklaşımı
    changed = True
    while changed:
        changed = False
        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                if clusters[i] is None or clusters[j] is None:
                    continue
                if rects_close(tuple(clusters[i][:4]), tuple(clusters[j][:4]), pad=8.0):
                    clusters[i][0], clusters[i][1], clusters[i][2], clusters[i][3] = union_rect(
                        tuple(clusters[i][:4]), tuple(clusters[j][:4]))
                    clusters[i][4].extend(clusters[j][4])
                    clusters[j] = None
                    changed = True
        clusters = [c for c in clusters if c is not None]

    figures = []
    text_block_bboxes = [b["bbox"] for b in text_blocks if "lines" in b]
    
    for c in clusters:
        rect = (c[0], c[1], c[2], c[3])
        members = c[4]
        w, h = rect[2] - rect[0], rect[3] - rect[1]
        if not (w > 14 and h > 9):
            continue

        # Check if it overlaps with any text block containing header/kurgu text
        is_header_bg = False
        for b in text_blocks:
            if "lines" not in b:
                continue
            tb_bbox = b["bbox"]
            if overlap_ratio(tb_bbox, rect) > 0.4:
                text_full = block_full_text(b).lower()
                if "kurgu" in text_full or any(ks.lower() in text_full for ks in [
                    "isinma hareketleri", "günlük hayat uygulamalari", "ösym sorularina hazirlik",
                    "ösym kurgularsa", "pist alani", "klasikleşmiş uygulamalar", "araliklar",
                    "sayi araliklarinin gösterimi"
                ]):
                    is_header_bg = True
                    break
        if is_header_bg:
            continue

        if len(members) == 1:
            m = members[0]
            if m.get("type") in ("f", "fs") and m.get("fill") is not None:
                has_overlaying_text = any(
                    overlap_ratio(tb, rect) > 0.6 for tb in text_block_bboxes
                )
                if has_overlaying_text:
                    continue  # dekoratif rozet/banner arka planı — figür değil
        figures.append(rect)
    return figures


def extract_page_images(doc, pnum, page, assets_dir):
    image_list = page.get_image_info(xrefs=True)
    images_in_page = []
    for idx, img in enumerate(image_list):
        x0, y0, x1, y1 = img["bbox"]
        if y0 < 70 and x0 < 100:
            continue  # header logosu
        xref = img["xref"]
        img_name = f"p{pnum+1}_img_{idx}.png"
        img_path = os.path.join(assets_dir, img_name)
        if xref == 0:
            pix = page.get_pixmap(clip=img["bbox"], dpi=150)
            pix.save(img_path)
        else:
            try:
                base_image = doc.extract_image(xref)
                with open(img_path, "wb") as f:
                    f.write(base_image["image"])
            except Exception:
                pix = page.get_pixmap(clip=img["bbox"], dpi=150)
                pix.save(img_path)
        images_in_page.append({
            "type": "image",
            "bbox": img["bbox"],
            "page": pnum + 1,
            "img_idx": idx,
            "path": f"assets/{img_name}",
        })
    return images_in_page


def extract_figure_crops(page, pnum, figure_regions, assets_dir, start_idx=0):
    figs = []
    for i, rect in enumerate(figure_regions):
        x0, y0, x1, y1 = rect
        pad = 2.5
        clip = (max(0, x0 - pad), max(0, y0 - pad), x1 + pad, y1 + pad)
        img_name = f"p{pnum+1}_fig_{start_idx+i}.png"
        img_path = os.path.join(assets_dir, img_name)
        try:
            pix = page.get_pixmap(clip=clip, dpi=150)
            pix.save(img_path)
        except Exception:
            continue
        figs.append({
            "type": "image",
            "bbox": clip,
            "page": pnum + 1,
            "img_idx": f"fig_{start_idx+i}",
            "path": f"assets/{img_name}",
            "_is_figure": True,
        })
    return figs


TESSERACT_BIN = shutil.which("tesseract")
OCR_QNUM_RE = re.compile(r"^\s*\d{1,3}[.)]")


def ocr_detect_question_number(page, bbox, ocr_stats):
    """F9 — bağımsız img-block yazılmadan önce SOL-ÜST köşesine (genişliğin ~%35'i x
    yüksekliğin ~%25'i) bakıp orada bir soru numarası ("12." / "7)") olup olmadığını
    tesseract ile denetler (SADECE rakam+nokta+parantez beyaz-listesiyle, --psm 6).

    Sistemde `eng` dil paketi YOK (yalnız afr+osd) — `-l eng` denemek her zaman
    "Failed loading language" hatasıyla başarısız olur, bu yüzden `-l afr`
    kullanılır (rakam tanımada dil script'i Latin olduğu sürece fark etmiyor).
    tesseract kurulu değilse/başarısız olursa SESSİZCE False döner — davranış
    OCR öncesiyle birebir aynı kalır (img-block olarak devam), bkz. ocr_stats.
    """
    ocr_stats["denendi"] = ocr_stats.get("denendi", 0) + 1
    if not TESSERACT_BIN:
        ocr_stats["atlandi_arac_yok"] = ocr_stats.get("atlandi_arac_yok", 0) + 1
        return False

    x0, y0, x1, y1 = bbox
    w, h = x1 - x0, y1 - y0
    if w <= 1 or h <= 1:
        ocr_stats["atlandi_gecersiz_bbox"] = ocr_stats.get("atlandi_gecersiz_bbox", 0) + 1
        return False
    corner = (x0, y0, x0 + 0.35 * w, y0 + 0.25 * h)

    tmp_path = None
    try:
        pix = page.get_pixmap(clip=corner, dpi=300)
        fd, tmp_path = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        pix.save(tmp_path)
        sonuc = subprocess.run(
            [
                TESSERACT_BIN, tmp_path, "stdout",
                "-l", "afr", "--psm", "6",
                "-c", "tessedit_char_whitelist=0123456789.)",
            ],
            capture_output=True, text=True, timeout=10,
        )
        if sonuc.returncode != 0:
            ocr_stats["atlandi_tesseract_hatasi"] = ocr_stats.get("atlandi_tesseract_hatasi", 0) + 1
            return False
        metin = sonuc.stdout.strip()
        ilk_satir = metin.splitlines()[0].strip() if metin else ""
        if OCR_QNUM_RE.match(ilk_satir):
            ocr_stats["donusturuldu"] = ocr_stats.get("donusturuldu", 0) + 1
            return True
        ocr_stats["eslesmedi"] = ocr_stats.get("eslesmedi", 0) + 1
        return False
    except subprocess.TimeoutExpired:
        ocr_stats["atlandi_zaman_asimi"] = ocr_stats.get("atlandi_zaman_asimi", 0) + 1
        return False
    except Exception:
        ocr_stats["atlandi_beklenmeyen_hata"] = ocr_stats.get("atlandi_beklenmeyen_hata", 0) + 1
        return False
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def normalize_ocr_text(s):
    """OCR/karşılaştırma için normalize: Türkçe büyük harfe çevirir (turkish_upper),
    sonra harf/rakam DIŞINDAKİ HER ŞEYİ (boşluk, noktalama, tesseract gürültüsü)
    atar. Hem profildeki yasaklı ifadeler (örn. "EGEMEN SARIKCI") hem
    tesseract'ın okuduğu kelimeler AYNI şekilde normalize edilip
    karşılaştırılır — böylece harf aralığı ("E G E M E N"), büyük/küçük harf
    ve Türkçe İ/ı farkları eşleşmeyi bozmaz."""
    s = turkish_upper(s or "")
    return re.sub(r"[^A-ZÇĞİÖŞÜ0-9]", "", s)


def _parse_tesseract_tsv(tsv_text):
    """`tesseract ... tsv` çıktısını kelime düzeyinde (level==5) satırlara
    ayrıştırır. Sütun sırası sürüme göre değişebileceği için başlık
    satırından isimle eşlenir (pozisyon varsayılmaz)."""
    lines = tsv_text.splitlines()
    if not lines:
        return []
    header = lines[0].split("\t")
    idx = {name: i for i, name in enumerate(header)}
    required = ("level", "block_num", "par_num", "line_num", "word_num",
                "left", "top", "width", "height", "text")
    if not all(r in idx for r in required):
        return []
    words = []
    for line in lines[1:]:
        if not line.strip():
            continue
        cols = line.split("\t")
        if len(cols) < len(header):
            continue
        try:
            if int(cols[idx["level"]]) != 5:
                continue
            text = cols[idx["text"]]
            if not text.strip():
                continue
            words.append({
                "block_num": int(cols[idx["block_num"]]),
                "par_num": int(cols[idx["par_num"]]),
                "line_num": int(cols[idx["line_num"]]),
                "word_num": int(cols[idx["word_num"]]),
                "left": int(cols[idx["left"]]),
                "top": int(cols[idx["top"]]),
                "width": int(cols[idx["width"]]),
                "height": int(cols[idx["height"]]),
                "text": text,
            })
        except (ValueError, KeyError):
            continue
    return words


def _redact_banned_text_on_pixmap(pix, banned_texts, pad=4.0):
    """F12 — tam-sayfa render edilmiş bir Pixmap üzerinde profildeki
    yasakli_metinler'i tesseract TSV (bbox'lı) çıktısıyla arar; eşleşen
    kelime dizisinin bbox BİRLEŞİMİNİ (küçük pay ile) BEYAZ doldurur.

    F9'daki (ocr_detect_question_number) çağrı deseniyle AYNI ikili/dil
    (TESSERACT_BIN, -l afr — sistemde eng yok) kullanılır, ama burada TÜM
    sayfa taranacağı ve kelimelerin sayfa üzerindeki KONUMU gerektiği için
    `stdout` metin çıktısı yerine `tsv` (bbox'lı) config kullanılır.

    Eşleştirme satır bazlı yapılır: aynı (block,par,line) içindeki kelimeler
    normalize edilip (normalize_ocr_text) birleştirilir, yasaklı ifade bu
    birleşik dizede aranır — böylece "EGEMEN SARIKCI" iki ayrı kelime olarak
    okunsa da (ya da OCR gürültüsüyle bitişik/ayrık okunsa da) yakalanır.
    tesseract çağrısı başarısız olursa (binary yok/timeout/hata) SESSİZCE 0
    döner; TESSERACT_BIN'in var olup olmadığını çağıran taraf ayrıca
    kontrol edip rapora UYARI yazar (bu fonksiyon o kararı vermez)."""
    banned_norm = [normalize_ocr_text(b) for b in banned_texts if b and b.strip()]
    banned_norm = [b for b in banned_norm if b]
    if not banned_norm or not TESSERACT_BIN:
        return 0

    tmp_path = None
    try:
        fd, tmp_path = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        pix.save(tmp_path)
        sonuc = subprocess.run(
            [TESSERACT_BIN, tmp_path, "stdout", "-l", "afr", "--psm", "3", "tsv"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
        )
        if sonuc.returncode != 0:
            return 0
        words = _parse_tesseract_tsv(sonuc.stdout)
    except Exception:
        return 0
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass

    lines = {}
    for w in words:
        key = (w["block_num"], w["par_num"], w["line_num"])
        lines.setdefault(key, []).append(w)

    silinen = 0
    white = (255,) * pix.n
    for line_words in lines.values():
        line_words.sort(key=lambda w: w["word_num"])
        condensed = ""
        spans = []  # (start, end, word) — normalize edilmiş dizedeki aralık
        for w in line_words:
            norm = normalize_ocr_text(w["text"])
            if not norm:
                continue
            start = len(condensed)
            condensed += norm
            spans.append((start, len(condensed), w))
        if not condensed:
            continue
        for banned in banned_norm:
            search_from = 0
            while True:
                pos = condensed.find(banned, search_from)
                if pos == -1:
                    break
                end = pos + len(banned)
                matched_words = [w for (s, e, w) in spans if s < end and e > pos]
                if matched_words:
                    x0 = min(w["left"] for w in matched_words) - pad
                    y0 = min(w["top"] for w in matched_words) - pad
                    x1 = max(w["left"] + w["width"] for w in matched_words) + pad
                    y1 = max(w["top"] + w["height"] for w in matched_words) + pad
                    irect = fitz.IRect(
                        max(0, int(x0)), max(0, int(y0)),
                        min(pix.width, int(x1)), min(pix.height, int(y1)),
                    )
                    if not irect.is_empty:
                        pix.set_rect(irect, white)
                        silinen += 1
                search_from = pos + 1
    return silinen


def render_full_page_tam_sayfa(page, pnum, assets_dir, banned_texts):
    """F12 — 'tam_sayfa' modunda resim tabanlı bir sayfayı 200dpi PNG olarak
    render eder (fitz), tesseract varsa profildeki yasaklı metinleri beyaz
    dolgu ile siler, ve assets/pNNN_tam.png olarak kaydeder.

    Dönen değer: (goreli_yol, silinen_bolge_sayisi, tesseract_eksik_mi).
    tesseract_eksik_mi: yasaklı metin listesi DOLU ama TESSERACT_BIN yoksa
    True (çağıran taraf bunu rapora tek seferlik UYARI olarak yazar)."""
    pix = page.get_pixmap(dpi=200, alpha=False)
    tesseract_eksik = bool(banned_texts) and not TESSERACT_BIN
    silinen = 0
    if banned_texts and TESSERACT_BIN:
        try:
            silinen = _redact_banned_text_on_pixmap(pix, banned_texts)
        except Exception:
            pass
    img_name = f"p{pnum+1:03d}_tam.png"
    img_path = os.path.join(assets_dir, img_name)
    pix.save(img_path)
    return f"assets/{img_name}", silinen, tesseract_eksik


def sort_blocks_reading_order(blocks):
    """Bir sütun içindeki blokları GÖRSEL SATIR okuma sırasına göre dizer.

    A4a/#6 düzeltmesi: sadece bbox y0'a göre sıralamak, aynı görsel satırda
    yan yana duran bloklardan biri RAISED içerik (kesir payı, kök vinculum'u
    gibi yükseltilmiş bir öğe) içeriyorsa yanılıyor — o bloğun y0'ı normal
    taban-hizalı bir etiket bloğundan (örn. "c) ") daha küçük (daha yukarıda)
    çıkıyor, bu da "d) [kesir] c) [kesir]" gibi etiket sırası karışıklığına
    yol açıyordu (bkz. COORDINATION.md QA: "alt-öğe etiket sırası bozuk").
    Düzeltme: dikey aralığı ÖRTÜŞEN ardışık bloklar aynı "satır" sayılıp
    SOLDAN SAĞA (x0) dizilir; örtüşmeyenler ayrı satırlar olarak y0 sırasına
    göre gelir."""
    ordered_input = sorted(blocks, key=lambda b: b["bbox"][1])
    rows = []
    cur = None
    for b in ordered_input:
        y0, y1 = b["bbox"][1], b["bbox"][3]
        if cur is not None:
            cy0, cy1 = cur["y0"], cur["y1"]
            overlap = min(y1, cy1) - max(y0, cy0)
            span = min(y1 - y0, cy1 - cy0)
            if span > 0 and overlap > 0.4 * span:
                cur["blocks"].append(b)
                cur["y0"] = min(cy0, y0)
                cur["y1"] = max(cy1, y1)
                continue
        cur = {"y0": y0, "y1": y1, "blocks": [b]}
        rows.append(cur)
    out = []
    for row in rows:
        row["blocks"].sort(key=lambda b: b["bbox"][0])
        out.extend(row["blocks"])
    return out


def is_footer_block(block, page_height):
    x0, y0, x1, y1 = block["bbox"]
    if y0 < page_height - FOOTER_Y_MARGIN:
        return False
    text = block_full_text(block).strip()
    return bool(re.fullmatch(r"\d{1,4}", text))


def filter_banned_lines(text_dict, banned_texts):
    """Profildeki yasakli_metinler'i (örn. kaynak sayfalardaki "EGEMEN SARIKCI"
    banner'ı) satır düzeyinde siler. Karşılaştırma boşluk/harf-aralığı ve
    büyük-küçük harf duyarsızdır ("E G E M E N  S A R I K C I" da yakalanır).
    Dönen değer: silinen satır sayısı."""
    if not banned_texts:
        return 0
    banned_condensed = [re.sub(r"\s+", "", b).upper() for b in banned_texts if b.strip()]
    if not banned_condensed:
        return 0
    removed = 0
    for block in text_dict.get("blocks", []):
        if "lines" not in block:
            continue
        kept_lines = []
        for line in block["lines"]:
            line_text = "".join(sp.get("text", "") for sp in line.get("spans", []))
            condensed = re.sub(r"\s+", "", line_text).upper()
            if condensed and any(b in condensed for b in banned_condensed):
                removed += 1
                continue
            kept_lines.append(line)
        block["lines"] = kept_lines
    return removed


# ---------------------------------------------------------------------------
# Token akışı: satır/şık boşluğu korunumu + kesir gruplama + kök gövdesi
# ---------------------------------------------------------------------------
def _compute_base_size(tokens):
    """Bu blok için 'normal gövde punto'sunu bulur (üs/derece tespiti MUTLAK
    bir eşiğe değil, bu değere GÖRELİ yapılır). Böylece tamamı küçük punto
    olan bölgeler (örn. cevap anahtarı satırları, ~7.4pt) yanlışlıkla üs/kök
    derecesi sanılmaz — bkz. dosya başlığı ve QA bulguları."""
    sizes = []

    def walk(toks):
        for t in toks:
            if t.get("type") == "fraction":
                walk(t["num_spans"])
                walk(t["den_spans"])
            elif t.get("type") == "image":
                continue
            elif t.get("text") and t.get("text") != "√":
                sizes.append(t.get("size", 10))

    walk(tokens)
    if not sizes:
        return 10.0
    sizes.sort()
    return sizes[len(sizes) // 2]


def tokens_to_html(tokens, base_size=None):
    if base_size is None:
        base_size = _compute_base_size(tokens)
    html_parts = []
    i = 0
    n = len(tokens)
    while i < n:
        t = tokens[i]

        # Satır/şık arası ayraç (boşluk ya da <br>) — sadece bu bloğun kendi
        # akışında ilk token değilse uygulanır (recursion'da radikand/kesir
        # içeriğinin BAŞINA sızmasın diye).
        brk = t.get("_break_before")
        if brk and html_parts:
            html_parts.append("<br>\n" if brk == "br" else " ")

        if t.get("type") == "fraction":
            num_html = tokens_to_html(t["num_spans"], base_size)
            den_html = tokens_to_html(t["den_spans"], base_size)
            html_parts.append(
                f'<span class="frac"><span class="num">{num_html}</span>'
                f'<span class="den">{den_html}</span></span>'
            )
            i += 1
            continue

        if t.get("type") == "image":
            html_parts.append(f'<div class="img-block"><img src="{t["path"]}" /></div>')
            i += 1
            continue

        text = t.get("text", "")

        # Kök derecesi tespiti: eskiden sadece "küçük punto + hemen ardından √"
        # bakıyordu — bu, TÜMÜ küçük puntolu bölgelerde (örn. cevap anahtarı
        # satırları, hepsi ~7.4pt) her düz metin parçasını (uzunluğu ne olursa
        # olsun) yanlışlıkla "derece" sayıyordu (bkz. QA: cevap anahtarının
        # tamamı bir .rt data-n değerine dönüşüyordu). Artık derece adayı KISA
        # bir rakam dizisi olmalı VE ardındaki √'den GERÇEKTEN (mutlak eşik
        # değil, göreli) daha küçük olmalı.
        next_tok = tokens[i + 1] if i + 1 < n else None
        is_degree = (
            next_tok is not None and next_tok.get("text") == "√"
            and len(text) <= 2 and text.isdigit()
            and t.get("size", 10) < next_tok.get("size", 10) - 0.8
        )
        if is_degree or text == "√":
            if is_degree:
                degree = text
                root_token = tokens[i + 1]
                start_j = i + 2
            else:
                degree = None
                root_token = t
                start_j = i + 1

            bar = root_token.get("root_bar")
            radicand_tokens = []
            j = start_j
            if bar:
                bx0, by0, bx1, by1 = bar
                while j < n:
                    nt = tokens[j]
                    text_clean = nt.get("text", "").strip().lower().rstrip(",.?!")
                    
                    # Prose word check
                    is_prose = False
                    if any(c in text_clean for c in "ığüşöç"):
                        is_prose = True
                    elif text_clean in {
                        "ise", "ve", "veya", "olduğuna", "göre", "ifadesinin", "değeri", "kaçtır",
                        "buna", "için", "tüm", "değerleri", "bir", "gerçel", "sayı", "sayısı",
                        "hangisi", "eşittir", "en", "sade", "hali", "nedir", "bu", "kareni", "küpü",
                        "toplamı", "farkı", "oranı", "çarpımı", "bölümü", "alanı", "çevresi",
                        "uzunluğu", "genişliği", "yüksekliği", "hacmi", "doğal", "tam", "rasyonel",
                        "reel", "gerçek", "karmaşık", "kümesi", "elemanı", "alt", "küme", "kesişim",
                        "birleşim", "fark", "tümleyen", "boş", "evrensel"
                    }:
                        is_prose = True
                    
                    if is_prose:
                        break
                        
                    nb = nt.get("bbox")
                    if nb is None:
                        break
                    nx0, ny0, nx1, ny1 = nb
                    if nx0 > bx1 + ROOT_BAR_TOL:
                        break
                    if ny0 > by1 + ROOT_BAR_Y_TOL or ny1 < by0 - ROOT_BAR_Y_TOL:
                        break
                    radicand_tokens.append(nt)
                    j += 1
                    if nx1 >= bx1 - ROOT_BAR_TOL:
                        break

                # Trim trailing operators
                while radicand_tokens:
                    last_text = radicand_tokens[-1].get("text", "").strip().lower().rstrip(",.?!")
                    if last_text in {"+", "-", "=", "<", ">", "<=", ">="}:
                        radicand_tokens.pop()
                        j -= 1
                    else:
                        break

                # Kısa vinculum + hemen bitişik kesir (bkz. QA: kaynak
                # PDF'te kimi zaman kökün üst-çizgisi radikandın SADECE ilk
                # kısmını kaplıyor — örn. √(1−11/36) fiziksel vinculum
                # sadece "1−" üzerinde bitiyor, "11/36" hemen ARDINDAN
                # boşluksuz geliyor). Ana tarama bittikten sonra, sıradaki
                # token bir KESİR ve öncekine görünür boşluk BIRAKMADAN
                # (≤2pt) bitişikse, bu da radikandın devamı sayılır —
                # aksi halde kesir kökün dışında kopuk kalır ("√(1−11) 36"
                # gibi anlamsız bir bölünme oluşur).
                while j < n and radicand_tokens:
                    nt = tokens[j]
                    if nt.get("type") != "fraction":
                        break
                    nb = nt.get("bbox")
                    if nb is None:
                        break
                    prev_bbox = radicand_tokens[-1].get("bbox")
                    if prev_bbox is None:
                        break
                    if nb[0] - prev_bbox[2] > 2.0:
                        break
                    if nb[1] > by1 + ROOT_BAR_Y_TOL or nb[3] < by0 - ROOT_BAR_Y_TOL:
                        break
                    radicand_tokens.append(nt)
                    j += 1
            else:
                # Bar bulunamadıysa (nadir/güvenlik ağı): tek token ile sınırla,
                # eski davranıştaki "cümlenin kalanını yutma" riskini önler.
                if j < n:
                    radicand_tokens.append(tokens[j])
                    j += 1

            radicand_html = tokens_to_html(radicand_tokens, base_size) if radicand_tokens else ""
            if degree:
                html_parts.append(f'<span class="rt" data-n="{degree}">{radicand_html}</span>')
            else:
                html_parts.append(f'<span class="rt">{radicand_html}</span>')
            i = j
            continue

        text_esc = text.replace("&infty;", "∞").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if t.get("size", 10) < base_size - 1.3:
            html_parts.append(f'<span class="sup">{text_esc}</span>')
        else:
            html_parts.append(text_esc)
        i += 1
    return "".join(html_parts)


def make_span_grouper(fraction_bars, root_bar_for):
    """process_spans'ı kapatan (closure) fabrika — sayfa başına bir kez
    kurulan fraction_bars/root_bar_for'a erişmek için."""

    def process_spans(spans):
        col_bars = fraction_bars

        used_span_indices = set()
        fraction_tokens = []

        for bar in col_bars:
            bx0, by0, bx1, by1 = bar
            bar_center = (by0 + by1) / 2
            bar_rk = rect_key(bar)

            # Bu bar aynı zamanda BAŞKA bir √'nin kendi vinculum'u (root_bar)
            # olarak mı eşleşmiş? Eşleşmişse, bu bar'ı kesir ayracı olarak
            # kullanmak SADECE o √'nin TAM OLARAK bu kesirin payının BAŞINDA
            # olduğu "kök bir kesri sarmalıyor" durumunda (örn. √(16/25))
            # güvenlidir. Aksi halde (örn. iki BAĞIMSIZ satır "a=√2" / "b=√3"
            # şans eseri aynı bar'a yakınsa) sahte kesir oluşur — bu durumda
            # bar TAMAMEN reddedilir (aşağıda).
            claiming_root_idx = None
            for s_idx, s in enumerate(spans):
                if s.get("text") == "√" and s.get("root_bar") is not None and rect_key(s["root_bar"]) == bar_rk:
                    claiming_root_idx = s_idx
                    break

            num_spans, den_spans = [], []
            for s_idx, s in enumerate(spans):
                if s_idx in used_span_indices:
                    continue
                sx0, sy0, sx1, sy1 = s["bbox"]
                if not (sx0 >= bx0 - FRAC_X_PAD and sx1 <= bx1 + FRAC_X_PAD):
                    continue

                span_center_y = (sy0 + sy1) / 2
                # üst/alt indisli glifler (kare/küp işareti, üs) çizgiyi birkaç
                # pt dikey olarak geçebilir — bu yüzden negatif (örtüşme) tarafı
                # da toleranslı; ama çizgiden ÇOK uzak (başka satır) span'lar
                # yine de reddedilir (FRAC_Y_GAP üst sınırı).
                is_num = span_center_y < bar_center and -FRAC_Y_OVERLAP <= (by0 - sy1) < FRAC_Y_GAP
                is_den = span_center_y > bar_center and -FRAC_Y_OVERLAP <= (sy0 - by1) < FRAC_Y_GAP
                if is_num:
                    num_spans.append((s_idx, s))
                elif is_den:
                    den_spans.append((s_idx, s))

            if claiming_root_idx is not None:
                min_num_idx = min((x[0] for x in num_spans), default=None)
                if min_num_idx != claiming_root_idx + 1:
                    # Bar başka bir köke ait VE bu kesirin payı o kökün hemen
                    # ardından başlamıyor — bağımsız/ilgisiz eşleşme, atla.
                    continue

            if num_spans and den_spans:
                num_text = "".join(s["text"] for _, s in sorted(num_spans, key=lambda x: x[1]["bbox"][0]))
                den_text = "".join(s["text"] for _, s in sorted(den_spans, key=lambda x: x[1]["bbox"][0]))
                # Güvenlik ağı: gerçek matematik kesirleri KISA ifadelerdir;
                # "soru cümlesi / şık" gibi DÜZYAZI iki satırın yanlışlıkla
                # kesir sanılmasını engelle (bkz. QA: "işleminin en sade hali
                # nedir? / B) a-5" sahte kesir dönüşümü).
                combined = num_text + " " + den_text
                if "?" in combined or PROSE_WORD_RE.search(combined):
                    continue
                if len(num_text) > 30 or len(den_text) > 30:
                    continue

                all_grouped = num_spans + den_spans
                min_idx = min(x[0] for x in all_grouped)
                brk = None
                for s_idx, s in all_grouped:
                    if s_idx == min_idx:
                        brk = s.get("_break_before")
                for s_idx, _ in all_grouped:
                    used_span_indices.add(s_idx)
                frac_token = {
                    "type": "fraction",
                    "bbox": (bx0, min(s[1]["bbox"][1] for s in num_spans), bx1, max(s[1]["bbox"][3] for s in den_spans)),
                    "num_spans": [s for _, s in sorted(num_spans, key=lambda x: x[1]["bbox"][0])],
                    "den_spans": [s for _, s in sorted(den_spans, key=lambda x: x[1]["bbox"][0])],
                }
                if brk:
                    frac_token["_break_before"] = brk
                fraction_tokens.append({"insert_idx": min_idx, "token": frac_token})

        tokens = []
        i = 0
        while i < len(spans):
            for ft in fraction_tokens:
                if ft["insert_idx"] == i:
                    tokens.append(ft["token"])
            if i not in used_span_indices:
                tokens.append(spans[i])
            i += 1
        return tokens

    return process_spans


def make_block_grouper(process_spans, root_bar_for, thin_bars):
    """process_blocks_together'ı kapatan fabrika. Ardışık PDF 'line'
    nesneleri arasına satır-boşluğu/şık-boşluğu ayracı ekler (bkz. dosya
    başlığı madde 3). `thin_bars` span'ları kesir/kök sınırlarına göre
    karakter düzeyinde bölmek için kullanılır (bkz. split_span_at_bars)."""

    def build_spans_with_breaks(blocks_list):
        spans_out = []
        prev_line = None  # (x0,y0,x1,y1)
        for b in blocks_list:
            if b.get("type") == "image":
                spans_out.append(b)
                prev_line = None
                continue
            if "lines" not in b:
                continue
            for line in b["lines"]:
                if not line["spans"]:
                    continue
                lx0 = min(sp["bbox"][0] for sp in line["spans"])
                ly0 = min(sp["bbox"][1] for sp in line["spans"])
                lx1 = max(sp["bbox"][2] for sp in line["spans"])
                ly1 = max(sp["bbox"][3] for sp in line["spans"])
                line_text = "".join(sp["text"] for sp in line["spans"]).strip()

                brk = None
                if prev_line is not None:
                    py0, py1 = prev_line[1], prev_line[3]
                    y_overlap = min(ly1, py1) - max(ly0, py0)
                    if y_overlap > SAME_ROW_Y_OVERLAP_TOL:
                        # Aynı görsel satır (PyMuPDF yatay boşluk yüzünden ayrı
                        # "line" nesnesine bölmüş, örn. şıklar A)...E)) — boşluk.
                        brk = "space"
                    else:
                        # Gerçek YENİ satır (dikey örtüşme yok) — kaynak PDF'te
                        # bu her zaman gerçek bir satır sonu demektir (bkz.
                        # COORDINATION.md QA bulguları: satır y-koordinatları
                        # korunmalı). Her zaman <br>.
                        brk = "br"

                first_in_line = True
                for span in line["spans"]:
                    if span["text"] == "":
                        continue
                    for piece in split_span_at_bars(span, thin_bars):
                        if not piece["text"]:
                            continue
                        tok = {
                            "text": piece["text"],
                            "font": piece["font"],
                            "size": piece["size"],
                            "bbox": piece["bbox"],
                        }
                        if piece["text"] == "√":
                            rb = root_bar_for.get(span_key(piece))
                            if rb:
                                tok["root_bar"] = rb
                        if first_in_line and brk and spans_out:
                            tok["_break_before"] = brk
                        first_in_line = False
                        spans_out.append(tok)
                prev_line = (lx0, ly0, lx1, ly1)
        return spans_out

    def process_blocks_together(blocks_list):
        tokens = []
        current_text_spans = []

        def flush():
            nonlocal current_text_spans
            if current_text_spans:
                tokens.extend(process_spans(current_text_spans))
                current_text_spans = []

        # image-block'ları ayır, aralarındaki text-block gruplarını birlikte işle
        run = []
        for b in blocks_list:
            if b.get("type") == "image":
                if run:
                    current_text_spans.extend(build_spans_with_breaks(run))
                    run = []
                flush()
                tokens.append(b)
            else:
                run.append(b)
        if run:
            current_text_spans.extend(build_spans_with_breaks(run))
        flush()
        return tokens

    return process_blocks_together


def parse_question_options_from_tokens(tokens):
    opt_start = -1
    for idx, t in enumerate(tokens):
        if "text" in t and ("A)" in t["text"] or t["text"].strip().startswith("A)")):
            opt_start = idx
            break
    if opt_start == -1:
        return tokens_to_html(tokens), ""
    question_part = tokens[:opt_start]
    options_part = tokens[opt_start:]
    q_html = tokens_to_html(question_part)
    opts_html = tokens_to_html(options_part)
    return q_html, f'<div class="opts">{opts_html}</div>'


# ---------------------------------------------------------------------------
# Ana çıkarım
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Extract structure and content from v2 PDF.")
    parser.add_argument("--pdf", default="/home/mesuto/Documents/PROJELER/test_hazirlik/1.tema_egemen_sarikci_v2.pdf")
    parser.add_argument("--out", default="/home/mesuto/Documents/PROJELER/test_hazirlik/temalar/01-tema")
    parser.add_argument("--first-page", type=int, default=None, help="1-indexli, test için tek/az sayfa")
    parser.add_argument("--last-page", type=int, default=None)
    parser.add_argument("--tema", default="01", help="Tema numarası (örn: 01, 02)")
    parser.add_argument("--profil", default="metin_yayinlari", help="Kullanılacak yayınevi profili json adı veya yolu")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)
    assets_dir = os.path.join(args.out, "assets")
    os.makedirs(assets_dir, exist_ok=True)

    doc = fitz.open(args.pdf)
    print(f"Extracting PDF: {args.pdf} ({len(doc)} pages)")

    page_range = range(len(doc))
    if args.first_page is not None:
        fp = max(1, args.first_page) - 1
        lp = (args.last_page or args.first_page)
        page_range = range(fp, min(len(doc), lp))

    blocks_db = []
    manifest_akis = []
    current_main_header = None

    q_count = t_count = k_count = a_count = g_count = p_count = 0
    total_roots = 0
    extraction_warnings = []
    ocr_stats = {}  # F9 — img-block -> question OCR sınıflandırma sayaçları

    # F12 — resim tabanlı ("tam sayfa") sayfa modu sayaçları
    tam_sayfa_count = 0
    tam_sayfa_silinen_toplam = 0
    tam_sayfa_tesseract_uyarisi = False

    # Varsayılan profil (Metin Yayınları)
    profile = {
        "known_sections": [
            "ISINMA HAREKETLERİ", "GÜNLÜK HAYAT UYGULAMALARI", "ÖSYM SORULARINA HAZIRLIK",
            "ÖSYM KURGULARSA", "PİST ALANI", "KLASİKLEŞMİŞ UYGULAMALAR", "ARALIKLAR",
            "SAYI ARALIKLARININ GÖSTERİMİ"
        ],
        "theory_box_color": {
            "r_range": [0.9, 0.95],
            "g_range": [0.95, 0.98],
            "b_range": [0.97, 0.99]
        },
        # Kaynak belgede görüldüğü HER yerde silinecek metinler (banner/başlık
        # kalıntıları). Çıktının header'ı zaten logo taşır; bu yazılar içerik değildir.
        "yasakli_metinler": ["EGEMEN SARIKCI"],
        # F12 (2026-07-10) — resim tabanlı (taranmış) sayfa davranışı:
        # "tam_sayfa" (varsayılan) = sayfa TEK görüntü bloğu olarak korunur;
        # "parcala" = eski davranış (bölge bölge kırpıp akışa dağıtma).
        "taranmis_sayfa_modu": "tam_sayfa",
        # Bir sayfanın "resim tabanlı" sayılması için eşikler (bkz. COORDINATION.md F12).
        "tam_sayfa_metin_esigi": 60,
        "tam_sayfa_alan_orani": 0.70,
    }

    # Profil yükleme
    if args.profil:
        profile_path = args.profil
        if not os.path.exists(profile_path):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            candidate = os.path.join(script_dir, "profiller", args.profil)
            if not candidate.endswith(".json"):
                candidate += ".json"
            if os.path.exists(candidate):
                profile_path = candidate
            else:
                candidate_root = os.path.join(os.path.dirname(script_dir), "sistem", "profiller", args.profil)
                if not candidate_root.endswith(".json"):
                    candidate_root += ".json"
                if os.path.exists(candidate_root):
                    profile_path = candidate_root

        if os.path.exists(profile_path):
            try:
                with open(profile_path, "r", encoding="utf-8") as f:
                    loaded_profile = json.load(f)
                profile.update(loaded_profile)
                print(f"Loaded profile: {profile_path}")
            except Exception as e:
                print(f"Warning: Failed to parse profile file '{profile_path}': {e}. Using default.")
        else:
            print(f"Warning: Profile '{args.profil}' not found. Using default Metin Yayınları profile.")

    known_sections = profile.get("known_sections", [])
    banned_removed_total = 0
    banned_texts = profile.get("yasakli_metinler", [])
    taranmis_sayfa_modu = profile.get("taranmis_sayfa_modu", "tam_sayfa")
    tam_sayfa_metin_esigi = profile.get("tam_sayfa_metin_esigi", 60)
    tam_sayfa_alan_orani = profile.get("tam_sayfa_alan_orani", 0.70)

    for pnum in page_range:
        page = doc[pnum]
        page_height = page.rect.height
        print(f"Processing page {pnum+1}/{len(doc)}...", end="\r", flush=True)

        text_dict = page.get_text("rawdict")
        _enrich_rawdict_text(text_dict)
        text_dict["blocks"] = split_mixed_blocks(text_dict["blocks"])
        banned_removed_total += filter_banned_lines(
            text_dict, profile.get("yasakli_metinler", [])
        )
        drawings = page.get_drawings()

        page_spans = []
        for block in text_dict["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        page_spans.append(span)

        thin_bars = collect_thin_bars(drawings)
        root_bar_for, used_bar_idx = match_root_bars(page_spans, thin_bars)

        # NOT: root-eşleşmesinde "kullanılmış" barlar burada BİLEREK hariç
        # TUTULMUYOR. Kök İÇİNDE bir kesir varsa (örn. √(16/25)) dış kökün
        # vinculum'u ile kesir çizgisi AYNI çizim olabilir — bu durumda çizgi
        # hem kökün sınırını hem kesrin pay/payda ayracını belirler. Kesir
        # tespiti kendi num+den şartını sağlamadıkça (aşağıda) zaten hiçbir
        # zaman yanlış bir kesir üretmez, bu yüzden paylaşım güvenli.
        fraction_bars = []
        for bi, (x0, y0, x1, y1) in enumerate(thin_bars):
            if x1 - x0 > 180.0:
                continue
            fraction_bars.append((x0, y0, x1, y1))

        theory_boxes = collect_theory_boxes(drawings, profile=profile)

        excluded_bar_keys = set(rect_key(b) for b in thin_bars)
        figure_regions = collect_figure_regions(drawings, theory_boxes, excluded_bar_keys, text_dict["blocks"])

        # --- F12 (2026-07-10): resim tabanlı sayfa sınıflandırma + tam-sayfa modu ---
        # Bir sayfa "resim tabanlı" sayılır ⇔ metin katmanı eşik altı (boşluk hariç
        # karakter sayımı) VEYA tek bir görsel/çizim bölgesi sayfa alanının
        # tam_sayfa_alan_orani'ndan fazlasını kaplıyor. Eşik ve mod profilden
        # okunur (bkz. yukarıdaki profile sözlüğü/known_sections'ın hemen altı).
        page_area = page.rect.width * page.rect.height
        raw_text_len = len(re.sub(r"\s+", "", page.get_text("text")))
        raw_image_bboxes = []
        for img in page.get_image_info(xrefs=True):
            ix0, iy0, ix1, iy1 = img["bbox"]
            if iy0 < 70 and ix0 < 100:
                continue  # header logosu (extract_page_images ile aynı filtre)
            raw_image_bboxes.append(img["bbox"])
        max_region_ratio = 0.0
        if page_area > 0:
            for rb in raw_image_bboxes + figure_regions:
                rx0, ry0, rx1, ry1 = rb
                area = max(0.0, rx1 - rx0) * max(0.0, ry1 - ry0)
                max_region_ratio = max(max_region_ratio, area / page_area)

        is_image_page = (raw_text_len < tam_sayfa_metin_esigi) or (max_region_ratio > tam_sayfa_alan_orani)

        if is_image_page and taranmis_sayfa_modu == "tam_sayfa":
            tam_sayfa_count += 1
            rel_path, silinen, tesseract_eksik = render_full_page_tam_sayfa(
                page, pnum, assets_dir, banned_texts
            )
            tam_sayfa_silinen_toplam += silinen
            if tesseract_eksik:
                tam_sayfa_tesseract_uyarisi = True
            block_id = f"t{args.tema}-g{len(blocks_db)+1:04d}"
            html = (
                f'<section class="img-block tam-sayfa" id="{block_id}" data-kaynak-sayfa="{pnum+1}">\n'
                f'  <img src="{rel_path}" alt="Sayfa {pnum+1} (taranmış)">\n</section>'
            )
            blocks_db.append((block_id, html))
            g_count += 1
            manifest_akis.append({"sayfa": pnum + 1, "bloklar": [block_id]})
            continue  # bu sayfa için başka blok ÜRETİLMEZ (metin/görsel çıkarımı atlanır)

        # Shrink figure regions to exclude non-suppressed text blocks
        shrunken_figure_regions = []
        for rect in figure_regions:
            non_suppressed_bboxes = []
            for b in text_dict["blocks"]:
                if "lines" not in b or is_footer_block(b, page_height):
                    continue
                bbox = b["bbox"]
                ov = overlap_ratio(bbox, rect)
                if 0.0 < ov <= 0.55:
                    non_suppressed_bboxes.append(bbox)
            
            shrunken_rect = shrink_rect_to_exclude(rect, non_suppressed_bboxes)
            sw, sh = shrunken_rect[2] - shrunken_rect[0], shrunken_rect[3] - shrunken_rect[1]
            if sw > 10 and sh > 5:
                shrunken_figure_regions.append(shrunken_rect)
            else:
                shrunken_figure_regions.append(rect)
        figure_regions = shrunken_figure_regions

        # 1. Raster görüntüler + vektör-şekil kırpmaları
        page_images = extract_page_images(doc, pnum, page, assets_dir)
        figure_crops = extract_figure_crops(page, pnum, figure_regions, assets_dir, start_idx=0)
        
        # De-duplicate: if a page_image overlaps with any figure_region, filter it out
        unique_page_images = []
        for img in page_images:
            if any(overlap_ratio(img["bbox"], fig_rect) > 0.4 for fig_rect in figure_regions):
                continue
            unique_page_images.append(img)
        page_images = unique_page_images
        
        all_images = page_images + figure_crops
        g_count += len(all_images)

        # 2. Footer (sayfa altı v2 numarası) süzme
        def keep_block(b):
            if "lines" not in b:
                return True
            return not is_footer_block(b, page_height)

        # 3. Sayfayı band/sütun sırasına diz (mimari korunuyor — bkz. dosya başlığı)
        full_width_blocks, column_blocks = [], []
        for b in text_dict["blocks"]:
            if "lines" not in b or not keep_block(b):
                continue
            x0, y0, x1, y1 = b["bbox"]
            if x0 < 250 and x1 > 350:
                full_width_blocks.append(b)
            else:
                column_blocks.append(b)
        full_width_blocks.sort(key=lambda x: x["bbox"][1])

        bands = []
        last_y = 0.0
        for fwb in full_width_blocks:
            fy0 = fwb["bbox"][1]
            band_blocks = [b for b in column_blocks if last_y <= b["bbox"][1] < fy0]
            bands.append({"type": "columns", "blocks": band_blocks})
            bands.append({"type": "full-width", "block": fwb})
            last_y = fwb["bbox"][3]
        band_blocks = [b for b in column_blocks if b["bbox"][1] >= last_y]
        bands.append({"type": "columns", "blocks": band_blocks})

        ordered_blocks = []
        for band in bands:
            if band["type"] == "full-width":
                ordered_blocks.append(band["block"])
            else:
                left_col = [b for b in band["blocks"] if b["bbox"][0] < 290]
                right_col = [b for b in band["blocks"] if b["bbox"][0] >= 290]
                left_col = sort_blocks_reading_order(left_col)
                right_col = sort_blocks_reading_order(right_col)
                ordered_blocks.extend(left_col)
                ordered_blocks.extend(right_col)

        # 4. Görüntü bölgeleri içinde KALAN metin bloklarını bastır (çift baskı önleme)
        suppressed_ids = set()
        for b in ordered_blocks:
            for img in all_images:
                if overlap_ratio(b["bbox"], img["bbox"]) > 0.55:
                    suppressed_ids.add(id(b))
                    break
        ordered_blocks = [b for b in ordered_blocks if id(b) not in suppressed_ids]

        # 5. Görüntüleri akışa (sütun/konum bazlı) yerleştir
        final_blocks = list(ordered_blocks)
        for img in all_images:
            ix0, iy0, ix1, iy1 = img["bbox"]
            inserted = False
            for idx, b in enumerate(final_blocks):
                if b.get("type") == "image":
                    continue
                bx0, by0, bx1, by1 = b["bbox"]
                if (ix0 < 290 and bx0 < 290) or (ix0 >= 290 and bx0 >= 290):
                    if iy0 < by0:
                        final_blocks.insert(idx, img)
                        inserted = True
                        break
            if not inserted:
                final_blocks.append(img)

        process_spans = make_span_grouper(fraction_bars, root_bar_for)
        process_blocks_together = make_block_grouper(process_spans, root_bar_for, thin_bars)

        page_manifest_blocks = []
        current_block_idx = 0
        while current_block_idx < len(final_blocks):
            block = final_blocks[current_block_idx]

            if block.get("type") == "image":
                g_count_local_id = block.get("img_idx")
                block_id = f"t{args.tema}-g{len(blocks_db)+1:04d}"
                # F9 — OCR ile bağımsız img-block'un aslında bir soru olup olmadığı
                # denetlenir (id g-serisinden devam eder, s-serisi sayaçlarına
                # karışmaz — SISTEM.md id dondurma kuralı + COORDINATION.md F9).
                if ocr_detect_question_number(page, block["bbox"], ocr_stats):
                    html = (f'<section class="question" id="{block_id}" data-kaynak-sayfa="{pnum+1}">\n'
                            f'  <img src="{block["path"]}" />\n'
                            f'  <div class="solve-space"></div>\n</section>')
                else:
                    html = (f'<section class="img-block" id="{block_id}" data-kaynak-sayfa="{pnum+1}">\n'
                            f'  <img src="{block["path"]}" />\n</section>')
                blocks_db.append((block_id, html))
                page_manifest_blocks.append(block_id)
                current_block_idx += 1
                continue

            x0, y0, x1, y1 = block["bbox"]
            col_x_range = (0, 290) if x0 < 290 else (290, 9999)
            full_text = block_full_text(block)
            text_str = full_text.strip()

            is_header = any(ks in turkish_upper(text_str) for ks in known_sections)
            is_ans_key = classify_answer_key(full_text, block_spans_flat(block))

            if is_header:
                text_upper = turkish_upper(text_str)
                matched = sorted(
                    {ks for ks in known_sections if ks in text_upper},
                    key=lambda ks: text_upper.find(ks),
                )
                
                # Check for duplicate running headers
                is_duplicate = False
                if len(matched) == 1 and matched[0] == current_main_header:
                    is_duplicate = True
                
                if is_duplicate:
                    current_block_idx += 1
                    continue
                
                # Update current_main_header
                if len(matched) == 1:
                    current_main_header = matched[0]

                # Kaynak PDF bazen BİRDEN FAZLA bölüm başlığını (örn.
                # tekrarlayan "ISINMA HAREKETLERİ" bölüm adı + "☑ Klasikleşmiş
                # Uygulamalar" çalışma takip etiketi) TEK bir PDF metin
                # bloğunda birleştiriyor. Bunu TEK (uzun, sarmalanan) .kur-tag
                # olarak basmak Chrome'un print/sütun bölümleme motorunda bu
                # kutunun sütun/sayfa sınırında YANLIŞLIKLA İKİ KEZ
                # boyanmasına yol açıyordu.
                pieces = []
                used_upto = 0
                for ks in matched:
                    pos = text_upper.find(ks, used_upto)
                    if pos == -1:
                        continue
                    pieces.append(text_str[pos:pos + len(ks)])
                    used_upto = pos + len(ks)
                if not pieces:
                    pieces = [text_str]
                for piece_text in pieces:
                    k_count += 1
                    block_id = f"t{args.tema}-k{k_count:03d}"
                    html = f'<section class="kur-tag" id="{block_id}" data-kaynak-sayfa="{pnum+1}">\n  {piece_text}\n</section>'
                    blocks_db.append((block_id, html))
                    page_manifest_blocks.append(block_id)
                current_block_idx += 1

                if current_block_idx < len(final_blocks):
                    next_b = final_blocks[current_block_idx]
                    if next_b.get("type") != "image":
                        next_text = block_full_text(next_b).strip()
                        if len(next_text) < 100 and not get_qnum(next_text)[0]:
                            sub_tokens = process_blocks_together([next_b])
                            sub_html = tokens_to_html(sub_tokens)
                            k_count += 1
                            sub_id = f"t{args.tema}-k{k_count:03d}"
                            blocks_db.append((sub_id, f'<div class="section-sub" id="{sub_id}" data-kaynak-sayfa="{pnum+1}">{sub_html}</div>'))
                            page_manifest_blocks.append(sub_id)
                            current_block_idx += 1
                continue

            if is_ans_key:
                a_count += 1
                block_id = f"t{args.tema}-a{a_count:03d}"
                ans_tokens = process_blocks_together([block])
                ans_html = tokens_to_html(ans_tokens)
                html = f'<section class="answer-key" id="{block_id}" data-kaynak-sayfa="{pnum+1}">\n  {ans_html}\n</section>'
                blocks_db.append((block_id, html))
                page_manifest_blocks.append(block_id)
                current_block_idx += 1
                continue

            in_theory = False
            for tb in theory_boxes:
                tx0, ty0, tx1, ty1 = tb
                if tx0 - 5 <= x0 <= tx1 + 5 and ty0 - 5 <= y0 <= ty1 + 5:
                    in_theory = True
                    # SADECE current_block_idx'ten başlayan ARDIŞIK (contiguous)
                    # eşleşen blokları al — eskiden kalan TÜM listeyi tarayıp
                    # filtreliyordu, bu da uzak/ilgisiz blokların yanlışlıkla
                    # bu kutuya dahil edilmesine ve current_block_idx'in yanlış
                    # miktarda ilerlemesine (içerik atlama/tekrar) yol açıyordu.
                    tb_blocks = []
                    k = current_block_idx
                    while k < len(final_blocks):
                        tb_b = final_blocks[k]
                        if tb_b.get("type") == "image":
                            break
                        bbx0, bby0, bbx1, bby1 = tb_b["bbox"]
                        if not (tx0 - 5 <= bbx0 <= tx1 + 5 and ty0 - 5 <= bby0 <= ty1 + 5):
                            break
                        tb_blocks.append(tb_b)
                        k += 1
                    if not tb_blocks:
                        tb_blocks = [block]
                        k = current_block_idx + 1
                    theory_tokens = process_blocks_together(tb_blocks)
                    t_count += 1
                    block_id = f"t{args.tema}-t{t_count:03d}"
                    theory_html = tokens_to_html(theory_tokens)
                    html = f'<section class="theory-box" id="{block_id}" data-kaynak-sayfa="{pnum+1}">\n  {theory_html}\n</section>'
                    blocks_db.append((block_id, html))
                    page_manifest_blocks.append(block_id)
                    current_block_idx = k
                    break
            if in_theory:
                continue

            qnum, _qtext = get_qnum(text_str)
            if qnum is not None:
                q_count += 1
                block_id = f"t{args.tema}-s{q_count:03d}"
                question_blocks = [block]
                j = current_block_idx + 1
                while j < len(final_blocks):
                    next_b = final_blocks[j]
                    if next_b.get("type") == "image":
                        ix0, iy0, ix1, iy1 = next_b["bbox"]
                        if col_x_range[0] <= ix0 < col_x_range[1]:
                            question_blocks.append(next_b)
                            j += 1
                            continue
                        else:
                            break
                    next_x0, next_y0, next_x1, next_y1 = next_b["bbox"]
                    if not (col_x_range[0] <= next_x0 < col_x_range[1]):
                        break
                    next_full = block_full_text(next_b).strip()
                    next_qnum, _ = get_qnum(next_full)
                    next_is_header = any(ks in turkish_upper(next_full) for ks in known_sections)
                    next_is_ans = classify_answer_key(next_full, block_spans_flat(next_b))
                    if next_qnum is not None or next_is_header or next_is_ans:
                        break
                    question_blocks.append(next_b)
                    j += 1

                question_tokens = process_blocks_together(question_blocks)
                total_roots += sum(1 for t in question_tokens if t.get("text") == "√")
                q_html, opts_html = parse_question_options_from_tokens(question_tokens)

                # çok maddeli (a/b/c...) sorularda daha fazla çözüm boşluğu
                multi_part = bool(re.search(r"\b[a-h]\)\s", full_text)) or \
                             sum(block_full_text(bb).count(")") for bb in question_blocks) > 6
                solve_class = "solve-space solve-space-lg" if multi_part else "solve-space"

                html = f'<section class="question" id="{block_id}" data-kaynak-sayfa="{pnum+1}">\n'
                html += f'  {q_html}\n'
                if opts_html:
                    html += f'  {opts_html}\n'
                html += f'  <div class="{solve_class}"></div>\n'
                html += f'</section>'
                blocks_db.append((block_id, html))
                page_manifest_blocks.append(block_id)
                current_block_idx = j
                continue

            # --- Fallback: ardışık sınıflandırılamayan blokları TEK .para'da birleştir ---
            run_blocks = [block]
            j = current_block_idx + 1
            while j < len(final_blocks):
                nb = final_blocks[j]
                if nb.get("type") == "image":
                    nx0, ny0, nx1, ny1 = nb["bbox"]
                    if col_x_range[0] <= nx0 < col_x_range[1]:
                        run_blocks.append(nb)
                        j += 1
                        continue
                    else:
                        break
                nx0, ny0, nx1, ny1 = nb["bbox"]
                if not (col_x_range[0] <= nx0 < col_x_range[1]):
                    break
                n_full = block_full_text(nb).strip()
                n_qnum, _ = get_qnum(n_full)
                n_is_header = any(ks in turkish_upper(n_full) for ks in known_sections)
                n_is_ans = classify_answer_key(n_full, block_spans_flat(nb))
                n_in_theory = any(
                    tb[0] - 5 <= nx0 <= tb[2] + 5 and tb[1] - 5 <= ny0 <= tb[3] + 5 for tb in theory_boxes
                )
                if n_qnum is not None or n_is_header or n_is_ans or n_in_theory:
                    break
                run_blocks.append(nb)
                j += 1

            fallback_tokens = process_blocks_together(run_blocks)
            fallback_html = tokens_to_html(fallback_tokens)
            if fallback_html.strip():
                p_count += 1
                block_id = f"t{args.tema}-p{p_count:03d}"
                extraction_warnings.append(f"Sayfa {pnum+1}: Sınıflandırılamayan metin bloğu fallback paragrafa (para) düştü.")
                html = f'<section class="para" id="{block_id}" data-kaynak-sayfa="{pnum+1}">\n  {fallback_html}\n</section>'
                blocks_db.append((block_id, html))
                page_manifest_blocks.append(block_id)
            current_block_idx = j

        if page_manifest_blocks:
            manifest_akis.append({"sayfa": pnum + 1, "bloklar": page_manifest_blocks})

    # -----------------------------------------------------------------
    # Çıktıları yaz
    # -----------------------------------------------------------------
    sorular_path = os.path.join(args.out, "sorular.html")
    with open(sorular_path, "w", encoding="utf-8") as f:
        for block_id, html in blocks_db:
            f.write(html + "\n\n")

    manifest_data = {
        "tema": args.tema, 
        "baslik": f"{int(args.tema)}. TEMA" if args.tema.isdigit() else f"{args.tema}. TEMA", 
        "surum": 1,
        "font": "Comic Sans MS Embedded",
        "akis": manifest_akis,
    }
    manifest_path = os.path.join(args.out, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2, ensure_ascii=False)

    html_out_path = os.path.join(args.out, f"{int(args.tema) if args.tema.isdigit() else args.tema}tema.html")
    html_content = f"""<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="utf-8">
  <title>{manifest_data['baslik']} — Egemen Sarıkcı</title>
  <link rel="stylesheet" href="../../sistem/flow.css">
</head>
<body>
  <div class="page-flow">
"""
    blocks_map = dict(blocks_db)
    for page_entry in manifest_akis:
        p_num = page_entry["sayfa"]
        html_content += f'    <div class="page-content" data-sayfa="{p_num}">\n'
        for b_id in page_entry["bloklar"]:
            if b_id in blocks_map:
                html_content += "      " + blocks_map[b_id].replace("\n", "\n      ") + "\n"
        html_content += '    </div>\n'
    html_content += "  </div>\n</body>\n</html>\n"
    with open(html_out_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"\nExtraction completed!")
    print(f"  Questions: {q_count}  Theory boxes: {t_count}  Kur-tags: {k_count}")
    print(f"  Answer keys: {a_count}  Images: {g_count}  Para(fallback): {p_count}")
    print(f"  Root symbols converted: {total_roots}")
    print(f"  Tam sayfa (resim tabanlı) mod: {taranmis_sayfa_modu} — {tam_sayfa_count} sayfa, {tam_sayfa_silinen_toplam} bölge silindi")
    if tam_sayfa_tesseract_uyarisi:
        print("  UYARI: tesseract yok, tam-sayfa görüntülerde yasaklı metin taraması yapılamadı")
    print(f"Saved files:\n  {sorular_path}\n  {manifest_path}\n  {html_out_path}")

    # Write extract_report.txt
    report_path = os.path.join(args.out, "extract_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("========================================================================\n")
        f.write("EXTRACTION REPORT\n")
        f.write("========================================================================\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
        f.write(f"PDF Input: {args.pdf}\n")
        f.write(f"Output Directory: {args.out}\n")
        f.write(f"Tema No: {args.tema}\n")
        f.write(f"Profile: {args.profil}\n")
        f.write(f"Pages Processed: {len(page_range)}\n")
        f.write(f"Total Pages in PDF: {len(doc)}\n")
        f.write(f"Yasaklı metin silinen satır sayısı (yasakli_metinler): {banned_removed_total}\n")
        f.write("------------------------------------------------------------------------\n")
        f.write("TAM SAYFA MODU (F12 — resim tabanlı sayfalar):\n")
        f.write(f"  Mod: {taranmis_sayfa_modu}\n")
        f.write(f"  Tam sayfa modu: {tam_sayfa_count} sayfa; yasaklı metin silinen bölge: {tam_sayfa_silinen_toplam}\n")
        if tam_sayfa_tesseract_uyarisi:
            f.write("  UYARI: tesseract yok, tam-sayfa görüntülerde yasaklı metin taraması yapılamadı\n")
        f.write("------------------------------------------------------------------------\n")
        f.write("STATISTICS:\n")
        f.write(f"  Questions Found: {q_count}\n")
        f.write(f"  Theory Boxes Found: {t_count}\n")
        f.write(f"  Kur-tags Found: {k_count}\n")
        f.write(f"  Answer Keys Found: {a_count}\n")
        f.write(f"  Images Found (Raster + Figure crops): {g_count}\n")
        f.write(f"  Fallback Paragraphs: {p_count}\n")
        f.write(f"  Root Mathematical Symbols Converted: {total_roots}\n")
        f.write("------------------------------------------------------------------------\n")
        f.write("OCR (F9 — img-block -> question sınıflandırma):\n")
        if not TESSERACT_BIN:
            f.write("  OCR atlandı: tesseract bulunamadı (davranış OCR-öncesi ile aynı).\n")
        else:
            f.write(f"  Denendi: {ocr_stats.get('denendi', 0)}\n")
            f.write(f"  Soruya çevrildi: {ocr_stats.get('donusturuldu', 0)}\n")
            f.write(f"  Eşleşmedi (img-block kaldı): {ocr_stats.get('eslesmedi', 0)}\n")
            atlanan = sum(v for k, v in ocr_stats.items() if k.startswith("atlandi_"))
            if atlanan:
                f.write(f"  Atlandı (hata/zaman aşımı, img-block kaldı): {atlanan}\n")
        f.write("------------------------------------------------------------------------\n")

        if extraction_warnings:
            f.write("WARNINGS & ERRORS:\n")
            for warning in extraction_warnings:
                f.write(f"  - [WARNING] {warning}\n")
        else:
            f.write("No warnings or errors reported during extraction.\n")
        f.write("========================================================================\n")
    print(f"Report saved to: {report_path}")

    log_dir = os.path.join(args.out, "log")
    os.makedirs(log_dir, exist_ok=True)
    runs_log_path = os.path.join(log_dir, "runs.jsonl")
    log_entry = {
        "ts": datetime.now().isoformat(),
        "islem": "extract",
        "girdi": args.pdf,
        "cikti": html_out_path,
        "sayfa": len(doc),
        "soru": q_count,
        "kok": total_roots,
        "gorsel": g_count,
        "dogrulama": "ok",
        "sha256": "",
        "ajan": "Antigravity",
    }
    with open(runs_log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    gunluk_path = os.path.join(log_dir, "islem_gunlugu.md")
    with open(gunluk_path, "a", encoding="utf-8") as f:
        f.write(f"\n## {datetime.now().strftime('%Y-%m-%d %H:%M')} (Antigravity — F3 tamamlandı)\n")
        f.write(f"- extract.py çalıştırıldı: {q_count} soru, {g_count} görsel, {total_roots} kök.\n")


if __name__ == "__main__":
    main()
