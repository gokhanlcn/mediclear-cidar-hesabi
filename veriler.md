# MediClear – Daldırma İstasyonu Malzeme Parametreleri

Oct 23, 2026 · @Gökhan

## Amaç ve kapsam

Bu rapor, daldırma istasyonu süre hesabında kullanılan malzeme parametrelerini ve her birinin dayanağını listeler. Değerler yalnızca online kaynaklardan alınmıştır; kaynak bulunamayan değerler "varsayım" olarak işaretlenmiştir. Rapor yeni parametrelerle genişletilecektir.

## Plastisol formülasyonu

Kabul edilen formülasyon: **100 phr emülsiyon (pasta) PVC + 60 phr DEHT + 3 phr Ca/Zn stabilizör**, dolgusuz ve pigmentsiz.

| Bileşen | Miktar | Neden / Kaynak |
| --- | --- | --- |
| Pasta PVC reçine | 100 phr | Tıbbi cihaz için onaylı K70 sınıfı pasta kaliteleri mevcut \[5\] |
| DEHT (DOTP) | 60 phr | Gerçek ET tüpünde %36,6 plastifiyan ölçülmüş (≈ 58 phr) \[1\]; DEHP yerine MDR/REACH nedeniyle DEHT seçildi; DEHT için eşdeğer miktar 60–65 phr \[2\]; 100/60 PVC/DOTP endüstride standart test oranı \[6\] |
| Ca/Zn stabilizör | 3 phr | Plastisol test formülasyonlarında 3 phr ısı stabilizörü kullanılıyor \[2\] |

Hesaplarda stabilizör plastifiyan payına katılmıştır. Kütle oranları:

```latex
w_{PVC} \approx 0{,}625 \qquad w_{pl} \approx 0{,}375
```

ESBO miktarı kaynakla bulunamadığı için formülasyona katılmamıştır (varsayım).

## Plastisol parametreleri

Tür: **Doğrudan** = bizim sistemimiz için ölçülmüş değer; **Dolaylı** = saf bileşen verisinden karışım kuralıyla hesap; **Varsayım** = özel veri yok, genel literatürden seçildi.

| Parametre | Seçilen değer | Aralık | Tür | Neden / Kaynak |
| --- | --- | --- | --- | --- |
| Yoğunluk, ρ | 1200 kg/m³ | 1180–1220 | Dolaylı | Ters karışım kuralı: ρ\_PVC = 1388 kg/m³ \[7\], ρ\_DEHT = 980 kg/m³ \[2\]. Tıbbi sınıf DOTP/TOTM'li PVC compound'ları 1,18–1,22 g/cm³ ile doğrulanıyor \[4\] |
| Özgül ısı, c\_p | 1350 J/(kg·K) | 1300–1400 | Dolaylı | Kütle ağırlıklı ortalama: c\_p,PVC = 1020 J/(kg·K) (20 °C) \[7\]; c\_p,pl = 1804 J/(kg·K) (DEHP, 25 °C; DEHT'in izomeri) \[8\], NOAA ile ≈ 2000 \[9\]. Oda sıcaklığı değeri; sıcaklıkla artar |
| Isıl iletkenlik, k | 0,14 W/(m·K) | 0,13–0,15 | Dolaylı | Bileşenler birbirine çok yakın: k\_pl = 0,135 W/(m·K) (21 °C) \[9\], k\_PVC = 0,130–0,143 W/(m·K) (15–45 °C) \[7\]. Karışım modelinin etkisi ihmal edilebilir |
| Jelleşme başlangıcı, T\_jel,0 | 70 °C | 65–100 | Varsayım | DEHT'e özel veri bulunamadı. Genel literatürde DSC ilk endotermik pik 70–100 °C \[10\] |
| Jel noktası, T\_jel | 108 °C | – | Doğrudan | Dolgusuz DOTP (=DEHT) plastisolü, reometre 5 °C/dk; hot bench testi 108,9 °C \[3\]. Not: ölçüm 100 phr ile, bizim formülasyon 60 phr |
| Füzyon sıcaklığı, T\_füz | 171 °C | 170–180 | Doğrudan | Aynı ölçüm \[3\]. Plastisol füzyon testlerinde kullanılan 177–204 °C fırın aralığıyla tutarlı \[2\] |
| Referans viskozite, η\_ref | 3 Pa·s | 2–6 | Dolaylı | Brookfield, düşük kayma hızı. 100/60 DOTP plastisolü eldiven/daldırma kalitelerinde 2–6 Pa·s \[6\]; 70 phr DOTP karışımı 1,7–2,4 Pa·s (20 rpm, ≈25 °C) \[12\]; 65 phr DEHT grafik aralığı 5–25 Pa·s, DEHT en düşük \[2\]. Hesaplayıcının tipik aralığı (1–10) içinde |
| Viskozite ölçüm sıcaklığı, T\_ref | 23 °C | 23–25 | Doğrudan | DEHT plastisol viskozitesi 23 °C, 20 rpm, #6 iğne ile ölçülüyor \[2\]; düşük kayma viskozitesi standardı ASTM D1824, daldırma prosesiyle ilişkili \[11\] |
| Viskozite aktivasyon enerjisi, E\_a | 40 800 J/mol | 35 500–40 800 | Dolaylı | DOTP TDS viskozite–sıcaklık tablosundan (20 °C: 86 mPa·s, 40 °C: 29,5 mPa·s) \[13\]; 20–80 °C uydurmasıyla 35 500 J/mol. Plastifiyan verisidir; plastisol üzerinde 3 900–4 600 J/mol ölçülmüş \[14\] → duyarlılıkta alt sınır |
| Yüzey gerilimi, γ | 0,032 N/m | 0,032–0,035 | Dolaylı | Plastisol yüzeyi sıvı fazdan (plastifiyan) oluşur. DOTP (=DEHT) TDS: 32,3 mN/m \[13\]; DEHT tahmini 35,4 ± 3,0 mN/m \[15\] |
| Akma gerilmesi, τ\_y | 0 Pa | 0–20 (duyarlılık) | Varsayım | Sayısal veri bulunamadı. Daldırma için önerilen pasta PVC "neredeyse Newtonian" akış gösteriyor \[16\]; akma gerilmesi dolgulu, polidispers formülasyonlarda \[17\] ve plastisol yaşlandıkça \[18\] ortaya çıkıyor. Bizim formülasyon dolgusuz |
| Kürde hacimsel çekme, ε | 0,04 | 0,027–0,053 | Dolaylı | Plastisolde buharlaşacak çözücü yok \[19\]; sıvı (1200 kg/m³) ve füzyonlu tıbbi compound (1180–1220 kg/m³ \[4\]) yoğunlukları ayırt edilemiyor → karışma çekmesi ≈ 0. Asıl katkı 171 °C → 23 °C ısıl çekme; PVC-P için α = 60–120 × 10⁻⁶ 1/K \[20\] |

Kullanılan karışım bağıntıları:

```latex
\rho_{plastisol} = \frac{1}{\dfrac{w_{PVC}}{\rho_{PVC}} + \dfrac{w_{pl}}{\rho_{pl}}} = \frac{1}{\dfrac{0{,}625}{1388} + \dfrac{0{,}375}{980}} \approx 1200\ \mathrm{kg/m^3}
```

```latex
c_{p,plastisol} = w_{PVC}\,c_{p,PVC} + w_{pl}\,c_{p,pl} = 0{,}625 \cdot 1020 + 0{,}375 \cdot 1804 \approx 1310\ \mathrm{J/(kg\,K)}
```

Viskozitenin sıcaklık bağımlılığı (Arrhenius) ve E\_a'nın iki noktadan hesabı:

```latex
\eta(T) = \eta_{ref}\,\exp\!\left[\frac{E_a}{R}\left(\frac{1}{T} - \frac{1}{T_{ref}}\right)\right]
```

```latex
E_a = \frac{R\,\ln(\eta_1/\eta_2)}{1/T_1 - 1/T_2} = \frac{8{,}314 \cdot \ln(86/29{,}5)}{1/293{,}15 - 1/313{,}15} \approx 40\,800\ \mathrm{J/mol}
```

Kürde hacimsel çekme (ısıl çekme, β = 3α, orta değer α = 90 × 10⁻⁶ 1/K):

```latex
\varepsilon \approx \beta\,\Delta T = 3\alpha\,(T_{f\ddot{u}z} - T_{oda}) = 3 \cdot 90\times10^{-6} \cdot (171 - 23) \approx 0{,}040
```

Açık noktalar: jelleşme başlangıcı varsayımdır (65–100 °C duyarlılığı denenmeli). E\_a plastifiyan verisinden alındı; plastisolün gerçek E\_a değeri daha düşük olabilir (3 900 J/mol ile duyarlılık denenmeli). Arrhenius yaklaşık 45 °C üstünde, jelleşme başladığı için geçerli değildir. τ\_y = 0 varsayımdır; yaşlanmış plastisol için 0–20 Pa ile duyarlılık denenmeli. ε oda sıcaklığı α değerinden hesaplandı; yüksek sıcaklıkta α arttığı için gerçek çekme biraz daha büyük olabilir.

## Mandrel parametreleri

Mandrel malzemesi grubun mandrel seçim raporu ve Pugh matrisiyle **elektropolisajlı AISI 316L paslanmaz çelik** olarak seçilmiştir \[23\]. Malzeme özellikleri açık veri sayfalarıyla doğrulanmıştır.

| Parametre | Seçilen değer | Tür | Neden / Kaynak |
| --- | --- | --- | --- |
| Mandrel yoğunluğu, ρ\_m | 7990 kg/m³ | Doğrudan | 316L, 20 °C: 7,99 g/cm³ \[21\], \[22\] |
| Mandrel özgül ısısı, c\_m | 500 J/(kg·K) | Doğrudan | 316L, 0–100 °C: 0,5 J/(g·°C) \[22\] |
| Mandrel ısıl iletkenliği, k\_m | 16,2 W/(m·K) | Doğrudan | 316L, 100 °C: 16,2 W/(m·K) \[21\], \[22\]; 500 °C'de 21,4 W/(m·K) \[22\] |
| Mandrel iç yarıçapı, R\_i | 0 mm | Tasarım kararı | Dolu mandrel \[23\] |
| Daldırma boyu, L | 400 mm | Tasarım kararı | Kaplama boyu 400 mm olarak kesinleşti (tüp boyu 360 mm); makine tedarikçisi teklifiyle uyumlu \[24\] |

Not: k\_m değeri 100 °C içindir; mandrelin çalışma sıcaklıkları (oda sıcaklığı–fırın) aralığında k\_m yaklaşık 16–20 W/(m·K) arasında değişir.

## Proses parametreleri

Bu parametrelerin çoğu ters tasarımla (hedef cidar kalınlığı ve çevrim süresinden geriye doğru) belirlenecektir. Aşağıdaki değerler hesabın başlangıç noktasıdır.

| Parametre | Başlangıç değeri | Tür | Neden / Kaynak |
| --- | --- | --- | --- |
| Ön ısıtma fırını sıcaklığı, T\_fırın | 200 °C | Ters tasarım (başlangıç kaynaklı) | Makine tedarikçisi teklifindeki fırın aralığında \[24\]; plastisol daldırmada mandrel ön ısıtma 190–220 °C \[19\], 171–193 °C \[25\] |
| Fırın konveksiyon katsayısı, h\_fırın | 50 W/(m²·K) | Dolaylı + varsayım | Churchill–Bernstein, D = 8 mm silindir, hava 400 K özellikleri \[26\]. Hava hızı 2 m/s varsayıldı (varsayım); 1–5 m/s için h = 37–83 W/(m²·K). Işınım dahil değil |
| Ön ısıtma süresi, t\_ön | D1'den hesaplanır | Ters tasarım | T\_m0 hedefine ulaşmak için gereken süre. Mertebe: zaman sabiti τ ≈ 200 s (aşağıda) |
| Mandrelin fırına giriş sıcaklığı, T\_0 | 23 °C | Tasarım kararı | Mandrel sıyırma/soğutma sonrası oda sıcaklığında kabul edildi; T\_ref ile aynı |
| 1. daldırmada mandrel sıcaklığı, T\_m0 | D1'den hesaplanır | Ters tasarım | 0,55 mm iç katmanı verecek sıcaklık. Kontrol: jelleşme başlangıcının (70 °C) üzerinde olmalı |
| Banyo sıcaklığı, T\_b | 23 °C | Tasarım kararı | T\_ref ile eşit alındı → banyoda η = η\_ref \[2\]; Arrhenius geçerlilik sınırı (≤ 42 °C) içinde \[14\]; soğuk banyo erken jelleşmeyi ve viskozite yaşlanmasını sınırlar |
| 1. daldırmada bekleme süresi, t\_bekleme | 5 s | Ters tasarım (başlangıç kaynaklı) | Isıtılmış mandrelde 5–15 s bekleme ile 0,76–1,5 mm jel tabakası \[25\]; hedef 0,55 mm olduğundan alt sınır alındı |
| Çekme hızı, U | Ters tasarım | Ters tasarım | D6–D7 ile sürüklenen film kalınlığından bulunacak; üst sınırı servo eksen belirler |
| Süzülme süresi, t\_süz | Ters tasarım | Ters tasarım | Çekmeden kür fırınına transfere kadar geçen süre; hat endeksleme süresine bağlı |
| Yerçekimi ivmesi, g | 9,81 m/s² | Sabit | – |

Fırın konveksiyon katsayısı (Churchill–Bernstein, silindir üzerinde çapraz akış):

```latex
\overline{Nu}_D = 0{,}3 + \frac{0{,}62\,Re_D^{1/2}\,Pr^{1/3}}{\left[1+(0{,}4/Pr)^{2/3}\right]^{1/4}}\left[1+\left(\frac{Re_D}{282\,000}\right)^{5/8}\right]^{4/5}, \qquad h = \frac{\overline{Nu}_D\,k_{hava}}{D}
```

```latex
Re_D = \frac{V D}{\nu} = \frac{2 \cdot 0{,}008}{26{,}41\times10^{-6}} \approx 606 \;\Rightarrow\; \overline{Nu}_D \approx 12{,}3 \;\Rightarrow\; h \approx \frac{12{,}3 \cdot 0{,}0338}{0{,}008} \approx 52\ \mathrm{W/(m^2 K)}
```

Ön ısıtma zaman sabiti (dolu silindir, toplu kapasite):

```latex
\tau = \frac{\rho_m\,c_m\,R}{2\,h} = \frac{7990 \cdot 500 \cdot 0{,}004}{2 \cdot 50} \approx 200\ \mathrm{s}
```

## Ürün ölçüleri

Hat No 8,0 referans boyutuna göre tasarlanıyor; bu nedenle ölçüler aralık değil, tek değerdir. No 8,0, ihale talebinin %31,0'ı ile en çok istenen spiralli tüp boyutudur \[27\].

| Parametre | Değer | Tür | Neden / Kaynak |
| --- | --- | --- | --- |
| İç çap, ID | 8,0 mm (R = 4,0 mm) | Tasarım kararı | No 8,0 = iç çap 8,0 mm (ISO 5361 numaralandırması) \[28\]; mandrel dış çapına eşit \[27\] |
| Dış çap hedefi, OD | 10,8 mm | Doğrudan | Piyasadaki takviyeli No 8,0 tüpler: Shiley Reinforced ve Rüsch Flex 10,8 mm \[27\]; et kalınlığı (10,8 − 8,0)/2 = 1,40 mm = 0,55 + 0,30 + 0,55 mm katman yapısı |
| Dış çap toleransı, ±OD | ±0,20 mm | Doğrudan | ISO 5361:2023 md. 6.3.1.4: No 6,5 ve üzeri için OD toleransı ±0,20 mm (No 6,0 ve altı ±0,15 mm) \[28\] |

Not: Şartname 2025-2442972'deki ±0,1 mm tolerans yalnızca ID 4,0 → OD 6,0 mm tüpler içindir \[29\]; No 8,0 için şartnamede OD verilmediğinden ISO 5361 toleransı kullanılmıştır. Daha sıkı bir iç hedef istenirse ±0,1 mm ile duyarlılık denenebilir.

## Yay teli ve 2. daldırma parametreleri

Yay teli malzemesi **AISI 304V** (vakum ergitmeli 304, UNS S30400) olarak seçilmiştir; üretici bu alaşımı kateter, kılavuz tel ve yay gibi tıbbi uygulamalar için öneriyor \[30\], \[31\].

| Parametre | Değer | Tür | Neden / Kaynak |
| --- | --- | --- | --- |
| Yay teli çapı, d\_tel | 0,30 mm | Tasarım kararı | Ekim 2026 grup kararı; cidar yapısı 0,55 / 0,30 / 0,55 mm \[27\] |
| Yay hatvesi, p | 1,3 mm | Varsayım (literatür dayanaklı) | Tel takviyeli ET tüpünde 0,21 mm tel ile 1,3 mm hatve \[32\]; ince cidarlı ET tüp patentinde 24 sarım/inç ≈ 1,06 mm \[33\]. Kesin hatve tasarım kararı olarak bekliyor |
| Tel yoğunluğu, ρ\_s | 8030 kg/m³ | Doğrudan | 304V tel veri sayfası: 8,03 g/cm³ \[30\] |
| Tel özgül ısısı, c\_s | 500 J/(kg·K) | Doğrudan | 304V, 0–100 °C: 0,50 kJ/(kg·K) \[30\] |
| Tel ısıl iletkenliği, k\_s | 16,2 W/(m·K) | Doğrudan | 304V, 100 °C: 16,2 W/(m·K) \[30\] (16,36 \[31\]); 500 °C'de 21,4 W/(m·K) \[30\] |
| 2. daldırmada mandrel sıcaklığı, T\_m0,2 | Ters tasarım (başlangıç: T\_m0) | Varsayım | Yay istasyonu çıkışına bağlı; 2. katmanın jelleşmesi için jelleşme başlangıcının (70 °C) üzerinde olmalı |
| 2. daldırmada iç katman sıcaklığı, T\_s1 | = T\_m0,2 | Varsayım | 0,55 mm PVC katmanın ısıl zaman sabiti ≈ 3,5 s (aşağıda) → mandrel sıcaklığına hızla ulaşır |
| 2. daldırmada tel sıcaklığı, T\_t | = T\_m0,2 | Varsayım | Tel metal ve ince (0,30 mm); iç katmanla temas halinde aynı sıcaklığa gelir |
| 2. daldırmada bekleme süresi, t\_bekleme,2 | 5 s | Ters tasarım (başlangıç kaynaklı) | İkinci daldırmada 5–30 s \[25\]; 1. daldırmayla aynı başlangıç alındı |

Tel hacim oranı ve iç katmanın ısıl zaman sabiti:

```latex
\varphi = \frac{\pi\,d_{tel}}{4\,p} = \frac{\pi \cdot 0{,}30}{4 \cdot 1{,}3} \approx 0{,}18
```

```latex
\alpha_{PVC} = \frac{k}{\rho\,c_p} = \frac{0{,}14}{1200 \cdot 1350} \approx 8{,}6\times10^{-8}\ \mathrm{m^2/s}, \qquad t_c = \frac{s_1^2}{\alpha_{PVC}} = \frac{(0{,}55\times10^{-3})^2}{8{,}6\times10^{-8}} \approx 3{,}5\ \mathrm{s}
```

## Model katsayıları

Film kalınlığı bağıntılarının katsayıları daldırma kaplama literatüründen alınmıştır.

| Parametre | Değer | Tür | Neden / Kaynak |
| --- | --- | --- | --- |
| LLD katsayısı, C\_LLD (D7a) | 0,94 | Doğrudan (teori) | Landau–Levich (1942) \[34\], Derjaguin (1943) \[35\]; plaka için h = 0,94 ℓ\_c Ca^(2/3) \[36\], \[37\]. Geçerlilik: Ca ≲ 10⁻² \[37\] |
| Fiber katsayısı, C\_fib (D7b) | 1,34 | Doğrudan (teori) | Fiber için h = 1,34 R Ca^(2/3) \[36\], \[38\]. Geçerlilik: R ≪ ℓ\_c |
| Viskoz–yerçekimi katsayısı, C\_grav (D7c) | 1,0 | Doğrudan (teori) | Derjaguin yüksek Ca sonucu h ≈ √(ηU/(ρg)) \[35\], \[39\]. Maksimum debi türetmesinde film tümüyle altık hızıyla taşınırsa 2/3 çıkar (aşağıda) → duyarlılıkta alt sınır 2/3 |
| Akma gerilmesi katsayısı, C\_dur (D8) | 0,3 | Doğrudan (deney) | Akma gerilmeli akışkanlarda düşük çekme hızında kaplama kalınlığı ≈ 0,3 τ\_y/(ρg) \[36\], \[40\]. Statik denge üst sınırı 1,0. Not: τ\_y = 0 alındığından bu katsayı şu an sonucu etkilemez |

Rejim seçimi için kapiler uzunluk ve kapiler sayı (γ = 0,032 N/m, ρ = 1200 kg/m³, η = 3 Pa·s):

```latex
\ell_c = \sqrt{\frac{\gamma}{\rho g}} = \sqrt{\frac{0{,}032}{1200 \cdot 9{,}81}} \approx 1{,}65\ \mathrm{mm}, \qquad \frac{R}{\ell_c} = \frac{4{,}0}{1{,}65} \approx 2{,}4
```

```latex
Ca = \frac{\eta\,U}{\gamma} = \frac{3 \cdot 0{,}001}{0{,}032} \approx 0{,}09 \quad (U = 1\ \mathrm{mm/s})
```

R/ℓ\_c > 1 olduğundan mandrel "fiber" değildir (D7b geçersiz). U ≥ 0,1 mm/s için Ca > 10⁻² olur, yani D7a sınırını aşar; hesap büyük olasılıkla D7c (viskoz–yerçekimi) rejimindedir.

C\_grav = 2/3 sonucu (maksimum debi): film akısı q = Uh − ρgh³/(3η) en büyük değerini h\_m = √(ηU/(ρg)) için alır:

```latex
q_{max} = U h_m - \frac{\rho g h_m^3}{3\eta} = \frac{2}{3}\,U h_m \;\;\Rightarrow\;\; q_{max} = U h \text{ ise } h = \frac{2}{3}\sqrt{\frac{\eta U}{\rho g}}
```

## Kaynak seçim kuralı

Yalnızca bizim bileşenlerimizle (pasta PVC + DEHT/DOTP + stabilizör, dolgusuz) yapılmış formülasyonların verisi veya saf bileşen verisi kullanılır. Dolgu ve pigment (CaCO₃, TiO₂) yoğunluğu ve ısıl özellikleri değiştirdiği için baskı mürekkebi, yapıştırıcı ve endüstriyel kaplama plastisolleri elenmiştir. Tıbbi plastisol üreticileri (Chemionics, Avient) TDS'lerini açık yayımlamadığı için doğrudan tıbbi plastisol verisi bulunamamıştır.

| Elenen kaynak | Neden |
| --- | --- |
| Tolber endüstriyel daldırma plastisolü | Dolgu içeriği bilinmiyor |
| SpecialChem yapıştırıcı plastisolleri | Dolgulu sistem |
| Ekran baskı plastisolleri | Pigment/dolgulu, farklı amaç |
| NETZSCH genel PVC-P aralıkları | Formülasyon belirsiz; yalnızca zayıf kontrol (ε için α aralığında başka kaynak bulunamadığından kullanıldı) |

## Referanslar

1. Brodie, K. (2003). *Studies of PVC Based Endotracheal Tubes From the Nano- to Macro-scale*, MIT, s. 41. [link](https://web.mit.edu/cortiz/www/OrtizGroupThesis/KristinBrodie2003Thesis.pdf)
2. Eastman. *Eastman 168 non-phthalate plasticizer for vinyl plastisols* (PZ-128), Tablo 1–2. [link](https://www.eastman.com/content/dam/eastman/corporate/en/literature/p/pz128.pdf)
3. Hallstar. *Novel Plasticizers for Low Fusion Temperature Plastisols*, slayt 10 ve 18. [link](https://www.hallstarindustrial.com/webfoo/wp-content/uploads/Hallstar-Novel-Plasticizers-for-Low-Fusion-Temperature-Plastisols-2.pdf)
4. Teknor Apex. Apex 33042RV-70NT, 33033RV-70NT1, 33033RV-80NT1 TDS. [70NT](https://www.teknorapex.com/datasheet/pdf/en/281105.pdf) · [70NT1](https://www.teknorapex.com/datasheet/pdf/en/281109.pdf) · [80NT1](https://www.teknorapex.com/datasheet/pdf/en/281115.pdf)
5. Vestolit. *Medical Devices – Biocompatibility and compatibility with sterilization methods*, Tablo B. [link](https://www.vestolit.com/wp-content/uploads/2022/10/Vestolit_BR_Medical-Devices_web_EN_2022-10.pdf)
6. Kaneka Malaysia. *PVC Paste Resin* ürün sayfası (test oranı 100/60 PVC/DOTP). [link](https://www.kaneka.com.my/product/pvc-paste-resin-2/)
7. FSRI Materials Database. *Polyvinyl Chloride (PVC)*. [link](https://materials.fsri.org/materialdetail/polyvinyl-chloride-pvc)
8. NIST Chemistry WebBook. *Bis(2-ethylhexyl) phthalate*, sıvı C\_p. [link](https://webbook.nist.gov/cgi/cbook.cgi?ID=C117817&Mask=1A8F)
9. NOAA CHRIS. *Dioctyl Phthalate (DOP)*, sıvı ısıl iletkenlik ve ısı kapasitesi tabloları. [link](https://cameochemicals.noaa.gov/chris/DOP.pdf)
10. Ejraee, H. R. (2023). *Advanced Plasticization Mechanisms and Gelation-Fusion Behavior in PVC Plastisols* (konferans bildirisi). [link](https://www.researchgate.net/publication/398909546_Advanced_Plasticization_Mechanisms_and_Gelation-Fusion_Behavior_in_PVC_Plastisols_Review_of_Molecular_Interactions_Rheology_and_Formulation_Strategies)
11. ASTM D1824-24. Standard Test Method for Apparent Viscosity of Plastisols and Organosols at Low Shear Rates. [link](https://store.astm.org/d1824-24.html)
12. Eastman Chemical Co. US9388293B2, Polyvinyl chloride compositions, Tablo I. [link](https://patents.google.com/patent/US9388293B2/en)
13. BASF. Palatinol DOTP Technical Data Sheet (2023), viskozite–sıcaklık tablosu. [link](https://chemicals.basf.com/global/plasticizers/Palatinol_DOTP_TDS_202305.pdf.assetdownload.pdf)
14. Zadhoush, A. vd. (2007). Temperature Dependent Rheological Behaviour of Plastisols Used in Coated Fabrics. Iranian Polymer Journal 16(11), 753–758. [link](https://www.researchgate.net/publication/228825860_Temperature_Dependent_Rheological_Behaviour_of_Plastisols_Used_in_Coated_Fabrics)
15. The Good Scents Company. Diethyl hexyl terephthalate (CAS 6422-86-2). [link](https://thegoodscentscompany.com/opl/6422-86-2.html)
16. Vestolit. VESTOLIT B 7021 Ultra ürün sayfası. [link](https://www.vestolit.com/shop/vestolit-b-7021-ultra/)
17. Abdesselam, Y. vd. (2017). Rheology of Plastisol Formulations for Coating Applications. Polymer Engineering & Science. [link](https://www.researchgate.net/publication/310473291_Rheology_of_Plastisol_Formulations_for_Coating_Applications)
18. Tomás, A., Rasteiro, M.G. vd. Rheology of Poly(vinyl chloride) Plastisol, Univ. Coimbra. [link](https://estudogeral.sib.uc.pt/bitstream/10316/12708/1/Rheology%20of%20Poly%28vinyl%20chloride%29%20Plastisol.pdf)
19. Harden, D. H. (1967). Plastisol Coatings and Application Techniques. Orthopedic & Prosthetic Appliance Journal. [link](https://oandplibrary.org/op/1967_02_128.asp)
20. NETZSCH. PVC-P: Polyvinylchloride (with plasticizer), doğrusal ısıl genleşme katsayısı. [link](https://analyzing-testing.netzsch.com/en/polymers-netzsch-com/commodity-thermoplastics/pvc-p-polyvinylchloride-with-plasticizer)
21. Combined Metals Company. 316L Alloy Data Sheet (2024). [link](https://www.combmet.com/wp-content/uploads/2024/01/316L-Alloy-Data-Sheet-CMC-2024-01-11.pdf)
22. Lenntech. Stainless steel 316L – fiziksel ve ısıl özellikler. [link](https://www.lenntech.com/stainless-steel-316l.htm)
23. MediClear grubu. Mandrel Seçimi Kısa Rapor ve Pugh matrisi (iç doküman, Ekim 2026).
24. Makine tedarikçisi teklif belgesi (gizli iç doküman, Eylül 2026).
25. US4800116A. Dip molding process and article (mandrel ön ısıtma 340–380 °F, daldırma 5–15 s). [link](https://patents.google.com/patent/US4800116A/en)
26. Incropera, F. P., DeWitt, D. P. vd. Fundamentals of Heat and Mass Transfer, Wiley – Denklem 7.54 (Churchill–Bernstein) ve Tablo A.4 (havanın özellikleri).
27. MediClear grubu. Spiralli ET Tüp Borusu: Boyut Seçimi ve Hat Boyutları (Spiralli\_ET\_Tup\_Boyut\_Karsilastirmasi\_v2.docx, 06.10.2026) – ihale talep analizi ve Medtronic/Teleflex ürün verileri.
28. ISO 5361:2023. Anaesthetic and respiratory equipment — Tracheal tubes and connectors, md. 6.3.1.3–6.3.1.4 (örnek bölüm). [link](https://cdn.standards.iteh.ai/samples/77497/e5b2ddedf65745c3a96333998ee21b28/ISO-5361-2023.pdf)
29. İhale 2025-2442972 teknik şartnamesi, kalem 1–4 (teknik\_şartnameler\_-\_24-12-25.pdf).
30. Ulbrich. 304V Stainless Steel Wire (UNS S30400) veri sayfası. [link](https://www.ulbrich.com/uploads/data-sheets/304V-Stainless-Steel-Wire-UNS-S30400-304V-Braid-Wire.pdf)
31. Fort Wayne Metals. 304V – Resource Library. [link](https://fwmetals.com/services/resource-library/304V/)
32. A Novel Magnetic Resonance Imaging-Compatible Titanium Alloy Wire-Reinforced Endotracheal Tube (2022), Şekil 1. [link](https://www.researchgate.net/publication/362775263_A_Novel_Magnetic_Resonance_Imaging-Compatible_Titanium_Alloy_Wire-Reinforced_Endotracheal_Tube)
33. US5429127A. Thin wall endotracheal tube (304 yay teli, 24 sarım/inç). [link](https://patents.google.com/patent/US5429127A/en)
34. Landau, L., Levich, B. (1942). Dragging of a liquid by a moving plate. Acta Physicochimica URSS, 17, 42–54.
35. Derjaguin, B. V. (1943). On the thickness of the liquid film adhering to the walls of a vessel after emptying. Comptes Rendus (Doklady) de l'Académie des Sciences de l'URSS, 39, 13–16.
36. Rio, E., Boulogne, F. (2017). Withdrawing a solid from a bath: How much liquid is coated? Advances in Colloid and Interface Science, 247, 100–114 (Denk. 8a–8b, Bölüm 4.3). [link](https://arxiv.org/pdf/1612.04602)
37. Gans, A. vd. (2019). Dip-coating of suspensions. Soft Matter (LLD geçerlilik sınırı Ca ≈ 10⁻²). [link](https://arxiv.org/pdf/1903.09350)
38. Quéré, D. (1999). Fluid coating on a fiber. Annual Review of Fluid Mechanics, 31, 347–384. [link](https://researchportal.ip-paris.fr/en/publications/fluid-coating-on-a-fiber/)
39. Levich, V. G. (1962). Physicochemical Hydrodynamics. Prentice-Hall (Derjaguin yüksek Ca bağıntısı); açıklaması: A semi-empirical power-law model for the dip-coating of a substrate (OSTI). [link](https://www.osti.gov/pages/servlets/purl/1614197)
40. Maillard, M., Bleyer, J., Andrieux, A. L., Boujlel, J., Coussot, P. (2016). Dip-coating of yield stress fluids. Physics of Fluids, 28, 053102. [link](https://www.researchgate.net/publication/301792827_Dip-coating_of_yield_stress_fluids)
