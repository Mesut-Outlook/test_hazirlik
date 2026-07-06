"""Boru hattı çağrıları TEK bu modülde toplanır (COORDINATION.md FAZ 4 notu):
AGY paralelde F3'te extract.py'ye --tema/--profil CLI parametreleri ekliyor;
CLI değiştiğinde yalnızca buradaki fonksiyonlar güncellenecek, çağıran kod
(temalar_api.py) değişmeyecek.
"""
from __future__ import annotations

import os
import shutil
import subprocess

from config import ASSEMBLE_PY, DOGRULA_PY, EXTRACT_PY, FLOW_CSS, PRINT_MJS, REPO_ROOT

PY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "venv", "bin", "python3")
if not os.path.exists(PY):
    PY = shutil.which("python3") or "python3"


class KomutHatasi(RuntimeError):
    def __init__(self, komut: list[str], returncode: int, cikti: str):
        super().__init__(f"Komut basarisiz ({returncode}): {' '.join(komut)}\n{cikti}")
        self.komut = komut
        self.returncode = returncode
        self.cikti = cikti


def _calistir(komut: list[str], log: callable, cwd: str = REPO_ROOT, izin_verilen_donus: tuple[int, ...] = (0,)) -> str:
    log(f"$ {' '.join(komut)}")
    sonuc = subprocess.run(komut, cwd=cwd, capture_output=True, text=True)
    cikti = (sonuc.stdout or "") + (sonuc.stderr or "")
    for satir in cikti.splitlines():
        log(satir)
    if sonuc.returncode not in izin_verilen_donus:
        raise KomutHatasi(komut, sonuc.returncode, cikti)
    return cikti


def docx_to_pdf(kaynak_dosya: str, hedef_dir: str, log) -> str:
    """soffice --headless --convert-to pdf ile docx/doc -> pdf. soffice yoksa
    anlaşılır hatayla düşer (task 3. madde)."""
    soffice = shutil.which("soffice")
    if not soffice:
        raise RuntimeError(
            "LibreOffice (soffice) bulunamadı — .docx/.doc kaynaklardan PDF üretilemiyor. "
            "Kurulum: sudo apt install libreoffice (veya dağıtımınıza uygun paket)."
        )
    _calistir([soffice, "--headless", "--convert-to", "pdf", "--outdir", hedef_dir, kaynak_dosya], log)
    taban = os.path.splitext(os.path.basename(kaynak_dosya))[0]
    beklenen = os.path.join(hedef_dir, f"{taban}.pdf")
    if not os.path.exists(beklenen):
        raise RuntimeError(f"soffice PDF üretti sanılıyor ama bulunamadı: {beklenen}")
    return beklenen


def run_extract(pdf_path: str, tema_dir: str, tema_no: str, log, profil: str = "metin_yayinlari") -> None:
    """sistem/extract.py çağrısı. --tema ve --profil parametreleri ile genelleştirildi."""
    komut = [PY, EXTRACT_PY, "--pdf", pdf_path, "--out", tema_dir, "--tema", tema_no, "--profil", profil]
    _calistir(komut, log)


def run_assemble(manifest_path: str, sorular_path: str, css_goreli: str, out_html: str, log) -> None:
    komut = [PY, ASSEMBLE_PY, manifest_path, sorular_path, css_goreli, out_html]
    _calistir(komut, log)


def run_print(html_path: str, pdf_path: str, log) -> None:
    node = shutil.which("node") or "node"
    komut = [node, PRINT_MJS, html_path, pdf_path]
    _calistir(komut, log)


def pdf_sayfa_sayisi(pdf_path: str) -> int | None:
    pdfinfo = shutil.which("pdfinfo")
    if not pdfinfo or not os.path.exists(pdf_path):
        return None
    sonuc = subprocess.run([pdfinfo, pdf_path], capture_output=True, text=True)
    for satir in sonuc.stdout.splitlines():
        if satir.startswith("Pages:"):
            try:
                return int(satir.split(":", 1)[1].strip())
            except ValueError:
                return None
    return None


def run_dogrula(kaynak_pdf: str, cikti_pdf: str, log) -> dict:
    """qa/dogrula.py — ifade sayımı doğrulaması (SISTEM.md §6). Bu betiğin
    TARGET_V3 hedef sayıları ve mükerrer-görsel kontrolü 01-tema'ya göre
    kalibre edilmiştir; başka temalarda çıktı bilgi amaçlıdır (FARK/UYARI
    beklenir, bu bir arayüz hatası değildir)."""
    if not os.path.exists(DOGRULA_PY):
        return {"calisti": False, "not": "qa/dogrula.py bulunamadı, atlandı"}
    komut = [PY, DOGRULA_PY, kaynak_pdf, cikti_pdf]
    cikti = _calistir(komut, log, izin_verilen_donus=(0, 1))
    return {"calisti": True, "cikti": cikti}
