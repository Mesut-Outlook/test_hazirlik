# Test Hazırlık — Matematik Testi Yeniden Düzenleme Hattı

Karışık kaynaklı matematik test PDF'lerini (taranmış sayfalar + yayınevi sayfaları)
**tek tip, temiz, soru düzeyinde düzenlenebilir** bir formata dönüştüren sistem.
İlk ürün: 9. sınıf 1. tema (Üslü/Köklü Sayılar, Gerçek Sayılar) —
`cikti/1.tema_egemen_sarikci_v3.pdf` (177 sayfa).

## Ne yapar?

Kaynak PDF'teki her soru, teori kutusu, görsel ve cevap anahtarı çıkarılır ve
kalıcı kimlikli HTML bloklarına dönüştürülür. Belge tek bir CSS sözleşmesiyle
yeniden dizilir ve PDF olarak basılır:

- **Tek tip görünüm**: Comic Sans MS (kaynaktan çıkarılan gömülü subset), iki
  sütunlu akış, sol üstte ES logosu, sayfa numarası.
- **Sayfa tasarımı**: sorular arası ince ayraç çizgileri, sütunlar arası dikey
  çizgi, her sorudan sonra en az 30mm çözüm boşluğu.
- **Bitişik kök tekniği (`.rt`)**: √ font glifi yerine yüksekliğe göre esneyen
  SVG çengel + bitişik üst çizgi — kök işareti hiçbir zaman kopuk/kırık çıkmaz.
- **İçerik kuralları**: matematik birebir korunur (tahmin yok); yayınevi
  "1.KUR/2.KUR" rozetleri atılır ama gerçek bölüm adları (ISINMA HAREKETLERİ,
  PİST ALANI…) ve "2023 TYT Kurgusu" tipi etiketler korunur; tablolar/şekiller
  görsel olarak kırpılıp yerleştirilir.
- **Soru düzeyinde düzenlenebilirlik**: soru silmek/taşımak/eklemek için PDF'e
  değil, `manifest.json` + `sorular.html` dosyalarına dokunulur.
- **Sınır**: otomatik dönüştürme yalnızca **metin tabanlı** (yazısı seçilebilen)
  PDF/Word belgelerde çalışır ve internet gerektirmez. Taranmış/fotoğraf
  belgeler otomatik dönüştürülmez — bunlar için sayfalar görüntüye çevrilip
  ajanlarla aktarım yapılır (SISTEM.md §4; ihtiyaç olursa arayüze "ajan aktarım
  kuyruğu" olarak eklenebilir). Arayüz ana sayfasında da bu not görünür.

## Nasıl çalışır? (boru hattı)

```
kaynak.pdf ──► sistem/extract.py ──► temalar/NN-ad/
                                       ├── sorular.html    (id'li bloklar)
                                       ├── manifest.json   (basım sırası/iskelet)
                                       └── assets/*.png    (kırpılmış görseller)
                    │
                    ▼
        sistem/assemble.py  (manifest + sorular.html → 1tema.html)
                    │
                    ▼
        sistem/print.mjs    (Chrome/puppeteer-core → cikti/…_vN.pdf;
                             logo header + sayfa no footer)
```

Doğrulama her üretimde zorunludur (`SISTEM.md` §6): pdftotext metin bütünlüğü,
anahtar ifade sayımları, görsel sayımı, blok-tekrar taraması, örneklemli göz
kontrolü (`qa/dogrula.py`, `qa/compare.py`).

## Klasör yapısı

```
test_hazirlik/
├── SISTEM.md            ← kural kitabı (anayasa) — yeni işe başlamadan önce oku
├── COORDINATION.md      ← canlı görev panosu / çok-ajanlı koordinasyon + günlük
├── CLAUDE.md            ← ajan oturumları için güncel durum özeti
├── sistem/              ← temadan bağımsız motor (tek kopya)
│   ├── extract.py       kaynak PDF → bloklar + manifest + görseller
│   ├── assemble.py      manifest + sorular.html → basılabilir HTML
│   ├── print.mjs        HTML → PDF (puppeteer-core + google-chrome-stable)
│   ├── flow.css         görünüm sözleşmesi (.rt kök, .frac, .question, ayraçlar…)
│   ├── fonts/           gömülü Comic Sans / Cambria Math subset'leri
│   └── logo_es.jpg
├── temalar/01-tema/     ← tema başına bir klasör (kaynak, bloklar, log)
├── cikti/               ← versiyonlu PDF çıktıları (üzerine yazılmaz)
└── qa/                  ← doğrulama/karşılaştırma araçları
```

## Sık işlemler

```bash
# Yeniden basım (düzenleme sonrası):
python3 sistem/assemble.py temalar/01-tema/manifest.json \
        temalar/01-tema/sorular.html ../../sistem/flow.css temalar/01-tema/1tema.html
node sistem/print.mjs temalar/01-tema/1tema.html cikti/1.tema_egemen_sarikci_v4.pdf

# Soru çıkarmak  = manifest.json'dan id satırını silmek (blok arşivde kalır)
# Sıra değiştirmek = manifest.json'da id'yi taşımak
# Soru eklemek   = sorular.html'e yeni <section> + manifest'e id yazmak
#                  (id MUTLAKA tNN-eNNN ek serisinden; son: t01-e002 —
#                   mevcut id kullanmak içerik kaybettirir, assemble.py hata verir)
```

**Önemli:** Onaylanmış bir tema için `extract.py` bir daha ÇALIŞTIRILMAZ
(id'leri yeniden üretir). Orijinal kaynak PDF'lere asla dokunulmaz.

## Gereksinimler

Linux + `google-chrome-stable`, `node` (puppeteer-core), Python 3 (pymupdf,
pillow), poppler (`pdftoppm`, `pdftotext`). Word kaynakları için (yol
haritasında) LibreOffice headless.

## Çok-ajanlı çalışma modeli

İş bölümü `COORDINATION.md` görev panosundan yürür:

- **Fable (ana oturum)**: planlama, şartname, hakemlik — her ajan raporu
  örneklemli çapraz kontrolden geçer.
- **Claude-Sonnet alt-ajanları**: kod yazımı, toplu dönüşüm, QA.
- **AGY (Antigravity)**: büyük düzeltme turları ve QA dilimleri — görevleri
  panodan alır, durumu kendisi günceller.

Kurallar: görev almadan önce panoyu TEKRAR oku (çakışma önlemi), her koşu
`temalar/NN/log/runs.jsonl`'e loglanır, her önemli aşama commit + push edilir.

## Yerel Web Arayüzü (Arayüz)

Hattı kod bilmeyen kullanıcılar için yerel bir web arayüzü sunulmaktadır. Kullanıcı bilgisayarından bir PDF veya Word dosyası (.docx/.doc) seçer, dönüştürme arka planda koşar, canlı ilerleme durumu gösterilir, sorular/bloklar ön yüzde sürükle-bırak yöntemiyle sıralanabilir, silinebilir veya yeni bloklar eklenebilir. Sonuç PDF'leri basılarak ön izleme alanında görüntülenebilir.

### Başlatma

Arayüzü başlatmak için proje kök dizininde şu komutu çalıştırın:

```bash
bash arayuz/calistir.sh
```

Arayüz otomatik olarak varsayılan tarayıcınızda `http://127.0.0.1:8756` adresinde açılacaktır.

### Özellikler

- **PDF & Word (.docx/.doc) Desteği**: Word belgesi seçildiğinde arka planda LibreOffice headless (`soffice`) ile PDF'e dönüştürülür ve otomatik işlenir.
- **Yayınevi Profilleri**: Dönüşüm sırasında kullanılacak bilinen başlık ve renk profilleri (örn: `sistem/profiller/metin_yayinlari.json`) seçilebilir.
- **Sürükle-Bırak Editör**: Soru ve bölümlerin yerleşimi ve sırası canlı olarak değiştirilebilir.
- **Canlı Job Kuyruğu & SSE**: Extract ve Print (PDF Üretim) işleri arka planda asenkron çalışır; loglar ve ilerleme canlı olarak arayüzde gösterilir.
- **Entegre Doğrulama**: Basılan her yeni PDF sürümünden sonra `qa/dogrula.py` otomatik olarak çalıştırılarak sonuçları ön yüzde listeler.
- **Serbest İstek Kutusu**: Yapay zekadan istenecek ek sadakat ve tasarım düzenlemeleri arayüzden istek olarak gönderilebilir.

## Sürüm geçmişi (özet)

- **v1–v2 (FAZ 1-2, Windows)**: 117 sayfalık kaynak 18 parçada transkribe edildi;
  logo header, `.rad` karekök yaması.
- **v3 (FAZ 3, Linux)**: v2'den tam yeniden kurulum — `.rt` bitişik kök, gömülü
  fontlar, soru-düzeyi manifest sistemi, yeni sayfa tasarımı, 4 tur QA + çapraz
  doğrulama. Ayrıntılı değişiklik günlüğü `COORDINATION.md`'dedir.
