"""GET/POST /api/temalar, /bloklar, /manifest, /uret, /istek — SISTEM.md §1-§2-§5-§6'ya uyar:
- Onaylı tema için extract.py bir daha çalıştırılmaz (yalnızca POST /api/temalar ile
  YENİ bir tema oluşturulur; var olan bir temaya extract yeniden koşulmaz).
- Elle blok ekleme tNN-eNNN serisinden id üretir (utils.sonraki_ek_id).
- Her üretim runs.jsonl'e loglanır (ajan: "Arayüz").
"""
from __future__ import annotations

import os
import re
import shutil

from fastapi import APIRouter
from pydantic import BaseModel

import blocks
import pipeline
import tema_meta
from config import CIKTI_DIR, FLOW_CSS, TEMALAR_DIR
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


def _slugla(ad: str) -> str:
    ad = ad.strip().lower()
    ad = ad.replace("ı", "i").replace("ğ", "g").replace("ü", "u").replace("ş", "s")
    ad = ad.replace("ö", "o").replace("ç", "c")
    ad = re.sub(r"[^a-z0-9]+", "-", ad).strip("-")
    return ad or "tema"


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
        manifest_yol = os.path.join(tema_dir, "manifest.json")
        if not os.path.exists(manifest_yol):
            sonuc.append(
                {
                    "tema_id": tema_id,
                    "ad": meta.get("ad", tema_id),
                    "durum": "hazırlanıyor",
                    "job_id": meta.get("son_extract_job"),
                    "surum": None,
                    "soru_sayisi": None,
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
                    "hata": str(exc),
                    "surum": None,
                    "soru_sayisi": None,
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
                "surum": manifest.get("surum"),
                "soru_sayisi": sayimlar["soru"],
                "kok_sayisi": sayimlar["kok"],
                "gorsel_sayisi": sayimlar["gorsel"],
                "son_pdf": son_pdf,
            }
        )
    return sonuc


# --------------------------------------------------------------- POST /api/temalar
class YeniTema(BaseModel):
    kaynak_dosya: str
    ad: str
    cikti_klasoru: str


@router.post("/api/temalar")
def post_tema(body: YeniTema):
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
        },
    )

    def calistir(job: Job) -> None:
        job.log(f"Tema oluşturuluyor: {tema_id}")
        pdf_yolu = kopya_yolu
        if uzanti in ("docx", "doc"):
            job.log("Word belgesi PDF'e çevriliyor (soffice)...")
            pdf_yolu = pipeline.docx_to_pdf(kopya_yolu, kaynak_dir, job.log)
            tema_meta.yaz(tema_dir, {"kaynak_pdf": pdf_yolu})
        else:
            tema_meta.yaz(tema_dir, {"kaynak_pdf": pdf_yolu})

        job.log("extract.py çalıştırılıyor...")
        pipeline.run_extract(pdf_yolu, tema_dir, tema_no, job.log)

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
        job.bitir({"tema_id": tema_id, "sayimlar": sayimlar})

    job = job_manager.yeni_is("extract", calistir, tema_id=tema_id)
    tema_meta.yaz(tema_dir, {"son_extract_job": job.id})
    return {"tema_id": tema_id, "job_id": job.id}


# ------------------------------------------------------- GET /api/temalar/{id}/bloklar
@router.get("/api/temalar/{tema_id}/bloklar")
def get_bloklar(tema_id: str):
    tema_dir = tema_dir_by_id(tema_id)
    return {"tema_id": tema_id, "bloklar": blocks.bloklar_listesi(tema_dir)}


# ------------------------------------------------------- PATCH /api/temalar/{id}/manifest
class ManifestPatch(BaseModel):
    akis: list[dict]


@router.patch("/api/temalar/{tema_id}/manifest")
def patch_manifest(tema_id: str, body: ManifestPatch):
    tema_dir = tema_dir_by_id(tema_id)
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
    tema_no = tema_id.split("-", 1)[0]
    sonuc = blocks.blok_ekle(tema_dir, tema_no, body.sinif, body.html_govde, body.konum)
    islem_gunlugu_yaz(
        tema_dir,
        "Arayüz - blok ekleme",
        [f"Yeni blok eklendi: {sonuc['id']} (sinif={body.sinif})"],
    )
    return sonuc


# ------------------------------------------------------- POST /api/temalar/{id}/uret
class UretIstek(BaseModel):
    cikti_adi: str | None = None


@router.post("/api/temalar/{tema_id}/uret")
def post_uret(tema_id: str, body: UretIstek):
    tema_dir = tema_dir_by_id(tema_id)
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
            }
        )

    job = job_manager.yeni_is("uret", calistir, tema_id=tema_id)
    tema_meta.yaz(tema_dir, {"son_uret_job": job.id})
    return {"tema_id": tema_id, "job_id": job.id}


# ------------------------------------------------------- POST /api/temalar/{id}/istek
class TalepIstek(BaseModel):
    metin: str


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

    return {"tema_id": tema_id, "kaydedildi": True}


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
