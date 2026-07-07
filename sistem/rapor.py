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


def kaynak_soru_tahmini(satirlar: list[str]) -> tuple[int, list[int]]:
    """Satır başında '12.'/'12)' + devamında metin arar; aynı satırda >=2 tane
    'N.HARF' deseni varsa (cevap anahtarı satırı, örn. '1.B 2.A 3.C') o satırı
    SAYMAZ. Salt sayfa numarası satırları ('53' tek başına) zaten regex'e
    (noktalama + devam metni şartı) takılmadığı için otomatik elenir."""
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


# ------------------------------------------------------------------ ana hesap


def rapor_hesapla(kaynak_pdf: str, tema_dir: str, cikti_pdf: str | None) -> dict:
    kaynak_satirlar = kaynak_metni_satirlar(kaynak_pdf)
    kaynak_tahmini, kaynak_numaralari = kaynak_soru_tahmini(kaynak_satirlar)
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
        "yontem_notu": (
            "Kaynak soru sayısı bir TAHMİNDİR (satır başı '12.' / '12)' deseni, cevap anahtarı "
            "satırları hariç); aktarım kontrolü her çıktı sorusunun ilk ~40 normalize karakterini "
            "kaynak metninde arar, kısa/salt-görsel sorular karşılaştırma dışı tutulur — kaba ama "
            "dürüst bir yöntemdir, kesin/otomatik doğrulama için qa/dogrula.py'ye bakın."
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
