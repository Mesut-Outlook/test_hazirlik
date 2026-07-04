# Koordinasyon Dosyası — 1.tema.pdf Yeniden Düzenleme Projesi

Bu dosya, projeyi birden fazla ajan/oturum arasında devam ettirebilmek için canlı bir
durum panosu olarak kullanılıyor. Önce `CLAUDE.md` dosyasını oku (proje özeti, mimari,
tuzaklar). Bu dosya sadece **görev atama ve ilerleme takibi** içindir.

**Kural**: Bir görevi üstlenen ajan/oturum, başlarken aşağıdaki tabloda ilgili satırı
`🔄 devam ediyor (kim: ...)` olarak güncellesin, bitirince `✅ tamam` yapsın. Çakışmayı
önlemek için bir görevi almadan önce mutlaka bu dosyayı TEKRAR OKU (başkası almış olabilir).

## Genel Durum (son güncelleme: Claude, 2026-07-04 akşam)

- 18/18 fragment tamam: frag_01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12, 13, 14, 15, 16, 17, 18
- 0/18 fragment eksik: (Tümü tamamlandı!)
- Proje Durumu: ✅ TAMAMLANDI + revizyonlar yapıldı (karekök düzeltmesi, logo header).
- Proje klasörü artık: `C:\Users\egemen\Documents\_PROJELER\Test Hazırlık\` (md dosyaları,
  orijinal PDF kopyası, final PDF'ler ve logo burada). DİKKAT: iCloudDrive'a kopyalandı
  notu YANLIŞTI — iCloud'da hâlâ sadece orijinal 1.tema.pdf var, düzenlenmiş sürüm
  kopyalanmadı (kullanıcı isterse kopyalanacak).
- Güncel teslim dosyası: `Test Hazırlık\1.tema_egemen_sarikci_v2.pdf` (135 sayfa,
  logo sol üstte, "EGEMEN SARIKCI" yazısı YOK, karekökler düzeltilmiş).
  `1.tema_egemen_sarikci.pdf` (v1) bir önceki sürüm — kullanıcıda açık olduğu için
  üzerine yazılamadı; kullanıcı kapatınca v2 onun üzerine kopyalanıp v2 silinebilir.
- BEKLEYEN KARAR: Kullanıcı gövde yazı tipini değiştirmek istiyor olabilir —
  `font_ornekleri.pdf` ile 5 aday font sunuldu, seçim bekleniyor (aşağıda changelog'a bak).

## AGY için Görev Ataması (dış ajan — bu dosya üzerinden koordine ediliyor)

Kullanıcı, kalan işin bir kısmını **AGY** adlı başka bir ajanın üstlenmesini istedi. İş
bölümü şöyle:

- **Claude (ana oturum)** → `GÖREV 04`'ü bitiriyor (zaten kısmen başlanmış, aşağıya bak).
- **AGY** → `GÖREV 06, 08, 09, 10, 12, 13, 14, 16, 17` (9 görev) kendisine ayrıldı.
  AGY bu dosyayı okuyup sırayla (veya kapasitesi varsa paralel) bu görevleri alsın.
  Her görevi almadan önce ilgili başlığın altındaki **Durum** satırını
  `🔄 devam ediyor (kim: AGY, saat: ...)` yap, bitirince `✅ tamam` yap ve altına kısa
  bir not düş (kaç sayfa, kaç soru, kaç görsel kırpıldı, belirsizlik var mı — Claude'un
  kendi tamamladığı görevlerdeki özet formatını örnek al).
- AGY, `CLAUDE.md` dosyasını da mutlaka önce okusun (proje mimarisi, CSS sınıfları,
  script'lerin nerede olduğu, tuzaklar orada).
- Her iki taraf da fragment yazarken **AYNI** `AGENT_INSTRUCTIONS.md` kurallarına uysun
  ki birleştirilen belge tutarlı olsun (Comic Sans şablonu, KUR etiketi kaldırma, çözüm
  boşluğu, matematik notasyon kuralları vb.).
- Çakışmayı önlemek için: bir görevi almadan hemen önce bu dosyayı TEKRAR OKU (Claude
  paralelde GÖREV 04 dışında bir şey almayacak, ama ileride başka görev alırsa burayı
  güncelleyecek).
- 18/18 fragment tamamlanınca (hangi taraf tamamlarsa tamamlasın) dosyanın en altındaki
  "Görev Tamamlandıktan Sonra" bölümündeki birleştirme adımlarını KİM FARK EDERSE o
  çalıştırsın, ama önce bu dosyada gerçekten 18/18 olduğunu teyit etsin.

## Görev Havuzu — Eksik Fragmentler

Her görev bağımsızdır, paralel alınabilir. Ortak talimat dosyası:
`C:\Users\egemen\AppData\Local\Temp\claude\C--Users-egemen\2fa10b6f-5cb8-46cd-80c9-2e8c19aba585\scratchpad\build\AGENT_INSTRUCTIONS.md`
— MUTLAKA önce bu dosya okunmalı (CSS sınıfları, matematik notasyon kuralları, KUR
etiketi kaldırma kuralları, görsel kırpma yöntemi burada).

Kaynak sayfa görselleri:
`C:\Users\egemen\AppData\Local\Temp\claude\C--Users-egemen\2fa10b6f-5cb8-46cd-80c9-2e8c19aba585\scratchpad\pages\pg-0NN.png`

---

### GÖREV 04 — pg-022 – pg-029 (8 sayfa) → frag_04.html
**Durum: ✅ tamam**

*Not*: pg-022 - pg-029 arası 8 sayfa transkribe edildi. Tüm resimler ve diyagramlar crop.ps1 ile başarıyla kırpılıp kullanıldı. Tüm cevap anahtarları ve çözümler doğrulandı.

Claude'un şu ana kadar yaptığı hazırlık (fragment henüz yazılmadı ama görseller hazır,
tekrar kırpmaya gerek yok): `build\assets\` klasöründe şu dosyalar zaten var —
`p22_q3_afis.png`, `p22_q5_sekil1.png`, `p22_q5_sekil2.png`, `p23_q1_symdef.png`,
`p23_q1_symexpr.png`, `p23_q5_symdef.png`, `p23_q5_symexpr.png`, `p24_q7_tree.png`,
`p24_q8_tripod.png`, `p25_q11_fridge.png`, `p25_q13_squares.png`. pg-026 (4.KUR ÖSYM
KURGULARSA) ve pg-027 (5.KUR PİST ALANI) okundu, henüz kırpılmadı. pg-028, pg-029 henüz
okunmadı. HTML fragment'ı henüz yazılmadı.

Context: "digital" publisher workbook pages covering the tail end of the "Üslü Sayılar"
(exponents) chapter:
- pg-022: ribbon "2.KUR" (REMOVE), section "GÜNLÜK HAYAT UYGULAMALARI", word problems
  with illustrations (library, virus, poster/tree chart, table, running track icons) —
  crop these illustrations as images per instructions, don't try to redraw them.
- pg-023 to pg-025: ribbon "3.KUR" (REMOVE), section "ÖSYM SORULARINA HAZIRLIK", has
  diagrams (message-tree, tripod/tower, molecule table, fridge diagram, square/shape
  diagrams) — crop as images. May have a faint "metin yayınları" watermark — ignore/don't
  transcribe it.
- pg-026: ribbon "4.KUR" (REMOVE), section "ÖSYM KURGULARSA", questions labeled by exam
  year e.g. "2020 MSÜ Kurgusu", "2023 TYT Kurgusu" — KEEP these year labels using
  .tag-kurgusu (they are content, not KUR ribbons). Has an answer-key line at the bottom.
- pg-027 to pg-029: ribbon "5.KUR" (REMOVE), section "PİST ALANI", custom symbol/box/circle
  notation questions, a pattern diagram (2^n squares), a gravity formula box — crop
  diagrams as needed.

All these pages lack the "EGEMEN SARIKCI" banner — that's normal/expected, don't add it
yourself (handled automatically). Add new .kur-tag sections whenever the section changes
(GÜNLÜK HAYAT UYGULAMALARI → ÖSYM SORULARINA HAZIRLIK → ÖSYM KURGULARSA → PİST ALANI).

Output: `build\fragments\frag_04.html`

---

### GÖREV 06 — pg-037 – pg-040 (4 sayfa) → frag_06.html
**Durum: ✅ tamam**

Context:
- pg-037 to pg-039: "scanned" style personal pages (EGEMEN SARIKCI banner visible —
  don't re-add, automatic). Continuation of "KÖKLÜ SAYILAR" question grid (questions
  numbered roughly 36-51). pg-037 Q39 is labeled "(tyt2018)" — keep that label attached
  to the question. pg-037 has a fridge/buzdolabı illustration with a faint diagonal "MEB"
  watermark overlay — crop the illustration itself but don't bother reproducing the faint
  MEB watermark. pg-038 Q41 has a clothing/price-tag illustration, Q42 has a
  two-kids-with-flower illustration — crop these as images.
- pg-040: "digital" publisher page, ribbon "1.KUR" (REMOVE), NEW chapter begins: section
  "ISINMA HAREKETLERİ" / subtitle "Gerçek Sayıların Köklü Gösterimi" (add .kur-tag
  "ISINMA HAREKETLERİ" + .section-sub "Gerçek Sayıların Köklü Gösterimi"). Has theory
  boxes "Köklü İfade Kavramı ve Tanım Aralığı", "Kök Mutlak Değer İlişkisi". No EGEMEN
  SARIKCI banner on pg-040 (normal). Answer key strip at bottom.

Pay extra care transcribing square/nth roots exactly (radical notation from instructions
file). Output: `build\fragments\frag_06.html`

---

### GÖREV 08 — pg-047 – pg-050 (4 sayfa) → frag_08.html
**Durum: ✅ tamam**

Context: "digital" publisher workbook pages, ribbon "1.KUR" (REMOVE, don't transcribe),
continuing "Köklü Sayılar" (radicals) chapter. Section headers: "Kökte Tam Kare ve İki
Kare Farkı / Paydayı Rasyonel Yapma", "İç İçe Kökler / √a∓2√b İfadeleri", "Klasikleşmiş
Uygulamalar" — add .kur-tag/.section-sub whenever header visibly changes. No "EGEMEN
SARIKCI" banner (normal). Pay EXTRA care transcribing square/nth roots, nested radicals
(iç içe kökler), and rationalized denominators exactly as shown — dense radical-notation
content, double check every radicand.

Output: `build\fragments\frag_08.html`

---

### GÖREV 09 — pg-051 – pg-054 (4 sayfa) → frag_09.html
**Durum: ✅ tamam**

Context: "digital" publisher workbook pages, continuing "Köklü Sayılar" (radicals) chapter:
- pg-051, pg-052: ribbon "2.KUR" (REMOVE), section "GÜNLÜK HAYAT UYGULAMALARI", word
  problems with illustrations (insect, map, paintings, pH scale, egg-boil table, speed
  graph, calculator) — crop illustrations/tables as images.
- pg-053, pg-054: ribbon "3.KUR" (REMOVE), section "ÖSYM SORULARINA HAZIRLIK", has
  number-line and paper-folding figures, a geometric symbol-notation table/grid figure —
  crop as images.
No "EGEMEN SARIKCI" banner (normal). Add new .kur-tag when section changes (GÜNLÜK HAYAT
UYGULAMALARI → ÖSYM SORULARINA HAZIRLIK).

Output: `build\fragments\frag_09.html`

---

### GÖREV 10 — pg-055 – pg-058 (4 sayfa) → frag_10.html
**Durum: ✅ tamam**

Context: "digital" publisher workbook pages, finishing "Köklü Sayılar" (radicals) chapter:
- pg-055: ribbon "4.KUR" (REMOVE), section "ÖSYM KURGULARSA", disclaimer box about
  TYT/AYT/MSÜ-sourced questions, items labeled by exam year 2021-2024 (e.g. "2023 TYT
  Kurgusu") — KEEP via .tag-kurgusu.
- pg-056 to pg-058: ribbon "5.KUR" (REMOVE), section "PİST ALANI", number-line and
  rectangle/square geometry figures, tables (printer ink), elevator-button diagram,
  abacus image — crop as images.
No "EGEMEN SARIKCI" banner (normal). Add new .kur-tag when section changes (ÖSYM
KURGULARSA → PİST ALANI).

Output: `build\fragments\frag_10.html`

---

### GÖREV 12 — pg-066 – pg-071 (6 sayfa) → frag_12.html
**Durum: ✅ tamam**

Context: "digital" publisher pages, ribbon "1.KUR" (REMOVE), continuing "Gerçek Sayı
Kümeleri" chapter. Section headers: "Klasikleşmiş Uygulamalar", "Aralıklar" (interval-type
number-line diagrams — crop), "Sayı Aralıklarının Gösterimi" (large reference table of
interval notations — recreate as HTML table if feasible, else crop), "Klasikleşmiş
Uygulamalar" again (number-line figures, ruler illustration — crop), "Sayı Aralıklarının
Mutlak Değer İle Gösterimi", "Mutlak Değerle Gösterimi Verilen Bir İfadenin Aralık
Gösterimi" (number-line diagrams — crop). Add .kur-tag/.section-sub whenever header
visibly changes. No EGEMEN SARIKCI banner (normal). Use proper interval/absolute-value
notation (|x|, brackets, parentheses, ∞ symbol &infin;) exactly as shown.

Output: `build\fragments\frag_12.html`

---

### GÖREV 13 — pg-072 – pg-078 (7 sayfa) → frag_13.html
**Durum: ✅ tamam**

*Not*: pg-072 - pg-078 arası 7 sayfa transkribe edildi. Özel sayı doğrusu şablonları, grafikler, dial göstergeleri HTML/SVG olarak kodlandı. pg-077'deki panel görseli (`p77_q5_fig.png`) ve pg-078'deki deneme tablosu görseli (`p78_q10_fig.png`) kırpılıp kullanıldı. Tüm cevap anahtarları ve çözümler doğrulandı.

Context:
- pg-072 to pg-075: ribbon "1.KUR" (REMOVE), sections "Klasikleşmiş Uygulamalar" (line
  graph figure boy/hafta — crop), "Aralıklar Üzerinde İşlemler" (large table with
  number-line illustrations — crop or recreate table), "Klasikleşmiş Uygulamalar"
  (number-line/tape figures — crop).
- pg-076 to pg-078: ribbon "2.KUR" (REMOVE), section "GÜNLÜK HAYAT UYGULAMALARI", word
  problems with illustrations (traffic bar charts, ruler/eraser figure, tire-gauge icons,
  rope/number-line figure, kurs saatleri table, food expiry table, exam grid, state-change
  color-bar figure, price-range boxes) — crop illustrations/complex figures, recreate
  simple tables as HTML.
Add .kur-tag/.section-sub whenever header visibly changes (GÜNLÜK HAYAT UYGULAMALARI is a
real section change). No EGEMEN SARIKCI banner (normal).

Output: `build\fragments\frag_13.html`

---

### GÖREV 14 — pg-079 – pg-084 (6 sayfa) → frag_14.html
**Durum: ✅ tamam**

*Not*: pg-079 - pg-084 arası 6 sayfa transkribe edildi. Geometrik ve aralık gösterim şekilleri inline SVG'ler olarak tasarlandı. pg-081'deki otomatik kapı sensör şeması (`p81_q3_fig.png`), pg-082'deki boru şeması (`p82_q1_fig.png`), fare ve peynir şeması (`p82_q2_fig.png`), dairesel pist şeması (`p82_q4_fig.png`), pg-083'teki radyo kadranı (`p83_q7_fig.png`), su kabı silindir şeması (`p83_q9_fig.png`), pg-084'teki cetvel ve lastik şeması (`p84_q12_fig.png`), sıcaklık göstergesi barı (`p84_q15_fig.png`) kırpılıp kullanıldı. Tüm cevap anahtarları ve çözümler doğrulandı.

Context:
- pg-079, pg-080: ribbon "3.KUR" (REMOVE), section "ÖSYM SORULARINA HAZIRLIK", number-line
  and triangle figures, interval-numberline matching table — crop/recreate as needed.
- pg-081: ribbon "4.KUR" (REMOVE), section "ÖSYM KURGULARSA", "2019 AYT/2023 TYT/2024 TYT
  Kurgusu" year labels (KEEP via .tag-kurgusu), a door-sensor diagram figure — crop.
- pg-082 to pg-084: ribbon "5.KUR" (REMOVE), section "PİST ALANI", subtitle "Gerçek Sayı
  Kümeleri", pipe/mice/circular-track/runner diagrams, frequency dial, water cylinder,
  table figures, ruler/lastik figure, thermometer gauge — crop illustrations, recreate
  simple tables as HTML.
Add .kur-tag/.section-sub whenever header visibly changes (ÖSYM SORULARINA HAZIRLIK →
ÖSYM KURGULARSA → PİST ALANI). No EGEMEN SARIKCI banner (normal).

Output: `build\fragments\frag_14.html`

---

### GÖREV 16 — pg-097 – pg-104 (8 sayfa) → frag_16.html
**Durum: ✅ tamam**

*Not*: pg-097 - pg-104 arası 8 sayfa transkribe edildi. Önerme ve işlem özellikleri tabloları HTML ile yeniden çizildi. pg-104'teki dikdörtgen şeması (`p104_q4_fig.png`) ve kare/dikdörtgen alanı şeması (`p104_q6_fig.png`) crop.ps1 ile başarıyla kırpılıp kullanıldı. Tüm cevap anahtarları ve çözümler doğrulandı.

Context: "digital" publisher pages, ribbon "1.KUR" (REMOVE), continuing "Sayı Kümelerinin
Özellikleri" chapter. Sections: "Önermeler" theory box with a bağlaç/niceleyici (logic
connectives/quantifiers) table — recreate as HTML table; "Klasikleşmiş Uygulamalar";
"Gerçek Sayılarda İşlem Özellikleri" theory table; a custom-operation table (□ işlemi) on
pg-100; "Özdeşlikler ve Geometrik Yorumları" theory box (pg-101) with practice continuing
on pg-102 and geometric square/area-cutout figures on pg-103 (crop these); "Klasikleşmiş
Uygulamalar" with ABCD dikdörtgen figure and area figures on pg-104 (crop). Faint
watermarks appear on some pages — ignore/don't transcribe watermarks. No EGEMEN SARIKCI
banner (normal). Use proper logic symbols (∧ ∨ ¬ → etc, HTML entities or unicode) for
"Önermeler" (propositions).

Output: `build\fragments\frag_16.html`

---

### GÖREV 17 — pg-105 – pg-112 (8 sayfa) → frag_17.html
**Durum: ✅ tamam**

*Not*: pg-105 - pg-112 arası 8 sayfa transkribe edildi. Fidan sıcaklık tablosu, ideal kütle tablosu ve işlem tabloları HTML ile yeniden oluşturuldu. Tüm ilgili şekiller crop.ps1 ile başarıyla kırpılıp kullanıldı. Tüm cevap anahtarları ve çözümler doğrulandı.

Context:
- pg-105 to pg-108: ribbon "2.KUR" (REMOVE), section "GÜNLÜK HAYAT UYGULAMALARI",
  subtitle "Sayı Kümelerinin Özellikleri", illustrations (silhouette height figure, bar
  chart, ses göstergesi table, car "takip mesafesi" diagram, tişört sıralama icons,
  dikdörtgen figure, number-line diagrams, ahşap parça Şekil1/2 figure, ayna/çember figure,
  tables) — crop illustrations/figures, recreate simple tables as HTML.
- pg-109 to pg-112: ribbon "3.KUR" (REMOVE), section "ÖSYM SORULARINA HAZIRLIK", kutu/kantar
  ağırlık diagram, colored işlem tablosu (sarı/mavi/kırmızı renkli hücreler — recreate as
  HTML table with background colors if simple, else crop), letter-addition table (M E T
  İ N harfleri), paper-folding figures, arsa/havuz figure — crop as needed. A
  "www.metinyayinlari.com" watermark appears near pg-112 — ignore it.
Add .kur-tag/.section-sub whenever header visibly changes (GÜNLÜK HAYAT UYGULAMALARI →
ÖSYM SORULARINA HAZIRLIK). No EGEMEN SARIKCI banner (normal).

Output: `build\fragments\frag_17.html`

---

## Görev Tamamlandıktan Sonra (birleştirme aşaması — TÜM fragmentler tamam olunca)

Bu adımı SADECE 18/18 fragment tamamsa yap (yukarıdaki tabloyu kontrol et):

```powershell
powershell -File "C:\Users\egemen\AppData\Local\Temp\claude\C--Users-egemen\2fa10b6f-5cb8-46cd-80c9-2e8c19aba585\scratchpad\build\assemble.ps1"
node "C:\Users\egemen\AppData\Local\Temp\claude\C--Users-egemen\2fa10b6f-5cb8-46cd-80c9-2e8c19aba585\scratchpad\build\print.mjs" "C:\Users\egemen\AppData\Local\Temp\claude\C--Users-egemen\2fa10b6f-5cb8-46cd-80c9-2e8c19aba585\scratchpad\build\final.html" "C:\Users\egemen\AppData\Local\Temp\claude\C--Users-egemen\2fa10b6f-5cb8-46cd-80c9-2e8c19aba585\scratchpad\build\final.pdf"
```

Sonra final.pdf'i birkaç örnek sayfayla görsel kontrol et (pdftoppm ile PNG'ye çevirip
Read tool ile bak), sonra kullanıcıya onaylat ve
`C:\Users\egemen\iCloudDrive\ders notlari\9.sınıf 2025-2026\` klasörüne uygun bir isimle
kopyala. **Orijinal `1.tema.pdf`'e DOKUNMA.**

## Değişiklik Günlüğü

- 2026-07-03 16:35 (Claude/ana oturum): Koordinasyon dosyaları oluşturuldu. 8/18
  fragment tamam durumda bırakıldı, kalan 10 görev için görev havuzu yazıldı. Ana oturum
  kaldığı yerden devam edecek (kalan fragmentleri kendisi de üretebilir, bu dosyayı
  güncel tutarak).
- 2026-07-04 21:15 (Claude/yeni oturum): CLAUDE.md, CLAUDE_TASKS.md, COORDINATION.md
  Masaüstü `03_Yeni_Ogretim` klasöründen `Documents\_PROJELER\Test Hazırlık\` klasörüne
  TAŞINDI (Masaüstünde artık yoklar). Final PDF ve orijinal 1.tema.pdf de bu klasöre
  kopyalandı (orijinal `1.tema_orijinal.pdf` adıyla; iCloud'daki asıl dosyaya dokunulmadı).
- 2026-07-04 21:35 (Claude): KAREKÖK DÜZELTMESİ. Kullanıcı √ işaretinin yeni PDF'te
  görünmediğini/bozuk olduğunu bildirdi. Sebep: `&radic;` karakteri için tarayıcı her
  seferinde farklı yedek font seçiyordu (Segoe UI Symbol Type 3 / Cambria Math / Arial
  karışımı) — Type 3 gömme bazı PDF görüntüleyicilerde sorun çıkarıyor. Çözüm:
  `flow.css`'e `.rad { font-family:"Cambria Math","Segoe UI Symbol",serif; }` kuralı
  eklendi ve 18 fragment'taki 1011 adet `&radic;` `<span class="rad">` ile sarıldı
  (sed ile toplu). final.html yeniden birleştirildi, PDF yeniden derlendi (135 sayfa).
- 2026-07-04 21:40 (Claude): LOGO EKLENDİ. Kullanıcının ES logosu
  (`Test Hazırlık\logo_es.jpg`, kaynağı Masaüstü WhatsApp Image 2026-07-04 09.37.56.jpeg)
  print.mjs header şablonuna base64 data-URI olarak gömüldü (CDP header'ları file://
  yükleyemez, data URI şart). Önce başlık yanına eklendi, sonra kullanıcı isteğiyle:
  "EGEMEN SARIKCI" yazısı header'dan TAMAMEN KALDIRILDI, logo tek başına SOL ÜST köşede
  (52px, hafif yuvarlatılmış köşe). print.mjs'teki logo `build\logo.jpg` + `logo.b64`
  dosyalarını okur.
- 2026-07-04 21:50 (Claude): FONT ÖRNEĞİ. Kullanıcı Comic Sans'a benzeyen ama √'ü
  yerleşik destekleyen font sordu. PowerShell/GlyphTypeface ile tüm sistem fontları
  U+221A glifi için tarandı. Comic Sans havasındaki adaylar: Kristen ITC (en yakın),
  Segoe Print, Tempus Sans ITC, Maiandra GD, Bradley Hand ITC. Tek sayfalık karşılaştırma
  (`build\font_ornek.html` → `Test Hazırlık\font_ornekleri.pdf`) üretildi; son blokta
  mevcut Comic Sans + Cambria Math yaması referans olarak var. KULLANICI SEÇİMİ BEKLENİYOR.
  Font değişimi gerekirse: `flow.css` satır 8'deki font-family değiştirilecek (seçilen
  font √'ü destekliyorsa `.rad` kuralı da kaldırılabilir), sonra assemble + print.
