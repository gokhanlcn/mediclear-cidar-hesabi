"""Parametre tablosu: oluşturma, örnek değerler, doğrulama, SI'ya çevirme, Excel/CSV.

Tablo sütunları .md'deki "Veri giriş tablosu" ile aynıdır:
Sembol | Parametre | Birim | Min | Nominal | Max | Kaynak | Not   (+ gizli "Kod", "Grup")
Değerler kullanıcı birimindedir; SI'ya çevirme yalnızca units.py üzerinden yapılır.
"""

from __future__ import annotations

import io
import math
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .symbols import MATERIALS, PARAMS
from .units import to_si

APPROX_NOTE = "YAKLAŞIK – kaynağa göre teyit edin"
PM10_NOTE = "±%10 varsayıldı (tek kaynak)"
COLUMNS = ["Kod", "Grup", "Sembol", "Parametre", "Birim", "Min", "Nominal", "Max", "Kaynak", "Not"]
VALUE_COLS = ["Min", "Nominal", "Max"]
TABLE_KEYS = [k for k in PARAMS if k != "m"]   # m (tartım) D10 sayfasında girilir
NO_PM10 = {"g", "phi", "ID", "OD", "OD_tol"}    # sabitler ve şartname hedefleri belirsiz değildir


@dataclass
class Settings:
    """Hesap seçenekleri (tabloyla birlikte kaydedilir)."""
    T_m0_mode: str = "direct"        # "direct" | "D1"
    material_type: str = "Plastisol"  # "Plastisol" | "Organosol"
    mandrel_material: str = "304 paslanmaz"
    spiral: bool = True
    draft: bool = False              # Taslak mod: kaynaksız değerlerle hesaba izin ver

    def to_dict(self) -> dict:
        return dict(self.__dict__)

    @classmethod
    def from_dict(cls, d: dict) -> "Settings":
        s = cls()
        for k, v in d.items():
            if hasattr(s, k):
                cur = getattr(s, k)
                setattr(s, k, _to_bool(v) if isinstance(cur, bool) else type(cur)(v))
        return s


def _to_bool(v) -> bool:
    if isinstance(v, str):
        return v.strip().lower() in ("1", "true", "evet", "doğru")
    return bool(v)


# --- Tablo oluşturma --------------------------------------------------------------------

def empty_table() -> pd.DataFrame:
    rows = []
    for k in TABLE_KEYS:
        p = PARAMS[k]
        rows.append({"Kod": k, "Grup": p.group, "Sembol": p.sym, "Parametre": p.name,
                     "Birim": p.unit, "Min": np.nan, "Nominal": np.nan, "Max": np.nan,
                     "Kaynak": "", "Not": ""})
    df = pd.DataFrame(rows, columns=COLUMNS)
    df.loc[df.Kod == "g", VALUE_COLS] = 9.81
    df.loc[df.Kod == "g", "Kaynak"] = "Sabit"
    df.loc[df.Kod == "phi", VALUE_COLS] = 1.0
    df.loc[df.Kod == "phi", "Kaynak"] = "Plastisolde tanım gereği 1"
    return df


def example_table() -> pd.DataFrame:
    """.md'deki 'Tipik aralık' ve onaylı başlangıç değerleriyle dolu tablo (kaynak boş)."""
    df = empty_table()
    for k in TABLE_KEYS:
        p = PARAMS[k]
        if p.example is None or k in ("g", "phi"):
            continue
        df.loc[df.Kod == k, VALUE_COLS] = list(p.example)
        df.loc[df.Kod == k, "Not"] = APPROX_NOTE
    return df


def apply_material(df: pd.DataFrame, material: str) -> pd.DataFrame:
    """Mandrel malzemesine göre ρ_m, c_m, k_m önerisini yazar."""
    df = df.copy()
    for k, v in MATERIALS.get(material, {}).items():
        df.loc[df.Kod == k, VALUE_COLS] = v
        df.loc[df.Kod == k, "Not"] = f"{material} – malzeme tablosu değeri, {APPROX_NOTE}"
    return df


def apply_editor_changes(df: pd.DataFrame, group: str, edited_rows: dict) -> pd.DataFrame:
    """Tablo düzenleyicisinin {satır_sırası: {sütun: değer}} değişikliklerini gruba uygular."""
    df = df.copy()
    rows = df.index[df.Grup == group]
    for pos, changes in edited_rows.items():
        i = rows[int(pos)]
        for col, val in changes.items():
            if col in VALUE_COLS:
                df.loc[i, col] = np.nan if val is None or val == "" else float(val)
            elif col in ("Kaynak", "Not"):
                df.loc[i, col] = "" if val is None else str(val)
    return df


def apply_pm10(df: pd.DataFrame, keys: list[str] | None = None) -> tuple[pd.DataFrame, list[str]]:
    """Min ve Max'ı boş (veya nominale eşit) satırlara nominal ±%10 yazar."""
    df = df.copy()
    changed = []
    for i, row in df.iterrows():
        if keys is not None and row.Kod not in keys:
            continue
        nom = row.Nominal
        if _blank(nom) or nom == 0 or row.Kod in NO_PM10:
            continue
        if (_blank(row.Min) or row.Min == nom) and (_blank(row.Max) or row.Max == nom):
            lo, hi = sorted((0.9 * nom, 1.1 * nom))
            df.loc[i, ["Min", "Max"]] = [lo, hi]
            df.loc[i, "Not"] = _append_note(row.Not, PM10_NOTE)
            changed.append(row.Kod)
    return df, changed


def _append_note(old: str, new: str) -> str:
    old = (old or "").strip()
    return new if not old else (old if new in old else f"{old}; {new}")


def _blank(x) -> bool:
    return x is None or (isinstance(x, float) and math.isnan(x)) or (isinstance(x, str) and not x.strip())


# --- Doğrulama --------------------------------------------------------------------------

@dataclass
class Issue:
    level: str        # "hata" | "uyarı"
    key: str | None
    message: str


@dataclass
class Validation:
    issues: list[Issue] = field(default_factory=list)
    missing_source: list[str] = field(default_factory=list)

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.level == "hata"]

    @property
    def warnings(self) -> list[Issue]:
        return [i for i in self.issues if i.level == "uyarı"]

    def can_calculate(self, draft: bool) -> bool:
        return not self.errors and (draft or not self.missing_source)

    def status(self, key: str, active: bool) -> str:
        if not active:
            return "⚪ Kullanılmıyor"
        if any(i.key == key and i.level == "hata" for i in self.issues):
            return "🔴 Hata"
        if key in self.missing_source:
            return "🟡 Kaynak yok"
        if any(i.key == key for i in self.issues):
            return "🟠 Uyarı"
        return "🟢 Tamam"


def active_keys(s: Settings) -> list[str]:
    keys = [k for k in TABLE_KEYS if k != "T_fuz"]
    if s.material_type != "Organosol":
        keys.remove("phi")
    if s.T_m0_mode == "D1":
        keys.remove("T_m0")
    if not s.spiral:
        keys.remove("d_wire")
    return keys


D1_KEYS = ("T_oven", "h_oven", "t_pre", "T_0")


def model_keys(s: Settings) -> list[str]:
    """Kalınlık sonucunu gerçekten etkileyen parametreler (Monte Carlo duyarlılığı için).

    T_m0 doğrudan girildiğinde D1 girdileri yalnızca ön ısıtma sayfasında kullanılır.
    """
    keys = active_keys(s)
    if s.T_m0_mode != "D1":
        keys = [k for k in keys if k not in D1_KEYS]
    return [k for k in keys if k not in ("g",)]


def _val(df: pd.DataFrame, key: str, col: str = "Nominal"):
    v = df.loc[df.Kod == key, col]
    return None if v.empty or _blank(v.iloc[0]) else float(v.iloc[0])


def _rng(df, key):
    """(min, max), boşsa nominal."""
    nom = _val(df, key)
    lo, hi = _val(df, key, "Min"), _val(df, key, "Max")
    return (nom if lo is None else lo), (nom if hi is None else hi)


def validate(df: pd.DataFrame, s: Settings) -> Validation:
    v = Validation()
    act = active_keys(s)
    for _, row in df.iterrows():
        k = row.Kod
        if k not in act and k != "T_fuz":
            continue
        p = PARAMS[k]
        sym = p.sym
        nom, lo, hi = row.Nominal, row.Min, row.Max
        if _blank(nom):
            if k in act:
                v.issues.append(Issue("hata", k, f"{sym} ({p.name}) için Nominal değer girilmemiş. "
                                      "Veri sayfasından değeri bulup Nominal sütununa yaz."))
            continue
        if k in act and (_blank(lo) or _blank(hi)):
            v.issues.append(Issue("uyarı", k, f"{sym}: Min veya Max boş; Monte Carlo'da bu "
                                  "parametre nominal değerde sabit tutulur."))
        lo = nom if _blank(lo) else lo
        hi = nom if _blank(hi) else hi
        if not (lo <= nom <= hi):
            v.issues.append(Issue("hata", k, f"{sym}: Min ≤ Nominal ≤ Max olmalı (şu an {lo:g} / "
                                  f"{nom:g} / {hi:g}). Sütunları kontrol et."))
        msg = _bound_message(p.bound, sym, p.name, min(lo, nom), max(hi, nom))
        if msg:
            v.issues.append(Issue("hata", k, msg))
        if k in act and not str(row.Kaynak or "").strip():
            v.missing_source.append(k)
    _relations(df, s, v)
    return v


def _bound_message(bound, sym, name, lo, hi) -> str | None:
    if bound == "positive" and lo <= 0:
        return f"{sym} ({name}) sıfırdan büyük olmalı; negatif veya sıfır değer fiziksel değil."
    if bound == "nonneg" and lo < 0:
        return f"{sym} ({name}) negatif olamaz."
    if bound == "fraction" and (lo < 0 or hi >= 1):
        return f"{sym} ({name}) 0 ile 1 arasında olmalı (ör. %2 için 0,02 yaz)."
    if bound == "fraction_closed" and (lo <= 0 or hi > 1):
        return f"{sym} ({name}) 0'dan büyük ve en fazla 1 olmalı."
    return None


def _relations(df: pd.DataFrame, s: Settings, v: Validation) -> None:
    n = lambda k: _val(df, k)  # noqa: E731
    T_g, T_b, T_m0 = n("T_g"), n("T_b"), n("T_m0")
    if T_g is not None and T_b is not None:
        if T_g <= T_b:
            v.issues.append(Issue("hata", "T_b", "T_g, T_b'den büyük olmalı: banyo jel sıcaklığındaysa "
                                  "banyo kendiliğinden jelleşir. Plastisol veri sayfasındaki jel "
                                  "sıcaklığını ve banyo sıcaklığını kontrol et."))
        elif _rng(df, "T_g")[0] <= _rng(df, "T_b")[1]:
            v.issues.append(Issue("uyarı", "T_b", "T_g ve T_b aralıkları çakışıyor; Monte Carlo'da bu "
                                  "örnekler geçersiz sayılıp atlanır."))
    if s.T_m0_mode == "direct" and T_m0 is not None and T_g is not None:
        if T_m0 <= T_g:
            v.issues.append(Issue("hata", "T_m0", "T_m0, T_g'den büyük olmalı; mandrel jel "
                                  "sıcaklığının altındaysa hiç jel oluşmaz. Fırın sıcaklığını veya "
                                  "ön ısıtma süresini artır."))
        elif _rng(df, "T_m0")[0] <= _rng(df, "T_g")[1]:
            v.issues.append(Issue("uyarı", "T_m0", "T_m0'ın alt sınırı T_g'nin üst sınırına ulaşmıyor; "
                                  "bazı Monte Carlo örneklerinde jel oluşmaz."))
    if s.T_m0_mode == "D1":
        T_oven, T_0 = n("T_oven"), n("T_0")
        if T_oven is not None and T_0 is not None and T_oven <= T_0:
            v.issues.append(Issue("hata", "T_oven", "T_fırın, mandrelin giriş sıcaklığı T_0'dan büyük "
                                  "olmalı; aksi halde mandrel ısınmaz."))
        if T_oven is not None and T_g is not None and T_oven <= T_g:
            v.issues.append(Issue("hata", "T_oven", "T_fırın, T_g'den büyük olmalı; aksi halde mandrel "
                                  "jel sıcaklığına hiç ulaşamaz."))
        R_i = n("R_i")
        if R_i is not None and R_i > 0:
            v.issues.append(Issue("hata", "R_i", "D1 (ön ısıtma) yalnızca dolu mandrel için tanımlı. "
                                  "R_i'yi 0 yap ya da Ayarlar'da 'T_m0'ı doğrudan gir' seçeneğine geç."))
    ID, OD, R_i = n("ID"), n("OD"), n("R_i")
    if ID is not None and R_i is not None and R_i >= ID / 2:
        v.issues.append(Issue("hata", "R_i", "R_i, mandrelin dış yarıçapından (ID/2) küçük olmalı."))
    if ID is not None and OD is not None and OD <= ID:
        v.issues.append(Issue("hata", "OD", "Dış çap hedefi (OD), iç çaptan (ID) büyük olmalı."))
    T_fuz = n("T_fuz")
    if T_fuz is not None and T_g is not None and T_fuz <= T_g:
        v.issues.append(Issue("uyarı", "T_fuz", "T_füz genellikle T_g'den yüksektir; veri sayfasını "
                              "kontrol et."))


# --- SI'ya çevirme ----------------------------------------------------------------------

def nominal_si(df: pd.DataFrame) -> dict[str, float]:
    out = {}
    for _, row in df.iterrows():
        if not _blank(row.Nominal):
            out[row.Kod] = to_si(float(row.Nominal), row.Birim)
    return out


def ranges_si(df: pd.DataFrame) -> dict[str, tuple[float, float, float]]:
    out = {}
    for _, row in df.iterrows():
        if _blank(row.Nominal):
            continue
        nom = float(row.Nominal)
        lo = nom if _blank(row.Min) else float(row.Min)
        hi = nom if _blank(row.Max) else float(row.Max)
        out[row.Kod] = tuple(to_si(x, row.Birim) for x in (lo, nom, hi))
    return out


# --- Kaydet / yükle ---------------------------------------------------------------------

EXPORT_COLS = ["Kod", "Sembol", "Parametre", "Birim", "Min", "Nominal", "Max", "Kaynak", "Not"]


def to_excel_bytes(df: pd.DataFrame, s: Settings, extra: dict[str, pd.DataFrame] | None = None) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        df[EXPORT_COLS].to_excel(xw, sheet_name="Parametreler", index=False)
        pd.DataFrame(list(s.to_dict().items()), columns=["Ayar", "Değer"]).to_excel(
            xw, sheet_name="Ayarlar", index=False)
        for name, frame in (extra or {}).items():
            frame.to_excel(xw, sheet_name=name[:31], index=False)
    return buf.getvalue()


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df[EXPORT_COLS].to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")


def load_file(data: bytes, filename: str) -> tuple[pd.DataFrame, Settings | None, list[str]]:
    """Kaydedilmiş Excel/CSV'yi okur. Döner: (tablo, ayarlar veya None, uyarılar)."""
    notes: list[str] = []
    settings = None
    if filename.lower().endswith((".xlsx", ".xlsm")):
        sheets = pd.read_excel(io.BytesIO(data), sheet_name=None)
        if "Parametreler" not in sheets:
            raise ValueError("Excel dosyasında 'Parametreler' sayfası bulunamadı. Bu programdan "
                             "kaydedilmiş bir dosya seç.")
        raw = sheets["Parametreler"]
        if "Ayarlar" in sheets:
            a = sheets["Ayarlar"]
            settings = Settings.from_dict(dict(zip(a.iloc[:, 0], a.iloc[:, 1])))
    elif filename.lower().endswith(".csv"):
        raw = pd.read_csv(io.BytesIO(data), sep=";", decimal=",", encoding="utf-8-sig")
    else:
        raise ValueError("Yalnızca .xlsx veya .csv dosyası yüklenebilir.")

    df = empty_table()
    by_sym = {PARAMS[k].sym: k for k in TABLE_KEYS}
    matched = 0
    for _, row in raw.iterrows():
        key = row.get("Kod") if "Kod" in raw.columns else None
        if key not in TABLE_KEYS:
            key = by_sym.get(str(row.get("Sembol", "")).strip())
        if key is None:
            notes.append(f"Tanınmayan satır atlandı: {row.get('Sembol', '?')}")
            continue
        unit = str(row.get("Birim", PARAMS[key].unit)).strip()
        if unit and unit != "nan" and unit != PARAMS[key].unit:
            notes.append(f"{PARAMS[key].sym}: dosyadaki birim '{unit}', program '{PARAMS[key].unit}' "
                         "bekliyor. Değerleri kontrol et.")
        for col in VALUE_COLS:
            df.loc[df.Kod == key, col] = pd.to_numeric(row.get(col), errors="coerce")
        for col in ("Kaynak", "Not"):
            val = row.get(col)
            df.loc[df.Kod == key, col] = "" if _blank(val) or str(val) == "nan" else str(val)
        matched += 1
    if matched == 0:
        raise ValueError("Dosyada tanınan parametre satırı yok. Sütun başlıklarının "
                         "'Sembol, Parametre, Birim, Min, Nominal, Max, Kaynak, Not' olduğundan emin ol.")
    return df, settings, notes
