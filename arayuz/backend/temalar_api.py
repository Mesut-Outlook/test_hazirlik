"""GET/POST /api/temalar, /bloklar, /manifest, /uret, /istek — SISTEM.md §1-§2-§5-§6'ya uyar:
- Onaylı tema için extract.py bir daha çalıştırılmaz (yalnızca POST /api/temalar ile
  YENİ bir tema oluşturulur; var olan bir temaya extract yeniden koşulmaz).
- Elle blok ekleme tNN-eNNN serisinden id üretir (utils.sonraki_ek_id).
- Her üretim runs.jsonl'e loglanır (ajan: "Arayüz").
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess

from fastapi import APIRouter
from pydantic import BaseModel

import blocks
import pipeline
import tema_meta
from config import CIKTI_DIR, FLOW_CSS, REPO_ROOT, TEMALAR_DIR
from jobs import Job, job_manager
from utils import (
    TR_TZ,
    ApiHata,
    guvenli_ev_yolu,
    islem_gunlugu_yaz,
    runs_jsonl_yaz,
    simdi_iso,
    sonraki_cikti_yolu,
    sonraki_tema_no,
    tema_dir_by_id,
)
from datetime import datetime

router = APIRouter()

DESTEKLENEN_KAYNAK_UZANTILARI = {"pdf", "docx", "doc"}
DESTEKLENEN_MODLAR = {"agir", "hafif"}


def _hafif_mod_engelle(tema_dir: str) -> None:
    """Bloklar/manifest/uret uç noktaları yalnızca AĞIR mod temaları için
    anlamlıdır (extract.py'nin ürettiği blok/soru modeline dayanır). Hafif
    modda bunlar hiç üretilmez — anlaşılır bir 400 ile reddet."""
    meta = tema_meta.oku(tema_dir)
    if meta.get("mod") == "hafif":
        raise ApiHata(
            400,
            "bu tema hafif modda oluşturuldu",
            "Hafif tema modunda blok düzenleme/yeniden üretim yok — PDF tek adımda üretilip son_pdf alanında sunulur.",
        )


def _slugla(ad: str) -> str:
    ad = ad.strip().lower()
    ad = ad.replace("ı", "i").replace("ğ", "g").replace("ü", "u").replace("ş", "s")
    ad = ad.replace("ö", "o").replace("ç", "c")
    ad = re.sub(r"[^a-z0-9]+", "-", ad).strip("-")
    return ad or "tema"


def _tema_guncellenme(tema_dir: str) -> str | None:
    """Tema kartında gösterilen 'son güncelleme' zamanı: manifest/sorular/meta
    dosyalarından en yenisinin mtime'ı (extract, blok düzenleme ve üretim
    hepsi bunlardan en az birine dokunur); hiçbiri yoksa klasörün mtime'ı."""
    en_son = None
    for ad in ("manifest.json", "sorular.html", "tema_meta.json"):
        yol = os.path.join(tema_dir, ad)
        try:
            mt = os.path.getmtime(yol)
        except OSError:
            continue
        if en_son is None or mt > en_son:
            en_son = mt
    if en_son is None:
        try:
            en_son = os.path.getmtime(tema_dir)
        except OSError:
            return None
    return datetime.fromtimestamp(en_son, TR_TZ).isoformat(timespec="seconds")


# ---------------------------------------------------------------- GET /api/temalar
@router.get("/api/temalar")
def get_temalar():
    sonuc = []
    if not os.path.isdir(TEMALAR_DIR):
        return sonuc
    for tema_id in sorted(os.listdir(TEMALAR_DIR)):
        if tema_id.startswith("."):
            continue  # temalar/.cop/ (silinen temaların arşivi, F7) bir tema DEĞİL
        tema_dir = os.path.join(TEMALAR_DIR, tema_id)
        if not os.path.isdir(tema_dir):
            continue
        meta = tema_meta.oku(tema_dir)
        mod = meta.get("mod", "agir")

        if mod == "hafif":
            # Hafif modda manifest.json HİÇ üretilmez (extract.py çalışmaz) —
            # "hazır" olup olmadığı yalnızca son_pdf'in varlığına bakılarak
            # anlaşılır (bkz. COORDINATION.md notu / bu dosyanın üst yorumu).
            son_pdf = meta.get("son_pdf")
            if son_pdf and not os.path.exists(son_pdf):
                son_pdf = None
            sonuc.append(
                {
                    "tema_id": tema_id,
                    "ad": meta.get("ad", tema_id),
                    "durum": "hazır" if son_pdf else "hazırlanıyor",
                    "mod": "hafif",
                    "surum": None,
                    "soru_sayisi": None,
                    "kok_sayisi": None,
                    "gorsel_sayisi": None,
                    "son_pdf": son_pdf,
                    "guncellenme": _tema_guncellenme(tema_dir),
                }
            )
            continue

        manifest_yol = os.path.join(tema_dir, "manifest.json")
        if not os.path.exists(manifest_yol):
            sonuc.append(
                {
                    "tema_id": tema_id,
                    "ad": meta.get("ad", tema_id),
                    "durum": "hazırlanıyor",
                    "mod": "agir",
                    "job_id": meta.get("son_extract_job"),
                    "surum": None,
                    "soru_sayisi": None,
                    "guncellenme": _tema_guncellenme(tema_dir),
                }
            )
            continue
        try:
            manifest = blocks.manifest_oku(tema_dir)
            sayimlar = blocks.sayim(tema_dir)
        except Exception as exc:  # manifest bozuksa da listeleme çökmesin
            sonuc.append(
                {
                    "tema_id": tema_id,
                    "ad": meta.get("ad", tema_id),
                    "durum": "hata",
                    "mod": "agir",
                    "hata": str(exc),
                    "surum": None,
                    "soru_sayisi": None,
                    "guncellenme": _tema_guncellenme(tema_dir),
                }
            )
            continue
        son_pdf = meta.get("son_pdf")
        if son_pdf and not os.path.exists(son_pdf):
            son_pdf = None
        sonuc.append(
            {
                "tema_id": tema_id,
                "ad": meta.get("ad", manifest.get("baslik", tema_id)),
                "durum": "hazır",
                "mod": "agir",
                "surum": manifest.get("surum"),
                "soru_sayisi": sayimlar["soru"],
                "kok_sayisi": sayimlar["kok"],
                "gorsel_sayisi": sayimlar["gorsel"],
                "son_pdf": son_pdf,
                "guncellenme": _tema_guncellenme(tema_dir),
            }
        )
    return sonuc


# --------------------------------------------------------------- POST /api/temalar
class YeniTema(BaseModel):
    kaynak_dosya: str
    ad: str
    cikti_klasoru: str
    mod: str = "agir"  # "agir" (Tam Dönüşüm, varsayılan) | "hafif" (Hafif Tema)


@router.post("/api/temalar")
def post_tema(body: YeniTema):
    if body.mod not in DESTEKLENEN_MODLAR:
        raise ApiHata(400, "geçersiz mod", f"'{body.mod}' — 'agir' veya 'hafif' bekleniyor")

    kaynak_gercek = guvenli_ev_yolu(body.kaynak_dosya, gerekli="file")
    uzanti = kaynak_gercek.rsplit(".", 1)[-1].lower() if "." in kaynak_gercek else ""
    if uzanti not in DESTEKLENEN_KAYNAK_UZANTILARI:
        raise ApiHata(400, "desteklenmeyen dosya türü", f"'{uzanti}' — pdf/docx/doc bekleniyor")

    cikti_klasoru_gercek = os.path.realpath(os.path.expanduser(body.cikti_klasoru))
    if not os.path.isdir(cikti_klasoru_gercek):
        raise ApiHata(404, "çıktı klasörü bulunamadı", cikti_klasoru_gercek)

    tema_no = sonraki_tema_no()
    slug = _slugla(body.ad)
    tema_id = f"{tema_no}-{slug}"
    tema_dir = os.path.join(TEMALAR_DIR, tema_id)
    if os.path.exists(tema_dir):
        raise ApiHata(409, "tema klasörü zaten var", tema_id)

    kaynak_dir = os.path.join(tema_dir, "kaynak")
    os.makedirs(kaynak_dir)
    os.makedirs(os.path.join(tema_dir, "assets"))
    os.makedirs(os.path.join(tema_dir, "log"))

    kopya_yolu = os.path.join(kaynak_dir, os.path.basename(kaynak_gercek))
    shutil.copy2(kaynak_gercek, kopya_yolu)

    tema_meta.yaz(
        tema_dir,
        {
            "tema_id": tema_id,
            "ad": body.ad,
            "kaynak_dosya_orijinal": kaynak_gercek,
            "kaynak_dosya_kopya": kopya_yolu,
            "cikti_klasoru": cikti_klasoru_gercek,
            "olusturuldu": simdi_iso(),
            "mod": body.mod,
        },
    )

    def calistir(job: Job) -> None:
        job.log(f"Tema oluşturuluyor: {tema_id} (mod={body.mod})")
        pdf_yolu = kopya_yolu
        if uzanti in ("docx", "doc"):
            job.log("Word belgesi PDF'e çevriliyor (soffice)...")
            pdf_yolu = pipeline.docx_to_pdf(kopya_yolu, kaynak_dir, job.log)
        tema_meta.yaz(tema_dir, {"kaynak_pdf": pdf_yolu})

        if body.mod == "hafif":
            job.log("hafif_tema.py çalıştırılıyor (tek adım — banner/rozet, filigran, orijinal sayfa no temizliği)...")
            cikti_pdf = sonraki_cikti_yolu(body.ad, 1)
            pipeline.run_hafif_tema(pdf_yolu, cikti_pdf, job.log)

            kopya_yolu_cikti = None
            if cikti_klasoru_gercek and os.path.isdir(cikti_klasoru_gercek):
                kopya_yolu_cikti = os.path.join(cikti_klasoru_gercek, os.path.basename(cikti_pdf))
                if os.path.realpath(cikti_pdf) != os.path.realpath(kopya_yolu_cikti):
                    shutil.copy2(cikti_pdf, kopya_yolu_cikti)
                    job.log(f"Kopyalandı: {kopya_yolu_cikti}")
                else:
                    job.log(f"Çıktı zaten hedef klasörde: {cikti_pdf}")

            sayfa = pipeline.pdf_sayfa_sayisi(cikti_pdf)
            tema_meta.yaz(tema_dir, {"son_pdf": cikti_pdf, "mod": "hafif"})
            runs_jsonl_yaz(
                tema_dir,
                {
                    "islem": "hafif_tema",
                    "girdi": pdf_yolu,
                    "cikti": cikti_pdf,
                    "sayfa": sayfa,
                    "dogrulama": "-",
                    "sha256": "",
                    "ajan": "Arayüz",
                },
            )
            islem_gunlugu_yaz(
                tema_dir,
                "Arayüz - hafif tema oluşturma",
                [
                    f"Kaynak: {kaynak_gercek}",
                    f"hafif_tema.py ile {os.path.basename(cikti_pdf)} üretildi ({sayfa} sayfa).",
                ],
            )
            job.bitir(
                {
                    "tema_id": tema_id,
                    "cikti_pdf": cikti_pdf,
                    "kopya": kopya_yolu_cikti,
                    "mod": "hafif",
                    "dogrulama": {"calisti": False, "not": "Hafif tema modunda ayrı doğrulama çalıştırılmaz"},
                    "rapor_ozet": None,
                }
            )
            return

        job.log("extract.py çalıştırılıyor...")
        pipeline.run_extract(pdf_yolu, tema_dir, tema_no, job.log)

        job.log("rapor.py çalıştırılıyor (F8 — dönüşüm raporu)...")
        rapor_sonuc = pipeline.run_rapor(pdf_yolu, tema_dir, job.log)
        rapor_ozet = rapor_sonuc.get("ozet") if rapor_sonuc.get("calisti") else None

        sayimlar = blocks.sayim(tema_dir)
        sayfa = pipeline.pdf_sayfa_sayisi(pdf_yolu)
        runs_jsonl_yaz(
            tema_dir,
            {
                "islem": "extract",
                "girdi": pdf_yolu,
                "cikti": tema_dir,
                "sayfa": sayfa,
                "soru": sayimlar["soru"],
                "kok": sayimlar["kok"],
                "gorsel": sayimlar["gorsel"],
                "dogrulama": "-",
                "sha256": "",
                "ajan": "Arayüz",
            },
        )
        islem_gunlugu_yaz(
            tema_dir,
            "Arayüz - tema oluşturma",
            [
                f"Kaynak: {kaynak_gercek}",
                f"extract.py ile {sayimlar['soru']} soru, {sayimlar['gorsel']} görsel çıkarıldı.",
            ],
        )
        job.bitir({"tema_id": tema_id, "sayimlar": sayimlar, "rapor_ozet": rapor_ozet})

    job = job_manager.yeni_is("extract", calistir, tema_id=tema_id)
    tema_meta.yaz(tema_dir, {"son_extract_job": job.id})
    return {"tema_id": tema_id, "job_id": job.id}


# ------------------------------------------------------- GET /api/temalar/{id}/bloklar
@router.get("/api/temalar/{tema_id}/bloklar")
def get_bloklar(tema_id: str):
    tema_dir = tema_dir_by_id(tema_id)
    _hafif_mod_engelle(tema_dir)
    return {"tema_id": tema_id, "bloklar": blocks.bloklar_listesi(tema_dir)}


# ------------------------------------------------------- GET /api/temalar/{id}/rapor
@router.get("/api/temalar/{tema_id}/rapor")
def get_rapor(tema_id: str):
    """F8 — en son üretilen dönüşüm raporu: {md, ozet}. Rapor henüz üretilmediyse
    (extract/uret hiç çalışmadıysa veya rapor.py atlandıysa) 404 döner."""
    tema_dir = tema_dir_by_id(tema_id)
    md_yol = os.path.join(tema_dir, "log", "donusum_raporu.md")
    json_yol = os.path.join(tema_dir, "log", "rapor.json")
    if not os.path.exists(md_yol) or not os.path.exists(json_yol):
        raise ApiHata(404, "rapor bulunamadı", "Bu tema için henüz bir dönüşüm raporu üretilmedi.")
    with open(md_yol, "r", encoding="utf-8") as f:
        md = f.read()
    with open(json_yol, "r", encoding="utf-8") as f:
        ozet = json.load(f)
    return {"tema_id": tema_id, "md": md, "ozet": ozet}


# ------------------------------------------------------- PATCH /api/temalar/{id}/manifest
class ManifestPatch(BaseModel):
    akis: list[dict]


@router.patch("/api/temalar/{tema_id}/manifest")
def patch_manifest(tema_id: str, body: ManifestPatch):
    tema_dir = tema_dir_by_id(tema_id)
    _hafif_mod_engelle(tema_dir)
    if tema_id == "01-tema":
        # ID dondurma kuralı yalnızca extract.py yeniden koşumunu yasaklar; sıralama/silme
        # SISTEM.md §2'ye göre serbesttir. Yine de yedek alınır (manifest_patch içinde).
        pass
    manifest = blocks.manifest_patch(tema_dir, body.akis)
    islem_gunlugu_yaz(
        tema_dir,
        "Arayüz - manifest güncelleme",
        ["Akış (sıralama/silme) güncellendi, yedek: manifest.json.bak"],
    )
    return manifest


# ------------------------------------------------------- POST /api/temalar/{id}/bloklar
class YeniBlok(BaseModel):
    sinif: str
    html_govde: str
    konum: dict | None = None


@router.post("/api/temalar/{tema_id}/bloklar")
def post_blok(tema_id: str, body: YeniBlok):
    tema_dir = tema_dir_by_id(tema_id)
    _hafif_mod_engelle(tema_dir)
    tema_no = tema_id.split("-", 1)[0]
    sonuc = blocks.blok_ekle(tema_dir, tema_no, body.sinif, body.html_govde, body.konum)
    islem_gunlugu_yaz(
        tema_dir,
        "Arayüz - blok ekleme",
        [f"Yeni blok eklendi: {sonuc['id']} (sinif={body.sinif})"],
    )
    return sonuc


# ------------------------------------------------------- PATCH /api/temalar/{id}/bloklar/{blok_id}
class BlokSinifPatch(BaseModel):
    sinif: str


@router.patch("/api/temalar/{tema_id}/bloklar/{blok_id}")
def patch_blok_sinif(tema_id: str, blok_id: str, body: BlokSinifPatch):
    """F9 — img-block <-> question dönüşümü. `question`'a çevrilirken solve-space
    eklenir (idempotent); `img-block`'a çevrilirken kaldırılır. id/data-kaynak-sayfa
    değişmez (SISTEM.md §2 id dondurma kuralı)."""
    tema_dir = tema_dir_by_id(tema_id)
    _hafif_mod_engelle(tema_dir)
    solve_space = body.sinif == "question"
    sonuc = blocks.blok_sinif_degistir(tema_dir, blok_id, body.sinif, solve_space)
    islem_gunlugu_yaz(
        tema_dir,
        "Arayüz - blok sınıf değiştirme",
        [f"{blok_id}: sınıf -> {body.sinif} (solve_space={solve_space})"],
    )
    return sonuc


# ------------------------------------------------------- POST /api/temalar/{id}/uret
class UretIstek(BaseModel):
    cikti_adi: str | None = None


@router.post("/api/temalar/{tema_id}/uret")
def post_uret(tema_id: str, body: UretIstek):
    tema_dir = tema_dir_by_id(tema_id)
    _hafif_mod_engelle(tema_dir)
    meta = tema_meta.oku(tema_dir)

    def calistir(job: Job) -> None:
        manifest = blocks.manifest_oku(tema_dir)
        tema_no = manifest.get("tema") or tema_id.split("-", 1)[0]
        surum_yeni = int(manifest.get("surum", 1)) + 1
        manifest["surum"] = surum_yeni
        blocks.manifest_yaz(tema_dir, manifest)
        job.log(f"Sürüm {surum_yeni} olarak işaretlendi.")

        sorular_path = os.path.join(tema_dir, "sorular.html")
        manifest_path = os.path.join(tema_dir, "manifest.json")
        out_html = os.path.join(tema_dir, f"{tema_no}tema.html")
        css_goreli = os.path.relpath(FLOW_CSS, tema_dir)

        job.log("assemble.py çalıştırılıyor...")
        pipeline.run_assemble(manifest_path, sorular_path, css_goreli, out_html, job.log)

        ad = body.cikti_adi or meta.get("ad") or f"tema{tema_no}"
        cikti_pdf = sonraki_cikti_yolu(ad, surum_yeni)
        job.log(f"print.mjs çalıştırılıyor -> {cikti_pdf}")
        pipeline.run_print(out_html, cikti_pdf, job.log)

        kopya_yolu = None
        cikti_klasoru = meta.get("cikti_klasoru")
        if cikti_klasoru and os.path.isdir(cikti_klasoru):
            kopya_yolu = os.path.join(cikti_klasoru, os.path.basename(cikti_pdf))
            if os.path.realpath(cikti_pdf) != os.path.realpath(kopya_yolu):
                shutil.copy2(cikti_pdf, kopya_yolu)
                job.log(f"Kopyalandı: {kopya_yolu}")
            else:
                job.log(f"Çıktı zaten hedef klasörde: {cikti_pdf}")

        kaynak_pdf = meta.get("kaynak_pdf")
        dogrula_sonuc = {"calisti": False, "not": "kaynak PDF bilinmiyor"}
        if kaynak_pdf and os.path.exists(kaynak_pdf):
            job.log("qa/dogrula.py çalıştırılıyor...")
            dogrula_sonuc = pipeline.run_dogrula(kaynak_pdf, cikti_pdf, job.log)

        job.log("rapor.py çalıştırılıyor (F8 — dönüşüm raporu)...")
        rapor_sonuc = pipeline.run_rapor(kaynak_pdf, tema_dir, job.log, cikti_pdf=cikti_pdf)
        rapor_ozet = rapor_sonuc.get("ozet") if rapor_sonuc.get("calisti") else None

        sayimlar = blocks.sayim(tema_dir)
        sayfa = pipeline.pdf_sayfa_sayisi(cikti_pdf)
        dogrulama_str = "ok"
        if dogrula_sonuc.get("calisti") and "cikti" in dogrula_sonuc:
            dogrulama_str = "ok" if "FARK" not in dogrula_sonuc["cikti"] else "UYARI: dogrula.py FARK bildirdi (bkz. sonuc.dogrulama.cikti)"
        elif not dogrula_sonuc.get("calisti"):
            dogrulama_str = f"atlandi: {dogrula_sonuc.get('not', '')}"

        runs_jsonl_yaz(
            tema_dir,
            {
                "islem": "uret",
                "girdi": out_html,
                "cikti": cikti_pdf,
                "sayfa": sayfa,
                "soru": sayimlar["soru"],
                "kok": sayimlar["kok"],
                "gorsel": sayimlar["gorsel"],
                "dogrulama": dogrulama_str,
                "sha256": "",
                "ajan": "Arayüz",
            },
        )
        islem_gunlugu_yaz(
            tema_dir,
            "Arayüz - üretim",
            [
                f"{os.path.basename(cikti_pdf)} üretildi (sürüm {surum_yeni}, {sayfa} sayfa).",
                f"Doğrulama: {dogrulama_str}",
            ],
        )
        # Önizleme oturumlar arası da çalışsın diye son çıktı yolu kalıcı tutulur
        tema_meta.yaz(tema_dir, {"son_pdf": cikti_pdf})
        job.bitir(
            {
                "cikti_pdf": cikti_pdf,
                "kopya": kopya_yolu,
                "surum": surum_yeni,
                "sayimlar": sayimlar,
                "dogrulama": dogrula_sonuc,
                "rapor_ozet": rapor_ozet,
            }
        )

    job = job_manager.yeni_is("uret", calistir, tema_id=tema_id)
    tema_meta.yaz(tema_dir, {"son_uret_job": job.id})
    return {"tema_id": tema_id, "job_id": job.id}


# ------------------------------------------------------- POST /api/temalar/{id}/istek
class TalepIstek(BaseModel):
    metin: str
    otomatik: bool = True  # F6: claude CLI ile otomatik uygulama


COORDINATION_MD = os.path.join(os.path.dirname(TEMALAR_DIR), "COORDINATION.md")
TALEP_BASLIGI = "### FAZ 4 Talep Kuyruğu"


@router.post("/api/temalar/{tema_id}/istek")
def post_istek(tema_id: str, body: TalepIstek):
    tema_dir = tema_dir_by_id(tema_id)
    satir = f"- {simdi_iso()} ({tema_id}): {body.metin.strip()}"

    istekler_yol = os.path.join(tema_dir, "istekler.md")
    with open(istekler_yol, "a", encoding="utf-8") as f:
        f.write(satir + "\n")

    if os.path.exists(COORDINATION_MD):
        with open(COORDINATION_MD, "r", encoding="utf-8") as f:
            icerik = f.read()
        idx = icerik.find(TALEP_BASLIGI)
        if idx != -1:
            satir_sonu = icerik.find("\n", idx)
            bolum_sonu = icerik.find("\n## ", satir_sonu)
            if bolum_sonu == -1:
                bolum_sonu = len(icerik)
            eklenecek_yer = bolum_sonu
            yeni_icerik = icerik[:eklenecek_yer] + satir + "\n" + icerik[eklenecek_yer:]
            with open(COORDINATION_MD, "w", encoding="utf-8") as f:
                f.write(yeni_icerik)

    # ---- F6 (2026-07-10): talebi headless `claude` CLI ile OTOMATİK uygula.
    # Talep her durumda yukarıda kuyruğa yazıldı (kayıt kaybolmaz); CLI yoksa
    # veya kullanıcı otomatiği kapattıysa davranış eskisiyle aynı kalır.
    if not body.otomatik:
        return {"tema_id": tema_id, "kaydedildi": True, "otomatik": False}

    claude_cli = shutil.which("claude")
    if not claude_cli:
        return {
            "tema_id": tema_id,
            "kaydedildi": True,
            "otomatik": False,
            "not": "claude CLI bulunamadı — talep yalnızca kuyruğa yazıldı.",
        }

    metin = body.metin.strip()

    def calistir(job: Job) -> None:
        prompt = (
            "Test Hazırlık deposunda çalışıyorsun. Önce SISTEM.md'yi (kural kitabı) oku.\n"
            f"Kullanıcının web arayüzünden gönderdiği serbest talep '{tema_id}' temasıyla\n"
            f"ilgili; temanın dosyaları temalar/{tema_id}/ altında (sorular.html +\n"
            "manifest.json + assets/), ortak görünüm sistem/flow.css.\n\n"
            f"TALEP: {metin}\n\n"
            "Kurallar:\n"
            "- SISTEM.md §2'ye uy: yeni blok id'si tNN-eNNN ek serisinden; mevcut\n"
            "  id'leri DEĞİŞTİRME; soru çıkarmak = manifest'ten satırını silmek;\n"
            "  sıra değiştirmek = manifest'te taşımak.\n"
            "- SADECE dosya düzenlemesi yap; PDF üretme, komut çalıştırma, git commit\n"
            "  atma — kullanıcı PDF'i arayüzdeki 'Yeniden Üret' düğmesiyle basacak.\n"
            "- Talep belirsizse ya da bu temayla ilgili değilse TAHMİN ETME: neyin\n"
            "  eksik/belirsiz olduğunu yaz ve dosya değiştirmeden bitir.\n"
            "- Bitince yaptığın değişiklikleri 2-3 cümleyle Türkçe özetle.\n"
        )
        job.log(f"$ claude -p … --permission-mode acceptEdits --model sonnet (tema: {tema_id})")
        try:
            sonuc = subprocess.run(
                [claude_cli, "-p", prompt, "--permission-mode", "acceptEdits", "--model", "sonnet"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=1200,
            )
        except subprocess.TimeoutExpired:
            job.basarisiz("claude CLI 20 dakikalık zaman aşımına takıldı — talep elle incelenmeli.")
            return
        cikti = ((sonuc.stdout or "") + (("\n" + sonuc.stderr) if sonuc.stderr else "")).strip()
        for log_satiri in cikti.splitlines():
            job.log(log_satiri)
        runs_jsonl_yaz(
            tema_dir,
            {
                "islem": "istek",
                "girdi": metin,
                "dogrulama": "ok" if sonuc.returncode == 0 else f"HATA rc={sonuc.returncode}",
                "ajan": "claude CLI (sonnet, F6)",
            },
        )
        islem_gunlugu_yaz(
            tema_dir,
            "Arayüz - serbest talep (F6, claude CLI)",
            [
                f"Talep: {metin}",
                "Sonuç: uygulandı" if sonuc.returncode == 0 else f"Sonuç: HATA (rc={sonuc.returncode})",
            ],
        )
        if sonuc.returncode != 0:
            job.basarisiz(f"claude CLI hata kodu {sonuc.returncode} döndürdü (loglara bakın).")
            return
        job.bitir({
            "ozet": cikti[-1500:],
            "not": "Değişiklikleri PDF'e yansıtmak için 'Yeniden Üret'i kullanın.",
        })

    job = job_manager.yeni_is("istek", calistir, tema_id=tema_id)
    return {"tema_id": tema_id, "kaydedildi": True, "otomatik": True, "job_id": job.id}


# ------------------------------------------------------- DELETE /api/temalar/{id}
COP_DIR = os.path.join(TEMALAR_DIR, ".cop")


@router.delete("/api/temalar/{tema_id}")
def delete_tema(tema_id: str):
    """KALICI SİLME YOK: tema klasörünü temalar/.cop/<id>-<zaman>/ altına taşır
    (F7 eki, 2026-07-06). Çalışan/bekleyen bir işi olan tema silinemez (409)."""
    tema_dir = tema_dir_by_id(tema_id)

    if job_manager.tema_mesgul_mu(tema_id):
        raise ApiHata(
            409,
            "tema meşgul",
            "Bu temada devam eden (bekleyen veya çalışan) bir iş var, bitmeden silinemez.",
        )

    os.makedirs(COP_DIR, exist_ok=True)
    damga = datetime.now(TR_TZ).strftime("%Y%m%d-%H%M%S")
    hedef = os.path.join(COP_DIR, f"{tema_id}-{damga}")
    sayac = 1
    while os.path.exists(hedef):
        sayac += 1
        hedef = os.path.join(COP_DIR, f"{tema_id}-{damga}-{sayac}")

    shutil.move(tema_dir, hedef)
    islem_gunlugu_yaz(
        hedef,
        "Arayüz - tema silme",
        [f"Tema çöpe taşındı: {tema_dir} -> {hedef}"],
    )
    return {"tema_id": tema_id, "tasindi": hedef}
