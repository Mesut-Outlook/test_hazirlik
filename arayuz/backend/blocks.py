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


_IMG_TAG_RE = re.compile(r"<img\b[^>]*/?>")
_SOLVE_SPACE_TAG_RE = re.compile(r'<div class="solve-space"></div>')


def _solve_space_var_mi(ic_html: str) -> bool:
    return bool(_SOLVE_SPACE_TAG_RE.search(ic_html))


def _solve_space_ekle(ic_html: str) -> str:
    """İlk `<img .../>` etiketinden sonra solve-space div'i ekler; zaten varsa
    DOKUNMAZ (F9 — ikinci çevirmede çiftlenme olmaz)."""
    if _solve_space_var_mi(ic_html):
        return ic_html
    ekleme = '\n  <div class="solve-space"></div>'
    m = _IMG_TAG_RE.search(ic_html)
    if not m:
        # img yoksa (beklenmez, savunma amaçlı) içeriğin sonuna ekle
        return ic_html.rstrip("\n") + ekleme + "\n"
    idx = m.end()
    return ic_html[:idx] + ekleme + ic_html[idx:]


def _solve_space_kaldir(ic_html: str) -> str:
    """solve-space div'ini (varsa, satır başındaki boşlukla birlikte) kaldırır."""
    return re.sub(r'[ \t]*<div class="solve-space"></div>\n?', "", ic_html)


def blok_sinif_degistir(tema_dir: str, blok_id: str, yeni_sinif: str, solve_space: bool) -> dict:
    """PATCH /bloklar/{id} — F9: img-block <-> question sınıf değişimi.

    id ve data-kaynak-sayfa AYNEN korunur (SISTEM.md §2 id dondurma kuralı ihlal
    edilmez — yalnızca class ve iç içerik değişir, blok kimliği sabit kalır).
    `solve_space=True` iken içerikte `<div class="solve-space"></div>` yoksa
    ilk `<img>` etiketinden hemen sonra eklenir (varsa DOKUNULMAZ — idempotent).
    `solve_space=False` iken solve-space (varsa) kaldırılır.
    """
    if yeni_sinif not in BILINEN_SINIFLAR:
        raise ApiHata(
            400,
            "bilinmeyen sınıf",
            f"'{yeni_sinif}' desteklenmiyor, izin verilenler: {sorted(BILINEN_SINIFLAR)}",
        )

    sorular_yol = os.path.join(tema_dir, "sorular.html")
    html_metin = sorular_html_oku(tema_dir)
    bloklar, mukerrer = parse_sorular(html_metin)

    if blok_id in mukerrer:
        raise ApiHata(
            409,
            "mükerrer id",
            f"'{blok_id}' sorular.html içinde birden fazla kez geçiyor — önce elle düzeltilmeli",
        )
    if blok_id not in bloklar:
        raise ApiHata(404, "blok bulunamadı", blok_id)

    blok = bloklar[blok_id]
    tag = blok["tag"]
    kaynak_sayfa = blok["kaynak_sayfa"]
    ic = blok["ic"]

    yeni_ic = _solve_space_ekle(ic) if solve_space else _solve_space_kaldir(ic)

    desen = re.compile(
        r'<' + re.escape(tag) + r'\s+class="[^"]+"\s+id="' + re.escape(blok_id)
        + r'"\s+data-kaynak-sayfa="[^"]+"[^>]*>.*?</' + re.escape(tag) + r'>',
        re.DOTALL,
    )
    yeni_blok_tam = (
        f'<{tag} class="{yeni_sinif}" id="{blok_id}" data-kaynak-sayfa="{kaynak_sayfa}">'
        f"{yeni_ic}</{tag}>"
    )

    yeni_html, n = desen.subn(lambda _m: yeni_blok_tam, html_metin, count=1)
    if n != 1:
        raise ApiHata(
            500,
            "blok değiştirilemedi",
            f"'{blok_id}' sorular.html içinde beklenen desenle tam olarak bulunamadı (eşleşme={n})",
        )

    if os.path.exists(sorular_yol):
        shutil.copy2(sorular_yol, sorular_yol + ".bak")
    with open(sorular_yol, "w", encoding="utf-8") as f:
        f.write(yeni_html)

    return {"id": blok_id, "sinif": yeni_sinif, "kaynak_sayfa": kaynak_sayfa, "solve_space": solve_space}


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
