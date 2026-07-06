"use strict";
/* ============================================================
   mock.js — Test Hazırlık Arayüzü SAHTE (mock) veri katmanı
   ============================================================
   Yalnızca URL'de ?mock=1 varsa devreye girer. window.fetch ve
   window.EventSource'u sarmalayarak arayuz/backend/ olmadan da
   arayuz/web/ tamamen gezilebilir/test edilebilir olsun diye yazıldı.
   ?mock=1 verilmediği sürece hiçbir şeye dokunmaz.

   ÖNEMLİ: Bu dosya arayuz/backend/'in (F1, Claude-Sonnet #9) GERÇEK
   kodu (fs_api.py, temalar_api.py, blocks.py, jobs.py, jobs_api.py)
   okunarak, aynı yanıt şekillerini taklit edecek şekilde hizalandı
   (2026-07-06, F2). Özellikle:
     - GET /api/temalar DÜZ dizi döner, PDF yolu İÇERMEZ.
     - POST /api/temalar işi SADECE extract'i simüle eder (PDF yok);
       PDF için ayrıca /uret gerekir (app.js bunu zinciriyor).
     - Job gövdesinde ilerleme yüzdesi / mesaj YOK, SSE İSİMLİ olaylar
       kullanır ("log" tekil satır, "durum" tam anlık — sadece bitişte).
   ============================================================ */

(function () {
  const params = new URLSearchParams(location.search);
  if (params.get("mock") !== "1") return;

  console.info("[mock] Sahte API modu aktif — gerçek backend çağrılmıyor.");

  const gecikme = (min, max) => new Promise((r) => setTimeout(r, min + Math.random() * (max - min)));

  // ---------------- Gömülü yer tutucu PDF (tek sayfa, ~800 bayt) ----------------

  const YER_TUTUCU_PDF_B64 =
    "JVBERi0xLjQKMSAwIG9iago8PCAvVHlwZSAvQ2F0YWxvZyAvUGFnZXMgMiAwIFIgPj4KZW5kb2JqCjIgMCBvYmoKPDwgL1R5cGUgL1BhZ2VzIC9LaWRzIFszIDAgUl0gL0NvdW50IDEgPj4KZW5kb2JqCjMgMCBvYmoKPDwgL1R5cGUgL1BhZ2UgL1BhcmVudCAyIDAgUiAvTWVkaWFCb3ggWzAgMCA1OTUgODQyXSAvUmVzb3VyY2VzIDw8IC9Gb250IDw8IC9GMSA0IDAgUiA+PiA+PiAvQ29udGVudHMgNSAwIFIgPj4KZW5kb2JqCjQgMCBvYmoKPDwgL1R5cGUgL0ZvbnQgL1N1YnR5cGUgL1R5cGUxIC9CYXNlRm9udCAvSGVsdmV0aWNhID4+CmVuZG9iago1IDAgb2JqCjw8IC9MZW5ndGggMjU5ID4+CnN0cmVhbQpCVCAvRjEgMjQgVGYgOTAgNzYwIFRkIChNb2NrIE9uaXpsZW1lIFBERiAtLSBFZ2VtZW4gU2FyaWtjaSkgVGogRVQKQlQgL0YxIDE0IFRmIDkwIDcyMCBUZCAoQnUsIGFyYXl1eiBnZWxpc3Rpcm1lc2kgaWNpbiBzYWh0ZSAobW9jaykgYmlyIFBERiBvbml6bGVtZXNpZGlyLikgVGogRVQKQlQgL0YxIDE0IFRmIDkwIDcwMCBUZCAoR2VyY2VrIGJhY2tlbmQgYmFnbGFuZGlnaW5kYSBidXJhZGEgZ2VyY2VrIGNpa3RpIFBERidpIGdvcnVuZWNlay4pIFRqIEVUCmVuZHN0cmVhbQplbmRvYmoKeHJlZgowIDYKMDAwMDAwMDAwMCA2NTUzNSBmIAowMDAwMDAwMDA5IDAwMDAwIG4gCjAwMDAwMDAwNTggMDAwMDAgbiAKMDAwMDAwMDExNSAwMDAwMCBuIAowMDAwMDAwMjQxIDAwMDAwIG4gCjAwMDAwMDAzMTEgMDAwMDAgbiAKdHJhaWxlcgo8PCAvU2l6ZSA2IC9Sb290IDEgMCBSID4+CnN0YXJ0eHJlZgo2MjEKJSVFT0Y=";

  function base64ToBytes(b64) {
    const ikili = atob(b64);
    const bayt = new Uint8Array(ikili.length);
    for (let i = 0; i < ikili.length; i++) bayt[i] = ikili.charCodeAt(i);
    return bayt;
  }

  // ---------------- Sahte dosya sistemi (ev dizini altı) ----------------
  // fs_api.py ile aynı alan adları: path, ust_dizin, tur:'dir'|'dosya'.

  const EV_DIZINI = "/home/kullanici";

  const FAKE_FS = {
    "/home/kullanici": [
      { ad: "Belgeler", tur: "dir" },
      { ad: "Masaüstü", tur: "dir" },
      { ad: "İndirilenler", tur: "dir" },
    ],
    "/home/kullanici/Belgeler": [
      { ad: "Ders Notları", tur: "dir" },
      { ad: "Çıktılar", tur: "dir" },
      { ad: "1.tema.pdf", tur: "dosya" },
      { ad: "2.tema_taslak.docx", tur: "dosya" },
      { ad: "notlar.txt", tur: "dosya" },
    ],
    "/home/kullanici/Belgeler/Ders Notları": [
      { ad: "9.sinif-fonksiyonlar.pdf", tur: "dosya" },
      { ad: "9.sinif-denklemler.docx", tur: "dosya" },
      { ad: "eski-taramalar.pdf", tur: "dosya" },
    ],
    "/home/kullanici/Belgeler/Çıktılar": [],
    "/home/kullanici/Masaüstü": [{ ad: "taslak-test.pdf", tur: "dosya" }],
    "/home/kullanici/İndirilenler": [],
  };

  function ustDizinHesapla(yol) {
    if (!yol || yol === EV_DIZINI) return null;
    const parcalar = yol.split("/");
    parcalar.pop();
    const ust = parcalar.join("/") || "/";
    return ust.length < EV_DIZINI.length ? null : ust;
  }

  function fsListele(yol, sadece) {
    const gercekYol = yol || EV_DIZINI;
    const girdilerHam = FAKE_FS[gercekYol] || [];
    const parcalar = (sadece || "").split(",").map((s) => s.trim().toLowerCase());
    const sadeceDizin = parcalar.includes("dir");
    const uzantilar = parcalar.filter((p) => p !== "dir");

    const girdiler = girdilerHam
      .filter((g) => {
        if (g.tur === "dir") return true;
        if (sadeceDizin) return false;
        if (!uzantilar.length) return true;
        const uzanti = g.ad.includes(".") ? g.ad.split(".").pop().toLowerCase() : "";
        return uzantilar.includes(uzanti);
      })
      .sort((a, b) => {
        if (a.tur !== b.tur) return a.tur === "dir" ? -1 : 1;
        return a.ad.localeCompare(b.ad, "tr");
      })
      .map((g) => ({ ad: g.ad, tur: g.tur, yol: gercekYol.replace(/\/$/, "") + "/" + g.ad }));

    return { path: gercekYol, ust_dizin: ustDizinHesapla(gercekYol), girdiler };
  }

  // ---------------- Sahte veri deposu ----------------

  const BILINEN_SINIFLAR = ["question", "theory-box", "kur-tag", "answer-key", "img-block", "para", "section-sub"];

  function ozetCikar(html, uzunluk) {
    const duz = String(html || "").replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
    return duz.slice(0, uzunluk || 80);
  }

  function blokUret(id, sinif, bolumUzun, ozet, sayfa) {
    return { id, sinif, bolum: bolumUzun, ozet, kaynak_sayfa: sayfa };
  }

  const DB = {
    ayarlar: {
      giris_klasoru: "/home/kullanici/Belgeler",
      cikti_klasoru: "/home/kullanici/Belgeler/Çıktılar",
    },
    temaSayaci: 2,
    // GET /api/temalar alan adları backend'le birebir: tema_id, ad, durum,
    // surum, soru_sayisi, kok_sayisi, gorsel_sayisi. PDF YOLU KASITLI OLARAK
    // YOK — gerçek backend de vermiyor (app.js'in state.sonPdfYollari
    // yedeğini test etmek için).
    temalar: [
      {
        tema_id: "01-uslu-ve-koklu-sayilar",
        ad: "1. Tema — Üslü ve Köklü Sayılar",
        durum: "hazır",
        surum: 3,
        soru_sayisi: 550,
        kok_sayisi: 612,
        gorsel_sayisi: 136,
      },
      {
        tema_id: "02-fonksiyonlar-taslak",
        ad: "2. Tema — Fonksiyonlar (taslak)",
        durum: "hazır",
        surum: 1,
        soru_sayisi: 6,
        kok_sayisi: 1,
        gorsel_sayisi: 1,
      },
    ],
    bloklarByTema: {
      "01-uslu-ve-koklu-sayilar": [
        blokUret("t01-s001", "kur-tag", "ISINMA HAREKETLERİ", "ISINMA HAREKETLERİ", 9),
        blokUret("t01-s002", "question", "ISINMA HAREKETLERİ", "1) 2³ · 2⁴ işleminin sonucu kaçtır? A) 2⁵ B) 2⁶ C) 2⁷ D) 2⁸", 9),
        blokUret("t01-s003", "question", "ISINMA HAREKETLERİ", "2) (−3)² + (−2)³ ifadesinin değeri nedir?", 9),
        blokUret("t01-s004", "theory-box", "ISINMA HAREKETLERİ", "UYARI: Negatif sayıların çift kuvvetleri her zaman pozitiftir.", 10),
        blokUret("t01-s005", "question", "ISINMA HAREKETLERİ", "3) √36 + √49 toplamının sonucu kaçtır?", 10),
        blokUret("t01-s006", "img-block", "ISINMA HAREKETLERİ", "[Şekil: dik üçgen, kenar uzunlukları verilmiş]", 11),
        blokUret("t01-s007", "kur-tag", "GÜNLÜK HAYAT UYGULAMALARI", "GÜNLÜK HAYAT UYGULAMALARI", 22),
        blokUret("t01-s008", "question", "GÜNLÜK HAYAT UYGULAMALARI", "4) Bir bahçenin alanı 144 m² ise bir kenarı kaç metredir?", 22),
        blokUret("t01-s009", "question", "GÜNLÜK HAYAT UYGULAMALARI", "5) Faiz hesabında üslü ifadeler nasıl kullanılır?", 23),
        blokUret("t01-s010", "kur-tag", "ÖSYM SORULARINA HAZIRLIK", "ÖSYM SORULARINA HAZIRLIK", 25),
        blokUret("t01-s011", "question", "ÖSYM SORULARINA HAZIRLIK", "6) 2020 TYT: √(1 − 11/36) ifadesinin değeri kaçtır?", 25),
        blokUret("t01-s012", "answer-key", "ÖSYM SORULARINA HAZIRLIK", "Cevap Anahtarı: 1.B 2.A 3.C 4.D 5.B 6.C", 26),
      ],
      "02-fonksiyonlar-taslak": [
        blokUret("t02-s001", "kur-tag", "FONKSİYON KAVRAMI", "FONKSİYON KAVRAMI", 1),
        blokUret("t02-s002", "question", "FONKSİYON KAVRAMI", "1) f(x) = 2x + 3 fonksiyonunda f(5) kaçtır?", 1),
        blokUret("t02-s003", "question", "FONKSİYON KAVRAMI", "2) Bir fonksiyonun tanım kümesi nedir, örnek veriniz.", 2),
        blokUret("t02-s004", "theory-box", "FONKSİYON KAVRAMI", "TANIM: Fonksiyon, bir kümenin her elemanını başka bir kümenin tam olarak bir elemanına eşler.", 2),
        blokUret("t02-s005", "img-block", "FONKSİYON KAVRAMI", "[Şekil: fonksiyon diyagramı, A kümesinden B kümesine oklar]", 3),
        blokUret("t02-s006", "question", "FONKSİYON KAVRAMI", "3) f(x) = x² − 4 fonksiyonunun kökleri nedir?", 3),
      ],
    },
    ekSayaci: { "01-uslu-ve-koklu-sayilar": 2, "02-fonksiyonlar-taslak": 0 },
    jobs: {},
    jobSayaci: 0,
  };

  // job.gorunum() ile aynı alanlar: id, tur, tema_id, durum, loglar, sonuc, hata.
  // İLERLEME YÜZDESİ / MESAJ ALANI YOK (gerçek backend de vermiyor).
  function jobUret(tur, temaId, adimlar, sonucUretici) {
    const id = "j-mock-" + ++DB.jobSayaci;
    const is_ = { id, tur, tema_id: temaId, durum: "çalışıyor", loglar: [], sonuc: {}, hata: null };
    DB.jobs[id] = is_;

    let idx = 0;
    const tikla = () => {
      if (idx < adimlar.length) {
        is_.loglar.push(adimlar[idx]);
        idx++;
        setTimeout(tikla, 500 + Math.random() * 450);
      } else {
        try {
          is_.sonuc = sonucUretici();
          is_.durum = "tamam";
        } catch (err) {
          is_.hata = String((err && err.message) || err);
          is_.durum = "hata";
        }
      }
    };
    setTimeout(tikla, 350);
    return id;
  }

  function olusturmaAdimlari(ad) {
    return [
      `Tema oluşturuluyor: ${ad}`,
      "extract.py çalıştırılıyor...",
      "Sayfa yapısı analiz ediliyor, sorular/teori kutuları çıkarılıyor...",
      "Kök/kesir/üs notasyonları dönüştürülüyor...",
      "Görseller kırpılıp yerleştiriliyor...",
    ];
  }

  function uretimAdimlari() {
    return [
      "Manifest okunuyor...",
      "assemble.py çalıştırılıyor...",
      "print.mjs çalıştırılıyor...",
      "qa/dogrula.py çalıştırılıyor...",
    ];
  }

  function sahteDogrulaCiktisi() {
    return [
      "=== qa/dogrula.py (mock) ===",
      "Soru metni bütünlüğü: 120/120 eşleşti",
      '"Kurgusu" etiketleri: 20/20 eşleşti',
      "Görsel sayımı: kaynakla birebir",
      "Çift basım taraması: tekrar bulunamadı",
      "SONUÇ: fark yok.",
    ].join("\n");
  }

  // ---------------- Yanıt yardımcıları ----------------

  function jsonYanit(obj, durumKodu) {
    return new Response(JSON.stringify(obj), {
      status: durumKodu || 200,
      headers: { "Content-Type": "application/json; charset=utf-8" },
    });
  }

  function hataYanit(hata, detay, durumKodu) {
    return jsonYanit({ hata, detay: detay || "" }, durumKodu || 400);
  }

  async function govdeOku(secenekler) {
    if (!secenekler || !secenekler.body) return {};
    try {
      return JSON.parse(secenekler.body);
    } catch (e) {
      return {};
    }
  }

  // ---------------- fetch sarmalayıcı ----------------

  window.fetch = async function (girdi, secenekler) {
    const urlNesnesi = new URL(typeof girdi === "string" ? girdi : girdi.url, location.href);
    const yol = urlNesnesi.pathname;
    const yontem = ((secenekler && secenekler.method) || "GET").toUpperCase();

    await gecikme(150, 420);

    if (yol === "/api/ayarlar" && yontem === "GET") return jsonYanit(DB.ayarlar);
    if (yol === "/api/ayarlar" && yontem === "PUT") {
      const govde = await govdeOku(secenekler);
      DB.ayarlar = { ...DB.ayarlar, ...govde };
      return jsonYanit(DB.ayarlar);
    }

    if (yol === "/api/fs/list" && yontem === "GET") {
      const yolParam = urlNesnesi.searchParams.get("path");
      const sadece = urlNesnesi.searchParams.get("sadece");
      return jsonYanit(fsListele(yolParam, sadece));
    }

    // GET /api/temalar -> DÜZ DİZİ (sarmalayıcı yok), PDF yolu yok.
    if (yol === "/api/temalar" && yontem === "GET") {
      return jsonYanit(DB.temalar);
    }

    // POST /api/temalar -> SADECE extract benzeri işi başlatır, PDF üretmez.
    if (yol === "/api/temalar" && yontem === "POST") {
      const govde = await govdeOku(secenekler);
      if (!govde.kaynak_dosya || !govde.ad || !govde.cikti_klasoru) {
        return hataYanit("eksik alan", "kaynak_dosya, ad ve cikti_klasoru zorunludur.", 422);
      }
      const slug = govde.ad
        .toLowerCase()
        .replace(/ı/g, "i").replace(/ğ/g, "g").replace(/ü/g, "u").replace(/ş/g, "s").replace(/ö/g, "o").replace(/ç/g, "c")
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-+|-+$/g, "");
      const temaId = `${String(++DB.temaSayaci).padStart(2, "0")}-${slug || "tema"}`;

      const yeniTema = { tema_id: temaId, ad: govde.ad, durum: "hazırlanıyor" };
      DB.temalar.push(yeniTema);

      const jobId = jobUret("extract", temaId, olusturmaAdimlari(govde.ad), () => {
        const sayimlar = { soru: 3, kok: 1, gorsel: 1 };
        yeniTema.durum = "hazır";
        yeniTema.surum = 1;
        yeniTema.soru_sayisi = sayimlar.soru;
        yeniTema.kok_sayisi = sayimlar.kok;
        yeniTema.gorsel_sayisi = sayimlar.gorsel;
        DB.bloklarByTema[temaId] = [
          blokUret(`t${temaId.slice(0, 2)}-s001`, "kur-tag", "GİRİŞ", "GİRİŞ", 1),
          blokUret(`t${temaId.slice(0, 2)}-s002`, "question", "GİRİŞ", "1) (mock) Örnek soru metni burada görünecek.", 1),
          blokUret(`t${temaId.slice(0, 2)}-s003`, "question", "GİRİŞ", "2) (mock) İkinci örnek soru metni.", 2),
        ];
        DB.ekSayaci[temaId] = 0;
        return { tema_id: temaId, sayimlar };
      });
      yeniTema.job_id = jobId;
      return jsonYanit({ tema_id: temaId, job_id: jobId });
    }

    // GET /api/jobs/{id}
    let eslesme = yol.match(/^\/api\/jobs\/([^/]+)$/);
    if (eslesme && yontem === "GET") {
      const is_ = DB.jobs[eslesme[1]];
      if (!is_) return hataYanit("iş bulunamadı", eslesme[1], 404);
      return jsonYanit(is_);
    }

    // GET /api/temalar/{id}/bloklar -> {tema_id, bloklar}
    eslesme = yol.match(/^\/api\/temalar\/([^/]+)\/bloklar$/);
    if (eslesme && yontem === "GET") {
      const bloklar = DB.bloklarByTema[eslesme[1]];
      if (!bloklar) return hataYanit("tema bulunamadı", eslesme[1], 404);
      return jsonYanit({ tema_id: eslesme[1], bloklar });
    }

    // POST /api/temalar/{id}/bloklar body: {sinif, html_govde, konum:{sonra_id}|null}
    if (eslesme && yontem === "POST") {
      const temaId = eslesme[1];
      const bloklar = DB.bloklarByTema[temaId];
      if (!bloklar) return hataYanit("tema bulunamadı", temaId, 404);
      const govde = await govdeOku(secenekler);
      if (!BILINEN_SINIFLAR.includes(govde.sinif)) {
        return hataYanit("bilinmeyen sınıf", `'${govde.sinif}' desteklenmiyor, izin verilenler: ${BILINEN_SINIFLAR.join(", ")}`, 400);
      }
      const temaNo = temaId.slice(0, 2);
      const sayac = (DB.ekSayaci[temaId] = (DB.ekSayaci[temaId] || 0) + 1);
      const yeniId = `t${temaNo}-e${String(sayac).padStart(3, "0")}`;
      const referansId = govde.konum && govde.konum.sonra_id;
      const referansBlok = referansId ? bloklar.find((b) => b.id === referansId) : null;
      const bolum = (referansBlok || bloklar[bloklar.length - 1] || {}).bolum || "GENEL";
      const kaynakSayfa = referansBlok ? referansBlok.kaynak_sayfa : "ek";
      const yeniBlok = blokUret(yeniId, govde.sinif, bolum, ozetCikar(govde.html_govde), kaynakSayfa);
      if (referansBlok) {
        bloklar.splice(bloklar.indexOf(referansBlok) + 1, 0, yeniBlok);
      } else {
        bloklar.push(yeniBlok);
      }
      return jsonYanit({ id: yeniId, sinif: govde.sinif, kaynak_sayfa: kaynakSayfa });
    }

    // PATCH /api/temalar/{id}/manifest body: {akis:[{sayfa,bloklar:[id,...]}, ...]}
    eslesme = yol.match(/^\/api\/temalar\/([^/]+)\/manifest$/);
    if (eslesme && yontem === "PATCH") {
      const temaId = eslesme[1];
      const mevcut = DB.bloklarByTema[temaId];
      if (!mevcut) return hataYanit("tema bulunamadı", temaId, 404);
      const govde = await govdeOku(secenekler);
      const haritalama = new Map(mevcut.map((b) => [b.id, b]));
      const yeniIdler = [];
      for (const grup of govde.akis || []) {
        if (!grup || !Array.isArray(grup.bloklar)) {
          return hataYanit("geçersiz akış girdisi", JSON.stringify(grup), 400);
        }
        yeniIdler.push(...grup.bloklar);
      }
      const bilinmeyen = yeniIdler.filter((id) => !haritalama.has(id));
      if (bilinmeyen.length) {
        return hataYanit("bilinmeyen blok id(leri)", bilinmeyen.join(", "), 400);
      }
      DB.bloklarByTema[temaId] = yeniIdler.map((id) => haritalama.get(id));
      return jsonYanit({ akis: govde.akis });
    }

    // POST /api/temalar/{id}/uret -> job.sonuc = {cikti_pdf, kopya, surum, sayimlar, dogrulama}
    eslesme = yol.match(/^\/api\/temalar\/([^/]+)\/uret$/);
    if (eslesme && yontem === "POST") {
      const temaId = eslesme[1];
      const tema = DB.temalar.find((t) => t.tema_id === temaId);
      if (!tema) return hataYanit("tema bulunamadı", temaId, 404);
      const jobId = jobUret("uret", temaId, uretimAdimlari(), () => {
        const surumYeni = (tema.surum || 1) + 1;
        tema.surum = surumYeni;
        const bloklar = DB.bloklarByTema[temaId] || [];
        const sayimlar = {
          soru: bloklar.filter((b) => b.sinif === "question").length,
          kok: 0,
          gorsel: bloklar.filter((b) => b.sinif === "img-block").length,
        };
        tema.soru_sayisi = sayimlar.soru;
        tema.gorsel_sayisi = sayimlar.gorsel;
        const dosyaAdi = tema.ad.replace(/[^A-Za-z0-9._-]+/g, "_") + `_v${surumYeni}.pdf`;
        const ciktiPdf = "/home/kullanici/test_hazirlik-mock/cikti/" + dosyaAdi;
        const kopya = DB.ayarlar.cikti_klasoru.replace(/\/$/, "") + "/" + dosyaAdi;
        return {
          cikti_pdf: ciktiPdf,
          kopya,
          surum: surumYeni,
          sayimlar,
          dogrulama: { calisti: true, cikti: sahteDogrulaCiktisi() },
        };
      });
      return jsonYanit({ tema_id: temaId, job_id: jobId });
    }

    // POST /api/temalar/{id}/istek -> {tema_id, kaydedildi:true}
    eslesme = yol.match(/^\/api\/temalar\/([^/]+)\/istek$/);
    if (eslesme && yontem === "POST") {
      return jsonYanit({ tema_id: eslesme[1], kaydedildi: true });
    }

    // GET /api/pdf
    if (yol === "/api/pdf" && yontem === "GET") {
      const bayt = base64ToBytes(YER_TUTUCU_PDF_B64);
      return new Response(bayt, { status: 200, headers: { "Content-Type": "application/pdf" } });
    }

    console.warn("[mock] Tanımsız uç nokta:", yontem, yol);
    return hataYanit("sahte modda tanımlı olmayan uç nokta", yol, 404);
  };

  // ---------------- Sahte EventSource (SSE) ----------------
  // Gerçek backend gibi İSİMLİ olaylar: "log" (tek satır, JSON string) art arda,
  // "durum" (TAM job gorunumu) sadece tamam/hata olduğunda BİR KEZ.

  window.EventSource = class SahteEventSource {
    constructor(url) {
      this.url = url;
      this._dinleyiciler = { log: [], durum: [], message: [], error: [] };
      this._kapandi = false;
      this._gonderilenLogSayisi = 0;
      const eslesme = String(url).match(/\/api\/jobs\/([^/]+)\/events/);
      this._jobId = eslesme ? eslesme[1] : null;
      this._interval = setInterval(() => this._tikla(), 400);
    }
    _yayinla(tur, veri) {
      const olay = { data: JSON.stringify(veri) };
      (this._dinleyiciler[tur] || []).forEach((cb) => {
        try {
          cb(olay);
        } catch (e) {
          /* dinleyici hatasını yut */
        }
      });
      if (tur === "message" && typeof this.onmessage === "function") this.onmessage(olay);
    }
    _tikla() {
      if (this._kapandi) return;
      const is_ = DB.jobs[this._jobId];
      if (!is_) return;
      while (this._gonderilenLogSayisi < is_.loglar.length) {
        this._yayinla("log", is_.loglar[this._gonderilenLogSayisi]);
        this._gonderilenLogSayisi++;
      }
      if (is_.durum === "tamam" || is_.durum === "hata") {
        this._yayinla("durum", is_);
        this.close();
      }
    }
    addEventListener(tur, geriCagri) {
      if (!this._dinleyiciler[tur]) this._dinleyiciler[tur] = [];
      this._dinleyiciler[tur].push(geriCagri);
    }
    close() {
      this._kapandi = true;
      clearInterval(this._interval);
    }
  };
})();
