"""Veri tablosu: oluşturma, örnek değerler, doğrulama, SI'ya çevirme, Excel/CSV.

Sütunlar: Sembol | Parametre | Birim | Değer | Kaynak | Not   (+ gizli "Kod", "Grup")
Değerler kullanıcı birimindedir; SI'ya çevirme yalnızca units.py üzerinden yapılır.
Hesapta kullanılan her sayı (model katsayıları dahil) bu tablodan gelir.
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
COLUMNS = ["Kod", "Grup", "Sembol", "Parametre", "Birim", "Değer", "Kaynak", "Not"]
VALUE_COL = "Değer"
TABLE_KEYS = [k for k in PARAMS if k != "m"]   # m (tartım) D10 sayfasında girilir
WIRE_KEYS = [k for k in PARAMS if PARAMS[k].group == "Tel / 2. daldırma"]
D1_KEYS = ("T_oven", "h_oven", "t_pre", "T_0", "t_tr", "T_amb", "h_amb")


@dataclass
class Settings:
    """Hesap seçenekleri (tabloyla birlikte kaydedilir)."""
    T_m0_mode: str = "direct"        # "direct" | "D1"
    material_type: str = "Plastisol"  # "Plastisol" | "Organosol"
    mandrel_material: str = "316L paslanmaz"
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
                if isinstance(cur, bool):
                    setattr(s, k, _to_bool(v))
                else:
                    setattr(s, k, "" if v is None or (isinstance(v, float) and math.isnan(v)) else type(cur)(v))
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
                     "Birim": p.unit, VALUE_COL: np.nan, "Kaynak": "", "Not": ""})
    df = pd.DataFrame(rows, columns=COLUMNS)
    df.loc[df.Kod == "g", [VALUE_COL, "Kaynak"]] = [9.81, "Standart yerçekimi"]
    df.loc[df.Kod == "phi", [VALUE_COL, "Kaynak"]] = [1.0, "Plastisolde tanım gereği 1"]
    return df


def example_table() -> pd.DataFrame:
    """Örnek değerlerle dolu tablo. Kaynağı belli olanların Kaynak sütunu dolar, diğerleri YAKLAŞIK."""
    df = empty_table()
    for k in TABLE_KEYS:
        p = PARAMS[k]
        if p.example is None or k in ("g", "phi"):
            continue
        sel = df.Kod == k
        df.loc[sel, VALUE_COL] = p.example
        if p.example_src:
            df.loc[sel, "Kaynak"] = p.example_src
        else:
            df.loc[sel, "Not"] = APPROX_NOTE
    return df


def project_table() -> pd.DataFrame:
    """MediClear proje verileri (veriler.md): değer, kaynak ve not ile dolu tablo.

    Belgede ters tasarımla belirlenecek olarak bırakılan değerler boştur; Not sütunu nedenini söyler.
    """
    from .project_data import PROJECT_DATA, DOC
    df = empty_table()
    for k, (val, src, note) in PROJECT_DATA.items():
        if k not in TABLE_KEYS:
            continue
        sel = df.Kod == k
        df.loc[sel, VALUE_COL] = np.nan if val is None else float(val)
        df.loc[sel, "Kaynak"] = f"{DOC}: {src}" if src else ""
        df.loc[sel, "Not"] = note
    return df


def project_settings() -> "Settings":
    from .project_data import SETTINGS
    return Settings.from_dict(SETTINGS)


def apply_material(df: pd.DataFrame, material: str) -> pd.DataFrame:
    """Mandrel malzemesine göre ρ_m, c_m, k_m önerisini yazar."""
    df = df.copy()
    for k, v in MATERIALS.get(material, {}).items():
        df.loc[df.Kod == k, VALUE_COL] = v
        df.loc[df.Kod == k, "Not"] = f"{material} – malzeme tablosu değeri, {APPROX_NOTE}"
    return df


def apply_editor_changes(df: pd.DataFrame, group: str, edited_rows: dict) -> pd.DataFrame:
    """Tablo düzenleyicisinin {satır_sırası: {sütun: değer}} değişikliklerini gruba uygular."""
    df = df.copy()
    rows = df.index[df.Grup == group]
    for pos, changes in edited_rows.items():
        i = rows[int(pos)]
        for col, val in changes.items():
            if col == VALUE_COL:
                df.loc[i, col] = np.nan if val is None or val == "" else float(val)
            elif col in ("Kaynak", "Not"):
                df.loc[i, col] = "" if val is None else str(val)
    return df


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
    """Bu ayarlarla hesapta kullanılan parametreler."""
    keys = [k for k in TABLE_KEYS if k != "T_fuz"]
    if s.material_type != "Organosol":
        keys.remove("phi")
    if s.T_m0_mode == "D1":
        keys.remove("T_m0")
    else:
        # T_m0 doğrudan girildiğinde t_ön D1'in sonucudur; taşıma soğuması kullanılmaz
        keys = [k for k in keys if k not in ("t_pre", "t_tr", "T_amb", "h_amb")]
    if not s.spiral:
        keys = [k for k in keys if k not in WIRE_KEYS]
    return keys


def _val(df: pd.DataFrame, key: str):
    v = df.loc[df.Kod == key, VALUE_COL]
    return None if v.empty or _blank(v.iloc[0]) else float(v.iloc[0])


def validate(df: pd.DataFrame, s: Settings) -> Validation:
    v = Validation()
    act = active_keys(s)
    for _, row in df.iterrows():
        k = row.Kod
        if k not in act and k != "T_fuz":
            continue
        p = PARAMS[k]
        val = row[VALUE_COL]
        if _blank(val):
            if k in act:
                v.issues.append(Issue("hata", k, f"{p.sym} ({p.name}) için değer girilmemiş. "
                                      "Kaynaktan değeri bulup Değer sütununa yaz."))
            continue
        msg = _bound_message(p.bound, p.sym, p.name, float(val))
        if msg:
            v.issues.append(Issue("hata", k, msg))
        if k in act and not str(row.Kaynak or "").strip():
            v.missing_source.append(k)
    _relations(df, s, v)
    return v


def _bound_message(bound, sym, name, x) -> str | None:
    if bound == "positive" and x <= 0:
        return f"{sym} ({name}) sıfırdan büyük olmalı; negatif veya sıfır değer fiziksel değil."
    if bound == "nonneg" and x < 0:
        return f"{sym} ({name}) negatif olamaz."
    if bound == "fraction" and not (0 <= x < 1):
        return f"{sym} ({name}) 0 ile 1 arasında olmalı (ör. %2 için 0,02 yaz)."
    if bound == "fraction_closed" and not (0 < x <= 1):
        return f"{sym} ({name}) 0'dan büyük ve en fazla 1 olmalı."
    return None


def _relations(df: pd.DataFrame, s: Settings, v: Validation) -> None:
    n = lambda k: _val(df, k)  # noqa: E731
    T_g, T_b, T_m0 = n("T_g"), n("T_b"), n("T_m0")
    if T_g is not None and T_b is not None and T_g <= T_b:
        v.issues.append(Issue("hata", "T_b", "T_g, T_b'den büyük olmalı: banyo jel sıcaklığındaysa "
                              "banyo kendiliğinden jelleşir. Plastisol veri sayfasındaki jel "
                              "sıcaklığını ve banyo sıcaklığını kontrol et."))
    if s.T_m0_mode == "direct" and T_m0 is not None and T_g is not None and T_m0 <= T_g:
        v.issues.append(Issue("hata", "T_m0", "T_m0, T_g'den büyük olmalı; mandrel jel sıcaklığının "
                              "altındaysa hiç jel oluşmaz. Fırın sıcaklığını veya ön ısıtma süresini artır."))
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
                                  "R_i'yi 0 yap ya da Hesap ayarları'nda 'T_m0'ı doğrudan gir' seçeneğine geç."))
    ID, OD, R_i = n("ID"), n("OD"), n("R_i")
    if ID is not None and R_i is not None and R_i >= ID / 2:
        v.issues.append(Issue("hata", "R_i", "R_i, mandrelin dış yarıçapından (ID/2) küçük olmalı."))
    if ID is not None and OD is not None and OD <= ID:
        v.issues.append(Issue("hata", "OD", "Dış çap hedefi (OD), iç çaptan (ID) büyük olmalı."))
    if s.spiral:
        d, p = n("d_wire"), n("p_wire")
        if d is not None and p is not None and p < d:
            v.issues.append(Issue("hata", "p_wire", "Hatve p, tel çapı d'den küçük olamaz; sarımlar üst "
                                  "üste biner. Yay teknik resmini kontrol et."))
    T_fuz = n("T_fuz")
    if T_fuz is not None and T_g is not None and T_fuz <= T_g:
        v.issues.append(Issue("uyarı", "T_fuz", "T_füz genellikle T_g'den yüksektir; veri sayfasını "
                              "kontrol et."))


# --- SI'ya çevirme ----------------------------------------------------------------------

def values_si(df: pd.DataFrame) -> dict[str, float]:
    out = {}
    for _, row in df.iterrows():
        if not _blank(row[VALUE_COL]):
            out[row.Kod] = to_si(float(row[VALUE_COL]), row.Birim)
    return out


# --- Kaydet / yükle ---------------------------------------------------------------------

EXPORT_COLS = ["Kod", "Sembol", "Parametre", "Birim", VALUE_COL, "Kaynak", "Not"]


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
    """Kaydedilmiş Excel/CSV'yi okur. Döner: (tablo, ayarlar veya None, uyarılar).

    Eski sürüm dosyalarındaki 'Nominal' sütunu 'Değer' olarak okunur; Min/Max yok sayılır.
    """
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
    if VALUE_COL not in raw.columns and "Nominal" in raw.columns:
        raw = raw.rename(columns={"Nominal": VALUE_COL})

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
        df.loc[df.Kod == key, VALUE_COL] = pd.to_numeric(row.get(VALUE_COL), errors="coerce")
        for col in ("Kaynak", "Not"):
            val = row.get(col)
            df.loc[df.Kod == key, col] = "" if _blank(val) or str(val) == "nan" else str(val)
        matched += 1
    if matched == 0:
        raise ValueError("Dosyada tanınan parametre satırı yok. Sütun başlıklarının "
                         "'Sembol, Parametre, Birim, Değer, Kaynak, Not' olduğundan emin ol.")
    return df, settings, notes
