"""sorular.html / manifest.json ayrıştırma ve düzenleme yardımcıları (SISTEM.md §2)."""
from __future__ import annotations

import json
import os
import re
import shutil

from config import BILINEN_SINIFLAR
from utils import ApiHata

BLOK_PATTERN = re.compile(
    r'<(section|div)\s+class="([^"]+)"\s+id="([^"]+)"\s+data-kaynak-sayfa="([^"]+)"[^>]*>(.*?)</\1>',
    re.DOTALL,
)

# Bölüm bağlamını belirleyen sınıflar (sorular.html'de gerçek bölüm/başlık taşırlar,
# bkz. temalar/01-tema/sorular.html: <section class="kur-tag">ISINMA HAREKETLERİ</section>
# ve <div class="section-sub">Gerçek Sayıların Üslü Gösterimi</div>).
BOLUM_SINIFLARI = {"kur-tag", "section-sub"}


def sorular_html_oku(tema_dir: str) -> str:
    yol = os.path.join(tema_dir, "sorular.html")
    if not os.path.exists(yol):
        raise ApiHata(404, "sorular.html bulunamadı", yol)
    with open(yol, "r", encoding="utf-8") as f:
        return f.read()


def parse_sorular(html_metin: str) -> dict[str, dict]:
    """id -> {tag, sinif, kaynak_sayfa, ic}. Mükerrer id'lerde SONUNCUSU kazanır
    (assemble.py ile aynı davranış, ama burada ayrıca mükerrer_idler listesi de dönülür)."""
    bloklar: dict[str, dict] = {}
    mukerrer: list[str] = []
    for tag, sinif, b_id, sayfa, ic in BLOK_PATTERN.findall(html_metin):
        if b_id in bloklar:
            mukerrer.append(b_id)
        bloklar[b_id] = {"tag": tag, "sinif": sinif, "kaynak_sayfa": sayfa, "ic": ic}
    return bloklar, mukerrer


def ozet_metin(ic_html: str, uzunluk: int = 80) -> str:
    metin = re.sub(r"<[^>]+>", " ", ic_html)
    metin = re.sub(r"\s+", " ", metin).strip()
    return metin[:uzunluk]


def manifest_oku(tema_dir: str) -> dict:
    yol = os.path.join(tema_dir, "manifest.json")
    if not os.path.exists(yol):
        raise ApiHata(404, "manifest.json bulunamadı", yol)
    with open(yol, "r", encoding="utf-8") as f:
        return json.load(f)


def manifest_yaz(tema_dir: str, manifest: dict) -> None:
    yol = os.path.join(tema_dir, "manifest.json")
    if os.path.exists(yol):
        shutil.copy2(yol, yol + ".bak")
    with open(yol, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)


def akis_id_sirasi(manifest: dict) -> list[str]:
    sira: list[str] = []
    for grup in manifest.get("akis", []):
        sira.extend(grup.get("bloklar", []))
    return sira


def bloklar_listesi(tema_dir: str) -> list[dict]:
    """API sözleşmesi: {id, sinif, kaynak_sayfa, ozet(ilk 80 kr), bolum} listesi,
    manifest akış sırasıyla."""
    manifest = manifest_oku(tema_dir)
    html_metin = sorular_html_oku(tema_dir)
    bloklar, _ = parse_sorular(html_metin)

    sonuc = []
    bolum = None
    for b_id in akis_id_sirasi(manifest):
        b = bloklar.get(b_id)
        if b is None:
            sonuc.append(
                {
                    "id": b_id,
                    "sinif": None,
                    "kaynak_sayfa": None,
                    "ozet": "(sorular.html içinde bulunamadı)",
                    "bolum": bolum,
                }
            )
            continue
        if b["sinif"] in BOLUM_SINIFLARI:
            bolum = ozet_metin(b["ic"], 120)
        sonuc.append(
            {
                "id": b_id,
                "sinif": b["sinif"],
                "kaynak_sayfa": b["kaynak_sayfa"],
                "ozet": ozet_metin(b["ic"], 80),
                "bolum": bolum,
            }
        )
    return sonuc


def manifest_patch(tema_dir: str, yeni_akis: list[dict]) -> dict:
    """PATCH /manifest — sıralama/silme, doğrulamalı. Bilinmeyen id varsa reddet,
    yazmadan önce .bak alır (SISTEM.md id kalıcılığı + hata toleransı)."""
    manifest = manifest_oku(tema_dir)
    html_metin = sorular_html_oku(tema_dir)
    bloklar, _ = parse_sorular(html_metin)

    yeni_idler = []
    for grup in yeni_akis:
        if not isinstance(grup, dict) or "bloklar" not in grup:
            raise ApiHata(400, "geçersiz akış girdisi", str(grup))
        yeni_idler.extend(grup.get("bloklar", []))

    bilinmeyen = sorted({i for i in yeni_idler if i not in bloklar})
    if bilinmeyen:
        raise ApiHata(400, "bilinmeyen blok id(leri)", ", ".join(bilinmeyen))

    tekrar_eden = sorted({i for i in yeni_idler if yeni_idler.count(i) > 1})
    if tekrar_eden:
        raise ApiHata(400, "akışta tekrar eden blok id(leri)", ", ".join(tekrar_eden))

    manifest["akis"] = yeni_akis
    manifest_yaz(tema_dir, manifest)
    return manifest


def blok_ekle(tema_dir: str, tema_no: str, sinif: str, html_govde: str, konum: dict | None) -> dict:
    """POST /bloklar — yeni id BACKEND'de sıradaki tNN-eNNN'den üretilir,
    hem sorular.html'e hem manifest.json'a eklenir."""
    from utils import sonraki_ek_id

    if sinif not in BILINEN_SINIFLAR:
        raise ApiHata(
            400,
            "bilinmeyen sınıf",
            f"'{sinif}' desteklenmiyor, izin verilenler: {sorted(BILINEN_SINIFLAR)}",
        )

    sorular_yol = os.path.join(tema_dir, "sorular.html")
    html_metin = sorular_html_oku(tema_dir)
    bloklar, _ = parse_sorular(html_metin)
    manifest = manifest_oku(tema_dir)

    yeni_id = sonraki_ek_id(sorular_yol, tema_no)

    konum = konum or {}
    referans_id = konum.get("sonra_id")
    kaynak_sayfa = "ek"
    if referans_id and referans_id in bloklar:
        kaynak_sayfa = bloklar[referans_id]["kaynak_sayfa"]

    etiket = "div" if sinif in ("section-sub",) else "section"
    yeni_blok_html = (
        f'\n<{etiket} class="{sinif}" id="{yeni_id}" data-kaynak-sayfa="{kaynak_sayfa}">\n'
        f"  {html_govde}\n"
        f"</{etiket}>\n"
    )
    with open(sorular_yol, "a", encoding="utf-8") as f:
        f.write(yeni_blok_html)

    akis = manifest.get("akis", [])
    eklendi = False
    if referans_id:
        for grup in akis:
            bl = grup.get("bloklar", [])
            if referans_id in bl:
                bl.insert(bl.index(referans_id) + 1, yeni_id)
                eklendi = True
                break
        if not eklendi:
            raise ApiHata(400, "referans blok akışta bulunamadı", referans_id)
    else:
        if akis:
            akis[-1].setdefault("bloklar", []).append(yeni_id)
        else:
            akis.append({"sayfa": 1, "bloklar": [yeni_id]})
        eklendi = True

    manifest["akis"] = akis
    manifest_yaz(tema_dir, manifest)
    return {"id": yeni_id, "sinif": sinif, "kaynak_sayfa": kaynak_sayfa}


def sayim(tema_dir: str) -> dict:
    """Aktif (manifest'teki) blokların kaba sayımı — runs.jsonl bilgi alanları için.
    Kesin doğrulama qa/dogrula.py'nin işidir; bu yalnızca özet bilgi amaçlıdır."""
    manifest = manifest_oku(tema_dir)
    html_metin = sorular_html_oku(tema_dir)
    bloklar, _ = parse_sorular(html_metin)
    soru = kok = gorsel = 0
    for b_id in akis_id_sirasi(manifest):
        b = bloklar.get(b_id)
        if not b:
            continue
        if b["sinif"] == "question":
            soru += 1
        kok += len(re.findall(r'class="rt"', b["ic"]))
        gorsel += len(re.findall(r"<img\b", b["ic"]))
    return {"soru": soru, "kok": kok, "gorsel": gorsel}
