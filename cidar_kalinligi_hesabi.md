# MediClear – Daldırma Cidar Kalınlığı Hesabı: Denklemler ve Gerekli Değerler

Oct 10, 2026 · @Gökhan

## Amaç ve yaklaşım

Cidar kalınlığı iki katmanın toplamı olarak hesaplanır: sıcak mandrel üzerinde jelleşen katman ve mandrel çekilirken sürüklenen sıvı film. Deney imkânı olmadığı için girdiler veri sayfaları ve literatürden toplanır, sonuç tek sayı değil bir aralık olarak verilir.

```latex
s_{toplam} = s_{jel} + h_{sürüklenen}
```

Hesap beş adımda yürür:

1. Aşağıdaki boş tabloyu veri sayfaları ve literatürle doldur.
2. Enerji tavanıyla kaba üst sınırı bul.
3. Isı iletimi modeliyle s\_jel(t) eğrisini hesapla, üzerine sürüklenen filmi ekle.
4. Parametre aralıklarıyla Monte Carlo çalıştır, kalınlık aralığını ve duyarlılığı çıkar.
5. Hedef cidarı yakalamak için gereken ayar aralıklarını (mandrel sıcaklığı, bekleme süresi, çekme hızı) makine tasarımına aktar.

## Denklemler

Denklemler hesap sırasına göre numaralandı (D1–D12). Tablodaki "Kullanıldığı denklem" sütunu bu numaralara bakar. Sıcaklık farklarında °C ve K aynıdır; D5'teki Arrhenius ifadesinde mutlak sıcaklık (K) kullanılır.

### D1 – Mandrel ön ısıtma (toplu kütle modeli)

Mandrelin fırında ne kadar sürede istenen sıcaklığa geldiğini verir. Geçerlilik için Biot sayısı 0,1'den küçük olmalı.

```latex
T_m(t) = T_{fırın} - (T_{fırın} - T_0)\, e^{-t/\tau}, \qquad \tau = \frac{\rho_m c_m R}{2 h_{fırın}}, \qquad Bi = \frac{h_{fırın} R}{2 k_m} < 0{,}1
```

### D2 – Enerji tavanı (jel katmanının üst sınırı)

Mandrelin depoladığı ısının tamamı plastisolü jel sıcaklığına çıkarmaya gitseydi oluşacak en büyük kalınlık. İçi boş mandrelde iç yarıçap R\_i girilir, dolu mandrelde R\_i = 0.

```latex
X = \frac{\rho_m c_m \,(R^2 - R_i^2)\,(T_{m0} - T_g)}{\rho_p c_p \, R^2 \,(T_g - T_b)}, \qquad s_{max} = R\left(\sqrt{1 + X} - 1\right)
```

İnce katman yaklaşımı (s ≪ R, dolu mandrel):

```latex
s_{max} \approx \frac{\rho_m c_m \, R \,(T_{m0} - T_g)}{2\, \rho_p c_p \,(T_g - T_b)}
```

### D3 – Isı iletimi modeli (jel cephesinin zamanla ilerlemesi)

Mandrel ve plastisol için silindirik koordinatta 1 boyutlu geçici ısı iletimi. Sayısal olarak (sonlu farklar) çözülür.

```latex
\rho c \,\frac{\partial T}{\partial t} = \frac{1}{r}\frac{\partial}{\partial r}\left(k\, r\, \frac{\partial T}{\partial r}\right)
```

Koşullar: t = 0'da mandrel (R\_i < r < R) T\_m0, plastisol (r > R) T\_b sıcaklığında. r = R'de sıcaklık ve ısı akısı süreklidir. Uzak sınırda T = T\_b. Jel kalınlığı, T ≥ T\_g olan plastisol bölgesinin kalınlığıdır:

```latex
s_{jel}(t) = \max\{\, r : T(r,t) \ge T_g \,\} - R
```

### D4 – Difüzyon yaklaşımı (kontrol için)

D3'ün sonucunun mertebesini kontrol etmek için. C katsayısı D3'ten veya literatürden bulunur.

```latex
s_{jel}(t) \approx C \sqrt{\alpha_p \, t_{bekleme}}, \qquad \alpha_p = \frac{k_p}{\rho_p c_p}
```

### D5 – Viskozitenin sıcaklığa bağlılığı

Banyo sıcaklığı değişince viskozite değişir. Referans viskozite veri sayfasından alınır.

```latex
\eta(T) = \eta_{ref} \, \exp\!\left[\frac{E_a}{R_g}\left(\frac{1}{T} - \frac{1}{T_{ref}}\right)\right]
```

### D6 – Boyutsuz sayılar (hangi film formülünün geçerli olduğuna karar)

```latex
Ca = \frac{\eta U}{\gamma}, \qquad \ell_c = \sqrt{\frac{\gamma}{\rho_p g}}
```

R ≫ ℓ\_c ve Ca < 0,1 ise D7a; R ≲ ℓ\_c ise D7b; Ca ≫ 1 ise D7c kullanılır.

### D7 – Sürüklenen film kalınlığı

D7a – Landau–Levich–Derjaguin (kalın mandrel, düşük hız):

```latex
h = 0{,}94 \, \frac{(\eta U)^{2/3}}{\gamma^{1/6} \, (\rho_p g)^{1/2}}
```

D7b – Fiber kaplama (ince mandrel):

```latex
h \approx 1{,}34 \, R \, Ca^{2/3}
```

D7c – Yüksek hız (viskoz–yerçekimi dengesi):

```latex
h \approx 0{,}8 \sqrt{\frac{\eta U}{\rho_p g}}
```

### D8 – Süzülme ve akma gerilmesi

Çekmeden sonra film yerçekimiyle incelir (x: üst uçtan mesafe). Akma gerilmesi süzülmeyi bir kalınlıkta durdurur.

```latex
h(x,t) \approx \sqrt{\frac{\eta \, x}{\rho_p g \, t}}, \qquad h_{dur} \approx \frac{\tau_y}{\rho_p g}
```

### D9 – Kür sonrası kalınlık

Plastisolde hacimsel çekme küçüktür; solventli sistemde katı oranı φ ile çarpılır.

```latex
s_{kür} \approx (1 - \varepsilon) \,(s_{jel} + h), \qquad h_{kuru} = \varphi \, h \;\text{(organosol)}
```

### D10 – Tartımla ortalama kalınlık (doğrulama)

Daldırma öncesi–sonrası kütle farkı m, kaplanan boy L.

```latex
s = \sqrt{R^2 + \frac{m}{\rho_p \pi L}} - R
```

### D11 – Spiralli tüpte toplam cidar

```latex
w = \frac{OD - ID}{2} = s_{iç} + d_{tel} + s_{dış}
```

Örnek hedef: ID 4,0 mm, OD 6,0 ± 0,1 mm → w = 1,00 ± 0,05 mm.

### D12 – Belirsizlik (Monte Carlo)

Her parametre tablodaki min–max aralığından N kez (ör. 1000) rastgele seçilir, D2–D11 her seferinde çalıştırılır. Sonuç P5–P95 aralığı olarak verilir; duyarlılık için her parametrenin sonuçla korelasyonu raporlanır.

```latex
s_{P5} \le s_{toplam} \le s_{P95}
```

## Ulaşılması gereken değerler

Hesap için 30 civarı değer gerekiyor; bunların çoğu plastisol veri sayfasından (TDS) ve malzeme tablolarından gelir. Tipik aralıklar yaklaşık değerlerdir, hesaba girmeden önce seçilen malzemenin kendi verisiyle teyit edilmeli.

### Plastisol

| Sembol | Parametre | Birim | Denklem | Tipik aralık (yaklaşık) | Nereden bulunur |
| --- | --- | --- | --- | --- | --- |
| ρ\_p | Yoğunluk | kg/m³ | D2, D3, D6–D10 | 1200–1300 | Plastisol TDS |
| c\_p | Özgül ısı | J/(kg·K) | D2, D3 | 1400–1800 | Literatür, DSC verisi |
| k\_p | Isıl iletkenlik | W/(m·K) | D3, D4 | 0,13–0,17 | Literatür |
| T\_g | Jelleşme başlangıç sıcaklığı | °C | D2, D3 | 70–100 | TDS jel eğrisi |
| T\_füz | Füzyon (tam kür) sıcaklığı | °C | Kür fırını ayarı | 160–190 | TDS |
| η\_ref | Referans viskozite | Pa·s | D5–D8 | 1–10 | TDS (Brookfield) |
| T\_ref | Viskozitenin ölçüldüğü sıcaklık | °C | D5 | 23–25 | TDS |
| E\_a | Viskozite aktivasyon enerjisi | J/mol | D5 | Eğriden hesaplanır | TDS viskozite–sıcaklık eğrisi |
| γ | Yüzey gerilimi | N/m | D6, D7 | 0,030–0,040 | Literatür |
| τ\_y | Akma gerilmesi | Pa | D8 | 0–20 | Reoloji verisi, TDS |
| ε | Kürde hacimsel çekme oranı | – | D9 | Birkaç % | TDS, literatür |

### Mandrel

| Sembol | Parametre | Birim | Denklem | Tipik aralık (yaklaşık) | Nereden bulunur |
| --- | --- | --- | --- | --- | --- |
| – | Malzeme | – | – | 304 paslanmaz veya Al | Tasarım kararı |
| ρ\_m | Yoğunluk | kg/m³ | D1–D3 | 304: 8000; Al: 2700 | Malzeme tablosu |
| c\_m | Özgül ısı | J/(kg·K) | D1–D3 | 304: 500; Al: 900 | Malzeme tablosu |
| k\_m | Isıl iletkenlik | W/(m·K) | D1, D3 | 304: 16; Al: 200 | Malzeme tablosu |
| R | Dış yarıçap (= ID/2) | mm | D1–D3, D7b, D10 | 1,0–5,5 (ID 2–11) | Ürün numarası |
| R\_i | İç yarıçap (içi boşsa) | mm | D2, D3 | 0 (dolu) | Tasarım kararı |
| L | Daldırma boyu | mm | D10 | Tasarım kararı | Makine tedarikçisi teklifi (gizli) |

### Proses

| Sembol | Parametre | Birim | Denklem | Tipik aralık (yaklaşık) | Nereden bulunur |
| --- | --- | --- | --- | --- | --- |
| T\_fırın | Ön ısıtma fırını sıcaklığı | °C | D1 | Tasarım kararı | Makine tedarikçisi teklifi (gizli) |
| h\_fırın | Fırın konveksiyon katsayısı | W/(m²·K) | D1 | 20–100 | Isı transferi kitabı, fırın üreticisi |
| t\_ön | Ön ısıtma süresi | s | D1 | Tasarım değişkeni | Çevrim süresi hesabı |
| T\_m0 | Daldırma anında mandrel sıcaklığı | °C | D2, D3 | D1'den hesaplanır | – |
| T\_b | Banyo sıcaklığı | °C | D2, D3, D5 | 20–40 | Tasarım kararı |
| t\_bekleme | Banyoda bekleme süresi | s | D3, D4 | Tasarım değişkeni | – |
| U | Çekme hızı | mm/s | D6, D7 | Tasarım değişkeni | Servo eksen sınırları |
| t\_süz | Çekme sonrası süzülme süresi | s | D8 | Tasarım değişkeni | Kür fırınına transfer süresi |
| g | Yerçekimi ivmesi | m/s² | D6–D10 | 9,81 | Sabit |

### Ürün ve doğrulama

| Sembol | Parametre | Birim | Denklem | Tipik aralık (yaklaşık) | Nereden bulunur |
| --- | --- | --- | --- | --- | --- |
| ID | İç çap | mm | D11 | 2,0–11,0 | İhale şartnameleri |
| OD | Dış çap | mm | D11 | ID 4,0 → 6,0 ± 0,1 | Şartname 2025-2442972 |
| d\_tel | Yay teli çapı | mm | D11 | 0,2–0,5 | Yay tedarikçisi |
| m | Kaplama kütlesi | g | D10 | Ölçülür | Tedarikçi denemesi |
| C | Difüzyon katsayısı | – | D4 | D3'ten bulunur | Model |

## Veri giriş tablosu

Bulduğun değerleri bu tabloya yaz; min ve max sütunları Monte Carlo (D12) için, nominal sütunu tek hesap için kullanılır. Kaynağı olmayan değer hesaba girmesin.

| Sembol | Parametre | Birim | Min | Nominal | Max | Kaynak | Not |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ρ\_p | Plastisol yoğunluğu | kg/m³ |  |  |  |  |  |
| c\_p | Plastisol özgül ısısı | J/(kg·K) |  |  |  |  |  |
| k\_p | Plastisol ısıl iletkenliği | W/(m·K) |  |  |  |  |  |
| T\_g | Jelleşme başlangıç sıcaklığı | °C |  |  |  |  |  |
| T\_füz | Füzyon sıcaklığı | °C |  |  |  |  |  |
| η\_ref | Referans viskozite | Pa·s |  |  |  |  |  |
| T\_ref | Viskozite ölçüm sıcaklığı | °C |  |  |  |  |  |
| E\_a | Viskozite aktivasyon enerjisi | J/mol |  |  |  |  |  |
| γ | Yüzey gerilimi | N/m |  |  |  |  |  |
| τ\_y | Akma gerilmesi | Pa |  |  |  |  |  |
| ε | Kürde hacimsel çekme | – |  |  |  |  |  |
| – | Mandrel malzemesi | – |  |  |  |  |  |
| ρ\_m | Mandrel yoğunluğu | kg/m³ |  |  |  |  |  |
| c\_m | Mandrel özgül ısısı | J/(kg·K) |  |  |  |  |  |
| k\_m | Mandrel ısıl iletkenliği | W/(m·K) |  |  |  |  |  |
| R\_i | Mandrel iç yarıçapı | mm |  |  |  |  |  |
| L | Daldırma boyu | mm |  |  |  |  |  |
| T\_fırın | Ön ısıtma fırını sıcaklığı | °C |  |  |  |  |  |
| h\_fırın | Fırın konveksiyon katsayısı | W/(m²·K) |  |  |  |  |  |
| t\_ön | Ön ısıtma süresi | s |  |  |  |  |  |
| T\_b | Banyo sıcaklığı | °C |  |  |  |  |  |
| t\_bekleme | Banyoda bekleme süresi | s |  |  |  |  |  |
| U | Çekme hızı | mm/s |  |  |  |  |  |
| t\_süz | Süzülme süresi | s |  |  |  |  |  |
| d\_tel | Yay teli çapı | mm |  |  |  |  |  |

### Numara bazında hedefler ve sonuçlar

Her ET numarası için bir satır. Sol taraf girdi, sağ taraf hesap sonucudur.

| ID (mm) | R (mm) | OD hedefi (mm) | w hedefi (mm) | d\_tel (mm) | T\_m0 (°C) | t\_bekleme (s) | U (mm/s) | s\_jel (mm) | h (mm) | s\_toplam (mm) | P5–P95 (mm) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |

## Kaynak önerileri ve doldurma notları

En çok değer tek bir belgeden gelir: seçilen plastisolün teknik veri sayfası. Önce o belgeyi temin etmek, tablonun yaklaşık yarısını doldurur.

- **Plastisol veya reçine tedarikçisi:** TDS'nin yanında jel eğrisi (sıcaklığa karşı jelleşme), viskozite–sıcaklık eğrisi ve mümkünse akma gerilmesi verisi istenmeli. E\_a, viskozite–sıcaklık eğrisine D5 uydurularak hesaplanır.
- **Malzeme tabloları:** Mandrel özellikleri (ρ\_m, c\_m, k\_m) için ders kitabı ekleri veya malzeme veri tabanları yeterli.
- **Isı transferi kitabı:** h\_fırın için zorlanmış konveksiyonda silindir korelasyonları (ör. Churchill–Bernstein) kullanılabilir; fırın hava hızı makine tedarikçisinden istenmeli.
- **Makine tedarikçisi teklifi (gizli iç belge):** fırın sıcaklık aralığı, daldırma boyu, servo eksen hassasiyeti.
- **İhale şartnameleri:** OD/ID hedefleri ve toleranslar.
- **Tedarikçi denemesi:** m ve kalınlık ölçümü (D10) için makine tedarikçisi, DEL veya plastisol tedarikçisinden numune denemesi istenebilir; bu, modeli doğrulayan tek gerçek veri olur.

Doldururken dikkat edilecekler:

- Denklemlere SI birimleriyle girilmeli: mm → m, Pa·s, J/(kg·K). Tablodaki mm değerleri hesaptan önce 1000'e bölünmeli.
- Aynı plastisol için tüm değerler aynı kaynaktan alınmalı; farklı ürünlerin verilerini karıştırmak hatalı sonuç verir.
- Bir değer için tek kaynak varsa min ve max, nominalin ±%10'u olarak alınabilir; bu varsayım Not sütununa yazılmalı.
- "Tipik aralık" sütunundaki değerler bu belgede kaynak taranmadan, genel bilgiyle yazıldı; raporda kaynak olarak kullanılmamalı.
