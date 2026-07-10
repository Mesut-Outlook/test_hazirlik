# Dönüşüm Raporu — 14. TEMA

Oluşturulma: 2026-07-10T17:37:34+03:00
Sürüm: 2
Kaynak: `C:\Users\egemen\Documents\_PROJELER\Test Hazırlık\temalar\14-6-tema\kaynak\9.sınıf 6.tema.pdf`
Çıktı: `C:\Users\egemen\Documents\_PROJELER\Test Hazırlık\cikti\6.tema_v2.pdf` (28 sayfa)

> Yöntem: Kaynak soru sayısı için İKİ bağımsız TAHMİN hesaplanır — (1) satır bazlı: satır başında '12.'/'12)' + AYNI SATIRDA devam metni arar; (2) span bazlı (F10): get_text('dict')'te satırın İLK span'ı tam olarak '12.'/'12)' ise sayar (taranmış/görsel ağırlıklı kaynaklarda soru numarası kendi satırında yalnız durur, devam metni resim olduğu için satırda YOKTUR — yöntem 1 bunu kaçırır). Nihai tahmin ikisinin BÜYÜĞÜdür (bu koşuda: span_bazli); her iki ham değer de kaynak_soru_tahmini_satir_bazli / kaynak_soru_tahmini_span_bazli alanlarında saklanır. Cevap anahtarı satırları (örn. '1.B 2.A 3.C') her iki yöntemde de elenir. Aktarım kontrolü her çıktı sorusunun ilk ~40 normalize karakterini kaynak metninde arar, kısa/salt-görsel sorular karşılaştırma dışı tutulur. Sayfa bazlı görsel karşılaştırması (sayfa_gorsel_karsilastirma / olasi_eksik_gorsel_sayfalar) kaynaktaki basitleştirilmiş görsel-bölge sayımını (extract.py'nin gömülü görüntü + büyük vektör çizim kümesi mantığının basit bir kopyası, extract.py'nin kendisi ÇALIŞTIRILMADI) çıktıdaki aynı kaynak sayfaya bağlı <img> sayısıyla karşılaştırır — extract.py'nin banner/tekil-dolgu istisnaları burada yok, bu yüzden bir miktar yanlış pozitif (abartılı 'olası eksik') beklenir; kesin/otomatik doğrulama için qa/dogrula.py'ye bakın.

## Özet Tablo

| Metrik | Sayı |
|---|---|
| Kaynaktaki soru sayısı (TAHMİN) | 77 |
|    — satır bazlı yöntem | 31 |
|    — span bazlı yöntem (F10) | 77 |
|    — kazanan yöntem | span_bazli |
| Çıktıya aktarılan soru sayısı | 60 |
| — metin formatında | 33 |
| — görsel içeren | 27 |
|    (bunların salt görsel/metinsiz olanı) | 0 |
| Düzgün aktarıldığı doğrulanan (eşleşti) | 48 |
| Eşleşmedi — elle kontrol önerilir | 4 |
| Görsel içerikli — metin karşılaştırması yapılamadı | 8 |

## Elle Kontrol Önerilen Sorular

**Eşleşmedi** (4 adet):

t14-s011, t14-s014, t14-s026, t14-s029


## Kayıp Olabilecek Kaynak Soru Numaraları (yaklaşık)

> Not: kaynak PDF'te her yeni bölüm (KUR) numaralamayı 1'den yeniden başlattığı için bu liste GLOBAL bir küme farkıdır, kesin kayıp kanıtı DEĞİLDİR — yalnızca hangi numaraların gözle kontrol edilmesi gerektiğine dair bir ipucudur.

yok

## Sayfa Bazlı Görsel Karşılaştırması (F10)

> Not: kaynak sütunu, extract.py'nin gömülü görüntü + büyük vektör çizim kümesi mantığının BASİTLEŞTİRİLMİŞ bir kopyasıyla sayılır (extract.py'nin kendisi ÇALIŞTIRILMADI); banner/tekil-dolgu istisnaları burada yok, bu yüzden kaynak sayısı gerçek görsel-bölge sayısından biraz FAZLA çıkabilir (yanlış pozitif). cikti sütunu yalnızca AKTİF (silinmemiş) bloklardaki `<img>` sayısıdır.

> **DİKKAT**: aşağıdaki sayfalarda kaynaktaki görsel-bölge sayısı çıktıdaki `<img>` sayısından FAZLA — olası eksik görsel, elle kontrol edin: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15

| Kaynak sayfa | Kaynak (tahmini) | Çıktı |
|---|---|---|
| 1 | 6 | 1 ⚠️ |
| 2 | 3 | 1 ⚠️ |
| 3 | 8 | 4 ⚠️ |
| 4 | 10 | 3 ⚠️ |
| 5 | 10 | 4 ⚠️ |
| 6 | 7 | 1 ⚠️ |
| 7 | 4 | 2 ⚠️ |
| 8 | 4 | 2 ⚠️ |
| 9 | 6 | 4 ⚠️ |
| 10 | 7 | 5 ⚠️ |
| 11 | 10 | 7 ⚠️ |
| 12 | 13 | 12 ⚠️ |
| 13 | 9 | 8 ⚠️ |
| 14 | 5 | 4 ⚠️ |
| 15 | 8 | 7 ⚠️ |

