"""GET/PUT /api/ayarlar — varsayılan giriş/çıkış klasörleri (arayuz/ayarlar.json)."""
from __future__ import annotations

import json
import os

from fastapi import APIRouter
from pydantic import BaseModel

from config import AYARLAR_PATH, CIKTI_DIR, EV_DIZINI
from utils import ApiHata, guvenli_ev_yolu

VARSAYILAN = {
    "giris_klasoru": EV_DIZINI,
    "cikti_klasoru": CIKTI_DIR,
}


def oku() -> dict:
    if not os.path.exists(AYARLAR_PATH):
        return dict(VARSAYILAN)
    try:
        with open(AYARLAR_PATH, "r", encoding="utf-8") as f:
            veri = json.load(f)
    except (json.JSONDecodeError, OSError):
        return dict(VARSAYILAN)
    return {**VARSAYILAN, **veri}


def yaz(giris_klasoru: str | None, cikti_klasoru: str | None) -> dict:
    mevcut = oku()
    if giris_klasoru is not None:
        mevcut["giris_klasoru"] = guvenli_ev_yolu(giris_klasoru, gerekli="dir")
    if cikti_klasoru is not None:
        # çıktı klasörü ev dizini altında olmak zorunda değil (harici disk vb.)
        # ama var olmalı.
        yol = os.path.realpath(os.path.expanduser(cikti_klasoru))
        if not os.path.isdir(yol):
            raise ApiHata(404, "klasör bulunamadı", yol)
        mevcut["cikti_klasoru"] = yol
    os.makedirs(os.path.dirname(AYARLAR_PATH), exist_ok=True)
    with open(AYARLAR_PATH, "w", encoding="utf-8") as f:
        json.dump(mevcut, f, ensure_ascii=False, indent=2)
    return mevcut


router = APIRouter()


class AyarlarGuncelle(BaseModel):
    giris_klasoru: str | None = None
    cikti_klasoru: str | None = None


@router.get("/api/ayarlar")
def get_ayarlar():
    return oku()


@router.put("/api/ayarlar")
def put_ayarlar(body: AyarlarGuncelle):
    return yaz(body.giris_klasoru, body.cikti_klasoru)
