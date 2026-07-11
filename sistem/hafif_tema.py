#!/usr/bin/env python3
"""
hafif_tema.py — "Hafif Tema" (light theme) motoru.

Mevcut AĞIR dönüşüm hattından (extract.py -> sorular.html/manifest.json ->
assemble.py -> print.mjs; metni HTML'e çıkarıp Comic Sans ile yeniden dizen)
TAMAMEN BAĞIMSIZ, ayrı bir motor. Kaynak PDF'i DOĞRUDAN PyMuPDF (fitz) ile
düzenler — sayfa bütünlüğü ve TÜM metin/font/görsel/tablo/şekil orijinal
vektör/metin/görüntü olarak KALIR, hiçbir şey HTML'e çevrilip yeniden
dizilmez.

Yapılan tek şeyler:
  1. Üstbilgideki renkli şerit + "N.KUR" rozetini kaldırır.
  2. "Metin Yayınları" filigranını kaldırır.
  3. Orijinal sayfa numarasını kaldırır, kendi sıralı sayfa numaramızı ekler.
  4. Kendi logomuzu (sistem/logo_es.jpg) her sayfanın üst ortasına ekler.
  5. Metin içeriğine, fontlara, diğer görsel/tablo/şekillere DOKUNMAZ.

Teknik not (bu script'i yazmadan önce doğrulandı, tekrar araştırmaya gerek
yok): "Metin Yayınları" filigranı ne gerçek metin katmanında, ne gömülü bir
görselde, ne bir annotation'da, ne bir Form XObject/OCG/soft-mask'te —
filigranın harfleri page.get_drawings() ile görülebilen, YÜKSEK ÖĞE SAYILI
("items" listesinde çok sayıda bezier eğrisi — harf glifleri) BİLEŞİK bir
vektör path'i olarak sayfaya gömülü, dolgu rengi çok soluk (neredeyse beyaz
ama tam beyaz DEĞİL — örn. (0.998,0.941,0.914) somon / (0.938,0.941,0.943)
gri). Basit dikdörtgen arkaplanlar (theory-box, şerit vb.) tek bir "re"
öğesinden oluşur (n_items=1) — filigran harfleri ise onlarca/yüzlerce öğe
içerir; bu yüzden ayırt edici kıstas RENK + ÖĞE SAYISI ikilisidir, salt renk
DEĞİL (aksi halde theory-box'un soluk mavi-beyaz tonlarıyla karışabilirdi).
Ayrıca "Metin"/"Yayınları" kelimelerinin METİN olarak arandığı durumlarda
(örn. bu script'in geliştirilmesi sırasında 6.tema.pdf sayfa 10 ve 12'de
görülen "Metin Yayınları Parkur kitabı", "Metin Okullarına" gibi eşleşmeler)
bunlar GERÇEK SORU İÇERİĞİ (marka adı geçen örnek problem metni) olduğu
tespit edildi — filigranla KARIŞTIRILMAMALI, metin arama YÖNTEMİ olarak
kullanılmadı. Filigran SADECE yukarıdaki vektör-path yöntemiyle bulunur.

Kullanım:
    python3 sistem/hafif_tema.py <kaynak.pdf> <cikti.pdf> [--profil metin_yayinlari]
"""

import argparse
import json
import os
import re
import sys

import fitz  # PyMuPDF

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_LOGO = os.path.join(SCRIPT_DIR, "logo_es.jpg")

# ------------------------------------------------------------------
# Varsayılan profil (yeni "hafif_" alanları — extract.py'nin kullandığı
# alanları BOZMADAN, sadece bu motora özgü yeni alanlar eklenmiştir).
# ------------------------------------------------------------------
DEFAULT_PROFILE = {
    # F12 (extract.py) ile AYNI eşikler — resim tabanlı (taranmış) sayfa tespiti.
    "hafif_tam_sayfa_metin_esigi": 60,
    "hafif_tam_sayfa_alan_orani": 0.70,

    # Üst şerit + KUR rozeti: y0 < bu değerden küçük olan VE genişliği
    # bu değerden büyük olan dolgulu (fill) vektör şekiller hedeftir.
    # Küçük dekoratif ikon (örn. "ISINMA HAREKETLERİ" yanındaki mavi ikon)
    # genişlik eşiğinin altında kaldığı için DOKUNULMAZ.
    "hafif_ust_serit_yukseklik_pt": 100,
    "hafif_ust_serit_min_genislik_pt": 30,

    # Orijinal sayfa numarası dairesi (gri dolgu + içinde beyaz rakam).
    "hafif_sayfa_no_daire_renk": {"r": 0.427, "g": 0.433, "b": 0.442, "tol": 0.06},
    "hafif_sayfa_no_bolge_yukseklik_pt": 100,

    # Filigran ("Metin Yayınları") — bkz. modül docstring'i.
    "hafif_filigran_min_items": 20,
    "hafif_filigran_renk_min": 0.80,
    "hafif_filigran_renk_max": 0.999,
    "hafif_filigran_bilinen_renkler": [
        [0.998, 0.941, 0.914],
        [0.938, 0.941, 0.943]
    ],
    "hafif_filigran_renk_tolerans": 0.02,

    # Kendi logo/sayfa no yerleşimimiz (print.mjs header'ıyla tutarlı:
    # logo üst ortada, sayfa no alt ortada).
    "hafif_logo_yukseklik_pt": 32,
    "hafif_logo_ust_bosluk_pt": 8,
    "hafif_sayfa_no_alt_bosluk_pt": 24,
    "hafif_sayfa_no_fontsize": 9,
    "hafif_sayfa_no_renk": [0.4, 0.4, 0.4],
}


def load_profile(args_profil):
    """extract.py'deki profil okuma tarzıyla tutarlı: adı verilen json
    sistem/profiller/ altında aranır, yoksa doğrudan yol denenir. Bulunamazsa
    varsayılan (Metin Yayınları) profille devam edilir. Sadece hafif_* alanları
    eklenir/okunur — mevcut alanlar (yayinevi, known_sections, ...) dokunulmadan
    olduğu gibi taşınır (rapor ve gelecekteki genişletmeler için)."""
    profile = dict(DEFAULT_PROFILE)
    if not args_profil:
        return profile

    profile_path = args_profil
    if not os.path.exists(profile_path):
        candidate = os.path.join(SCRIPT_DIR, "profiller", args_profil)
        if os.path.exists(candidate):
            profile_path = candidate
        elif os.path.exists(candidate + ".json"):
            profile_path = candidate + ".json"

    if os.path.exists(profile_path):
        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            profile.update(loaded)
            print(f"Profil yuklendi: {profile_path}")
        except (json.JSONDecodeError, OSError) as e:
            print(f"UYARI: profil '{profile_path}' okunamadi ({e}), varsayilan kullaniliyor.")
    else:
        print(f"UYARI: profil '{args_profil}' bulunamadi, varsayilan (Metin Yayinlari) kullaniliyor.")
    return profile


def color_close(fill, target, tol):
    if fill is None or target is None:
        return False
    if len(fill) != len(target):
        return False
    return all(abs(a - b) <= tol for a, b in zip(fill, target))


def is_image_based_page(page, profile):
    """extract.py F12 ile aynı mantık: metin katmanı eşik altındaysa VEYA tek
    bir görsel sayfa alaninin buyuk bir oranini kapliyorsa sayfa "resim
    tabanli/taranmis" sayilir."""
    page_area = page.rect.width * page.rect.height
    raw_text_len = len(re.sub(r"\s+", "", page.get_text("text")))
    max_ratio = 0.0
    if page_area > 0:
        for img in page.get_image_info(xrefs=True):
            ix0, iy0, ix1, iy1 = img["bbox"]
            if iy0 < 70 and ix0 < 100:
                continue  # header logosu vb. küçük dekoratif — atla
            area = max(0.0, ix1 - ix0) * max(0.0, iy1 - iy0)
            max_ratio = max(max_ratio, area / page_area)
    esik = profile.get("hafif_tam_sayfa_metin_esigi", 60)
    oran = profile.get("hafif_tam_sayfa_alan_orani", 0.70)
    return (raw_text_len < esik) or (max_ratio > oran), raw_text_len, max_ratio


def find_banner_ribbon_rects(page, profile):
    """Üst şerit (tam genişlik açık renkli bant) + rozet/kurdele şeklini
    (aynı ton, daha koyu) bulur. Sınır: y0 üst-şerit bölgesinde VE genişlik
    eşiğin üzerinde olan HER dolgulu vektör şekil — böylece hem şerit hem
    rozet (iki parçalı olabilir: üst çentik + gövde) yakalanır, küçük ikon
    (dar) ve bölüm başlığı/alt başlık METNİ (drawing değil, text) etkilenmez."""
    ust_y = profile.get("hafif_ust_serit_yukseklik_pt", 100)
    min_w = profile.get("hafif_ust_serit_min_genislik_pt", 30)
    rects = []
    for d in page.get_drawings():
        fill = d.get("fill")
        rect = d.get("rect")
        if fill is None or rect is None or rect.is_empty:
            continue
        if rect.y0 < ust_y and (rect.x1 - rect.x0) >= min_w:
            rects.append(fitz.Rect(rect))
    return rects


def find_page_number_rect(page, profile):
    """Orijinal sayfa numarası dairesini (gri dolgu, sayfa alt bölgesi) bulur."""
    renk = profile.get("hafif_sayfa_no_daire_renk", {})
    target = (renk.get("r", 0.427), renk.get("g", 0.433), renk.get("b", 0.442))
    tol = renk.get("tol", 0.06)
    bolge_y = profile.get("hafif_sayfa_no_bolge_yukseklik_pt", 100)
    page_h = page.rect.height
    for d in page.get_drawings():
        fill = d.get("fill")
        rect = d.get("rect")
        if fill is None or rect is None or rect.is_empty:
            continue
        if rect.y0 > page_h - bolge_y and color_close(fill, target, tol):
            return fitz.Rect(rect)
    return None


def find_filigran_rects(page, profile):
    """Filigran ("Metin Yayınları") harflerini oluşturan bileşik vektör
    path'lerini bulur — bkz. modül docstring'indeki teknik not. İki ayrı
    kıstas OR'lanır:
      1) BİLİNEN renk (tam filigran rengiyle sıkı tolerans eşleşmesi) —
         öğe sayısı şartı YOK. Gerekçe: filigran sayfa üzerindeki konuma
         göre bazen bir sütun/kutu tarafından kırpılıyor ve daha AZ öğeli
         (örn. 13) bir parça olarak kalıyor (6.tema.pdf sayfa 5'te
         yakalandı — 20 öğe eşiği bu parçayı kaçırıp filigran yarım
         silinmişti, bkz. islem_gunlugu.md). Bu renkler o kadar spesifik
         (CMYK türevi ondalıklar) ki başka bir meşru içerikle çakışma
         riski ihmal edilebilir düzeyde.
      2) GENEL soluk-ama-tam-beyaz-değil renk aralığı — bu daha gevşek/
         genel kıstas olduğundan YANLIŞ POZİTİF riskini sınırlamak için
         öğe sayısı (bezier eğri sayısı — harf glifi göstergesi) eşiği
         KORUNUR (basit dikdörtgen arkaplanlar n_items=1'dir)."""
    min_items = profile.get("hafif_filigran_min_items", 20)
    renk_min = profile.get("hafif_filigran_renk_min", 0.80)
    renk_max = profile.get("hafif_filigran_renk_max", 0.999)
    bilinen = [tuple(c) for c in profile.get("hafif_filigran_bilinen_renkler", [])]
    tol = profile.get("hafif_filigran_renk_tolerans", 0.02)

    rects = []
    for d in page.get_drawings():
        fill = d.get("fill")
        rect = d.get("rect")
        items = d.get("items", [])
        if fill is None or rect is None or rect.is_empty:
            continue
        eslesme_bilinen = any(color_close(fill, bc, tol) for bc in bilinen)
        eslesme_genel = len(items) >= min_items and all(renk_min <= c <= renk_max for c in fill)
        if eslesme_bilinen or eslesme_genel:
            rects.append(fitz.Rect(rect))
    return rects


def redact_rects(page, rects, pad=1.2, remove_text=False):
    """Verilen dikdörtgenleri gerçekten SİLER (add_redact_annot + apply).

    KRİTİK ders (ilk denemede yakalanan hata, bkz. islem_gunlugu.md): bir
    redaksiyon annotasyonuna `fill=(1,1,1)` verilirse, apply_redactions() bu
    beyaz dolguyu rect'in TAMAMINA, text/graphics/images parametrelerinden
    BAĞIMSIZ olarak, HER ZAMAN üstüne boyar — yani text=1 ("ignore/dokunma")
    verilse bile, o bölgeye denk gelen GERÇEK metin görsel olarak beyazın
    ALTINDA kalıp görünmez olur (metin katmanında hâlâ var ama render'da
    görünmez) — 6.tema.pdf sayfa 1'de "2. Aşağıdaki veri gruplarının tepe
    değerlerini bulunuz." sorusu filigranın ikinci parçasıyla bbox olarak
    çakıştığı için tam olarak bu şekilde "kayboldu". Çözüm: banner/rozet/
    filigran gibi gerçek içerikle ÇAKIŞABİLECEK bölgeler için fill=None
    (hiçbir şey boyanmaz, SADECE altındaki vektör grafik kaldırılır — sayfanın
    boyanmamış/şeffaf zemini olağan beyaz kağıtta zaten beyaz görünür); sadece
    çakışma riski doğrulanmış DAR/İZOLE bölgeler (sayfa no dairesi) için
    remove_text=True + fill=(1,1,1) kullanılır (orada gerçek soru metni
    olmadığı ayrıca doğrulandı, güvenli)."""
    if not rects:
        return 0
    fill = (1, 1, 1) if remove_text else None
    for r in rects:
        rr = fitz.Rect(r)
        rr.x0 -= pad
        rr.y0 -= pad
        rr.x1 += pad
        rr.y1 += pad
        page.add_redact_annot(rr, fill=fill, cross_out=False)
    text_mode = 0 if remove_text else 1
    # graphics=2 ("tüm ÇAKIŞAN grafikleri kaldır") kullanılır — graphics=1
    # ("SADECE rect içinde TAM kapsanan grafiği kaldır") büyük/eğrili
    # (bezier) bileşik path'lerde bbox hassasiyeti yüzünden bazen kaçırıyor
    # (ilk denemede ribbon'un ana gövdesi böyle atlanmıştı — küçük çentik
    # parçası kaldırıldı ama büyük gövde kalmıştı, bkz. islem_gunlugu.md).
    page.apply_redactions(images=2, graphics=2, text=text_mode)
    return len(rects)


def add_logo_and_page_number(page, page_no, logo_path, profile):
    """Üst ortaya logo, alt ortaya kendi sıralı sayfa numaramızı ekler."""
    page_w = page.rect.width
    page_h = page.rect.height

    # Logo — üst ortada.
    if logo_path and os.path.exists(logo_path):
        try:
            with fitz.open(logo_path) as limg:
                lw, lh = limg[0].rect.width, limg[0].rect.height
        except Exception:
            from PIL import Image
            with Image.open(logo_path) as im:
                lw, lh = im.size
        h = profile.get("hafif_logo_yukseklik_pt", 32)
        w = h * (lw / lh) if lh else h
        top = profile.get("hafif_logo_ust_bosluk_pt", 8)
        rect = fitz.Rect((page_w - w) / 2, top, (page_w + w) / 2, top + h)
        page.insert_image(rect, filename=logo_path)

    # Sayfa numarası — alt ortada.
    fontsize = profile.get("hafif_sayfa_no_fontsize", 9)
    color = tuple(profile.get("hafif_sayfa_no_renk", [0.4, 0.4, 0.4]))
    text = str(page_no)
    tw = fitz.get_text_length(text, fontname="helv", fontsize=fontsize)
    bottom = profile.get("hafif_sayfa_no_alt_bosluk_pt", 24)
    x = (page_w - tw) / 2
    y = page_h - bottom
    page.insert_text((x, y), text, fontsize=fontsize, fontname="helv", color=color)


def process_text_page(doc, page, pnum, profile, stats):
    banner_rects = find_banner_ribbon_rects(page, profile)
    pagenum_rect = find_page_number_rect(page, profile)
    filigran_rects_ = find_filigran_rects(page, profile)

    # 1. geçiş: banner/rozet + filigran — SADECE grafik kaldırılır, üzerine
    #    binen gerçek metne DOKUNULMAZ (bkz. redact_rects docstring). pad=4
    #    (varsayılan 1.2'den daha bol): bileşik bezier path'lerin (özellikle
    #    filigran harfleri) get_drawings() bbox'ı bazen gerçek boyanan
    #    alandan biraz DAR çıkıyor — 6.tema.pdf sayfa 5'te dar pad ile ince
    #    bir kenar artığı kalmıştı (bkz. islem_gunlugu.md). text=1 (ignore)
    #    kullanıldığı için bol pad güvenli — gerçek metne asla dokunmaz.
    graphic_rects = list(banner_rects) + list(filigran_rects_)
    n1 = redact_rects(page, graphic_rects, pad=4.0, remove_text=False)

    # 2. geçiş: sayfa no dairesi — İÇİNDEKİ orijinal rakam da kasıtlı olarak
    #    silinir (o dar bölgede gerçek soru metni olmadığı doğrulandı).
    n2 = redact_rects(page, [pagenum_rect] if pagenum_rect is not None else [], remove_text=True)

    stats["banner_silinen"] += len(banner_rects)
    stats["sayfa_no_silinen"] += 1 if pagenum_rect is not None else 0
    stats["filigran_silinen"] += len(filigran_rects_)
    stats["toplam_redaksiyon"] += n1 + n2
    return {
        "sayfa": pnum + 1,
        "mod": "vektor",
        "banner": len(banner_rects),
        "sayfa_no": 1 if pagenum_rect is not None else 0,
        "filigran": len(filigran_rects_),
    }


def process_image_page(doc, page, pnum, profile, stats, assets_tmp_dir):
    """Taranmış (tam-sayfa resim) sayfalar için en-iyi-çaba (best-effort)
    yol: sayfa zaten vektör içermediğinden (get_drawings boş döner) aynı
    geometrik bölgeleri ORANTILI olarak piksel düzeyinde beyazla — banner
    (üst ~%6'lık bant), sayfa no dairesi (alt-orta) ve filigran (bilinen
    somon/gri renk imzası, piksel toleransıyla). Bu test setinde (6.tema.pdf,
    15 sayfa) HİÇ taranmış sayfa yok; bu yol dolayısıyla gerçek veriyle
    doğrulanamadı — best-effort olarak işaretlenir, rapora düşer."""
    stats["taranmis_sayfa_sayisi"] += 1
    stats["taranmis_best_effort_uyari"] = True

    pix = page.get_pixmap(dpi=200, alpha=False)
    w, h = pix.width, pix.height
    scale = pix.width / page.rect.width  # px per pt

    def whiteout(x0, y0, x1, y1):
        irect = fitz.IRect(max(0, int(x0)), max(0, int(y0)), min(w, int(x1)), min(h, int(y1)))
        if not irect.is_empty:
            pix.set_rect(irect, (255,) * pix.n)

    # Üst banner: sayfanın tam genişliği, üst ~ (hafif_ust_serit_yukseklik_pt) pt.
    ust_y_pt = profile.get("hafif_ust_serit_yukseklik_pt", 100) * 0.55  # bant asıl ~50-90pt
    whiteout(0, 0, w, ust_y_pt * scale)

    # Sayfa no dairesi: alt-orta, referans şablon oranına göre (x ~ %47-53, y ~ son 100pt).
    bolge_y = profile.get("hafif_sayfa_no_bolge_yukseklik_pt", 100)
    whiteout(w * 0.46, h - bolge_y * scale, w * 0.54, h)

    # Filigran: bilinen renk imzasını (0-255 RGB) piksel bazında ara ve beyazla.
    try:
        import numpy as np
        arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(h, w, pix.n)[:, :, :3]
        bilinen = profile.get("hafif_filigran_bilinen_renkler", [])
        tol = profile.get("hafif_filigran_renk_tolerans", 0.02) * 255 + 12  # piksel/JPEG toleransı daha gevşek
        mask = np.zeros((h, w), dtype=bool)
        for (r, g, b) in bilinen:
            target = np.array([r, g, b]) * 255
            diff = np.abs(arr.astype(np.int16) - target.astype(np.int16))
            mask |= (diff.max(axis=2) <= tol)
        if mask.any():
            arr2 = np.frombuffer(pix.samples, dtype=np.uint8).reshape(h, w, pix.n).copy()
            arr2[mask] = 255
            pix = fitz.Pixmap(pix.colorspace, pix.width, pix.height, arr2.tobytes(), pix.alpha)
            stats["filigran_silinen"] += 1
    except ImportError:
        stats["taranmis_numpy_eksik"] = True

    img_path = os.path.join(assets_tmp_dir, f"p{pnum+1:03d}_hafif.png")
    pix.save(img_path)

    # Sayfadaki eski resmi kaldırıp temizlenmiş rasteri tam sayfa olarak bas.
    page.add_redact_annot(page.rect, fill=(1, 1, 1), cross_out=False)
    page.apply_redactions(images=2, graphics=1, text=0)
    page.insert_image(page.rect, filename=img_path)

    stats["banner_silinen"] += 1
    stats["sayfa_no_silinen"] += 1
    return {"sayfa": pnum + 1, "mod": "tam_sayfa_raster_best_effort"}


def main():
    parser = argparse.ArgumentParser(description="Hafif tema motoru — kaynak PDF'i dogrudan duzenler (extract.py/assemble.py/print.mjs hattindan bagimsiz).")
    parser.add_argument("kaynak", help="Kaynak PDF yolu")
    parser.add_argument("cikti", help="Cikti PDF yolu")
    parser.add_argument("--profil", default="metin_yayinlari", help="sistem/profiller/ altindaki profil json adi veya dogrudan yol")
    parser.add_argument("--logo", default=DEFAULT_LOGO, help="Logo dosyasi (varsayilan: sistem/logo_es.jpg)")
    parser.add_argument("--rapor", default=None, help="Rapor txt yolu (varsayilan: cikti ile ayni klasor, hafif_tema_rapor.txt)")
    args = parser.parse_args()

    if not os.path.exists(args.kaynak):
        print(f"HATA: kaynak bulunamadi: {args.kaynak}")
        sys.exit(1)

    profile = load_profile(args.profil)

    out_dir = os.path.dirname(os.path.abspath(args.cikti)) or "."
    os.makedirs(out_dir, exist_ok=True)
    rapor_path = args.rapor or os.path.join(out_dir, "hafif_tema_rapor.txt")

    doc = fitz.open(args.kaynak)
    print(f"Aciliyor: {args.kaynak} ({len(doc)} sayfa)")

    stats = {
        "banner_silinen": 0,
        "sayfa_no_silinen": 0,
        "filigran_silinen": 0,
        "toplam_redaksiyon": 0,
        "taranmis_sayfa_sayisi": 0,
        "metin_sayfa_sayisi": 0,
    }
    per_page_log = []

    for pnum in range(len(doc)):
        page = doc[pnum]
        img_based, raw_text_len, max_ratio = is_image_based_page(page, profile)
        if img_based:
            info = process_image_page(doc, page, pnum, profile, stats, out_dir)
        else:
            stats["metin_sayfa_sayisi"] += 1
            info = process_text_page(doc, page, pnum, profile, stats)
        per_page_log.append(info)

        # Logo + kendi sayfa numaramız — HER sayfada, redaksiyondan SONRA.
        add_logo_and_page_number(page, pnum + 1, args.logo, profile)
        print(f"Islendi: sayfa {pnum+1}/{len(doc)} ({'taranmis' if img_based else 'metin'})", end="\r", flush=True)

    print()
    doc.save(args.cikti, garbage=4, deflate=True)
    doc.close()
    print(f"Yazildi: {args.cikti}")

    with open(rapor_path, "w", encoding="utf-8") as f:
        f.write("HAFİF TEMA MOTORU — İŞLEM RAPORU\n")
        f.write("=" * 50 + "\n")
        f.write(f"Kaynak: {args.kaynak}\n")
        f.write(f"Cikti: {args.cikti}\n")
        f.write(f"Profil: {args.profil}\n")
        f.write(f"Toplam sayfa: {len(per_page_log)}\n")
        f.write(f"  Metin tabanli sayfa: {stats['metin_sayfa_sayisi']}\n")
        f.write(f"  Taranmis (resim tabanli) sayfa: {stats['taranmis_sayfa_sayisi']}\n")
        if stats["taranmis_sayfa_sayisi"] and stats.get("taranmis_best_effort_uyari"):
            f.write("  UYARI: taranmis sayfa(lar) icin banner/sayfa-no/filigran temizligi\n")
            f.write("  BEST-EFFORT (piksel-orantili) yontemle yapildi — bu test setinde\n")
            f.write("  gercek taranmis sayfa olmadigindan gercek veriyle DOGRULANAMADI.\n")
        f.write(f"Banner/rozet silinen bolge sayisi: {stats['banner_silinen']}\n")
        f.write(f"Sayfa numarasi silinen sayfa sayisi: {stats['sayfa_no_silinen']}\n")
        f.write(f"Filigran silinen bolge sayisi: {stats['filigran_silinen']}\n")
        f.write(f"Yontem: vektor redaksiyon (page.add_redact_annot + apply_redactions)\n")
        f.write("\nSayfa sayfa detay:\n")
        for info in per_page_log:
            f.write(f"  {info}\n")

    print(f"Rapor: {rapor_path}")
    print(f"Ozet: banner={stats['banner_silinen']} sayfa_no={stats['sayfa_no_silinen']} filigran={stats['filigran_silinen']} (metin sayfa={stats['metin_sayfa_sayisi']}, taranmis={stats['taranmis_sayfa_sayisi']})")


if __name__ == "__main__":
    main()
