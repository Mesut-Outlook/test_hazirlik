"""Ortak yollar ve sabitler.

Depo düzeni (bkz. SISTEM.md §1):
    test_hazirlik/
    ├── sistem/            motor (extract.py, assemble.py, print.mjs, flow.css...)
    ├── temalar/NN-ad/     tema başına klasör
    ├── cikti/             üretilen PDF'ler
    ├── qa/                doğrulama araçları
    └── arayuz/
        ├── ayarlar.json   varsayılan giriş/çıkış klasörleri (bu modülün yazdığı)
        ├── backend/       bu FastAPI uygulaması
        └── web/           F2'nin dolduracağı statik ön yüz
"""
from __future__ import annotations

import os

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
ARAYUZ_DIR = os.path.dirname(BACKEND_DIR)
REPO_ROOT = os.path.dirname(ARAYUZ_DIR)

SISTEM_DIR = os.path.join(REPO_ROOT, "sistem")
TEMALAR_DIR = os.path.join(REPO_ROOT, "temalar")
CIKTI_DIR = os.path.join(REPO_ROOT, "cikti")
QA_DIR = os.path.join(REPO_ROOT, "qa")
WEB_DIR = os.path.join(ARAYUZ_DIR, "web")
AYARLAR_PATH = os.path.join(ARAYUZ_DIR, "ayarlar.json")

EXTRACT_PY = os.path.join(SISTEM_DIR, "extract.py")
ASSEMBLE_PY = os.path.join(SISTEM_DIR, "assemble.py")
FLOW_CSS = os.path.join(SISTEM_DIR, "flow.css")
PRINT_MJS = os.path.join(SISTEM_DIR, "print.mjs")
DOGRULA_PY = os.path.join(QA_DIR, "dogrula.py")
RAPOR_PY = os.path.join(SISTEM_DIR, "rapor.py")

# fs/list ve dosya seçimi bu kökle sınırlı (path-traversal koruması, bkz. utils.py)
EV_DIZINI = os.path.realpath(os.path.expanduser("~"))

PORT = 8756

# Bloklar için izin verilen sınıflar (sistem/flow.css sözleşmesi, SISTEM.md §3)
BILINEN_SINIFLAR = {
    "question",
    "theory-box",
    "kur-tag",
    "answer-key",
    "img-block",
    "para",
    "section-sub",
}

os.makedirs(TEMALAR_DIR, exist_ok=True)
os.makedirs(CIKTI_DIR, exist_ok=True)
os.makedirs(WEB_DIR, exist_ok=True)
