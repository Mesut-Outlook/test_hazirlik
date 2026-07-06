"""GET /api/fs/list?path=&sadece=pdf,docx|dir — yalnızca kullanıcının ev dizini
altında gezinme (path-traversal ve symlink kaçışı korumalı, bkz. utils.guvenli_ev_yolu).

POST /api/fs/mkdir {path, ad} — seçili dizin altında yeni klasör oluşturur
(F7 eki, 2026-07-06); aynı güvenlik sınırı (ev dizini altı) geçerli."""
from __future__ import annotations

import os

from fastapi import APIRouter, Query
from pydantic import BaseModel

from config import EV_DIZINI
from utils import ApiHata, guvenli_ev_yolu

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


class YeniKlasor(BaseModel):
    path: str
    ad: str


@router.post("/api/fs/mkdir")
def fs_mkdir(body: YeniKlasor):
    """Seçili dizin (body.path) altında body.ad adıyla yeni bir klasör oluşturur.
    Ad boş olamaz, '/' veya '\\' içeremez, '.' ya da '..' olamaz (path-traversal)."""
    ust_gercek = guvenli_ev_yolu(body.path or EV_DIZINI, gerekli="dir")

    ad = (body.ad or "").strip()
    if not ad or ad in (".", "..") or "/" in ad or "\\" in ad or "\x00" in ad:
        raise ApiHata(400, "geçersiz klasör adı", f"'{body.ad}' geçerli bir klasör adı değil")

    hedef = os.path.join(ust_gercek, ad)
    hedef_gercek = os.path.realpath(hedef)
    if hedef_gercek != ust_gercek and not hedef_gercek.startswith(ust_gercek + os.sep):
        raise ApiHata(403, "izin yok", f"'{ad}' üst klasörün dışına çıkıyor")

    if os.path.exists(hedef_gercek):
        raise ApiHata(409, "klasör zaten var", hedef_gercek)

    try:
        os.makedirs(hedef_gercek)
    except OSError as exc:
        raise ApiHata(400, "klasör oluşturulamadı", str(exc))

    return {"path": hedef_gercek, "ad": ad}
