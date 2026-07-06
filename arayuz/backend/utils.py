"""Ortak yardımcılar: güvenli yol çözümleme, id üretimi, loglama."""
from __future__ import annotations

import glob
import json
import os
import re
from datetime import datetime, timezone, timedelta

from fastapi import HTTPException

from config import EV_DIZINI, REPO_ROOT, CIKTI_DIR

TR_TZ = timezone(timedelta(hours=3))  # Europe/Istanbul (DST'siz sabit ofset, günlük için yeterli)


class ApiHata(HTTPException):
    """Sözleşmedeki hata gövdesi: {hata, detay}."""

    def __init__(self, status_code: int, hata: str, detay: str = ""):
        super().__init__(status_code=status_code, detail={"hata": hata, "detay": detay})


def guvenli_ev_yolu(yol: str, gerekli: str | None = None) -> str:
    """`yol`u ev dizini (EV_DIZINI) altına sınırlar; symlink kaçışını da engeller
    (os.path.realpath sembolik bağları çözer, sonra containment kontrolü yapılır).

    gerekli: "dir" | "file" | None — varsa tipi doğrular.
    """
    if not yol:
        yol = EV_DIZINI
    ham = os.path.expanduser(yol)
    if not os.path.isabs(ham):
        ham = os.path.join(EV_DIZINI, ham)
    gercek = os.path.realpath(ham)
    if gercek != EV_DIZINI and not gercek.startswith(EV_DIZINI + os.sep):
        raise ApiHata(403, "izin yok", f"'{yol}' ev dizini ({EV_DIZINI}) dışında")
    if gerekli == "dir" and not os.path.isdir(gercek):
        raise ApiHata(404, "klasör bulunamadı", gercek)
    if gerekli == "file" and not os.path.isfile(gercek):
        raise ApiHata(404, "dosya bulunamadı", gercek)
    return gercek


def guvenli_proje_yolu(yol: str) -> str:
    """PDF stream endpoint'i için: yalnızca proje kökü (REPO_ROOT) altına izin verir
    (cikti/ ve temalar/ burada zaten içerilir). Ev dizini kısıtı yerine bunu kullan
    çünkü kullanıcının seçtiği harici çıktı klasörü de önizlenebilmeli — o durumda
    ayrıca EV_DIZINI kontrolü uygulanır (bkz. pdf_api.py)."""
    ham = os.path.expanduser(yol)
    if not os.path.isabs(ham):
        raise ApiHata(400, "geçersiz yol", "mutlak yol bekleniyor")
    gercek = os.path.realpath(ham)
    if not os.path.isfile(gercek):
        raise ApiHata(404, "dosya bulunamadı", gercek)
    icinde_mi = gercek.startswith(REPO_ROOT + os.sep) or gercek.startswith(
        os.path.realpath(EV_DIZINI) + os.sep
    )
    if not icinde_mi:
        raise ApiHata(403, "izin yok", f"'{yol}' proje kökü veya ev dizini dışında")
    return gercek


def simdi_iso() -> str:
    return datetime.now(TR_TZ).strftime("%Y-%m-%dT%H:%M:%S+03:00")


def runs_jsonl_yaz(tema_dir: str, kayit: dict) -> None:
    log_dir = os.path.join(tema_dir, "log")
    os.makedirs(log_dir, exist_ok=True)
    yol = os.path.join(log_dir, "runs.jsonl")
    kayit = {"ts": simdi_iso(), **kayit}
    with open(yol, "a", encoding="utf-8") as f:
        f.write(json.dumps(kayit, ensure_ascii=False) + "\n")


def islem_gunlugu_yaz(tema_dir: str, baslik: str, satirlar: list[str]) -> None:
    log_dir = os.path.join(tema_dir, "log")
    os.makedirs(log_dir, exist_ok=True)
    yol = os.path.join(log_dir, "islem_gunlugu.md")
    gövde = f"\n## {simdi_iso()} ({baslik})\n" + "\n".join(f"- {s}" for s in satirlar) + "\n"
    with open(yol, "a", encoding="utf-8") as f:
        f.write(gövde)


_ID_PATTERN = re.compile(r'id="(t(\d+)-e(\d+))"')


def sonraki_ek_id(sorular_html_path: str, tema_no: str) -> str:
    """tNN-eNNN serisinden bir sonraki id'yi üretir (SISTEM.md §2)."""
    en_buyuk = 0
    if os.path.exists(sorular_html_path):
        with open(sorular_html_path, "r", encoding="utf-8") as f:
            icerik = f.read()
        for tam, tema_grp, sayi in re.findall(r'id="t(\d+)-e(\d+)"', icerik):
            if tema_grp == tema_no:
                en_buyuk = max(en_buyuk, int(sayi))
    return f"t{tema_no}-e{en_buyuk + 1:03d}"


def tema_klasorleri() -> list[str]:
    if not os.path.isdir(REPO_ROOT):
        return []
    from config import TEMALAR_DIR

    if not os.path.isdir(TEMALAR_DIR):
        return []
    return sorted(
        d for d in os.listdir(TEMALAR_DIR) if os.path.isdir(os.path.join(TEMALAR_DIR, d))
    )


def sonraki_tema_no() -> str:
    en_buyuk = 0
    for ad in tema_klasorleri():
        m = re.match(r"^(\d+)-", ad)
        if m:
            en_buyuk = max(en_buyuk, int(m.group(1)))
    return f"{en_buyuk + 1:02d}"


def tema_dir_by_id(tema_id: str) -> str:
    from config import TEMALAR_DIR

    yol = os.path.join(TEMALAR_DIR, tema_id)
    gercek = os.path.realpath(yol)
    if not gercek.startswith(os.path.realpath(TEMALAR_DIR) + os.sep) and gercek != os.path.realpath(
        TEMALAR_DIR
    ):
        raise ApiHata(400, "geçersiz tema id", tema_id)
    if not os.path.isdir(gercek):
        raise ApiHata(404, "tema bulunamadı", tema_id)
    return gercek


def sonraki_cikti_yolu(ad: str, surum: int) -> str:
    """cikti/<ad>_vN.pdf — üzerine yazmaz, dolu ise N'i artırır (SISTEM.md §7)."""
    guvenli_ad = re.sub(r"[^A-Za-z0-9._-]+", "_", ad)
    n = surum
    while True:
        aday = os.path.join(CIKTI_DIR, f"{guvenli_ad}_v{n}.pdf")
        if not os.path.exists(aday):
            return aday
        n += 1
