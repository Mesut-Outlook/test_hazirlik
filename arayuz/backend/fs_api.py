"""GET /api/fs/list?path=&sadece=pdf,docx|dir — yalnızca kullanıcının ev dizini
altında gezinme (path-traversal ve symlink kaçışı korumalı, bkz. utils.guvenli_ev_yolu)."""
from __future__ import annotations

import os

from fastapi import APIRouter, Query

from config import EV_DIZINI
from utils import guvenli_ev_yolu

router = APIRouter()


@router.get("/api/fs/list")
def fs_list(path: str = Query(default=""), sadece: str = Query(default="")):
    gercek = guvenli_ev_yolu(path or EV_DIZINI, gerekli="dir")

    sadece_uzantilar: set[str] | None = None
    sadece_dir = False
    if sadece:
        parcalar = [p.strip().lower() for p in sadece.split(",") if p.strip()]
        if "dir" in parcalar:
            sadece_dir = True
        sadece_uzantilar = {p for p in parcalar if p != "dir"} or None

    girisler = []
    try:
        with os.scandir(gercek) as it:
            adaylar = list(it)
    except PermissionError:
        adaylar = []

    for giris in sorted(adaylar, key=lambda e: (not e.is_dir(follow_symlinks=True), e.name.lower())):
        ad = giris.name
        if ad.startswith("."):
            continue
        try:
            dizin_mi = giris.is_dir(follow_symlinks=True)
        except OSError:
            continue
        if dizin_mi:
            girisler.append({"ad": ad, "tur": "dir", "yol": os.path.join(gercek, ad)})
        else:
            if sadece_dir:
                continue
            if sadece_uzantilar is not None:
                uzanti = ad.rsplit(".", 1)[-1].lower() if "." in ad else ""
                if uzanti not in sadece_uzantilar:
                    continue
            girisler.append({"ad": ad, "tur": "dosya", "yol": os.path.join(gercek, ad)})

    ust = os.path.dirname(gercek) if gercek != EV_DIZINI else None
    if ust is not None and not (ust == EV_DIZINI or ust.startswith(EV_DIZINI + os.sep)):
        ust = None

    return {"path": gercek, "ust_dizin": ust, "girdiler": girisler}
