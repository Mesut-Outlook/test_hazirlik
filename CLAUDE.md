# Proje: 9. Sınıf Matematik PDF Yeniden Düzenleme (1.tema.pdf)

> **GÜNCEL DURUM (2026-07-05, FAZ 3 — Linux):** Proje kullanıcının Linux (CachyOS)
> makinesine taşındı; depo `/home/mesuto/Documents/PROJELER/test_hazirlik/` (GitHub:
> Mesut-Outlook/test_hazirlik). Bu dosyanın aşağısı FAZ 1-2'nin (Windows) tarihi
> planlama dokümanıdır — Windows yolları artık GEÇERSİZ. Güncel kural kitabı:
> **`SISTEM.md`**, canlı görev panosu ve değişiklik günlüğü: **`COORDINATION.md`**
> (önce bu ikisini oku). Kısa özet:
> - FAZ 1-2 çıktısı: `1.tema_egemen_sarikci_v2.pdf` (135 sayfa; logo sol üstte, header
>   yazısız, karekökler `.rad` yamalı) — bu dosya ve `1.tema_orijinal.pdf` SALT OKUNUR.
> - **FAZ 3 TAMAMLANDI (2026-07-05):** v2'den düzenlenebilir HTML yeniden kuruldu,
>   kökler bitişik kök tekniği `.rt` ile, yeni sayfa tasarımı (soru ayraç çizgileri,
>   sütunlar arası dikey çizgi, 30mm çözüm alanı — örnek: 11.Köklü Sayılar.pdf,
>   sadeleştirilerek). Nihai çıktı: **`cikti/1.tema_egemen_sarikci_v3.pdf`** (177
>   sayfa; kökte kopyası var) — **kullanıcı onayı bekleniyor**.
> - Kalıcı yerleşim aktif (SISTEM.md §1): motor `sistem/` (extract.py, assemble.py,
>   print.mjs, flow.css, fonts), tema `temalar/01-tema/` (sorular.html +
>   manifest.json + assets + log), çıktılar `cikti/`. `build_linux/` tarihe karıştı.
> - **ID'ler DONDURULDU**: 01-tema için extract.py bir daha ÇALIŞTIRILMAZ (id'leri
>   yeniden üretir). Düzeltme/soru ekleme-çıkarma-taşıma `sorular.html` +
>   `manifest.json` üzerinden (SISTEM.md §2); elle eklenen bloklar `t01-eNNN`
>   serisinden id alır — mevcut id kullanmak assemble'da içerik kaybettirir
>   (assemble.py artık mükerrer id'de hata verip durur).
> - Yeniden basım: `python3 sistem/assemble.py temalar/01-tema/manifest.json
>   temalar/01-tema/sorular.html ../../sistem/flow.css temalar/01-tema/1tema.html`
>   sonra `node sistem/print.mjs temalar/01-tema/1tema.html cikti/<ad>.pdf`.
> - İş bölümü: planlama/denetim Fable (ana oturum), kod Sonnet alt-ajanları, QA +
>   büyük düzeltmeler AGY (Antigravity, COORDINATION.md üzerinden). DERS: ajan
>   "tamam/sıfır hata" raporları mutlaka örneklemle çapraz doğrulanır (SISTEM.md §6).
> - Font değişikliği kararı (FAZ 2'den kalan) KAPANDI sayılır: `.rt` kök çizimi font
>   glifi kullanmıyor, v3 gömülü Comic Sans subset'iyle basılıyor — kullanıcı estetik
>   değişiklik isterse yeni iş olarak açılır.

## Amaç

Kaynak dosya: `C:\Users\egemen\iCloudDrive\ders notlari\9.sınıf 2025-2026\1.tema.pdf`
(117 sayfa, karışık kaynak: bazı sayfalar kullanıcının kendi taranmış/fotokopi sayfaları
"EGEMEN SARIKCI" başlıklı, bazı sayfalar bir yayınevinin (Metin Yayınları) dijital
sayfaları "N.KUR" rozetli).

Kullanıcı (Egemen Sarıkcı, öğretmen) bu PDF'i tek tip bir görünüme dönüştürmemizi istedi:

1. **Tüm sorular Comic Sans MS yazı tipiyle** yeniden düzenlensin.
2. **Her sayfada "Egemen Sarıkcı" logosu/başlığı** görünsün (tekrarlanan üst banner).
3. **"1.KUR" "2.KUR" "3.KUR" "4.KUR" "5.KUR" gibi yayınevi rozet etiketleri kaldırılsın**
   (ama altındaki gerçek bölüm adları — "ISINMA HAREKETLERİ", "GÜNLÜK HAYAT UYGULAMALARI",
   "ÖSYM SORULARINA HAZIRLIK", "ÖSYM KURGULARSA", "PİST ALANI" — KORUNSUN).
4. **Tablo, resim, geometrik şekil, diyagram olduğu gibi korunsun** (görsel olarak kırpılıp
   yeni sayfaya yapıştırılacak, yeniden çizilmeyecek).
5. **Matematiksel ifadelerin (üs, kesir, kök, işaret) orijinali TAM korunmalı** — kullanıcı
   bunu özellikle vurguladı, tahmin yürütülmeyecek.
6. **Her sorudan sonra çözüm için yeterli boşluk bırakılsın** (kullanıcı ek olarak istedi).
7. Kullanıcı daha sonra soruların yerini değiştirebilir / yeni soru ekleyebilir — bu yüzden
   çıktı **tek bir HTML dosyası** olarak da tutuluyor (PDF'e dönüştürülmeden önce), düzenlemeye
   açık olsun diye.
8. Nihai çıktı: **tek bir PDF dosyası**, orijinal PDF ile **aynı klasöre** kaydedilecek:
   `C:\Users\egemen\iCloudDrive\ders notlari\9.sınıf 2025-2026\` (muhtemelen
   `1.tema_duzenlenmis.pdf` gibi bir isimle — kullanıcıyla kesin isim teyit edilmedi,
   üzerine yazmamaya dikkat et, orijinali ASLA değiştirme/silme).

Kullanıcı ayrıca **"düşük modellerle" alt görevlerin paralel/parçalı yürütülmesini** istedi —
bu yüzden 117 sayfa 18 gruba bölünüp `general-purpose` alt-ajanlara dağıtıldı (bkz. aşağı).

## Çalışma Alanı (scratchpad) — TÜM ARA DOSYALAR BURADA

```
C:\Users\egemen\AppData\Local\Temp\claude\C--Users-egemen\2fa10b6f-5cb8-46cd-80c9-2e8c19aba585\scratchpad\
├── pages\                     117 adet kaynak sayfa PNG'si, 200dpi, pg-001.png ... pg-117.png
│                               (A4, yaklaşık 1654x2339 piksel). Bunlar poppler ile
│                               `pdftoppm -png -r 200` komutuyla üretildi, TEKRAR ÜRETMEYE GEREK YOK.
└── build\
    ├── AGENT_INSTRUCTIONS.md  Alt-ajanlara verilen ORTAK transkripsiyon talimatı (çok
    │                           detaylı — CSS sınıfları, matematik notasyon kuralları,
    │                           KUR etiketi kaldırma kuralları, görsel kırpma yöntemi vb.
    │                           Kalan sayfaları işlerken AYNI talimatları kullan.)
    ├── flow.css                Nihai belge için tek CSS dosyası (Comic Sans MS, akan
    │                           sayfalama, .question/.qmath/.frac/.theory-box/.kur-tag vb.
    │                           sınıflar burada tanımlı). DEĞİŞTİRME — zaten test edildi.
    ├── crop.ps1                Kaynak sayfa PNG'sinden dikdörtgen bölge kırpıp
    │                           build\assets\ klasörüne kaydeden PowerShell script'i.
    │                           Kullanım: `powershell -File crop.ps1 -SrcPage 22 -X 800
    │                           -Y 400 -Width 500 -Height 300 -OutName "p22_q3_fig.png"`
    ├── print.mjs                Node.js script'i — Edge headless (CDP/DevTools Protocol)
    │                           kullanarak final.html'i PDF'e dönüştürür, HER SAYFADA
    │                           tekrarlanan "EGEMEN SARIKCI" header + sayfa numarası
    │                           footer'ı otomatik ekler (Page.printToPDF headerTemplate/
    │                           footerTemplate). Kullanım:
    │                           `node print.mjs <input.html> <output.pdf>`
    │                           ÖNEMLİ: flow.css'te `@page { margin:0 }` OLMAMALI —
    │                           bu CDP margin parametrelerini eziyor, zaten düzeltildi.
    ├── assemble.ps1             fragments\frag_01.html ... frag_18.html dosyalarını
    │                           NÜMERİK sırayla birleştirip build\final.html üretir
    │                           (flow.css link'i ile sarmalanmış tam HTML). Kullanım:
    │                           `powershell -File assemble.ps1`
    ├── fragments\                Her alt-ajanın ürettiği HTML PARÇALARI (sadece body
    │                           içeriği, <html>/<head>/<body> YOK). frag_01.html ...
    │                           frag_18.html olmalı — AŞAĞIDAKİ DURUM TABLOSUNA BAK.
    ├── assets\                   crop.ps1 ile kırpılmış görsel/tablo/şekil PNG'leri
    │                           (71 adet zaten var, sayfa 1-65 ve 85-96 civarından).
    │                           fragments içindeki <img src="assets/...png"> referansları
    │                           buraya işaret ediyor.
    └── testflow5.pdf, testflow5render-1.png, margintest.*, testrender*.png
                                Şablon geliştirme sırasında üretilen TEST dosyaları,
                                silinebilir, önemli değil.
```

## Sayfa Haritası (117 sayfa → 18 grup → hangi fragment)

Her grup bir alt-ajana verildi, çıktısı `build\fragments\frag_NN.html` olacak şekilde.
Sayfa numaraları `pg-0NN.png` dosya adlarına karşılık gelir (basılı sayfa numarası
FARKLI olabilir, örn. pg-041.png = basılı sayfa "25"). Aşağıdaki notlar önceki bir
yapısal tarama ajanının bulgularıdır — ana yol gösterici olarak kullan ama her sayfayı
kendin de görüp doğrula.

| Grup | Sayfa Aralığı | Fragment | Durum | Not |
|---|---|---|---|---|
| 1 | pg-001–008 | frag_01.html | ✅ TAMAM | ÜSLÜ SAYILAR başlangıcı, taranmış, Q1-44, ÖSS2008/2009 etiketleri korunmuş |
| 2 | pg-009–014 | frag_02.html | ✅ TAMAM | 1.KUR, ISINMA HAREKETLERİ, teori kutuları |
| 3 | pg-015–021 | frag_03.html | ✅ TAMAM | 1.KUR devamı, Üslü Denklemler teori kutuları |
| 4 | pg-022–029 | frag_04.html | ✅ TAMAM | 2.KUR GÜNLÜK HAYAT, 3.KUR ÖSYM SORULARINA HAZIRLIK, 4.KUR ÖSYM KURGULARSA, 5.KUR PİST ALANI — görsel/diyagram ağırlıklı |
| 5 | pg-030–036 | frag_05.html | ✅ TAMAM | KÖKLÜ SAYILAR başlangıcı, taranmış, boş Tanım/Açıklama kutuları var |
| 6 | pg-037–040 | frag_06.html | ✅ TAMAM | Taranmış devam + pg-040'ta yeni 1.KUR (Köklü Gösterim) başlangıcı |
| 7 | pg-041–046 | frag_07.html | ✅ TAMAM | 1.KUR Köklü İfadeler devam |
| 8 | pg-047–050 | frag_08.html | ✅ TAMAM | 1.KUR İç İçe Kökler, Paydayı Rasyonel Yapma |
| 9 | pg-051–054 | frag_09.html | ✅ TAMAM | 2.KUR GÜNLÜK HAYAT, 3.KUR ÖSYM SORULARINA HAZIRLIK |
| 10 | pg-055–058 | frag_10.html | ✅ TAMAM | 4.KUR ÖSYM KURGULARSA, 5.KUR PİST ALANI |
| 11 | pg-059–065 | frag_11.html | ✅ TAMAM | GERÇEK SAYI KÜMELERİ divider + 1.KUR başlangıcı |
| 12 | pg-066–071 | frag_12.html | ✅ TAMAM | 1.KUR Aralıklar, Mutlak Değer |
| 13 | pg-072–078 | frag_13.html | ✅ TAMAM | 1.KUR devam + 2.KUR GÜNLÜK HAYAT |
| 14 | pg-079–084 | frag_14.html | ✅ TAMAM | 3.KUR, 4.KUR ÖSYM KURGULARSA, 5.KUR PİST ALANI |
| 15 | pg-085–096 | frag_15.html | ✅ TAMAM | SAYI KÜMELERİNİN ÖZELLİKLERİ divider + 1.KUR başlangıcı |
| 16 | pg-097–104 | frag_16.html | ✅ TAMAM | 1.KUR Önermeler, İşlem Özellikleri, Özdeşlikler |
| 17 | pg-105–112 | frag_17.html | ✅ TAMAM | 2.KUR GÜNLÜK HAYAT, 3.KUR ÖSYM SORULARINA HAZIRLIK |
| 18 | pg-113–117 | frag_18.html | ✅ TAMAM | 4.KUR ÖSYM KURGULARSA, 5.KUR PİST ALANI, BELGENİN SONU |

**Eksik 10 grup için tam talimat metni** `COORDINATION.md` dosyasında satır satır
kopyalanmıştır (her grubun context notları dahil) — orijinal ajan prompt'larından alındı.

## Kalan İşler (sırayla)

1. **10 eksik fragment'ı üret** (04, 06, 08, 09, 10, 12, 13, 14, 16, 17) —
   `AGENT_INSTRUCTIONS.md` talimatlarına göre, ilgili `pg-0NN.png` sayfalarını okuyup
   `build\fragments\frag_NN.html` olarak yaz. Görsel/tablo/şekil kırpma gerekiyorsa
   `crop.ps1` kullan, çıktıyı `build\assets\` klasörüne koy.
   - NOT: Bu 10 grup, önceki oturumda API oturum limiti (session limit) yüzünden
     yarıda kesildi. Bazıları kırpma/doğrulama aşamasındaydı ama HTML dosyasını henüz
     YAZMAMIŞTI (frag dosyası yok = baştan başla). İki grup (05, 18) dosyayı yazmıştı
     ama doğrulama sırasında hata aldı — onlar TAMAM sayılabilir (kontrol edildi, dosya
     sağlam/tam).
2. **Birleştir**: `powershell -File build\assemble.ps1` → `build\final.html` üretir
   (18 fragment'ın hepsi mevcut olmalı).
3. **PDF'e dönüştür**: `node build\print.mjs build\final.html build\final.pdf`
4. **Kalite kontrolü**: `pdftoppm` ile final.pdf'in birkaç sayfasını PNG'ye çevirip
   Read tool ile görsel kontrol et — matematik doğru mu, KUR etiketi kalmış mı,
   logo her sayfada var mı, çözüm boşlukları yeterli mi.
5. **Kopyala**: Onaylanan final.pdf dosyasını kullanıcıya sorup uygun bir isimle
   (örn. `1.tema_duzenlenmis.pdf`) `C:\Users\egemen\iCloudDrive\ders notlari\9.sınıf 2025-2026\`
   klasörüne kopyala. ORİJİNAL `1.tema.pdf` dosyasına DOKUNMA.

## Önemli Teknik Notlar / Tuzaklar

- **Poppler PATH'te**: `C:\Users\egemen\AppData\Local\Microsoft\WinGet\Packages\oschwartz10612.Poppler_Microsoft.Winget.Source_8wekyb3d8bbwe\poppler-25.07.0\Library\bin`
  (kullanıcının User PATH'ine kalıcı eklendi, yeni PowerShell oturumunda otomatik
  çalışmalı; çalışmazsa bu klasörü $env:PATH'e ekle).
- **Edge headless yolu**: `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`
- **Comic Sans MS** sistemde zaten kurulu, ek kuruluma gerek yok.
- **`@page { margin: 0 }` kullanma** — flow.css'te bu satır YOK, öyle kalsın. CDP
  print.mjs kendi margin'lerini (marginTop:1.15in, marginBottom:0.5in vb.) veriyor,
  CSS @page margin:0 bunu eziyordu, bu yüzden kaldırıldı.
- **KUR rakamlarını (1.KUR, 2.KUR...) ASLA transkribe etme** — sadece yanındaki gerçek
  bölüm adını (ISINMA HAREKETLERİ vb.) `.kur-tag` olarak yaz.
- **"ÖSYM KURGULARSA" içindeki yıl etiketleri** (örn. "2020 MSÜ Kurgusu") KUR rakamı
  DEĞİL, bunlar içeriktir, `.tag-kurgusu` sınıfıyla KORUNMALI.
- Her fragment kendi başlığını tekrar eklemek yerine, bölüm/başlık SADECE gerçekten
  değiştiğinde bir kez eklenmeli (fragment'lar art arda birleştiği için gereksiz
  tekrar önlenmeli) — bu yüzden komşu fragment'ların hangi başlıkla bittiğini bilmek
  faydalı (yukarıdaki tabloya bak).
- Alt-ajanlar arka planda (`Agent` tool, `run_in_background: true`) çalıştırıldı ama
  **API oturum limitine takılıp toplu şekilde başarısız oldu** (12 ajan aynı anda).
  Limit sıfırlanma zamanı: **20:10 (Europe/Istanbul)**. Bu saatten önce yeni arka plan
  ajan başlatmak muhtemelen yine başarısız olur — bunun yerine ana konuşma içinde
  (subagent olmadan) doğrudan Read/Write ile ilerlemek daha güvenli olabilir, veya
  saat 20:10'u bekleyip agent tool'u tekrar dene.

## Kullanıcı Tercihleri / Geri Bildirim

- Kullanıcı matematiksel ifadelerin OCR ile yeniden yazılmasını (tahmin riski olsa
  bile) taranmış görüntü olarak dondurmaya TERCİH ETTİ — yani transkripsiyon
  yaklaşımı kullanıcı onaylı, geri dönüp "aslında görüntü olarak bırak" demedi.
- "Full otomatik modda çalış" dedi — onay beklemeden ilerlemeye devam et.
- "Testlerin çözümü için yeterli boşluk bırakmayı unutma" — her sorudan sonra
  `.solve-space` (min 26mm, çok parçalı sorularda daha fazla) zaten şablonda var,
  bu kurala kalan fragment'larda da uy.
