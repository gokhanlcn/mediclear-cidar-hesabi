"""Sembol sözlüğü – kod içindeki ASCII adları arayüzdeki Unicode sembollerle eşleyen TEK yer.

Kaynak: cidar_kalinligi_hesabi.md ("Ulaşılması gereken değerler" ve "Veri giriş tablosu").
`example` değerleri .md'deki "Tipik aralık (yaklaşık)" sütunundan alınmıştır; .md'de sayısal
örneği olmayanlar (E_a, ε, T_m0, t_ön, t_bekleme, U, t_süz, d_tel) proje grubunun onayladığı
başlangıç değerleridir. Hepsi YAKLAŞIK'tır ve kaynağa göre teyit edilmelidir.
"""

from __future__ import annotations

from dataclasses import dataclass

GROUPS = ("Plastisol", "Mandrel", "Proses", "Ürün")


@dataclass(frozen=True)
class Param:
    key: str            # koddaki ASCII ad
    sym: str            # arayüzdeki sembol
    name: str           # Türkçe ad
    unit: str           # kullanıcının girdiği birim (units.py'de tanımlı)
    group: str          # sekme
    eqs: str            # kullanıldığı denklem(ler)
    help: str           # kısa açıklama (tooltip)
    typical: str        # .md'deki "Tipik aralık" metni
    source_hint: str    # .md'deki "Nereden bulunur"
    example: tuple[float, float, float] | None  # (min, nominal, max) – YAKLAŞIK
    bound: str = "positive"   # "positive" (>0), "nonneg" (>=0), "fraction" (0..1), "any"
    in_md_table: bool = True  # .md "Veri giriş tablosu"nda satırı var mı


PARAMS: dict[str, Param] = {}


def _add(*args, **kwargs) -> None:
    p = Param(*args, **kwargs)
    PARAMS[p.key] = p


# --- Plastisol -------------------------------------------------------------------------
_add("rho_p", "ρ_p", "Plastisol yoğunluğu", "kg/m³", "Plastisol", "D2, D3, D6–D10",
     "Sıvı plastisolün birim hacminin kütlesi.", "1200–1300", "Plastisol TDS",
     (1200, 1250, 1300))
_add("c_p", "c_p", "Plastisol özgül ısısı", "J/(kg·K)", "Plastisol", "D2, D3",
     "1 kg plastisolün sıcaklığını 1 K artırmak için gereken enerji.", "1400–1800",
     "Literatür, DSC verisi", (1400, 1600, 1800))
_add("k_p", "k_p", "Plastisol ısıl iletkenliği", "W/(m·K)", "Plastisol", "D3, D4",
     "Plastisolün ısıyı ne kadar iyi ilettiği.", "0,13–0,17", "Literatür",
     (0.13, 0.15, 0.17))
_add("T_g", "T_g", "Jelleşme başlangıç sıcaklığı", "°C", "Plastisol", "D2, D3",
     "Plastisolün bu sıcaklığın üstünde katılaşmaya (jelleşmeye) başladığı sıcaklık.",
     "70–100", "TDS jel eğrisi", (70, 85, 100), bound="any")
_add("T_fuz", "T_füz", "Füzyon sıcaklığı", "°C", "Plastisol", "Kür fırını ayarı",
     "Tam kür için gereken sıcaklık; kalınlık hesabına girmez, kür fırını ayarı için raporlanır.",
     "160–190", "TDS", (160, 175, 190), bound="any")
_add("eta_ref", "η_ref", "Referans viskozite", "Pa·s", "Plastisol", "D5–D8",
     "Plastisolün T_ref sıcaklığında ölçülen viskozitesi (akmaya direnci).", "1–10",
     "TDS (Brookfield)", (1, 3, 10))
_add("T_ref", "T_ref", "Viskozite ölçüm sıcaklığı", "°C", "Plastisol", "D5",
     "η_ref'in ölçüldüğü sıcaklık.", "23–25", "TDS", (23, 24, 25), bound="any")
_add("E_a", "E_a", "Viskozite aktivasyon enerjisi", "J/mol", "Plastisol", "D5",
     "Viskozitenin sıcaklıkla ne kadar hızlı düştüğünü belirler. TDS'deki viskozite–sıcaklık "
     "eğrisinden hesaplanır (E_a yardımcısı).", "Eğriden hesaplanır",
     "TDS viskozite–sıcaklık eğrisi", (30000, 45000, 60000), bound="nonneg")
_add("gamma", "γ", "Yüzey gerilimi", "N/m", "Plastisol", "D6, D7",
     "Sıvı yüzeyinin gerginliği; sürüklenen filmi inceltir.", "0,030–0,040", "Literatür",
     (0.030, 0.035, 0.040))
_add("tau_y", "τ_y", "Akma gerilmesi", "Pa", "Plastisol", "D8",
     "Bu gerilmenin altında plastisol akmaz; süzülmeyi bir kalınlıkta durdurur.", "0–20",
     "Reoloji verisi, TDS", (0, 5, 20), bound="nonneg")
_add("eps", "ε", "Kürde hacimsel çekme", "–", "Plastisol", "D9",
     "Kür sırasında hacmin küçülme oranı (0,02 = %2).", "Birkaç %", "TDS, literatür",
     (0.01, 0.02, 0.05), bound="fraction")
_add("phi", "φ", "Katı oranı (yalnız organosol)", "–", "Plastisol", "D9",
     "Solventli sistemde (organosol) kuruyunca kalan katı oranı. Plastisolde 1'dir.", "1 (plastisol)",
     "TDS", (1, 1, 1), bound="fraction_closed", in_md_table=False)

# --- Mandrel ---------------------------------------------------------------------------
_add("rho_m", "ρ_m", "Mandrel yoğunluğu", "kg/m³", "Mandrel", "D1–D3",
     "Mandrel malzemesinin yoğunluğu.", "304: 8000; Al: 2700", "Malzeme tablosu",
     (8000, 8000, 8000))
_add("c_m", "c_m", "Mandrel özgül ısısı", "J/(kg·K)", "Mandrel", "D1–D3",
     "Mandrel malzemesinin özgül ısısı.", "304: 500; Al: 900", "Malzeme tablosu",
     (500, 500, 500))
_add("k_m", "k_m", "Mandrel ısıl iletkenliği", "W/(m·K)", "Mandrel", "D1, D3",
     "Mandrel malzemesinin ısıl iletkenliği.", "304: 16; Al: 200", "Malzeme tablosu",
     (16, 16, 16))
_add("R_i", "R_i", "Mandrel iç yarıçapı", "mm", "Mandrel", "D2, D3",
     "İçi boş mandrelde iç yarıçap; dolu mandrelde 0.", "0 (dolu)", "Tasarım kararı",
     (0, 0, 0), bound="nonneg")
_add("L", "L", "Daldırma boyu", "mm", "Mandrel", "D8, D10",
     "Mandrelin plastisole batan (kaplanan) boyu.", "≤ 400 (opsiyon 1000)", "Litzler teklifi",
     (400, 400, 400))

# --- Proses ----------------------------------------------------------------------------
_add("T_oven", "T_fırın", "Ön ısıtma fırını sıcaklığı", "°C", "Proses", "D1",
     "Mandrelin ısıtıldığı fırının hava sıcaklığı.", "150–425", "Litzler teklifi",
     (200, 220, 240), bound="any")
_add("h_oven", "h_fırın", "Fırın konveksiyon katsayısı", "W/(m²·K)", "Proses", "D1",
     "Fırın havasından mandrele ısı geçiş katsayısı.", "20–100",
     "Isı transferi kitabı, fırın üreticisi", (20, 50, 100))
_add("t_pre", "t_ön", "Ön ısıtma süresi", "s", "Proses", "D1",
     "Mandrelin fırında kaldığı süre.", "Tasarım değişkeni", "Çevrim süresi hesabı",
     (300, 600, 900))
_add("T_0", "T_0", "Mandrelin fırına giriş sıcaklığı", "°C", "Proses", "D1",
     "Mandrel fırına girerken sahip olduğu sıcaklık (D1'deki T_0).", "Oda sıcaklığı",
     "Hat ölçümü / tasarım", (20, 25, 30), bound="any", in_md_table=False)
_add("T_m0", "T_m0", "Daldırma anında mandrel sıcaklığı", "°C", "Proses", "D2, D3",
     "Mandrel banyoya girerken sahip olduğu sıcaklık. D1'den hesaplanabilir veya doğrudan girilir.",
     "D1'den hesaplanır", "–", (120, 150, 180), bound="any", in_md_table=False)
_add("T_b", "T_b", "Banyo sıcaklığı", "°C", "Proses", "D2, D3, D5",
     "Plastisol banyosunun sıcaklığı.", "20–40", "Tasarım kararı", (20, 25, 40), bound="any")
_add("t_wait", "t_bekleme", "Banyoda bekleme süresi", "s", "Proses", "D3, D4",
     "Mandrelin banyoda hareketsiz beklediği süre.", "Tasarım değişkeni", "–", (5, 10, 30))
_add("U", "U", "Çekme hızı", "mm/s", "Proses", "D6, D7",
     "Mandrelin banyodan çekilme hızı.", "Tasarım değişkeni", "Servo eksen sınırları",
     (0.5, 1, 5))
_add("t_drain", "t_süz", "Süzülme süresi", "s", "Proses", "D8",
     "Çekmeden sonra kür fırınına girene kadar geçen süre.", "Tasarım değişkeni",
     "Kür fırınına transfer süresi", (30, 60, 120), bound="nonneg")
_add("g", "g", "Yerçekimi ivmesi", "m/s²", "Proses", "D6–D10", "Sabit.", "9,81", "Sabit",
     (9.81, 9.81, 9.81), in_md_table=False)

# --- Ürün ------------------------------------------------------------------------------
_add("ID", "ID", "İç çap", "mm", "Ürün", "D11",
     "Tüpün iç çapı; mandrel dış çapına eşittir (R = ID/2).", "2,0–11,0", "İhale şartnameleri",
     (4.0, 4.0, 4.0), in_md_table=False)
_add("OD", "OD", "Dış çap hedefi", "mm", "Ürün", "D11",
     "Şartnamedeki dış çap hedefi.", "ID 4,0 → 6,0 ± 0,1", "Şartname 2025-2442972",
     (6.0, 6.0, 6.0), in_md_table=False)
_add("OD_tol", "±OD", "Dış çap toleransı", "mm", "Ürün", "D11",
     "Dış çapta izin verilen ± sapma.", "0,1", "Şartname", (0.1, 0.1, 0.1), in_md_table=False)
_add("d_wire", "d_tel", "Yay teli çapı", "mm", "Ürün", "D11",
     "Spiral yay telinin çapı. Spiral yoksa 0.", "0,2–0,5", "Yay tedarikçisi", (0.2, 0.3, 0.5),
     bound="nonneg")
_add("m", "m", "Kaplama kütlesi (tartım)", "g", "Ürün", "D10",
     "Daldırma öncesi–sonrası kütle farkı; ölçülür.", "Ölçülür", "Tedarikçi denemesi", None,
     in_md_table=False)

# Mandrel malzemesi (.md: 304 paslanmaz veya Al) – ρ_m, c_m, k_m önerileri
MATERIALS: dict[str, dict[str, float]] = {
    "304 paslanmaz": {"rho_m": 8000.0, "c_m": 500.0, "k_m": 16.0},
    "Alüminyum": {"rho_m": 2700.0, "c_m": 900.0, "k_m": 200.0},
}

# Sonuç sembolleri (arayüz ve rapor için)
RESULT_SYMBOLS: dict[str, tuple[str, str, str]] = {
    "tau": ("τ", "s", "Mandrel ısınma zaman sabiti"),
    "Bi": ("Bi", "–", "Biot sayısı"),
    "s_max": ("s_max", "mm", "Enerji tavanı (en büyük jel kalınlığı)"),
    "s_jel": ("s_jel", "mm", "Jel katmanı kalınlığı"),
    "C": ("C", "–", "Difüzyon katsayısı"),
    "eta_b": ("η(T_b)", "Pa·s", "Banyo sıcaklığındaki viskozite"),
    "Ca": ("Ca", "–", "Kapiler sayı"),
    "l_c": ("ℓ_c", "mm", "Kapiler uzunluk"),
    "h0": ("h_0", "mm", "Çekme anındaki film kalınlığı (D7)"),
    "h_dur": ("h_dur", "mm", "Akma gerilmesinin durdurduğu kalınlık"),
    "h": ("h", "mm", "Süzülme sonrası ortalama film kalınlığı"),
    "s_kur": ("s_kür", "mm", "Kür sonrası kalınlık"),
    "s_toplam": ("s_toplam", "mm", "Toplam kalınlık (tek daldırma)"),
    "w": ("w", "mm", "Toplam cidar kalınlığı"),
}


def param(key: str) -> Param:
    return PARAMS[key]


def label(key: str) -> str:
    """Arayüz etiketi: 'ρ_p – Plastisol yoğunluğu [kg/m³]'."""
    p = PARAMS[key]
    return f"{p.sym} – {p.name} [{p.unit}]"


def keys_in_group(group: str) -> list[str]:
    return [k for k, p in PARAMS.items() if p.group == group]
