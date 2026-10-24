"""MediClear proje verileri – grubun kabul ettiği güncel parametreler.

Kaynak belge: veriler.md ("MediClear – Daldırma İstasyonu Malzeme Parametreleri", 23.10.2026).
Her değer (kullanıcı birimiyle) dayanağıyla birlikte tutulur; köşeli parantezli numaralar veriler.md
referans listesine aittir. Değeri None olanlar belgede ters tasarımla belirlenecek olarak bırakılmıştır.
"""

from __future__ import annotations

DOC = "veriler.md"
DATE = "23.10.2026"

# Kod: (değer, kaynak, not)
PROJECT_DATA: dict[str, tuple[float | None, str, str]] = {
    # --- Plastisol (100 phr pasta PVC + 60 phr DEHT + 3 phr Ca/Zn) ----------------------
    "rho_p": (1200, "Dolaylı: ters karışım kuralı, ρ_PVC 1388 [7], ρ_DEHT 980 [2]; doğrulama [4]", "Aralık 1180–1220"),
    "c_p": (1350, "Dolaylı: kütle ağırlıklı ortalama, c_PVC 1020 [7], c_pl 1804 [8]", "Aralık 1300–1400; oda sıcaklığı"),
    "k_p": (0.14, "Dolaylı: k_pl 0,135 [9], k_PVC 0,130–0,143 [7]", "Aralık 0,13–0,15"),
    "T_g": (70, "Varsayım: DSC ilk endotermik pik 70–100 °C [10]",
            "Jelleşme başlangıcı; DEHT'e özel veri yok. Jel noktası 108 °C [3]. Aralık 65–100"),
    "T_fuz": (171, "Doğrudan: DOTP plastisolü, reometre [3]", "Aralık 170–180"),
    "eta_ref": (3, "Dolaylı: 100/60 DOTP plastisolü 2–6 Pa·s [6]; [12], [2]", "Brookfield, düşük kayma; aralık 2–6"),
    "T_ref": (23, "Doğrudan: 23 °C, 20 rpm [2]; ASTM D1824 [11]", "Aralık 23–25"),
    "E_a": (40800, "Dolaylı: DOTP TDS viskozite–sıcaklık (20 °C 86, 40 °C 29,5 mPa·s) [13]",
            "Plastifiyan verisi; plastisolde 3900–4600 J/mol ölçülmüş [14]. Arrhenius ≈ 45 °C üstünde geçersiz"),
    "gamma": (0.032, "Dolaylı: DOTP TDS 32,3 mN/m [13]; DEHT 35,4 ± 3,0 [15]", "Aralık 0,032–0,035"),
    "tau_y": (0, "Varsayım: dolgusuz pasta PVC neredeyse Newtonian [16]; [17], [18]",
              "Sayısal veri yok; yaşlanmış plastisol için 0–20 Pa denenmeli"),
    "eps": (0.04, "Dolaylı: ısıl çekme 3α(T_füz − T_oda), α = 90×10⁻⁶ 1/K [20]; [19], [4]", "Aralık 0,027–0,053"),
    # --- Mandrel (elektropolisajlı AISI 316L) --------------------------------------------
    "rho_m": (7990, "Doğrudan: 316L, 20 °C [21], [22]", ""),
    "c_m": (500, "Doğrudan: 316L, 0–100 °C [22]", ""),
    "k_m": (16.2, "Doğrudan: 316L, 100 °C [21], [22]", "Çalışma aralığında ≈ 16–20 W/(m·K)"),
    "R_i": (0, "Tasarım kararı: dolu mandrel [23]", ""),
    "L": (400, "Tasarım kararı: kaplama boyu 400 mm (tüp 360 mm); makine teklifiyle uyumlu [24]", ""),
    # --- Proses --------------------------------------------------------------------------
    "T_oven": (200, "Makine teklifi aralığında [24]; ön ısıtma 190–220 °C [19], 171–193 °C [25]",
               "Ters tasarım başlangıç değeri"),
    "h_oven": (50, "Dolaylı + varsayım: Churchill–Bernstein, D = 8 mm, hava 400 K [26]",
               "Hava hızı 2 m/s varsayıldı (1–5 m/s → 37–83); ışınım dahil değil"),
    "t_pre": (None, "", "Girilecek: fırında kalma süresi. T_m0 = D1 (fırın) + taşıma soğumasından hesaplanır"),
    "T_0": (23, "Tasarım kararı: sıyırma/soğutma sonrası oda sıcaklığı", "T_ref ile aynı"),
    "t_tr": (12, "Rev. 2 Bölüm 1.2: hat indeksleme süresi 12 s", "Fırından banyoya bir indeksleme adımı kabul edildi"),
    "T_amb": (23, "Tasarım kararı: oda sıcaklığı (T_0 ile aynı)", ""),
    "h_amb": (7.5, "Rev. 2 Bölüm 2.2 ve 2.6: doğal taşınım, Churchill–Chu, 4–11 W/(m²·K); nominal 7,5",
              "Işınım ayrıca eklenmedi"),
    "T_m0": (None, "", "D1 modunda kullanılmaz (D1 + taşıma soğumasından hesaplanır); doğrudan modda girilir"),
    "T_b": (23, "Tasarım kararı: T_ref ile eşit → η = η_ref [2]; Arrhenius sınırı ≤ 42 °C [14]", ""),
    "t_wait": (5, "Ters tasarım başlangıcı: 5–15 s bekleme ile 0,76–1,5 mm jel [25]", "Hedef 0,55 mm → alt sınır"),
    "U": (None, "", "Ters tasarım: D6–D7 ile film kalınlığından bulunacak; üst sınır servo eksen (veriler.md)"),
    "t_drain": (None, "", "Ters tasarım: çekmeden kür fırınına transfer süresi; endekslemeye bağlı (veriler.md)"),
    "g": (9.81, "Sabit", ""),
    # --- Ürün (No 8,0) -------------------------------------------------------------------
    "ID": (8.0, "Tasarım kararı: No 8,0 = ID 8,0 mm (ISO 5361) [28]; [27]", "R = 4,0 mm"),
    "OD": (10.8, "Doğrudan: Shiley Reinforced, Rüsch Flex No 8,0 [27]", "Et 1,40 = 0,55 + 0,30 + 0,55 mm"),
    "OD_tol": (0.20, "Doğrudan: ISO 5361:2023 md. 6.3.1.4 (No ≥ 6,5) [28]", "Daha sıkı iç hedef için ±0,1 denenebilir"),
    # --- Tel ve 2. daldırma (AISI 304V) ---------------------------------------------------
    "d_wire": (0.30, "Tasarım kararı: Ekim 2026 grup kararı [27]", "Cidar 0,55 / 0,30 / 0,55 mm"),
    "p_wire": (1.3, "Varsayım (literatür): 0,21 mm tel ile 1,3 mm hatve [32]; 24 sarım/inç ≈ 1,06 mm [33]",
               "Kesin hatve tasarım kararı olarak bekliyor"),
    "rho_s": (8030, "Doğrudan: 304V tel veri sayfası [30]", ""),
    "c_s": (500, "Doğrudan: 304V, 0–100 °C [30]", ""),
    "k_s": (16.2, "Doğrudan: 304V, 100 °C [30]; 16,36 [31]", ""),
    "T_m0_2": (98.5, "Rev. 2 Bölüm 4.4 [H]: yay istasyonu çıkışında ortalama mandrel sıcaklığı",
               "Rev. 2 koşulları: T_m0 = 100 °C, kısmi jel 165 °C, şartlandırma hedefi 100 °C; bunlar değişirse güncellenmeli"),
    "T_s1": (95.9, "Rev. 2 Bölüm 4.4 [H]: daldırma-2 girişinde iç katman yüzeyi", "Aynı Rev. 2 koşulları"),
    "T_t": (95.5, "Rev. 2 Bölüm 4.4 [H]: daldırma-2 girişinde tel", "Aynı Rev. 2 koşulları"),
    "t_wait_2": (5, "Ters tasarım başlangıcı: 2. daldırmada 5–30 s [25]", "1. daldırmayla aynı"),
    # --- Model katsayıları ----------------------------------------------------------------
    "C_lld": (0.94, "Teori: Landau–Levich (1942) [34], Derjaguin (1943) [35]; [36], [37]", "Geçerlilik Ca ≲ 10⁻² [37]"),
    "C_fib": (1.34, "Teori: fiber kaplama [36], [38]", "Geçerlilik R ≪ ℓ_c"),
    "C_grav": (1.0, "Teori: Derjaguin yüksek Ca, h ≈ √(ηU/(ρg)) [35], [39]", "Maks. debi türetmesi 2/3 verir → alt sınır"),
    "C_dur": (0.3, "Deney: akma gerilmeli akışkanlarda h ≈ 0,3 τ_y/(ρg) [36], [40]", "Statik üst sınır 1,0; τ_y = 0 iken etkisiz"),
}

# Mandrel malzemesi ve diğer ayarlar
SETTINGS = {"mandrel_material": "316L paslanmaz", "T_m0_mode": "D1", "spiral": True,
            "material_type": "Plastisol"}


def missing_keys() -> list[str]:
    return [k for k, (v, _, _) in PROJECT_DATA.items() if v is None]
