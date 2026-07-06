# SİSTEM — Test PDF'lerini Tek Formata Dönüştürme Hattı (kural kitabı)

> Amaç: Kullanıcının verdiği HERHANGİ bir kaynak test PDF'i (1.tema, 2.tema, deneme
> sınavı…) aynı kurallarla, aynı görünümde, **soru düzeyinde düzenlenebilir** tek bir
> formata dönüştürmek; her işlemi loglamak. Bu dosya hattın anayasasıdır — yeni bir
> kaynak dosya geldiğinde önce bu dosya okunur. Güncel görev durumu COORDINATION.md'de.

## 1. Klasör Yapısı

```
test_hazirlik/
├── SISTEM.md                ← bu dosya (kurallar; nadiren değişir)
├── COORDINATION.md          ← canlı görev panosu / ajan koordinasyonu
├── sistem/                  ← TEMADAN BAĞIMSIZ ortak motor (tek kopya)
│   ├── flow.css             sınıf sözleşmesi CSS'i (bkz. §3) — tema fark etmez
│   ├── print.mjs            HTML→PDF (puppeteer-core, logo header + sayfa no footer)
│   ├── assemble.py          manifest.json + sorular.html → final.html
│   ├── extract.py           kaynak PDF → sorular.html + manifest.json + assets/ (içe aktarıcı)
│   ├── fonts/               @font-face fontları (gömülü Comic Sans subset vb.)
│   └── logo_es.jpg
├── temalar/
│   └── NN-ad/               her kaynak PDF için bir klasör (örn. 01-tema)
│       ├── kaynak/          orijinal PDF — SALT OKUNUR, asla değiştirilmez
│       ├── sorular.html     tüm içerik blokları (bkz. §2) — elle düzenlenebilir
│       ├── manifest.json    sıra + bölüm + meta; soru ekle/çıkar/taşı BURADAN yapılır
│       ├── assets/          o temanın görselleri (pNN_qNN_*.png)
│       └── log/             islem_gunlugu.md (insan) + runs.jsonl (makine)
└── cikti/                   üretilen PDF'ler — versiyonlu, ÜZERİNE YAZILMAZ
    └── 1.tema_egemen_sarikci_v3.pdf
```

## 2. İçerik Formatı — soru düzeyinde düzenlenebilirlik

`sorular.html` gövdesi sıralı bloklardan oluşur; her blok **kalıcı kimlikli** bir
`<section>`'dır:

```html
<section class="question" id="t01-s042" data-kaynak-sayfa="53">
  <span class="qnum">12.</span> <span class="frac">…</span> işleminin sonucu kaçtır?
  <div class="opts">A) … B) … C) … D) … E) …</div>
  <div class="solve-space"></div>
</section>
```

- Kimlik şeması: `tNN-sNNN` (tema no + soru sırası, üretimde bir kez verilir, sonra
  ASLA değişmez — yeni soru eklerken aradaki sayıya sıkıştırma yok, sona ekle:
  elle eklenen sorular `tNN-eNNN` ("e"=ek) serisinden gider).
  **UYARI (FAZ 3 dersi, 2026-07-05):** elle blok eklerken MEVCUT bir id'yi kullanmak
  assemble aşamasında sessiz içerik kaybı yaratır (aynı id'li son blok kazanır, öbür
  konumlara da o basılır). `sistem/assemble.py` bu yüzden mükerrer id görürse HATA
  verip durur (exit 2) — id vermeden önce `grep 'id="tNN-' sorular.html` ile son
  kullanılan numaraya bak. 01-tema'da son ek id: `t01-e002`.
- **ID DONDURMA:** bir temanın üretimi kullanıcı onayına ulaştıktan sonra o tema için
  `extract.py` bir daha ÇALIŞTIRILMAZ (id'leri baştan üretir, kalıcılığı bozar);
  her düzeltme sorular.html + manifest.json üzerinden yapılır.
- Soru dışı bloklar da aynı düzende: `class="theory-box"`, `class="kur-tag"`,
  `class="answer-key"`, `class="img-block"` — hepsi id'li.
- `manifest.json` belgenin İSKELETİDİR: hangi blokların hangi sırayla basılacağı.
  **Soru çıkarmak = manifest'ten satırını silmek** (blok sorular.html'de kalır → arşiv).
  **Sıra değiştirmek = manifest'te satırı taşımak.** **Soru eklemek = sorular.html'e
  yeni section + manifest'e id yazmak.** sorular.html'e dokunmadan belge kurgulanabilir.

```json
{
  "tema": "01", "baslik": "1. TEMA", "surum": 3,
  "font": "Comic Sans MS Embedded",
  "akis": [
    {"bolum": "ÜSLÜ SAYILAR — ISINMA HAREKETLERİ",
     "bloklar": ["t01-k001", "t01-t001", "t01-s001", "t01-s002"]}
  ]
}
```

## 3. Görünüm Sözleşmesi (tek format)

Tüm temalar aynı `sistem/flow.css`'i kullanır. Çekirdek sınıflar:

- `.page-flow` (iki sütun), `.question` (`break-inside:avoid`), `.qnum`, `.opts`
- **Matematik**: `.rt` / `.rt[data-n]` (bitişik kök — SVG çengel + bitişik şerit; √
  karakteri KULLANILMAZ), `.sup`, `.sub`, `.frac > .num/.den`. Referans uygulama:
  depo kökündeki `kok_bitisik_ornek.html` (kullanıcı onaylı, 2026-07-04).
- `.theory-box`, `.kur-tag`, `.tag-kurgusu`, `.answer-key`, `.solve-space` (min 26mm),
  `.img-block`
- Header: SADECE logo (yazı yok), footer: sayfa numarası — print.mjs verir.
- İçerik kuralları (değişmez): matematik birebir korunur (tahmin yok); yayınevi KUR
  rozetleri atılır, gerçek bölüm adları korunur; "2020 MSÜ Kurgusu" tipi etiketler
  içeriktir, korunur; her sorudan sonra çözüm boşluğu.

## 4. Yeni Kaynak PDF Geldiğinde İş Akışı

1. `temalar/NN-ad/kaynak/` içine kopyala (orijinal neredeyse oradan da SİLME).
2. `sistem/extract.py` çalıştır → sorular.html + manifest.json + assets/ + rapor.
   - Kaynak taranmış görüntüyse (metin katmanı yoksa): sayfalar 200dpi PNG'ye çevrilir,
     transkripsiyon ajanlarla yapılır (FAZ 1-2'deki AGENT_INSTRUCTIONS yöntemi); ajan
     çıktısı yine §2 formatında blok üretir. extract.py yalnızca metin katmanlı PDF'lerde
     tam otomatiktir.
3. Doğrulama (§6) → `sistem/assemble.py` → `sistem/print.mjs` → `cikti/…_vN.pdf`.
4. Log yaz (§5), COORDINATION.md panosunu güncelle, git commit at.
5. İş bölümü: planlama/denetim Fable (ana oturum), kod ve toplu dönüşüm Sonnet
   alt-ajanları, görsel QA Sonnet + AGY (Antigravity, COORDINATION.md üzerinden).

## 5. Loglama

Her çalıştırma iki yere yazar:

- `temalar/NN-ad/log/runs.jsonl` (makine; satır başına bir koşu):
  `{"ts":"2026-07-04T22:40+02:00","islem":"extract|assemble|print|qa|duzeltme",
    "girdi":"…","cikti":"…","sayfa":135,"soru":412,"kok":830,"gorsel":71,
    "dogrulama":"ok|UYARI: …","sha256":"…","ajan":"Claude-Sonnet #1"}`
- `temalar/NN-ad/log/islem_gunlugu.md` (insan; tarih + 1-3 satır özet + bilinen
  eksikler). Soru ekleme/çıkarma gibi elle müdahaleler de buraya işlenir.

## 6. Doğrulama Standardı (her üretimde zorunlu)

1. **Metin bütünlüğü**: kaynak ve çıktı PDF'e `pdftotext`, normalize edip diff —
   kayıp satır sıfır olmalı (√ karakterinin kaybı beklenen tek farktır, §3 gereği).
2. **Görsel sayımı**: kaynaktaki gömülü/kırpılmış görsel sayısı = çıktıdaki `<img>` sayısı.
3. **Görsel QA**: kök/kesir-yoğun sayfalar + rastgele örneklem PNG'ye çevrilip ucuz
   modelli ajanlarca kaynakla karşılaştırılır; bulgular COORDINATION.md'ye yazılır.
4. Çıktı adı `…_vN.pdf` — bir öncekinin üzerine ASLA yazılmaz; onaydan sonra eski
   sürüm silinebilir (kullanıcı kararı).
5. **Sayfa eşlemesi** (FAZ 3 dersi): akan HTML yeniden sayfalandığı için çıktı sayfa
   sayısı kaynaktan farklı olabilir — görsel QA, aynı numaralı sayfaları değil, içerik
   çapasıyla (pdftotext'te ayırt edici dize arayarak) eşlenen sayfaları karşılaştırır.
   Sayfalama farkının kendisi bulgu DEĞİLDİR; soru sırası + içerik bütünlüğü esastır.
6. **Anahtar ifade sayımı** (FAZ 3 dersi): bölüm başlıkları ("ISINMA HAREKETLERİ",
   "PİST ALANI"…), "Kurgusu" etiketleri ve "işleminin sonucu kaçtır" gibi kritik
   ifadelerin kaynak↔çıktı adet EŞİTLİĞİ otomatik kontrol edilir (örnek uygulama:
   `build_linux/qa/dogrula.py`; CSS text-transform büyük harfe çevirebilir,
   karşılaştırmayı buna dayanıklı yap).
7. **Blok tekrarı taraması** (FAZ 3 dersi — bilinen tuzak): Chrome, tek sürekli
   çok-sütunlu (multicol) akışta `break-inside:avoid`'lu büyük blokları (tablo, görselli
   soru) sayfa/sütun sınırında ÇİFT BASABİLİR. Her üretimde pdftotext çıktısında ardışık
   yinelenen ≥2 satırlık bloklar taranmalı; görsel QA sayfa geçişlerine ayrıca bakmalı.

## 7. Sürümleme

- Her başarılı üretim `manifest.json` içindeki `surum` sayısını artırır ve çıktı adına yansır.
- Her üretim sonrası git commit (mesajda: tema, sürüm, koşu özeti). PDF'ler büyükse ve
  depo şişerse yalnızca son 2 sürüm depoda tutulur (eski sürümler commit geçmişinde zaten var).
