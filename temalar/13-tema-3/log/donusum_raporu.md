# Dönüşüm Raporu — 13. TEMA

Oluşturulma: 2026-07-10T17:18:41+03:00
Sürüm: 2
Kaynak: `C:\Users\egemen\Documents\_PROJELER\Test Hazırlık\temalar\13-tema-3\kaynak\3.tema.pdf`
Çıktı: `C:\Users\egemen\Documents\_PROJELER\Test Hazırlık\cikti\tema_3_v2.pdf` (46 sayfa)

> Yöntem: Kaynak soru sayısı için İKİ bağımsız TAHMİN hesaplanır — (1) satır bazlı: satır başında '12.'/'12)' + AYNI SATIRDA devam metni arar; (2) span bazlı (F10): get_text('dict')'te satırın İLK span'ı tam olarak '12.'/'12)' ise sayar (taranmış/görsel ağırlıklı kaynaklarda soru numarası kendi satırında yalnız durur, devam metni resim olduğu için satırda YOKTUR — yöntem 1 bunu kaçırır). Nihai tahmin ikisinin BÜYÜĞÜdür (bu koşuda: satir_bazli); her iki ham değer de kaynak_soru_tahmini_satir_bazli / kaynak_soru_tahmini_span_bazli alanlarında saklanır. Cevap anahtarı satırları (örn. '1.B 2.A 3.C') her iki yöntemde de elenir. Aktarım kontrolü her çıktı sorusunun ilk ~40 normalize karakterini kaynak metninde arar, kısa/salt-görsel sorular karşılaştırma dışı tutulur. Sayfa bazlı görsel karşılaştırması (sayfa_gorsel_karsilastirma / olasi_eksik_gorsel_sayfalar) kaynaktaki basitleştirilmiş görsel-bölge sayımını (extract.py'nin gömülü görüntü + büyük vektör çizim kümesi mantığının basit bir kopyası, extract.py'nin kendisi ÇALIŞTIRILMADI) çıktıdaki aynı kaynak sayfaya bağlı <img> sayısıyla karşılaştırır — extract.py'nin banner/tekil-dolgu istisnaları burada yok, bu yüzden bir miktar yanlış pozitif (abartılı 'olası eksik') beklenir; kesin/otomatik doğrulama için qa/dogrula.py'ye bakın.

## Özet Tablo

| Metrik | Sayı |
|---|---|
| Kaynaktaki soru sayısı (TAHMİN) | 0 |
|    — satır bazlı yöntem | 0 |
|    — span bazlı yöntem (F10) | 0 |
|    — kazanan yöntem | satir_bazli |
| Çıktıya aktarılan soru sayısı | 0 |
| — metin formatında | 0 |
| — görsel içeren | 0 |
|    (bunların salt görsel/metinsiz olanı) | 0 |
| Düzgün aktarıldığı doğrulanan (eşleşti) | 0 |
| Eşleşmedi — elle kontrol önerilir | 0 |
| Görsel içerikli — metin karşılaştırması yapılamadı | 0 |

## Elle Kontrol Önerilen Sorular

**Eşleşmedi:** yok


## Kayıp Olabilecek Kaynak Soru Numaraları (yaklaşık)

> Not: kaynak PDF'te her yeni bölüm (KUR) numaralamayı 1'den yeniden başlattığı için bu liste GLOBAL bir küme farkıdır, kesin kayıp kanıtı DEĞİLDİR — yalnızca hangi numaraların gözle kontrol edilmesi gerektiğine dair bir ipucudur.

yok

## Sayfa Bazlı Görsel Karşılaştırması (F10)

> Not: kaynak sütunu, extract.py'nin gömülü görüntü + büyük vektör çizim kümesi mantığının BASİTLEŞTİRİLMİŞ bir kopyasıyla sayılır (extract.py'nin kendisi ÇALIŞTIRILMADI); banner/tekil-dolgu istisnaları burada yok, bu yüzden kaynak sayısı gerçek görsel-bölge sayısından biraz FAZLA çıkabilir (yanlış pozitif). cikti sütunu yalnızca AKTİF (silinmemiş) bloklardaki `<img>` sayısıdır.

| Kaynak sayfa | Kaynak (tahmini) | Çıktı |
|---|---|---|
| 1 | 1 | 1 |
| 2 | 1 | 1 |
| 3 | 1 | 1 |
| 4 | 1 | 1 |
| 5 | 1 | 1 |
| 6 | 1 | 1 |
| 7 | 1 | 1 |
| 8 | 1 | 1 |
| 9 | 1 | 1 |
| 10 | 1 | 1 |
| 11 | 1 | 1 |
| 12 | 1 | 1 |
| 13 | 1 | 1 |
| 14 | 1 | 1 |
| 15 | 1 | 1 |
| 16 | 1 | 1 |
| 17 | 1 | 1 |
| 18 | 1 | 1 |
| 19 | 1 | 1 |
| 20 | 1 | 1 |
| 21 | 1 | 1 |
| 22 | 1 | 1 |
| 23 | 1 | 1 |
| 24 | 1 | 1 |
| 25 | 1 | 1 |
| 26 | 1 | 1 |
| 27 | 1 | 1 |
| 28 | 1 | 1 |
| 29 | 1 | 1 |
| 30 | 1 | 1 |
| 31 | 1 | 1 |
| 32 | 1 | 1 |
| 33 | 1 | 1 |
| 34 | 1 | 1 |
| 35 | 1 | 1 |
| 36 | 1 | 1 |
| 37 | 1 | 1 |
| 38 | 1 | 1 |
| 39 | 1 | 1 |
| 40 | 1 | 1 |
| 41 | 1 | 1 |
| 42 | 1 | 1 |
| 43 | 1 | 1 |
| 44 | 1 | 1 |
| 45 | 1 | 1 |
| 46 | 1 | 1 |

