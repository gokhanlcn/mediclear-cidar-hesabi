"""Sembol sözlüğü – kod içindeki ASCII adları arayüzdeki Unicode sembollerle eşleyen TEK yer.

Kaynak: cidar_kalinligi_hesabi.md ("Ulaşılması gereken değerler" ve "Veri giriş tablosu").
Hesapta kullanılan HER değer (malzeme, proses, tel ve model katsayıları) burada tanımlıdır;
kodda gizli katsayı yoktur. `example` örnek değerdir: `example_src` doluysa o kaynaktan alınmıştır
ve "Kaynak" sütununa yazılır, boşsa YAKLAŞIK'tır ve kullanıcı kaynakla teyit etmelidir.
"""

from __future__ import annotations

from dataclasses import dataclass

GROUPS = ("Plastisol", "Mandrel", "Proses", "Ürün", "Tel / 2. daldırma", "Model katsayıları")


@dataclass(frozen=True)
class Param:
    key: str            # koddaki ASCII ad
    sym: str            # arayüzdeki sembol
    name: str           # Türkçe ad
    unit: str           # kullanıcının girdiği birim (units.py'de tanımlı)
    group: str          # sekme
    eqs: str            # kullanıldığı denklem(ler)
    help: str           # ne olduğu (tooltip / açıklama)
    typical: str        # tipik değer / aralık metni
    source_hint: str    # nereden bulunur
    example: float | None        # örnek değer
    bound: str = "positive"      # "positive" (>0), "nonneg" (>=0), "fraction" (0..1), "any"
    in_md_table: bool = True     # .md "Veri giriş tablosu"nda satırı var mı
    example_src: str = ""        # örnek değerin kaynağı (boşsa YAKLAŞIK)


PARAMS: dict[str, Param] = {}


def _add(*args, **kwargs) -> None:
    p = Param(*args, **kwargs)
    PARAMS[p.key] = p


MD = "cidar_kalinligi_hesabi.md"

# --- Plastisol -------------------------------------------------------------------------
_add("rho_p", "ρ_p", "Plastisol yoğunluğu", "kg/m³", "Plastisol", "D2, D3, D6–D10",
     "Sıvı plastisolün birim hacminin kütlesi.", "1200–1300", "Plastisol TDS", 1250)
_add("c_p", "c_p", "Plastisol özgül ısısı", "J/(kg·K)", "Plastisol", "D2, D3",
     "1 kg plastisolün sıcaklığını 1 K artırmak için gereken enerji.", "1400–1800",
     "Literatür, DSC verisi", 1600)
_add("k_p", "k_p", "Plastisol ısıl iletkenliği", "W/(m·K)", "Plastisol", "D3, D4",
     "Plastisolün ısıyı ne kadar iyi ilettiği.", "0,13–0,17", "Literatür", 0.15)
_add("T_g", "T_g", "Jelleşme başlangıç sıcaklığı", "°C", "Plastisol", "D2, D3",
     "Plastisolün bu sıcaklığın üstünde katılaşmaya (jelleşmeye) başladığı sıcaklık.",
     "70–100", "TDS jel eğrisi", 85, bound="any")
_add("T_fuz", "T_füz", "Füzyon sıcaklığı", "°C", "Plastisol", "Kür fırını ayarı",
     "Tam kür için gereken sıcaklık; kalınlık hesabına girmez, kür fırını ayarı için raporlanır.",
     "160–190", "TDS", 175, bound="any")
_add("eta_ref", "η_ref", "Referans viskozite", "Pa·s", "Plastisol", "D5–D8",
     "Plastisolün T_ref sıcaklığında ölçülen viskozitesi (akmaya direnci).", "1–10",
     "TDS (Brookfield)", 3)
_add("T_ref", "T_ref", "Viskozite ölçüm sıcaklığı", "°C", "Plastisol", "D5",
     "η_ref'in ölçüldüğü sıcaklık.", "23–25", "TDS", 24, bound="any")
_add("E_a", "E_a", "Viskozite aktivasyon enerjisi", "J/mol", "Plastisol", "D5",
     "Viskozitenin sıcaklıkla ne kadar hızlı düştüğünü belirler. TDS'deki viskozite–sıcaklık "
     "eğrisinden hesaplanır (E_a yardımcısı).", "Eğriden hesaplanır",
     "TDS viskozite–sıcaklık eğrisi", 45000, bound="nonneg")
_add("gamma", "γ", "Yüzey gerilimi", "N/m", "Plastisol", "D6, D7",
     "Sıvı yüzeyinin gerginliği; sürüklenen filmi inceltir.", "0,030–0,040", "Literatür", 0.035)
_add("tau_y", "τ_y", "Akma gerilmesi", "Pa", "Plastisol", "D8",
     "Bu gerilmenin altında plastisol akmaz; süzülmeyi bir kalınlıkta durdurur.", "0–20",
     "Reoloji verisi, TDS", 5, bound="nonneg")
_add("eps", "ε", "Kürde hacimsel çekme", "–", "Plastisol", "D9",
     "Kür sırasında hacmin küçülme oranı (0,02 = %2).", "Birkaç %", "TDS, literatür", 0.02,
     bound="fraction")
_add("phi", "φ", "Katı oranı (yalnız organosol)", "–", "Plastisol", "D9",
     "Solventli sistemde (organosol) kuruyunca kalan katı oranı. Plastisolde 1'dir.", "1 (plastisol)",
     "TDS", 1, bound="fraction_closed", in_md_table=False)

# --- Mandrel ---------------------------------------------------------------------------
_add("rho_m", "ρ_m", "Mandrel yoğunluğu", "kg/m³", "Mandrel", "D1–D3",
     "Mandrel malzemesinin yoğunluğu.", "304: 8000; Al: 2700", "Malzeme tablosu", 8000)
_add("c_m", "c_m", "Mandrel özgül ısısı", "J/(kg·K)", "Mandrel", "D1–D3",
     "Mandrel malzemesinin özgül ısısı.", "304: 500; Al: 900", "Malzeme tablosu", 500)
_add("k_m", "k_m", "Mandrel ısıl iletkenliği", "W/(m·K)", "Mandrel", "D1, D3",
     "Mandrel malzemesinin ısıl iletkenliği.", "304: 16; Al: 200", "Malzeme tablosu", 16)
_add("R_i", "R_i", "Mandrel iç yarıçapı", "mm", "Mandrel", "D2, D3",
     "İçi boş mandrelde iç yarıçap; dolu mandrelde 0.", "0 (dolu)", "Tasarım kararı", 0,
     bound="nonneg")
_add("L", "L", "Daldırma boyu", "mm", "Mandrel", "D8, D10",
     "Mandrelin plastisole batan (kaplanan) boyu.", "Tasarım kararı", "Makine tedarikçisi teklifi", 400)

# --- Proses (1. daldırma) ----------------------------------------------------------------
_add("T_oven", "T_fırın", "Ön ısıtma fırını sıcaklığı", "°C", "Proses", "D1",
     "Mandrelin ısıtıldığı fırının hava sıcaklığı.", "Tasarım kararı", "Makine tedarikçisi teklifi", 220, bound="any")
_add("h_oven", "h_fırın", "Fırın konveksiyon katsayısı", "W/(m²·K)", "Proses", "D1",
     "Fırın havasından mandrele ısı geçiş katsayısı.", "20–100",
     "Isı transferi kitabı (ör. Churchill–Bernstein, Zukauskas), fırın üreticisi", 50)
_add("t_pre", "t_ön", "Ön ısıtma süresi", "s", "Proses", "D1",
     "Mandrelin fırında kaldığı süre.", "Tasarım değişkeni", "Çevrim süresi hesabı", 600)
_add("T_0", "T_0", "Mandrelin fırına giriş sıcaklığı", "°C", "Proses", "D1",
     "Mandrel fırına girerken sahip olduğu sıcaklık (D1'deki T_0).", "Oda sıcaklığı",
     "Hat ölçümü / tasarım", 25, bound="any", in_md_table=False)
_add("T_m0", "T_m0", "1. daldırmada mandrel sıcaklığı", "°C", "Proses", "D2, D3",
     "Mandrel banyoya girerken sahip olduğu sıcaklık. D1'den hesaplanabilir veya doğrudan girilir.",
     "D1'den hesaplanır", "–", 150, bound="any", in_md_table=False)
_add("T_b", "T_b", "Banyo sıcaklığı", "°C", "Proses", "D2, D3, D5",
     "Plastisol banyosunun sıcaklığı.", "20–40", "Tasarım kararı", 25, bound="any")
_add("t_wait", "t_bekleme", "1. daldırmada bekleme süresi", "s", "Proses", "D3, D4",
     "Mandrelin banyoda hareketsiz beklediği süre.", "Tasarım değişkeni", "–", 10)
_add("U", "U", "Çekme hızı", "mm/s", "Proses", "D6, D7",
     "Mandrelin banyodan çekilme hızı (her iki daldırmada).", "Tasarım değişkeni",
     "Servo eksen sınırları", 1)
_add("t_drain", "t_süz", "Süzülme süresi", "s", "Proses", "D8",
     "Çekmeden sonra kür fırınına girene kadar geçen süre.", "Tasarım değişkeni",
     "Kür fırınına transfer süresi", 60, bound="nonneg")
_add("g", "g", "Yerçekimi ivmesi", "m/s²", "Proses", "D6–D10", "Sabit.", "9,81", "Sabit", 9.81,
     in_md_table=False, example_src="Standart yerçekimi")

# --- Ürün ------------------------------------------------------------------------------
_add("ID", "ID", "İç çap", "mm", "Ürün", "D11",
     "Tüpün iç çapı; mandrel dış çapına eşittir (R = ID/2).", "2,0–11,0", "İhale şartnameleri",
     4.0, in_md_table=False)
_add("OD", "OD", "Dış çap hedefi", "mm", "Ürün", "D11",
     "Şartnamedeki dış çap hedefi.", "ID 4,0 → 6,0 ± 0,1", "Şartname 2025-2442972", 6.0,
     in_md_table=False, example_src=f"Şartname 2025-2442972 ({MD}, D11 örneği)")
_add("OD_tol", "±OD", "Dış çap toleransı", "mm", "Ürün", "D11",
     "Dış çapta izin verilen ± sapma.", "0,1", "Şartname", 0.1, in_md_table=False,
     example_src=f"Şartname 2025-2442972 ({MD}, D11 örneği)")
_add("m", "m", "Kaplama kütlesi (tartım)", "g", "Ürün", "D10",
     "Daldırma öncesi–sonrası kütle farkı; ölçülür.", "Ölçülür", "Tedarikçi denemesi", None,
     in_md_table=False)

# --- Tel ve 2. daldırma ---------------------------------------------------------------
_add("d_wire", "d_tel", "Yay teli çapı", "mm", "Tel / 2. daldırma", "D11, tel halkası",
     "Spiral yay telinin çapı. Tel halkasının kalınlığıdır.", "0,2–0,5", "Yay tedarikçisi", 0.3,
     bound="nonneg")
_add("p_wire", "p", "Yay hatvesi", "mm", "Tel / 2. daldırma", "Tel halkası (φ)",
     "Komşu iki sarımın eksenleri arasındaki eksenel mesafe. Tel hacim oranı φ = πd/(4p).",
     "0,1–4 (tel tedarikçisi)", "Yay teknik resmi / tedarikçi", 2.0)
_add("rho_s", "ρ_s", "Tel yoğunluğu", "kg/m³", "Tel / 2. daldırma", "Tel halkası",
     "Yay teli malzemesinin yoğunluğu (paslanmaz çelik ≈ 8000).", "7900–8000", "Malzeme tablosu",
     8000)
_add("c_s", "c_s", "Tel özgül ısısı", "J/(kg·K)", "Tel / 2. daldırma", "Tel halkası",
     "Yay teli malzemesinin özgül ısısı.", "≈ 500 (paslanmaz)", "Malzeme tablosu", 500)
_add("k_s", "k_s", "Tel ısıl iletkenliği", "W/(m·K)", "Tel / 2. daldırma", "Tel halkası",
     "Yay teli malzemesinin ısıl iletkenliği.", "≈ 16 (paslanmaz)", "Malzeme tablosu", 16.2)
_add("T_m0_2", "T_m0,2", "2. daldırmada mandrel sıcaklığı", "°C", "Tel / 2. daldırma", "D3 (2. daldırma)",
     "Mandrel 2. daldırmaya girerken sahip olduğu sıcaklık.", "Yay istasyonu çıkışı",
     "Hat tasarımı / ölçüm", 150, bound="any", in_md_table=False)
_add("T_s1", "T_s1", "2. daldırmada iç katman sıcaklığı", "°C", "Tel / 2. daldırma", "D3 (2. daldırma)",
     "1. daldırmadan gelen (kürlenmiş) iç PVC katmanının 2. daldırmaya girişteki sıcaklığı.",
     "Mandrel sıcaklığına yakın", "Hat tasarımı / ölçüm", 150, bound="any", in_md_table=False)
_add("T_t", "T_t", "2. daldırmada tel sıcaklığı", "°C", "Tel / 2. daldırma", "Tel halkası",
     "Yay telinin 2. daldırmaya girişteki sıcaklığı.", "Katman sıcaklığına yakın",
     "Hat tasarımı / ölçüm", 150, bound="any", in_md_table=False)
_add("t_wait_2", "t_bekleme,2", "2. daldırmada bekleme süresi", "s", "Tel / 2. daldırma",
     "D3 (2. daldırma)", "Mandrelin 2. daldırmada banyoda beklediği süre.", "Tasarım değişkeni",
     "–", 10, in_md_table=False)

# --- Model katsayıları (formüllerin sayısal sabitleri – kullanıcı kaynağıyla girer) -------
_add("C_lld", "C_LLD", "D7a katsayısı (Landau–Levich–Derjaguin)", "–", "Model katsayıları", "D7a",
     "h = C_LLD·(ηU)^(2/3) / (γ^(1/6)·(ρ_p g)^(1/2)). Kalın mandrel, düşük hız teorisinin sabiti.",
     "0,94 (teori)", "Landau & Levich (1942); Derjaguin (1943)", 0.94, in_md_table=False,
     example_src=f"{MD} D7a; Landau & Levich (1942)")
_add("C_fib", "C_fib", "D7b katsayısı (fiber kaplama)", "–", "Model katsayıları", "D7b",
     "h = C_fib·R·Ca^(2/3). İnce mandrel (fiber) kaplama teorisinin sabiti.",
     "1,34 (teori)", "Quéré (1999), fiber kaplama", 1.34, in_md_table=False,
     example_src=f"{MD} D7b; Quéré (1999)")
_add("C_grav", "C_grav", "D7c katsayısı (viskoz–yerçekimi)", "–", "Model katsayıları", "D7c",
     "h = C_grav·√(ηU/(ρ_p g)). Yüksek hızda yerçekiminin baskın olduğu rejimin sabiti "
     "(Derjaguin en büyük debi türetmesi 2/3–1 aralığını verir).",
     "0,8 (.md); 2/3–1 (Derjaguin)", "Derjaguin (1943); Rev. 2 Bölüm 2.4", 0.8, in_md_table=False,
     example_src=f"{MD} D7c")
_add("C_dur", "C_dur", "Akma gerilmesi katsayısı", "–", "Model katsayıları", "D8",
     "h_dur = C_dur·τ_y/(ρ_p g). Akma gerilmesinin süzülmeyi durdurduğu film kalınlığının sabiti.",
     "1 (.md D8); 0,3 (Rev. 2)", "Reoloji literatürü", 1.0, in_md_table=False,
     example_src=f"{MD} D8")

# Mandrel malzemesi (.md: 304 paslanmaz veya Al) – ρ_m, c_m, k_m önerileri
MATERIALS: dict[str, dict[str, float]] = {
    "316L paslanmaz": {"rho_m": 7990.0, "c_m": 500.0, "k_m": 16.2},
    "304 paslanmaz": {"rho_m": 8000.0, "c_m": 500.0, "k_m": 16.0},
    "Alüminyum": {"rho_m": 2700.0, "c_m": 900.0, "k_m": 200.0},
}

# Film formülü seçenekleri (kullanıcı seçer; program seçim yapmaz)
FILM_MODELS: dict[str, str] = {
    "D7a": "D7a – Landau–Levich–Derjaguin (kalın mandrel, düşük hız)",
    "D7b": "D7b – Fiber kaplama (ince mandrel)",
    "D7c": "D7c – Viskoz–yerçekimi (yüksek hız)",
    "min_ac": "D7a ile D7c'nin küçüğü (Rev. 2 yaklaşımı)",
}


def param(key: str) -> Param:
    return PARAMS[key]


def label(key: str) -> str:
    """Arayüz etiketi: 'ρ_p – Plastisol yoğunluğu [kg/m³]'."""
    p = PARAMS[key]
    return f"{p.sym} – {p.name} [{p.unit}]"


def keys_in_group(group: str) -> list[str]:
    return [k for k, p in PARAMS.items() if p.group == group]
