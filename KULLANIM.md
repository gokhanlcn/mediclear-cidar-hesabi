# MediClear Cidar Hesabı – Kullanım Kılavuzu

Bu program, spiralli PVC endotrakeal tüpün daldırma (dip molding) ile üretiminde oluşacak cidar
kalınlığını deney yapmadan, veri sayfası ve literatür değerleriyle tahmin eder. Denklemlerin hepsi
`cidar_kalinligi_hesabi.md` dosyasındadır (D1–D12).

> **Önemli:** Sonuçlar modele dayalı tahmindir; kesin değerler devreye almada ölçümle kalibre edilmelidir.

---

## 1. Python kurulumu (yalnızca bir kez)

Program Python ile çalışır. Bilgisayarında Python 3.11 veya daha yenisi yoksa:

### Windows
1. Tarayıcıda **https://www.python.org/downloads/** adresine git.
2. Sarı **Download Python 3.12.x** (veya daha yeni) düğmesine bas ve dosyayı indir.
3. İndirilen dosyaya çift tıkla. Açılan **ilk ekranın en altında** iki kutu vardır:
   - ☑ **Add python.exe to PATH** → **MUTLAKA işaretle.** (En sık yapılan hata bunu unutmaktır.)
   - ☑ Use admin privileges… → işaretli kalabilir.
4. **Install Now**'a bas, kurulum bitince **Close**'a bas.

### macOS
1. **https://www.python.org/downloads/** adresinden macOS kurulum dosyasını (.pkg) indir.
2. Çift tıklayıp **Devam → Kabul et → Yükle** adımlarını izle.

### Linux
Paket yöneticisiyle `python3` ve `python3-venv` paketlerini kur (ör. Ubuntu: `sudo apt install python3 python3-venv`).

---

## 2. Programı açmak

### Windows
1. Program klasörünü aç (içinde `app.py`, `baslat.bat` ve bu dosya var).
2. **`baslat.bat`** dosyasına **çift tıkla**.
3. Siyah bir pencere açılır.
   - **İlk açılışta** gerekli paketler internetten kurulur. Bu birkaç dakika sürer; pencereyi kapatma.
   - Sonraki açılışlarda program birkaç saniyede açılır.
4. Tarayıcı kendiliğinden açılır ve programı gösterir (adres: `http://localhost:8501`).
5. **Kapatmak için** siyah pencereyi kapat.

> Windows "Bilinmeyen yayımcı" / "Windows kişisel bilgisayarınızı korudu" uyarısı verirse
> **Ek bilgi → Yine de çalıştır**'a bas.

### macOS / Linux
1. Terminali aç, program klasörüne gel (ör. `cd ~/Desktop/hesaplayıcı`).
2. İlk seferde: `chmod +x baslat.sh`
3. Her seferde: `./baslat.sh`
4. Kapatmak için terminalde **Ctrl+C**.

### Programı arkadaşına göndermek
Klasörü zip'lerken **`.venv` klasörünü dahil etme** (çok büyüktür ve başka bilgisayarda çalışmaz).
Program `.venv` yoksa veya bozuksa kendisi yeniden kurar. Veri setini paylaşmak için
**1. Parametre girişi → Excel olarak kaydet** dosyasını göndermen yeterli.

---

## 3. Örnek bir hesabın baştan sona yapılışı

Sol menüdeki sayfalar hesap sırasını izler. Her grafiğin altında **"Bu grafik ne gösteriyor?"**
kutusu vardır.

1. **1. Parametre girişi**
   - Elinde veri yoksa **📋 Örnek değerlerle doldur**'a bas. Tüm değerler "YAKLAŞIK" işaretlidir.
   - Gerçek veriyle çalışırken her satırın **Nominal**, **Min**, **Max** ve **Kaynak** sütunlarını doldur.
     Hücreye çift tıkla, yaz, **Enter**'a bas.
   - Satır renkleri: 🟢 tamam · 🟡 kaynak yok · 🔴 hata (mesaj ne yapacağını söyler).
   - Kaynak sütunu boşken hesap yapılmaz (.md kuralı). Denemek için sol menüden **Taslak mod**'u aç.
   - **Hesap ayarları**: T_m0 doğrudan mı girilecek yoksa fırından (D1) mı hesaplanacak, spiral var mı,
     mandrel malzemesi.
   - **E_a yardımcısı** (Plastisol sekmesi): TDS'deki viskozite–sıcaklık eğrisinden en az iki nokta gir;
     E_a hesaplanır ve tabloya yazılır.
   - **Excel olarak kaydet** ile veri setini sakla; sonra **yükle** ile geri getir.
2. **2. Mandrel ön ısıtma (D1)** – Mandrelin fırında hedef sıcaklığa kaç saniyede ulaştığını ve
   Biot kontrolünü gösterir.
3. **3. Jel katmanı (D2–D4)** – Jel kalınlığının zamanla artışı, radyal sıcaklık profili (zaman
   kaydırıcısıyla) ve sıcaklık haritası.
4. **4. Sürüklenen film (D5–D8)** – Viskozite, hangi film formülünün geçerli olduğu, çekme hızına göre
   film kalınlığı ve süzülme.
5. **5. Toplam cidar (D9, D11)** – Spiralli tüpte w = s₁ + d_tel + s₂; hedefle karşılaştırma
   (**✅ Uygun / ❌ Uygun değil**).
6. **6. Tartım doğrulama (D10)** – Deneme numunesinin kütle farkını gir; ölçülen ortalama kalınlık
   modelle karşılaştırılır.
7. **7. Belirsizlik – Monte Carlo (D12)** – **Monte Carlo'yu çalıştır**'a bas. P5–P95 aralığı, hedefi
   tutturma olasılığı ve sonucu en çok etkileyen parametreler (tornado grafiği).
8. **8. Ters tasarım** – **Haritayı hesapla**'ya bas. Hedef cidarı veren mandrel sıcaklığı ve bekleme
   süresi bölgesi kırmızı bantla gösterilir; altındaki tablo fırın ve çevrim süresi tasarımı içindir.
9. **9. Numara bazında sonuçlar ve rapor**
   - Her ET numarası için bir satır ekle, **Tümünü hesapla**'ya bas.
   - **Excel** ile tüm girdi, kaynak ve sonuçları indir.
   - **Özet raporu hazırla → indir**. HTML dosyasını çift tıklayıp aç; PDF için tarayıcıda
     **Yazdır → PDF olarak kaydet** (internet gerekmez).

**Grafikleri PNG olarak kaydetmek:** fareyi grafiğin üstüne getir, sağ üstte çıkan **📷 kamera**
simgesine tıkla.

---

## 4. Sık karşılaşılan sorunlar

| Sorun | Çözüm |
| --- | --- |
| `baslat.bat` "Python bulunamadı" diyor | Python'u kur ve **Add python.exe to PATH** kutusunu işaretle (bkz. bölüm 1). Kurulumdan sonra bilgisayarı yeniden başlatmak gerekebilir. |
| İlk kurulumda "Paketler kurulamadı" | İnternet bağlantını kontrol et. Okul/şirket ağında güvenlik duvarı engelliyor olabilir; başka ağda dene. Sonra klasördeki `.venv` klasörünü silip tekrar çalıştır. |
| Tarayıcı açılmadı | Tarayıcıya elle **http://localhost:8501** yaz. |
| "Program zaten açık" yazıp kapanıyor | Program başka bir pencerede çalışıyor; tarayıcıdaki sekmeyi kullan ya da diğer siyah pencereyi kapatıp tekrar aç. |
| Sayfada "Parametre tablosunda … hata var" | **1. Parametre girişi**'ne dön; 🔴 satırları ve en alttaki "Kontrol sonucu" mesajlarını düzelt. |
| Sayfada "… parametrenin kaynağı boş" | Kaynak sütununu doldur ya da sol menüden **Taslak mod**'u aç. |
| "T_g, T_b'den büyük olmalı" | Jel sıcaklığı banyo sıcaklığından yüksek olmalı; TDS'deki jel sıcaklığını kontrol et. |
| "T_m0, T_g'den büyük olmalı" | Mandrel jel sıcaklığının altındaysa jel oluşmaz; fırın sıcaklığını veya ön ısıtma süresini artır. |
| Monte Carlo / harita yavaş | Deneme sayısını (N) veya ızgara çözünürlüğünü düşür; hızlı modu kullan. |
| Sonuçlar "eski" uyarısı | Girdiler değişti; ilgili sayfada düğmeye tekrar bas. |
| Program pencereyi kapatınca durdu | Normaldir; siyah pencere programın kendisidir. Tekrar `baslat.bat`. |
| Yaptığım değişiklikler kayboldu | Tarayıcı sayfasını yenilemek (F5) verileri sıfırlar. Çalışmayı **Excel olarak kaydet** ile sakla. |

---

## 5. Geliştiriciler için

- Hesap kodu `physics/` klasöründedir (arayüzden bağımsız, SI birimleri). Arayüz `app.py`, `sayfalar/`, `ui/`.
- Testler: `.venv\Scripts\python -m pytest -q` (macOS/Linux: `.venv/bin/python -m pytest -q`).
