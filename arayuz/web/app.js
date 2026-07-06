"use strict";
/* ============================================================
   Test Hazırlık Arayüzü — Uygulama Mantığı
   Framework yok, build adımı yok. mock.js ?mock=1 ile window.fetch
   ve window.EventSource'u sahteleştirir; bu dosya gerçek/sahte
   backend farkını bilmeden aynı şekilde çalışır.

   VERİ ŞEKİLLERİ — arayuz/backend/ (F1, Claude-Sonnet #9) kodu okunarak
   GERÇEK uygulamayla hizalandı (2026-07-06, F2 tarafı). COORDINATION.md'deki
   "API sözleşmesi" yalnızca uç nokta isimlerini sabitliyor; yanıt gövdeleri
   burada F1'in fiilen yazdığı haliyle özetlenmiştir:
     GET  /api/ayarlar            -> { giris_klasoru, cikti_klasoru }
     GET  /api/fs/list            -> { path, ust_dizin, girdiler:[{ad,yol,tur:'dir'|'dosya'}] }
     GET  /api/temalar            -> DÜZ DİZİ (sarmalayıcı yok):
                                      [{tema_id, ad, durum:'hazırlanıyor'|'hazır'|'hata',
                                        surum?, soru_sayisi?, kok_sayisi?, gorsel_sayisi?,
                                        job_id?, hata?}]  — PDF YOLU YOK (bkz. not aşağıda).
     POST /api/temalar            -> { tema_id, job_id }  (bu iş SADECE extract.py'yi
                                      çalıştırır — PDF ÜRETMEZ; PDF için ayrıca /uret
                                      çağrılması gerekir, bkz. sihirbazJobIzle zinciri)
     GET  /api/jobs/{id}          -> { id, tur, tema_id, durum:'bekliyor'|'çalışıyor'|'tamam'|'hata',
                                        loglar:[düz metin satırları], sonuc, hata }
                                      — ilerleme YÜZDESİ ve mesaj alanı YOK; durum metni
                                      son log satırından türetilir, ilerleme çubuğu
                                      "belirsiz" (indeterminate) modda gösterilir.
     GET  /api/jobs/{id}/events   -> SSE, İSİMLİ olaylar: "log" (data=tek log satırı,
                                      JSON string) ve "durum" (data=TAM job gorunumu,
                                      sadece tamam/hata'da BİR KEZ gönderilir).
     GET  /api/temalar/{id}/bloklar -> { tema_id, bloklar:[{id,sinif,kaynak_sayfa,ozet,bolum}] }
     PATCH /api/temalar/{id}/manifest body: { akis:[{sayfa, bloklar:[id,...]}, ...] }
                                      (SAYFA/GRUP yapılı — GET bloklar bunu düzleştirip
                                      verdiği için F2 tek grupta gönderiyor, bkz. not)
     POST /api/temalar/{id}/bloklar body: { sinif, html_govde, konum: {sonra_id}|null }
                                      -> { id, sinif, kaynak_sayfa }
     POST /api/temalar/{id}/uret    -> { tema_id, job_id }; job.sonuc =
                                      { cikti_pdf, kopya, surum, sayimlar, dogrulama:
                                        {calisti:bool, cikti?(dogrula.py ham çıktısı), not?} }
     POST /api/temalar/{id}/istek   -> { tema_id, kaydedildi: true }

   BİLİNEN AÇIK NOKTA (F1/Fable ile hizalanmalı, COORDINATION.md'ye not düşüldü):
   GET /api/temalar hiçbir sürümde üretilmiş PDF'in yolunu döndürmüyor (yalnızca
   /uret işinin SONUCUNDA bir kerelik gelir). Bu yüzden "Önizle" kartı, o oturumda
   en az bir kez üretim yapılmış temalar için state.sonPdfYollari (localStorage'a
   da yazılır) üzerinden çalışır; hiç üretilmemiş bir temada "Önizle" bilgilendirici
   bir mesaj gösterir.
   ============================================================ */

(function () {
  const el = (sel, kok) => (kok || document).querySelector(sel);
  const elAll = (sel, kok) => Array.from((kok || document).querySelectorAll(sel));

  const JSON_BASLIK = { "Content-Type": "application/json" };

  const state = {
    ayarlar: null,
    temalar: null,
    sihirbaz: { kaynakDosya: null, ciktiKlasoru: null, temaAdi: "", temaId: null, jobId: null },
    duzenle: { temaId: null, akis: [], suruklenenId: null },
    gezgin: null,
    aktifJobIzleyici: null,
  };

  // ---------------- Yardımcılar ----------------

  function kacisliMetin(s) {
    const d = document.createElement("div");
    d.textContent = s == null ? "" : String(s);
    return d.innerHTML;
  }

  function bildirimGoster(mesaj, tur) {
    const alan = el("#bildirim-alani");
    const kutu = document.createElement("div");
    kutu.className = "bildirim" + (tur ? " " + tur : "");
    kutu.textContent = mesaj;
    alan.appendChild(kutu);
    setTimeout(() => kutu.remove(), 4200);
  }

  async function govdeAyristir(yanit) {
    let govde = null;
    try {
      govde = await yanit.json();
    } catch (e) {
      /* gövde JSON değilse (ör. boş yanıt) sessiz geç */
    }
    if (!yanit.ok) {
      const mesaj = (govde && (govde.hata || govde.detay)) || `İstek başarısız oldu (kod ${yanit.status})`;
      throw new Error(mesaj);
    }
    return govde;
  }

  // ---------------- API katmanı ----------------

  const api = {
    async ayarlarGetir() {
      return govdeAyristir(await fetch("/api/ayarlar"));
    },
    async ayarlarKaydet(veri) {
      return govdeAyristir(
        await fetch("/api/ayarlar", { method: "PUT", headers: JSON_BASLIK, body: JSON.stringify(veri) })
      );
    },
    async fsListele(yol, sadece) {
      const p = new URLSearchParams();
      if (yol) p.set("path", yol);
      if (sadece) p.set("sadece", sadece);
      return govdeAyristir(await fetch("/api/fs/list?" + p.toString()));
    },
    async temalar() {
      return govdeAyristir(await fetch("/api/temalar"));
    },
    async temaOlustur(veri) {
      return govdeAyristir(
        await fetch("/api/temalar", { method: "POST", headers: JSON_BASLIK, body: JSON.stringify(veri) })
      );
    },
    async jobDurumu(id) {
      return govdeAyristir(await fetch(`/api/jobs/${encodeURIComponent(id)}`));
    },
    async bloklar(temaId) {
      return govdeAyristir(await fetch(`/api/temalar/${encodeURIComponent(temaId)}/bloklar`));
    },
    async manifestGuncelle(temaId, akis) {
      return govdeAyristir(
        await fetch(`/api/temalar/${encodeURIComponent(temaId)}/manifest`, {
          method: "PATCH",
          headers: JSON_BASLIK,
          body: JSON.stringify({ akis }),
        })
      );
    },
    async blokEkle(temaId, veri) {
      return govdeAyristir(
        await fetch(`/api/temalar/${encodeURIComponent(temaId)}/bloklar`, {
          method: "POST",
          headers: JSON_BASLIK,
          body: JSON.stringify(veri),
        })
      );
    },
    async uret(temaId, veri) {
      return govdeAyristir(
        await fetch(`/api/temalar/${encodeURIComponent(temaId)}/uret`, {
          method: "POST",
          headers: JSON_BASLIK,
          body: JSON.stringify(veri || {}),
        })
      );
    },
    async istekGonder(temaId, metin) {
      return govdeAyristir(
        await fetch(`/api/temalar/${encodeURIComponent(temaId)}/istek`, {
          method: "POST",
          headers: JSON_BASLIK,
          body: JSON.stringify({ metin }),
        })
      );
    },
    pdfUrl(yol) {
      return "/api/pdf?path=" + encodeURIComponent(yol || "");
    },
  };

  // <embed src="..."> tarayıcı düzeyinde DOĞRUDAN bir ağ isteği başlatır — bu
  // istek window.fetch'i sarmalayan mock.js tarafından YAKALANAMAZ. Bu yüzden
  // PDF'i her zaman fetch() ile çekip blob: URL'e çeviriyoruz; hem gerçek
  // backend'de hem ?mock=1 modunda aynı kod yolu çalışır.
  const oncekiBlobUrller = new WeakMap();

  async function pdfEmbedYukle(embedEl, yol) {
    embedEl.removeAttribute("src");
    if (!yol) return;
    const eskiUrl = oncekiBlobUrller.get(embedEl);
    if (eskiUrl) URL.revokeObjectURL(eskiUrl);
    try {
      const yanit = await fetch(api.pdfUrl(yol));
      if (!yanit.ok) throw new Error("PDF alınamadı (kod " + yanit.status + ")");
      const blob = await yanit.blob();
      const blobUrl = URL.createObjectURL(blob);
      oncekiBlobUrller.set(embedEl, blobUrl);
      embedEl.setAttribute("src", blobUrl);
    } catch (err) {
      bildirimGoster("PDF önizleme yüklenemedi: " + err.message, "hata");
    }
  }

  // ---------------- İş (job) izleme: SSE, düşerse 1sn polling ----------------

  // Not: backend (arayuz/backend/jobs_api.py) SSE'de İSİMLİ olaylar gönderiyor —
  // "log" (data: tek log satırı, JSON string) ve "durum" (data: TAM job gorunumu,
  // sadece tamam/hata'da BİR KEZ). Job gövdesinde ilerleme YÜZDESİ / mesaj alanı
  // yok; durum metni son log satırından türetilir, ilerleme çubuğu bu yüzden
  // "belirsiz" (indeterminate) modda gösterilir (bkz. ilerlemeCubuguGuncelle).
  function jobIzle(jobId, geriCagrilar) {
    let es = null;
    let poller = null;
    let durduruldu = false;
    let birikenLoglar = [];

    function durdur() {
      durduruldu = true;
      if (es) {
        try {
          es.close();
        } catch (e) {}
        es = null;
      }
      if (poller) {
        clearInterval(poller);
        poller = null;
      }
    }

    function guncelleVeBitirKontrolEt(veri) {
      if (durduruldu) return;
      geriCagrilar.guncelle(veri);
      if (veri.durum === "tamam" || veri.durum === "hata") {
        durdur();
        geriCagrilar.bitti(veri);
      }
    }

    // Polling / "durum" olayı / mock'un "message" olayı: TAM anlık durum gelir.
    function tamAnlikDurumIsle(veri) {
      if (veri.loglar) birikenLoglar = veri.loglar;
      guncelleVeBitirKontrolEt({ ...veri, loglar: birikenLoglar });
    }

    // Gerçek backend'in "log" olayı: TEK bir yeni satır gelir, biriktir.
    function tekLogSatiriIsle(satir) {
      birikenLoglar = birikenLoglar.concat([satir]);
      guncelleVeBitirKontrolEt({ durum: "çalışıyor", loglar: birikenLoglar });
    }

    function pollingBaslat() {
      if (poller || durduruldu) return;
      poller = setInterval(async () => {
        try {
          const veri = await api.jobDurumu(jobId);
          tamAnlikDurumIsle(veri);
        } catch (err) {
          /* geçici ağ hatası — bir sonraki turda tekrar dener */
        }
      }, 1000);
    }

    try {
      es = new EventSource(`/api/jobs/${encodeURIComponent(jobId)}/events`);
      es.addEventListener("log", (e) => {
        try {
          tekLogSatiriIsle(JSON.parse(e.data));
        } catch (err) {
          /* ayrıştırılamayan log satırını yok say */
        }
      });
      es.addEventListener("durum", (e) => {
        try {
          tamAnlikDurumIsle(JSON.parse(e.data));
        } catch (err) {
          /* ayrıştırılamayan durumu yok say */
        }
      });
      // Genel "message" olayı: mock.js veya isim vermeyen bir yayıncı için
      // geriye dönük uyumluluk — TAM anlık durum varsayılır.
      es.onmessage = (e) => {
        try {
          tamAnlikDurumIsle(JSON.parse(e.data));
        } catch (err) {
          /* ayrıştırılamayan mesajı yok say */
        }
      };
      es.onerror = () => {
        if (durduruldu) return;
        if (es) {
          try {
            es.close();
          } catch (e2) {}
          es = null;
        }
        pollingBaslat();
      };
    } catch (err) {
      pollingBaslat();
    }

    return { durdur };
  }

  // Job durumunda sayısal "ilerleme" yoksa (gerçek backend) çubuğu "belirsiz"
  // (kayan animasyon) moda al; mock veya ileride sayısal ilerleme eklenirse
  // normal genişlik modunu kullan.
  function ilerlemeCubuguGuncelle(cubukEl, yuzdeEl, veri) {
    if (typeof veri.ilerleme === "number") {
      cubukEl.classList.remove("belirsiz");
      const yuzde = Math.max(0, Math.min(100, veri.ilerleme));
      cubukEl.style.width = yuzde + "%";
      yuzdeEl.textContent = "%" + yuzde;
      yuzdeEl.hidden = false;
    } else {
      cubukEl.classList.add("belirsiz");
      cubukEl.style.width = "";
      yuzdeEl.hidden = true;
      if (veri.durum === "tamam") {
        cubukEl.classList.remove("belirsiz");
        cubukEl.style.width = "100%";
        yuzdeEl.hidden = false;
        yuzdeEl.textContent = "%100";
      }
    }
  }

  // mesaj alanı yoksa (gerçek backend) son log satırını / durum metnini göster.
  function jobDurumMetni(veri) {
    if (veri.mesaj) return veri.mesaj;
    if (veri.loglar && veri.loglar.length) return veri.loglar[veri.loglar.length - 1];
    const durumMetinleri = { bekliyor: "Sırada bekliyor…", "çalışıyor": "İşleniyor…", calisiyor: "İşleniyor…" };
    return durumMetinleri[veri.durum] || "İşleniyor…";
  }

  // ---------------- Görünüm (ekran) yönlendirme ----------------

  function gotoView(ad) {
    elAll(".gorunum").forEach((g) => g.classList.remove("gorunur"));
    const hedef = el("#view-" + ad);
    if (hedef) hedef.classList.add("gorunur");
    elAll(".sekme-btn").forEach((b) => b.classList.toggle("aktif", b.dataset.gorunum === ad));

    if (ad === "anasayfa") anaSayfaYukle();
    if (ad === "ayarlar") ayarlarEkraniYukle();
    if (ad === "sihirbaz") sihirbazSifirla();
  }

  elAll(".sekme-nav .sekme-btn").forEach((btn) => {
    btn.addEventListener("click", () => gotoView(btn.dataset.gorunum));
  });

  // ================= KLASÖR / DOSYA GEZGİNİ MODALI =================

  function gezginKapat() {
    el("#gezgin-modal").classList.remove("acik");
    state.gezgin = null;
  }

  el("#gezgin-modal-kapat").addEventListener("click", gezginKapat);
  el("#gezgin-btn-iptal").addEventListener("click", gezginKapat);
  el("#gezgin-modal").addEventListener("click", (e) => {
    if (e.target.id === "gezgin-modal") gezginKapat();
  });
  el("#gezgin-btn-sec").addEventListener("click", () => {
    if (state.gezgin && state.gezgin.mevcutYol) {
      state.gezgin.onSecim(state.gezgin.mevcutYol);
      gezginKapat();
    }
  });

  function gezginSatirOlustur({ ad, ikon, dizinMi, secilebilir }) {
    const btn = document.createElement("button");
    btn.className = "gezgin-satiri" + (!dizinMi ? " dosya" : "") + (secilebilir ? " secilebilir" : "");
    btn.innerHTML = `<span class="gezgin-satiri__ikon">${ikon}</span><span>${kacisliMetin(ad)}</span>`;
    return btn;
  }

  async function gezginYukle(yol) {
    const govdeEl = el("#gezgin-govde");
    govdeEl.innerHTML = '<p class="yukleniyor-metni">Yükleniyor…</p>';
    try {
      const sadeceParam = state.gezgin.mod === "dizin" ? "dir" : state.gezgin.sadece || "pdf,docx";
      const veri = await api.fsListele(yol, sadeceParam);
      // backend alan adları: path (mevcut yol), ust_dizin (üst klasör), tur:'dir'|'dosya'
      const mevcutYol = veri.path;
      const ustDizin = veri.ust_dizin;
      state.gezgin.mevcutYol = mevcutYol;
      el("#gezgin-yol-cubugu").textContent = mevcutYol || "/";
      el("#gezgin-secili-yol").textContent = mevcutYol || "";
      govdeEl.innerHTML = "";

      if (ustDizin) {
        const ustSatir = gezginSatirOlustur({ ad: ".. (üst klasöre çık)", ikon: "⬆️", dizinMi: true });
        ustSatir.addEventListener("click", () => gezginYukle(ustDizin));
        govdeEl.appendChild(ustSatir);
      }

      const girdiler = veri.girdiler || [];
      if (!girdiler.length) {
        const p = document.createElement("p");
        p.className = "yukleniyor-metni";
        p.textContent = "Bu klasörde uygun dosya/klasör bulunamadı.";
        govdeEl.appendChild(p);
      }

      girdiler.forEach((g) => {
        const dizinMi = g.tur === "dir";
        const secilebilir = state.gezgin.mod === "dosya" && !dizinMi;
        const satir = gezginSatirOlustur({ ad: g.ad, ikon: dizinMi ? "📁" : "📄", dizinMi, secilebilir });
        satir.addEventListener("click", () => {
          if (dizinMi) {
            gezginYukle(g.yol);
          } else if (secilebilir) {
            state.gezgin.onSecim(g.yol);
            gezginKapat();
          }
        });
        govdeEl.appendChild(satir);
      });
    } catch (err) {
      govdeEl.innerHTML = "";
      bildirimGoster("Klasör listelenemedi: " + err.message, "hata");
    }
  }

  function klasorGezginiAc({ baslik, mod, sadece, baslangicYolu, onSecim }) {
    state.gezgin = { mod, sadece, mevcutYol: baslangicYolu || null, onSecim };
    el("#gezgin-modal-baslik").textContent = baslik;
    el("#gezgin-btn-sec").hidden = mod !== "dizin";
    el("#gezgin-modal").classList.add("acik");
    gezginYukle(baslangicYolu || null);
  }

  // ================= ANA SAYFA: TEMA LİSTESİ =================

  // Gerçek sınıf adları sistem/flow.css + config.BILINEN_SINIFLAR ile birebir
  // eşleşir; önce tam eşleşme denenir, tanınmayan/özel bir değer gelirse
  // (ör. eski veri, deney) esnek (fuzzy) eşleşmeye düşer.
  const TAM_TUR_ESLEME = {
    question: { ad: "Soru", veri: "soru" },
    "theory-box": { ad: "Teori Kutusu", veri: "teori" },
    "img-block": { ad: "Görsel", veri: "gorsel" },
    "answer-key": { ad: "Cevap Anahtarı", veri: "cevap-anahtari" },
    "kur-tag": { ad: "Bölüm Başlığı", veri: "bolum" },
    "section-sub": { ad: "Alt Başlık", veri: "bolum" },
    para: { ad: "Paragraf / Not", veri: "diger" },
  };

  function turEtiket(sinif) {
    if (sinif == null) return { ad: "Bilinmiyor", veri: "diger" };
    if (TAM_TUR_ESLEME[sinif]) return TAM_TUR_ESLEME[sinif];
    const s = String(sinif).toLowerCase();
    if (s.includes("soru")) return { ad: "Soru", veri: "soru" };
    if (s.includes("teori") || s.includes("theory")) return { ad: "Teori Kutusu", veri: "teori" };
    if (s.includes("gorsel") || s.includes("img") || s.includes("figur")) return { ad: "Görsel", veri: "gorsel" };
    if (s.includes("cevap") || s.includes("answer")) return { ad: "Cevap Anahtarı", veri: "cevap-anahtari" };
    if (s.includes("bolum") || s.includes("baslik")) return { ad: "Bölüm Başlığı", veri: "bolum" };
    return { ad: sinif, veri: "diger" };
  }

  // GET /api/temalar PDF yolu döndürmüyor (yalnızca bir /uret işi TAMAMLANDIĞINDA
  // job.sonuc.cikti_pdf/kopya olarak bir kerelik gelir) — bu yüzden bu oturumda
  // (veya önceki bir oturumda, localStorage sayesinde) üretilmiş son PDF yolu
  // burada tema_id'ye göre saklanır. Bilinmiyor olabilir; "Önizle" o zaman
  // bilgilendirici bir mesaj gösterir.
  const PDF_YOLU_ANAHTARI = "th_son_pdf_yollari";

  function sonPdfYollariOku() {
    try {
      return JSON.parse(localStorage.getItem(PDF_YOLU_ANAHTARI) || "{}");
    } catch (e) {
      return {};
    }
  }

  function sonPdfYoluKaydet(temaId, yol) {
    if (!temaId || !yol) return;
    const harita = sonPdfYollariOku();
    harita[temaId] = yol;
    localStorage.setItem(PDF_YOLU_ANAHTARI, JSON.stringify(harita));
  }

  const DURUM_ROZETI = {
    "hazırlanıyor": { metin: "İşleniyor…", sinif: "durum-rozeti" },
    hata: { metin: "Hata", sinif: "durum-rozeti hata" },
  };

  function temaKartiOlustur(tema) {
    const kart = document.createElement("div");
    kart.className = "tema-kart";
    const hazirDegil = tema.durum && tema.durum !== "hazır";
    const rozetBilgi = DURUM_ROZETI[tema.durum];
    kart.innerHTML = `
      <h3 class="tema-kart__baslik">${kacisliMetin(tema.ad)}</h3>
      <div class="tema-kart__meta">
        ${tema.surum ? `<span>v${kacisliMetin(tema.surum)}</span>` : ""}
        ${tema.soru_sayisi != null ? `<span>${kacisliMetin(tema.soru_sayisi)} soru</span>` : ""}
        ${tema.gorsel_sayisi != null ? `<span>${kacisliMetin(tema.gorsel_sayisi)} görsel</span>` : ""}
        ${rozetBilgi ? `<span class="${rozetBilgi.sinif}" style="background:none;">${rozetBilgi.metin}</span>` : ""}
      </div>
      ${tema.hata ? `<p style="color:var(--renk-hata); font-size:13px; margin:0;">${kacisliMetin(tema.hata)}</p>` : ""}
      <div class="tema-kart__butonlar">
        <button class="btn" data-aksiyon="onizle" ${hazirDegil ? "disabled" : ""}>Önizle</button>
        <button class="btn btn-birincil" data-aksiyon="duzenle" ${hazirDegil ? "disabled" : ""}>Düzenle</button>
        <button class="btn" data-aksiyon="uret" ${hazirDegil ? "disabled" : ""}>Yeniden Üret</button>
      </div>
    `;
    kart.querySelector('[data-aksiyon="onizle"]').addEventListener("click", () => pdfOnizlemeAc(tema));
    kart.querySelector('[data-aksiyon="duzenle"]').addEventListener("click", () => duzenleAc(tema.tema_id));
    kart.querySelector('[data-aksiyon="uret"]').addEventListener("click", () => temaYenidenUret(tema));
    return kart;
  }

  async function anaSayfaYukle() {
    const alan = el("#tema-izgara-alani");
    alan.innerHTML = '<p class="yukleniyor-metni">Temalar yükleniyor…</p>';
    try {
      // GET /api/temalar DÜZ bir dizi döner (sarmalayıcı yok).
      const veri = await api.temalar();
      state.temalar = Array.isArray(veri) ? veri : veri.temalar || [];
      if (!state.temalar.length) {
        alan.innerHTML = '<div class="bos-durum">Henüz bir tema oluşturmadınız. Yukarıdaki "Yeni Tema Oluştur" butonuyla başlayın.</div>';
        return;
      }
      const izgara = document.createElement("div");
      izgara.className = "tema-izgara";
      state.temalar.forEach((t) => izgara.appendChild(temaKartiOlustur(t)));
      alan.innerHTML = "";
      alan.appendChild(izgara);
    } catch (err) {
      alan.innerHTML = `<div class="bos-durum">Temalar yüklenemedi: ${kacisliMetin(err.message)}</div>`;
    }
  }

  el("#btn-yeni-tema-anasayfa").addEventListener("click", () => gotoView("sihirbaz"));
  el("#btn-landing-basla").addEventListener("click", () => gotoView("sihirbaz"));
  el(".ust-baslik__logo").addEventListener("click", () => gotoView("landing"));
  el(".ust-baslik__baslik").addEventListener("click", () => gotoView("landing"));

  // ---- PDF önizleme modalı (kartlardan / sonuç ekranından ortak) ----

  function pdfOnizlemeAc(tema) {
    // Öncelik: backend'in kalıcı son_pdf alanı; yoksa bu oturumun localStorage kaydı
    const bilinenYol = (tema && tema.son_pdf) || sonPdfYollariOku()[tema.tema_id];
    if (!tema || !bilinenYol) {
      bildirimGoster(
        'Bu tema için bu oturumda üretilmiş bir PDF yok. "Yeniden Üret" ile bir PDF oluşturduktan sonra önizleyebilirsiniz.',
        "hata"
      );
      return;
    }
    el("#pdf-onizleme-modal-baslik").textContent = tema.ad || "PDF Önizleme";
    pdfEmbedYukle(el("#pdf-onizleme-embed"), bilinenYol);
    el("#pdf-onizleme-modal").classList.add("acik");
  }

  el("#pdf-onizleme-modal-kapat").addEventListener("click", () => {
    el("#pdf-onizleme-modal").classList.remove("acik");
    el("#pdf-onizleme-embed").removeAttribute("src");
  });
  el("#pdf-onizleme-modal").addEventListener("click", (e) => {
    if (e.target.id === "pdf-onizleme-modal") el("#pdf-onizleme-modal-kapat").click();
  });

  async function temaYenidenUret(tema) {
    if (!confirm(`"${tema.ad}" temasını mevcut soru sıralamasıyla yeniden üretmek istiyor musunuz?`)) return;
    try {
      const sonuc = await api.uret(tema.tema_id, {});
      bildirimGoster("İş kuyruğa alındı, arka planda üretiliyor…");
      let sonLog = null;
      jobIzle(sonuc.job_id, {
        guncelle(veri) {
          const guncelMesaj = jobDurumMetni(veri);
          if (guncelMesaj && guncelMesaj !== sonLog) {
            sonLog = guncelMesaj;
            bildirimGoster(`"${tema.ad}": ${guncelMesaj}`);
          }
        },
        bitti(veri) {
          if (veri.durum === "tamam") {
            const pdfYolu = veri.sonuc && (veri.sonuc.kopya || veri.sonuc.cikti_pdf);
            sonPdfYoluKaydet(tema.tema_id, pdfYolu);
            bildirimGoster(`"${tema.ad}" başarıyla yeniden üretildi.`, "basari");
            anaSayfaYukle();
          } else {
            bildirimGoster(`"${tema.ad}" üretimi başarısız: ${veri.hata || "bilinmeyen hata"}`, "hata");
          }
        },
      });
    } catch (err) {
      bildirimGoster("Üretim başlatılamadı: " + err.message, "hata");
    }
  }

  // ================= SİHİRBAZ =================

  function sihirbazSifirla() {
    if (state.sihirbaz.jobId) return; // devam eden bir iş varsa sıfırlama
    state.sihirbaz = { kaynakDosya: null, ciktiKlasoru: null, temaAdi: "", temaId: null, jobId: null };
    el("#girdi-kaynak-dosya").value = "";
    el("#girdi-cikti-klasoru").value = state.ayarlar ? state.ayarlar.cikti_klasoru || "" : "";
    el("#girdi-tema-adi").value = "";
    adimGoster(1);
  }

  function adimGoster(n) {
    for (let i = 1; i <= 3; i++) {
      el(`#panel-adim-${i}`).hidden = i !== n;
      const adimEl = el(`.adim[data-adim="${i}"]`);
      adimEl.classList.toggle("aktif", i === n);
      adimEl.classList.toggle("tamam", i < n);
    }
    elAll(".adim-cizgi").forEach((c) => {
      c.classList.toggle("tamam", Number(c.dataset.cizgi) < n);
    });
  }

  el("#btn-kaynak-sec").addEventListener("click", () => {
    klasorGezginiAc({
      baslik: "Kaynak Ders Notu Seç (PDF / Word)",
      mod: "dosya",
      sadece: "pdf,docx",
      baslangicYolu: state.ayarlar ? state.ayarlar.giris_klasoru : null,
      onSecim: (yol) => {
        state.sihirbaz.kaynakDosya = yol;
        el("#girdi-kaynak-dosya").value = yol;
      },
    });
  });

  el("#btn-cikti-sec").addEventListener("click", () => {
    klasorGezginiAc({
      baslik: "Çıktı Klasörü Seç",
      mod: "dizin",
      baslangicYolu: state.sihirbaz.ciktiKlasoru || (state.ayarlar ? state.ayarlar.cikti_klasoru : null),
      onSecim: (yol) => {
        state.sihirbaz.ciktiKlasoru = yol;
        el("#girdi-cikti-klasoru").value = yol;
      },
    });
  });

  el("#btn-adim1-iptal").addEventListener("click", () => gotoView("anasayfa"));

  el("#btn-adim1-donustur").addEventListener("click", async () => {
    const temaAdi = el("#girdi-tema-adi").value.trim();
    if (!state.sihirbaz.kaynakDosya) {
      bildirimGoster("Lütfen bir kaynak dosya seçin.", "hata");
      return;
    }
    if (!state.sihirbaz.ciktiKlasoru) {
      bildirimGoster("Lütfen bir çıktı klasörü seçin.", "hata");
      return;
    }
    if (!temaAdi) {
      bildirimGoster("Lütfen tema için bir ad yazın.", "hata");
      return;
    }
    state.sihirbaz.temaAdi = temaAdi;

    el("#adim2-log-paneli").innerHTML = "";
    el("#adim2-ilerleme-cubuk").style.width = "0%";
    el("#adim2-yuzde").textContent = "%0";
    el("#adim2-durum-metni").textContent = "İş kuyruğa alınıyor…";
    el("#adim2-hata-eylemler").hidden = true;
    adimGoster(2);

    try {
      const sonuc = await api.temaOlustur({
        kaynak_dosya: state.sihirbaz.kaynakDosya,
        ad: state.sihirbaz.temaAdi,
        cikti_klasoru: state.sihirbaz.ciktiKlasoru,
      });
      state.sihirbaz.temaId = sonuc.tema_id;
      state.sihirbaz.jobId = sonuc.job_id;
      sihirbazJobIzle(sonuc.job_id, "olustur");
    } catch (err) {
      el("#adim2-durum-metni").textContent = "Başlatılamadı.";
      logSatiriEkle(el("#adim2-log-paneli"), "HATA: " + err.message);
      el("#adim2-hata-eylemler").hidden = false;
      bildirimGoster("Dönüştürme başlatılamadı: " + err.message, "hata");
    }
  });

  el("#btn-adim2-geri").addEventListener("click", () => {
    state.sihirbaz.jobId = null;
    adimGoster(1);
  });

  function logSatiriEkle(panel, satir) {
    const p = document.createElement("div");
    p.className = "log-satiri";
    p.textContent = satir;
    panel.appendChild(p);
    panel.scrollTop = panel.scrollHeight;
  }

  function logPaneliDoldur(panel, satirlar) {
    panel.innerHTML = "";
    (satirlar || []).forEach((s) => logSatiriEkle(panel, s));
  }

  // ÖNEMLİ (F1 kodu okunarak doğrulandı): POST /api/temalar İŞİ yalnızca
  // extract.py'yi çalıştırır — henüz basılı bir PDF üretmez. PDF'i elde etmek
  // için ayrıca POST /api/temalar/{id}/uret çağrılması gerekir. Sihirbazın tek
  // "Dönüştür" tıklamasıyla 3. adımda gerçek bir PDF önizlemesi göstermesi için
  // burada İKİ işi ZİNCİRLİYORUZ: önce oluşturma (extract) işi, o bitince
  // otomatik olarak üretim (assemble+print+doğrula) işi.
  function sihirbazJobIzle(jobId, asama) {
    jobIzle(jobId, {
      guncelle(veri) {
        ilerlemeCubuguGuncelle(el("#adim2-ilerleme-cubuk"), el("#adim2-yuzde"), veri);
        el("#adim2-durum-metni").textContent = jobDurumMetni(veri);
        if (veri.loglar) logPaneliDoldur(el("#adim2-log-paneli"), veri.loglar);
      },
      async bitti(veri) {
        if (veri.durum !== "tamam") {
          el("#adim2-durum-metni").textContent = "İşlem hata ile sonuçlandı.";
          logSatiriEkle(el("#adim2-log-paneli"), "HATA: " + (veri.hata || "bilinmeyen hata"));
          el("#adim2-hata-eylemler").hidden = false;
          bildirimGoster("Dönüştürme başarısız oldu.", "hata");
          return;
        }
        if (asama === "olustur") {
          // Bloklar hazır — şimdi PDF üretimini başlat (aynı adım 2 ekranında devam).
          logSatiriEkle(el("#adim2-log-paneli"), "Bloklar hazır, PDF üretimi başlatılıyor…");
          el("#adim2-durum-metni").textContent = "PDF üretiliyor…";
          try {
            const uretSonuc = await api.uret(state.sihirbaz.temaId, {});
            sihirbazJobIzle(uretSonuc.job_id, "uret");
          } catch (err) {
            el("#adim2-durum-metni").textContent = "PDF üretimi başlatılamadı.";
            logSatiriEkle(el("#adim2-log-paneli"), "HATA: " + err.message);
            el("#adim2-hata-eylemler").hidden = false;
            bildirimGoster("PDF üretimi başlatılamadı: " + err.message, "hata");
          }
          return;
        }
        // asama === "uret": PDF hazır.
        const pdfYolu = veri.sonuc && (veri.sonuc.kopya || veri.sonuc.cikti_pdf);
        sonPdfYoluKaydet(state.sihirbaz.temaId, pdfYolu);
        adim3Doldur(veri.sonuc || {});
        adimGoster(3);
        bildirimGoster("Dönüştürme tamamlandı.", "basari");
      },
    });
  }

  // job.sonuc.dogrulama = { calisti: bool, cikti?: qa/dogrula.py'nin ham metin
  // çıktısı, not?: çalışmadıysa neden } — backend'in kendi mantığıyla aynı ölçüt
  // kullanılır: çıktıda "FARK" geçmiyorsa temiz kabul edilir (bkz. temalar_api.py).
  function dogrulamaPaneliOlustur(dogrulama) {
    const sarmalayici = document.createElement("div");
    if (!dogrulama || !dogrulama.calisti) {
      const not = (dogrulama && dogrulama.not) || "Doğrulama çalıştırılmadı.";
      sarmalayici.innerHTML = `<div class="rozet" style="background:var(--renk-uyari-zemin); color:var(--renk-uyari);">
        <span class="rozet__isaret" style="background:var(--renk-uyari);">i</span>
        <span>Doğrulama atlandı — ${kacisliMetin(not)}</span>
      </div>`;
      return sarmalayici;
    }
    const cikti = dogrulama.cikti || "";
    const gecti = !cikti.includes("FARK");
    const ozetRozet = document.createElement("div");
    ozetRozet.className = "rozet " + (gecti ? "ok" : "hata");
    ozetRozet.innerHTML = `<span class="rozet__isaret">${gecti ? "✓" : "✕"}</span><span>${
      gecti ? "qa/dogrula.py: fark bulunamadı" : "qa/dogrula.py: FARK bildirdi — ayrıntı için aşağıdaki çıktıyı inceleyin"
    }</span>`;
    sarmalayici.appendChild(ozetRozet);
    if (cikti.trim()) {
      const ciktiKutu = document.createElement("div");
      ciktiKutu.className = "log-paneli";
      ciktiKutu.style.marginTop = "10px";
      ciktiKutu.style.maxHeight = "220px";
      ciktiKutu.textContent = cikti;
      sarmalayici.appendChild(ciktiKutu);
    }
    return sarmalayici;
  }

  function adim3Doldur(sonuc) {
    const pdfYolu = sonuc.kopya || sonuc.cikti_pdf;
    if (pdfYolu) {
      pdfEmbedYukle(el("#adim3-pdf-onizleme"), pdfYolu);
    }
    const liste = el("#adim3-dogrulama-listesi");
    liste.innerHTML = "";
    liste.appendChild(dogrulamaPaneliOlustur(sonuc.dogrulama));
    el("#adim3-cikti-notu").innerHTML = pdfYolu
      ? `PDF şu konuma kaydedildi:<br><code>${kacisliMetin(pdfYolu)}</code><br>Dosya yöneticinizden bu klasöre giderek dosyayı bulabilirsiniz.`
      : "Çıktı konumu bilgisi alınamadı.";
  }

  el("#btn-adim3-duzenle").addEventListener("click", () => {
    const temaId = state.sihirbaz.temaId;
    state.sihirbaz.jobId = null;
    if (temaId) duzenleAc(temaId);
  });
  el("#btn-adim3-anasayfa").addEventListener("click", () => {
    state.sihirbaz.jobId = null;
    gotoView("anasayfa");
  });

  // ================= DÜZENLEME EKRANI =================

  async function duzenleAc(temaId) {
    state.duzenle.temaId = temaId;
    elAll(".gorunum").forEach((g) => g.classList.remove("gorunur"));
    el("#view-duzenle").classList.add("gorunur");
    elAll(".sekme-btn").forEach((b) => b.classList.remove("aktif")); // düzenle ekranı üst menüde bir sekme değil

    el("#blok-listesi-alani").innerHTML = '<p class="yukleniyor-metni">Bloklar yükleniyor…</p>';
    el("#duzenle-uretim-paneli").hidden = true;

    let tema = (state.temalar || []).find((t) => t.tema_id === temaId);
    if (!tema) {
      try {
        const veri = await api.temalar();
        state.temalar = Array.isArray(veri) ? veri : veri.temalar || [];
        tema = state.temalar.find((t) => t.tema_id === temaId);
      } catch (e) {
        /* tema listesi alınamazsa sadece başlık geneli kalır */
      }
    }
    el("#duzenle-tema-baslik").textContent = tema ? `"${tema.ad}" — Düzenle` : "Tema Düzenle";

    try {
      const veri = await api.bloklar(temaId);
      state.duzenle.akis = veri.bloklar || [];
      blokListesiRenderEt();
    } catch (err) {
      el("#blok-listesi-alani").innerHTML = `<div class="bos-durum">Bloklar yüklenemedi: ${kacisliMetin(
        err.message
      )}</div>`;
    }

    talepListesiRenderEt(temaId);
  }

  function blokListesiRenderEt() {
    const alan = el("#blok-listesi-alani");
    alan.innerHTML = "";
    if (!state.duzenle.akis.length) {
      alan.innerHTML = '<div class="bos-durum">Bu temada henüz blok yok.</div>';
      return;
    }

    let mevcutBolum = null;
    let ul = null;

    state.duzenle.akis.forEach((blok) => {
      if (blok.bolum !== mevcutBolum || !ul) {
        mevcutBolum = blok.bolum;
        const grup = document.createElement("div");
        grup.className = "bolum-grup";
        const baslik = document.createElement("div");
        baslik.className = "bolum-grup__baslik";
        baslik.textContent = mevcutBolum || "Bölümsüz";
        grup.appendChild(baslik);
        ul = document.createElement("ul");
        ul.className = "blok-listesi";
        grup.appendChild(ul);
        alan.appendChild(grup);
      }
      ul.appendChild(blokOgesiOlustur(blok));
    });
  }

  function blokOgesiOlustur(blok) {
    const li = document.createElement("li");
    li.className = "blok-ogesi";
    li.draggable = true;
    li.dataset.id = blok.id;
    const tur = turEtiket(blok.sinif);
    li.innerHTML = `
      <span class="blok-ogesi__tut" title="Sürükleyerek sırala">⠿</span>
      <div class="blok-ogesi__govde">
        <div class="blok-ogesi__ust">
          <span class="tur-rozeti" data-tur="${tur.veri}">${kacisliMetin(tur.ad)}</span>
          ${blok.kaynak_sayfa != null ? `<span class="blok-ogesi__sayfa">kaynak s. ${kacisliMetin(blok.kaynak_sayfa)}</span>` : ""}
        </div>
        <div class="blok-ogesi__ozet">${kacisliMetin(blok.ozet || "")}</div>
      </div>
      <div class="blok-ogesi__eylemler">
        <button class="icon-btn sil" title="Sil" data-eylem="sil">🗑</button>
      </div>
    `;
    li.querySelector('[data-eylem="sil"]').addEventListener("click", () => blokSil(blok.id));

    li.addEventListener("dragstart", () => {
      state.duzenle.suruklenenId = blok.id;
      li.classList.add("surukleniyor");
    });
    li.addEventListener("dragend", () => {
      li.classList.remove("surukleniyor");
      elAll(".blok-ogesi.hedef-uzeri").forEach((e) => e.classList.remove("hedef-uzeri"));
    });
    li.addEventListener("dragover", (e) => {
      e.preventDefault();
      if (blok.id === state.duzenle.suruklenenId) return;
      li.classList.add("hedef-uzeri");
    });
    li.addEventListener("dragleave", () => li.classList.remove("hedef-uzeri"));
    li.addEventListener("drop", (e) => {
      e.preventDefault();
      li.classList.remove("hedef-uzeri");
      const kaynakId = state.duzenle.suruklenenId;
      if (!kaynakId || kaynakId === blok.id) return;
      blokTasi(kaynakId, blok.id, e);
    });

    return li;
  }

  function blokTasi(kaynakId, hedefId, dropEventi) {
    const akis = state.duzenle.akis;
    const kaynakIdx = akis.findIndex((b) => b.id === kaynakId);
    let hedefIdx = akis.findIndex((b) => b.id === hedefId);
    if (kaynakIdx === -1 || hedefIdx === -1) return;

    const [tasinan] = akis.splice(kaynakIdx, 1);
    hedefIdx = akis.findIndex((b) => b.id === hedefId);

    // Bırakılan öğenin üst yarısına mı alt yarısına mı bırakıldığına göre önce/sonra karar ver
    const hedefEl = el(`.blok-ogesi[data-id="${CSS.escape(hedefId)}"]`);
    let sonraEkle = false;
    if (hedefEl && dropEventi) {
      const dikdortgen = hedefEl.getBoundingClientRect();
      sonraEkle = dropEventi.clientY - dikdortgen.top > dikdortgen.height / 2;
    }
    akis.splice(sonraEkle ? hedefIdx + 1 : hedefIdx, 0, tasinan);

    // Not: sürükleme, bloğun kayıtlı "bolum" alanını DEĞİŞTİRMEZ; farklı bir
    // bölüm grubunun içine bırakılsa bile bir sonraki kaydetmede/render'da
    // kendi bölüm başlığı altında yeniden gruplanır. Bu; öğretmenin serbestçe
    // sıralamasına izin verirken bölüm etiketini bilgi amaçlı tutar.
    blokListesiRenderEt();
  }

  function blokSil(blokId) {
    const onay = confirm(
      "Bu bloğu listeden kaldırmak istediğinize emin misiniz?\n\n" +
        "Not: Blok tamamen silinmez, arşivde saklanır ve istenirse ileride tekrar eklenebilir."
    );
    if (!onay) return;
    state.duzenle.akis = state.duzenle.akis.filter((b) => b.id !== blokId);
    blokListesiRenderEt();
    bildirimGoster('Blok listeden kaldırıldı. Kalıcı olması için "Sıralamayı Kaydet" butonuna basın.');
  }

  el("#btn-duzenle-anasayfa").addEventListener("click", () => gotoView("anasayfa"));

  el("#btn-duzenle-kaydet").addEventListener("click", async () => {
    const temaId = state.duzenle.temaId;
    if (!temaId) return;
    try {
      // PATCH gövdesi backend'de SAYFA/GRUP yapılı bekleniyor: {akis:[{sayfa,bloklar:[id...]}]}.
      // GET /bloklar bunu zaten düzleştirip verdiği için (grup sınırları bilgisi
      // kaybolmuş durumda) burada TÜM sırayı TEK bir grupta gönderiyoruz — id
      // kümesi/sırası korunduğu sürece blocks.manifest_patch bunu kabul eder
      // (yalnızca id varlığı ve tekrarsızlığı doğrular).
      const tekGrupAkis = [{ sayfa: 1, bloklar: state.duzenle.akis.map((b) => b.id) }];
      await api.manifestGuncelle(temaId, tekGrupAkis);
      bildirimGoster("Sıralama kaydedildi.", "basari");
    } catch (err) {
      bildirimGoster("Kaydedilemedi: " + err.message, "hata");
    }
  });

  el("#btn-duzenle-uret").addEventListener("click", async () => {
    const temaId = state.duzenle.temaId;
    if (!temaId) return;
    const panel = el("#duzenle-uretim-paneli");
    panel.hidden = false;
    el("#duzenle-uretim-log").innerHTML = "";
    el("#duzenle-uretim-cubuk").classList.remove("belirsiz");
    el("#duzenle-uretim-cubuk").style.width = "0%";
    el("#duzenle-uretim-yuzde").textContent = "%0";
    el("#duzenle-uretim-durum").textContent = "İş kuyruğa alınıyor…";
    el("#duzenle-uretim-sonuc").hidden = true;
    panel.scrollIntoView({ behavior: "smooth", block: "nearest" });

    try {
      const sonuc = await api.uret(temaId, {});
      jobIzle(sonuc.job_id, {
        guncelle(veri) {
          ilerlemeCubuguGuncelle(el("#duzenle-uretim-cubuk"), el("#duzenle-uretim-yuzde"), veri);
          el("#duzenle-uretim-durum").textContent = jobDurumMetni(veri);
          if (veri.loglar) logPaneliDoldur(el("#duzenle-uretim-log"), veri.loglar);
        },
        bitti(veri) {
          if (veri.durum === "tamam") {
            el("#duzenle-uretim-durum").textContent = "Yeniden üretim tamamlandı.";
            const s = veri.sonuc || {};
            const pdfYolu = s.kopya || s.cikti_pdf;
            if (pdfYolu) {
              pdfEmbedYukle(el("#duzenle-uretim-embed"), pdfYolu);
              sonPdfYoluKaydet(temaId, pdfYolu);
            }
            const dogrulamaKutu = el("#duzenle-uretim-dogrulama");
            if (dogrulamaKutu) {
              dogrulamaKutu.innerHTML = "";
              dogrulamaKutu.appendChild(dogrulamaPaneliOlustur(s.dogrulama));
            }
            el("#duzenle-uretim-sonuc").hidden = false;
            bildirimGoster("Yeni PDF üretildi.", "basari");
          } else {
            el("#duzenle-uretim-durum").textContent = "Üretim hata ile sonuçlandı: " + (veri.hata || "");
            bildirimGoster("Yeniden üretim başarısız oldu.", "hata");
          }
        },
      });
    } catch (err) {
      el("#duzenle-uretim-durum").textContent = "Başlatılamadı: " + err.message;
      bildirimGoster("Yeniden üretim başlatılamadı: " + err.message, "hata");
    }
  });

  el("#btn-yeni-blok-ekle").addEventListener("click", async () => {
    const temaId = state.duzenle.temaId;
    if (!temaId) return;
    const tur = el("#yeni-blok-tur").value;
    const metin = el("#yeni-blok-metin").value.trim();
    if (!metin) {
      bildirimGoster("Lütfen blok içeriğini yazın.", "hata");
      return;
    }
    try {
      // konum: null -> backend son gruba ekler (blocks.blok_ekle varsayılan davranışı).
      await api.blokEkle(temaId, { sinif: tur, html_govde: metin, konum: null });
      el("#yeni-blok-metin").value = "";
      bildirimGoster("Blok eklendi (listenin sonunda).", "basari");
      const veri = await api.bloklar(temaId);
      state.duzenle.akis = veri.bloklar || [];
      blokListesiRenderEt();
    } catch (err) {
      bildirimGoster("Blok eklenemedi: " + err.message, "hata");
    }
  });

  // ---- Serbest talep kutusu ----

  function talepAnahtari(temaId) {
    return "th_talepler_" + temaId;
  }

  function talepleriOku(temaId) {
    try {
      return JSON.parse(localStorage.getItem(talepAnahtari(temaId)) || "[]");
    } catch (e) {
      return [];
    }
  }

  function talepleriYaz(temaId, liste) {
    localStorage.setItem(talepAnahtari(temaId), JSON.stringify(liste));
  }

  function talepListesiRenderEt(temaId) {
    const ul = el("#talep-listesi");
    const talepler = talepleriOku(temaId);
    ul.innerHTML = "";
    if (!talepler.length) {
      ul.innerHTML = '<li class="yukleniyor-metni" style="padding:6px 0;">Henüz gönderilmiş bir talep yok.</li>';
      return;
    }
    talepler
      .slice()
      .reverse()
      .forEach((t) => {
        const li = document.createElement("li");
        li.className = "talep-ogesi";
        li.innerHTML = `<span class="talep-ogesi__metin">${kacisliMetin(t.metin)}</span><span class="durum-rozeti">${kacisliMetin(
          t.durum || "kuyrukta"
        )}</span>`;
        ul.appendChild(li);
      });
  }

  el("#btn-talep-gonder").addEventListener("click", async () => {
    const temaId = state.duzenle.temaId;
    if (!temaId) return;
    const metin = el("#serbest-talep-metin").value.trim();
    if (!metin) {
      bildirimGoster("Lütfen talebinizi yazın.", "hata");
      return;
    }
    try {
      const sonuc = await api.istekGonder(temaId, metin);
      const talepler = talepleriOku(temaId);
      talepler.push({ id: (sonuc && sonuc.id) || Date.now(), metin, durum: (sonuc && sonuc.durum) || "kuyrukta" });
      talepleriYaz(temaId, talepler);
      talepListesiRenderEt(temaId);
      el("#serbest-talep-metin").value = "";
      bildirimGoster("Talebiniz ajanlara iletildi.", "basari");
    } catch (err) {
      bildirimGoster("Talep gönderilemedi: " + err.message, "hata");
    }
  });

  // ================= AYARLAR =================

  async function ayarlarEkraniYukle() {
    try {
      const veri = await api.ayarlarGetir();
      state.ayarlar = veri;
      el("#ayar-giris-klasoru").value = veri.giris_klasoru || "";
      el("#ayar-cikti-klasoru").value = veri.cikti_klasoru || "";
    } catch (err) {
      bildirimGoster("Ayarlar alınamadı: " + err.message, "hata");
    }
  }

  el("#btn-ayar-giris-sec").addEventListener("click", () => {
    klasorGezginiAc({
      baslik: "Varsayılan Giriş Klasörü Seç",
      mod: "dizin",
      baslangicYolu: el("#ayar-giris-klasoru").value || null,
      onSecim: (yol) => (el("#ayar-giris-klasoru").value = yol),
    });
  });
  el("#btn-ayar-cikti-sec").addEventListener("click", () => {
    klasorGezginiAc({
      baslik: "Varsayılan Çıktı Klasörü Seç",
      mod: "dizin",
      baslangicYolu: el("#ayar-cikti-klasoru").value || null,
      onSecim: (yol) => (el("#ayar-cikti-klasoru").value = yol),
    });
  });
  el("#btn-ayarlar-kaydet").addEventListener("click", async () => {
    try {
      const veri = await api.ayarlarKaydet({
        giris_klasoru: el("#ayar-giris-klasoru").value,
        cikti_klasoru: el("#ayar-cikti-klasoru").value,
      });
      state.ayarlar = veri;
      bildirimGoster("Ayarlar kaydedildi.", "basari");
    } catch (err) {
      bildirimGoster("Ayarlar kaydedilemedi: " + err.message, "hata");
    }
  });

  // ================= BAŞLANGIÇ =================

  if (new URLSearchParams(location.search).get("mock") === "1") {
    const rozet = el("#mock-rozeti");
    if (rozet) rozet.hidden = false;
  }

  (async function baslat() {
    try {
      state.ayarlar = await api.ayarlarGetir();
    } catch (err) {
      /* ayarlar alınamazsa sihirbaz varsayılansız devam eder */
    }
    gotoView("landing");
  })();
})();
