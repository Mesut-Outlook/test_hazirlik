# Dönüşüm Raporu — 9. TEMA

Oluşturulma: 2026-07-10T13:54:08+03:00
Sürüm: 1
Kaynak: `C:\Users\egemen\Documents\_PROJELER\Test Hazırlık\temalar\09-2-tema\kaynak\2.tema.pdf`

> Yöntem: Kaynak soru sayısı için İKİ bağımsız TAHMİN hesaplanır — (1) satır bazlı: satır başında '12.'/'12)' + AYNI SATIRDA devam metni arar; (2) span bazlı (F10): get_text('dict')'te satırın İLK span'ı tam olarak '12.'/'12)' ise sayar (taranmış/görsel ağırlıklı kaynaklarda soru numarası kendi satırında yalnız durur, devam metni resim olduğu için satırda YOKTUR — yöntem 1 bunu kaçırır). Nihai tahmin ikisinin BÜYÜĞÜdür (bu koşuda: span_bazli); her iki ham değer de kaynak_soru_tahmini_satir_bazli / kaynak_soru_tahmini_span_bazli alanlarında saklanır. Cevap anahtarı satırları (örn. '1.B 2.A 3.C') her iki yöntemde de elenir. Aktarım kontrolü her çıktı sorusunun ilk ~40 normalize karakterini kaynak metninde arar, kısa/salt-görsel sorular karşılaştırma dışı tutulur. Sayfa bazlı görsel karşılaştırması (sayfa_gorsel_karsilastirma / olasi_eksik_gorsel_sayfalar) kaynaktaki basitleştirilmiş görsel-bölge sayımını (extract.py'nin gömülü görüntü + büyük vektör çizim kümesi mantığının basit bir kopyası, extract.py'nin kendisi ÇALIŞTIRILMADI) çıktıdaki aynı kaynak sayfaya bağlı <img> sayısıyla karşılaştırır — extract.py'nin banner/tekil-dolgu istisnaları burada yok, bu yüzden bir miktar yanlış pozitif (abartılı 'olası eksik') beklenir; kesin/otomatik doğrulama için qa/dogrula.py'ye bakın.

## Özet Tablo

| Metrik | Sayı |
|---|---|
| Kaynaktaki soru sayısı (TAHMİN) | 111 |
|    — satır bazlı yöntem | 0 |
|    — span bazlı yöntem (F10) | 111 |
|    — kazanan yöntem | span_bazli |
| Çıktıya aktarılan soru sayısı | 111 |
| — metin formatında | 33 |
| — görsel içeren | 78 |
|    (bunların salt görsel/metinsiz olanı) | 78 |
| Düzgün aktarıldığı doğrulanan (eşleşti) | 0 |
| Eşleşmedi — elle kontrol önerilir | 0 |
| Görsel içerikli — metin karşılaştırması yapılamadı | 111 |

## Elle Kontrol Önerilen Sorular

**Eşleşmedi:** yok


## Kayıp Olabilecek Kaynak Soru Numaraları (yaklaşık)

> Not: kaynak PDF'te her yeni bölüm (KUR) numaralamayı 1'den yeniden başlattığı için bu liste GLOBAL bir küme farkıdır, kesin kayıp kanıtı DEĞİLDİR — yalnızca hangi numaraların gözle kontrol edilmesi gerektiğine dair bir ipucudur.

1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55

## Sayfa Bazlı Görsel Karşılaştırması (F10)

> Not: kaynak sütunu, extract.py'nin gömülü görüntü + büyük vektör çizim kümesi mantığının BASİTLEŞTİRİLMİŞ bir kopyasıyla sayılır (extract.py'nin kendisi ÇALIŞTIRILMADI); banner/tekil-dolgu istisnaları burada yok, bu yüzden kaynak sayısı gerçek görsel-bölge sayısından biraz FAZLA çıkabilir (yanlış pozitif). cikti sütunu yalnızca AKTİF (silinmemiş) bloklardaki `<img>` sayısıdır.

| Kaynak sayfa | Kaynak (tahmini) | Çıktı |
|---|---|---|
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
| 45 | 2 | 2 |
| 46 | 6 | 6 |
| 47 | 6 | 6 |
| 48 | 1 | 1 |
| 50 | 6 | 6 |
| 51 | 6 | 6 |
| 52 | 6 | 6 |
| 53 | 6 | 6 |
| 54 | 6 | 6 |
| 55 | 6 | 6 |
| 56 | 6 | 6 |
| 57 | 1 | 1 |
| 58 | 1 | 1 |
| 59 | 1 | 1 |
| 60 | 3 | 3 |
| 61 | 6 | 6 |
| 62 | 6 | 6 |
| 63 | 6 | 6 |
| 64 | 5 | 5 |
| 65 | 6 | 6 |
| 66 | 6 | 6 |
| 67 | 5 | 5 |
| 68 | 6 | 6 |
| 69 | 6 | 6 |
| 70 | 1 | 1 |
| 71 | 1 | 1 |
| 72 | 1 | 1 |
| 73 | 1 | 1 |
| 74 | 1 | 1 |
| 75 | 1 | 1 |
| 76 | 1 | 1 |
| 77 | 1 | 1 |
| 78 | 1 | 1 |
| 79 | 1 | 1 |
| 80 | 1 | 1 |
| 81 | 1 | 1 |
| 82 | 1 | 1 |
| 83 | 1 | 1 |
| 84 | 1 | 1 |

