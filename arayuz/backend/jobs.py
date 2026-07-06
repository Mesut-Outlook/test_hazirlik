"""Tek işçili iş (job) kuyruğu — aynı anda tek extract/print koşsun diye
(Chrome/puppeteer çakışmasın, SISTEM.md FAZ 4 mimari kararı).

Job durumları: bekliyor | çalışıyor | tamam | hata
Her job'ın log satırları birikir; SSE endpoint'i bunları akıtır.
"""
from __future__ import annotations

import queue
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class Job:
    id: str
    tur: str
    tema_id: Optional[str] = None
    durum: str = "bekliyor"  # bekliyor | çalışıyor | tamam | hata
    loglar: list[str] = field(default_factory=list)
    sonuc: dict = field(default_factory=dict)
    hata: Optional[str] = None
    olusturma: float = field(default_factory=time.time)
    guncelleme: float = field(default_factory=time.time)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def log(self, satir: str) -> None:
        with self._lock:
            self.loglar.append(satir)
            self.guncelleme = time.time()

    def durum_ayarla(self, durum: str) -> None:
        with self._lock:
            self.durum = durum
            self.guncelleme = time.time()

    def bitir(self, sonuc: dict) -> None:
        with self._lock:
            self.sonuc = sonuc
            self.durum = "tamam"
            self.guncelleme = time.time()

    def basarisiz(self, hata: str) -> None:
        with self._lock:
            self.hata = hata
            self.durum = "hata"
            self.guncelleme = time.time()

    def gorunum(self) -> dict:
        with self._lock:
            return {
                "id": self.id,
                "tur": self.tur,
                "tema_id": self.tema_id,
                "durum": self.durum,
                "loglar": list(self.loglar),
                "sonuc": self.sonuc,
                "hata": self.hata,
            }


class JobManager:
    """Tek arka plan iş parçacığı ile sırayla çalışan job kuyruğu."""

    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._kuyruk: "queue.Queue[tuple[Job, Callable[[Job], None]]]" = queue.Queue()
        self._lock = threading.Lock()
        self._worker = threading.Thread(target=self._calis, daemon=True)
        self._worker.start()

    def yeni_is(self, tur: str, calistir: Callable[[Job], None], tema_id: str | None = None) -> Job:
        job = Job(id=uuid.uuid4().hex[:12], tur=tur, tema_id=tema_id)
        with self._lock:
            self._jobs[job.id] = job
        self._kuyruk.put((job, calistir))
        return job

    def al(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def _calis(self) -> None:
        while True:
            job, calistir = self._kuyruk.get()
            job.durum_ayarla("çalışıyor")
            try:
                calistir(job)
                if job.durum == "çalışıyor":
                    # calistir kendi bitir()/basarisiz() çağırmadıysa güvenlik ağı
                    job.bitir(job.sonuc)
            except Exception as exc:  # noqa: BLE001 - job hatasını kullanıcıya taşımak için
                job.log(f"HATA: {exc}")
                job.basarisiz(str(exc))
            finally:
                self._kuyruk.task_done()


job_manager = JobManager()
