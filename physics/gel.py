"""D2 (enerji tavanı), D3 (silindirik 1B geçici ısı iletimi) ve D4 (difüzyon yaklaşımı).

Tüm girdi ve çıktılar SI (m, K, s).

D3 sayısal şeması
-----------------
* Sonlu hacim, radyal ızgara; bölge sınırları hücre yüzlerine denk gelir.
* Yüzey iletkenliği iki yarım hücrenin seri direnci (harmonik ortalama):
  G = r_f / (d_sol/k_sol + d_sağ/k_sağ).
* r = 0'da simetri, içi boş mandrelde r = R_i'de yalıtım: iç yüzeyde akı sıfır.
* Dış sınırda T = T_b (Dirichlet), yarıçap en az R_s + max(5·√(α_p·t), 3 mm).
* Zaman: Crank–Nicolson (θ = 0,5); başlangıçtaki keskin sıçramanın salınım üretmemesi için
  ilk adımlar tam örtük (θ = 1, Rannacher başlangıcı). Adımlar t_k = t·(k/n)² ile sıklaşır,
  böylece cephenin hızlı ilerlediği ilk anlar ince çözülür. Her iki şema da koşulsuz kararlıdır.
* Jel cephesi: plastisolde T ≥ T_g olan en dış nokta, T_g izotermi doğrusal interpolasyonla.
  Jelleşme geri dönüşsüz: s_jel(t) = max_{t' ≤ t} s_ham(t').
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from scipy.linalg import solve_banded

# ---------------------------------------------------------------------------------------
# D2 – Enerji tavanı
# ---------------------------------------------------------------------------------------


def energy_ceiling(rho_m: float, c_m: float, R: float, R_i: float, T_m0: float, T_g: float,
                   rho_p: float, c_p: float, T_b: float) -> tuple[float, float]:
    """D2 tam ifade: (X, s_max)."""
    if T_m0 <= T_g:
        return 0.0, 0.0
    X = rho_m * c_m * (R**2 - R_i**2) * (T_m0 - T_g) / (rho_p * c_p * R**2 * (T_g - T_b))
    return X, R * (math.sqrt(1.0 + X) - 1.0)


def energy_ceiling_thin(rho_m: float, c_m: float, R: float, T_m0: float, T_g: float,
                        rho_p: float, c_p: float, T_b: float) -> float:
    """D2 ince katman yaklaşımı (s ≪ R, dolu mandrel)."""
    if T_m0 <= T_g:
        return 0.0
    return rho_m * c_m * R * (T_m0 - T_g) / (2.0 * rho_p * c_p * (T_g - T_b))


def energy_ceiling_layers(layers: list["Layer"], T_g: float, rho_p: float, c_p: float,
                          T_b: float) -> float:
    """D2'nin bileşik bölgeye uygulanışı (spiralli tüpte 2. daldırma için).

    Payda mandrel yerine tüm katı katmanların ısı kapasitesi kullanılır; tek mandrel
    katmanında energy_ceiling ile aynı sonucu verir.
    """
    R_s = layers[-1].r_out
    stored = sum(L.rho * L.c * (L.r_out**2 - L.r_in**2) * max(L.T_init - T_g, 0.0) for L in layers)
    if stored <= 0.0:
        return 0.0
    X = stored / (rho_p * c_p * R_s**2 * (T_g - T_b))
    return R_s * (math.sqrt(1.0 + X) - 1.0)


# ---------------------------------------------------------------------------------------
# D3 – Isı iletimi
# ---------------------------------------------------------------------------------------

QUALITY = {
    # bath: plastisol bölgesindeki hücre, mandrel: mandreldeki hücre, steps: zaman adımı
    "hızlı": {"bath": 60, "mandrel": 15, "steps": 80},
    "normal": {"bath": 300, "mandrel": 60, "steps": 400},
    "hassas": {"bath": 600, "mandrel": 120, "steps": 800},
}
MIN_FAR_FIELD = 3e-3     # dış sınır, yüzeyden en az bu kadar uzakta [m]
N_STARTUP = 4            # Rannacher başlangıcındaki tam örtük adım sayısı


@dataclass
class Layer:
    r_in: float
    r_out: float
    rho: float
    c: float
    k: float
    T_init: float
    name: str = ""


@dataclass
class RadialSolution:
    t: np.ndarray            # (nt,)
    faces: np.ndarray        # (N+1,)
    rc: np.ndarray           # (N,) hücre merkezleri
    T: np.ndarray            # (nt, N)
    region: np.ndarray       # (N,) hücrenin katman indeksi
    energy: np.ndarray       # (nt,) Σ C·(T − T_out)  [J/(m·rad)]
    q_out: np.ndarray        # (nt,) dış sınırdan çıkan birikimli enerji
    k_cell: np.ndarray       # (N,)
    T_out: float

    @property
    def energy_error(self) -> float:
        """Göreli enerji dengesizliği |E(t) + Q_out(t) − E(0)| / |E(0)| (en büyük)."""
        E0 = self.energy[0]
        return float(np.max(np.abs(self.energy + self.q_out - E0)) / max(abs(E0), 1e-300))


def _grid(layers: list[Layer], cells: list[int]):
    faces = [np.array([layers[0].r_in])]
    region = []
    for i, (L, n) in enumerate(zip(layers, cells)):
        faces.append(np.linspace(L.r_in, L.r_out, n + 1)[1:])
        region.extend([i] * n)
    faces = np.concatenate(faces)
    return faces, 0.5 * (faces[:-1] + faces[1:]), np.array(region)


def solve_radial(layers: list[Layer], cells: list[int], T_out: float, t_end: float,
                 n_steps: int, theta: float = 0.5, n_startup: int = N_STARTUP,
                 grading: float = 2.0) -> RadialSolution:
    """Çok katmanlı silindirde ρc ∂T/∂t = (1/r) ∂/∂r (k r ∂T/∂r) çözümü.

    layers: içten dışa bitişik katmanlar. İç yüzey yalıtımlı (veya r = 0 simetri),
    dış yüzey T = T_out.
    """
    faces, rc, region = _grid(layers, cells)
    rho = np.array([layers[i].rho for i in region])
    cp = np.array([layers[i].c for i in region])
    k = np.array([layers[i].k for i in region])
    T = np.array([layers[i].T_init for i in region], dtype=float)
    N = len(rc)

    C = rho * cp * 0.5 * (faces[1:] ** 2 - faces[:-1] ** 2)
    G = faces[1:-1] / ((faces[1:-1] - rc[:-1]) / k[:-1] + (rc[1:] - faces[1:-1]) / k[1:])
    G_out = faces[-1] * k[-1] / (faces[-1] - rc[-1])
    diag = np.zeros(N)
    diag[:-1] -= G
    diag[1:] -= G
    diag[-1] -= G_out
    b = np.zeros(N)
    b[-1] = G_out * T_out

    def apply_A(x):
        y = diag * x + b
        y[:-1] += G * x[1:]
        y[1:] += G * x[:-1]
        return y

    t = t_end * (np.arange(n_steps + 1) / n_steps) ** grading
    T_hist = np.empty((n_steps + 1, N))
    T_hist[0] = T
    q_out = np.zeros(n_steps + 1)
    ab = np.zeros((3, N))
    for n in range(n_steps):
        dt = t[n + 1] - t[n]
        th = 1.0 if n < n_startup else theta
        ab[0, 1:] = -th * G
        ab[1] = C / dt - th * diag
        ab[2, :-1] = -th * G
        rhs = C / dt * T + (1.0 - th) * (apply_A(T) - b) + b
        T_new = solve_banded((1, 1), ab, rhs)
        q_out[n + 1] = q_out[n] + G_out * (th * T_new[-1] + (1 - th) * T[-1] - T_out) * dt
        T = T_new
        T_hist[n + 1] = T

    energy = (T_hist - T_out) @ C
    return RadialSolution(t=t, faces=faces, rc=rc, T=T_hist, region=region, energy=energy,
                          q_out=q_out, k_cell=k, T_out=T_out)


def gel_front(sol: RadialSolution, i_surf: int, T_g: float) -> np.ndarray:
    """Her zaman adımı için ham jel kalınlığı s_ham(t) (geri dönüşsüzlük uygulanmadan)."""
    R_s = sol.faces[i_surf]
    # yüzey (arayüz) sıcaklığı: iki yarım hücre arasında akı sürekliliği
    wl = sol.k_cell[i_surf - 1] / (R_s - sol.rc[i_surf - 1])
    wr = sol.k_cell[i_surf] / (sol.rc[i_surf] - R_s)
    T_if = (wl * sol.T[:, i_surf - 1] + wr * sol.T[:, i_surf]) / (wl + wr)
    rr = np.concatenate([[R_s], sol.rc[i_surf:]])
    TT = np.column_stack([T_if, sol.T[:, i_surf:]])

    s = np.zeros(len(sol.t))
    hot = TT >= T_g
    for n in range(len(sol.t)):
        idx = np.flatnonzero(hot[n])
        if idx.size == 0:
            continue
        j = idx[-1]
        if j == len(rr) - 1:
            s[n] = rr[-1] - R_s
            continue
        T1, T2 = TT[n, j], TT[n, j + 1]
        frac = (T1 - T_g) / (T1 - T2) if T1 != T2 else 0.0
        s[n] = rr[j] + frac * (rr[j + 1] - rr[j]) - R_s
    return s


@dataclass
class GelResult:
    t: np.ndarray
    s_raw: np.ndarray        # D3 tanımı (anlık)
    s_gel: np.ndarray        # geri dönüşsüz jel kalınlığı
    sol: RadialSolution
    R_s: float               # plastisolle temas eden yüzeyin yarıçapı
    i_surf: int
    layers: list[Layer] = field(default_factory=list)
    alpha_p: float = 0.0

    @property
    def s_final(self) -> float:
        return float(self.s_gel[-1])


def gel_layer(layers: list[Layer], rho_p: float, c_p: float, k_p: float, T_b: float,
              T_g: float, t_wait: float, quality: str | dict = "normal") -> GelResult:
    """D3: katı katmanlar (mandrel [+ önceki kaplama]) + plastisol banyosu.

    quality: QUALITY anahtarı veya {"bath", "mandrel", "steps"} sözlüğü.
    """
    if t_wait <= 0:
        raise ValueError("Bekleme süresi sıfırdan büyük olmalı.")
    q = QUALITY[quality] if isinstance(quality, str) else quality
    alpha_p = k_p / (rho_p * c_p)
    R_s = layers[-1].r_out
    R_far = R_s + max(5.0 * math.sqrt(alpha_p * t_wait), MIN_FAR_FIELD)
    bath = Layer(R_s, R_far, rho_p, c_p, k_p, T_b, "plastisol banyosu")
    dr_bath = (R_far - R_s) / q["bath"]

    cells = []
    for i, L in enumerate(layers):
        if i == 0:
            cells.append(q["mandrel"])
        else:   # önceki kaplama: banyo ile aynı çözünürlük
            cells.append(max(4, int(math.ceil((L.r_out - L.r_in) / dr_bath))))
    cells.append(q["bath"])

    sol = solve_radial(layers + [bath], cells, T_b, t_wait, q["steps"])
    i_surf = int(sum(cells[:-1]))
    s_raw = gel_front(sol, i_surf, T_g)
    return GelResult(t=sol.t, s_raw=s_raw, s_gel=np.maximum.accumulate(s_raw), sol=sol,
                     R_s=R_s, i_surf=i_surf, layers=layers, alpha_p=alpha_p)


# ---------------------------------------------------------------------------------------
# D4 – Difüzyon yaklaşımı
# ---------------------------------------------------------------------------------------


def diffusion_estimate(C: float, alpha_p: float, t) -> np.ndarray:
    return C * np.sqrt(alpha_p * np.asarray(t, dtype=float))


def fit_diffusion_coefficient(t: np.ndarray, s: np.ndarray, alpha_p: float) -> float:
    """s ≈ C·√(α_p·t) için en küçük kareler C (t > 0 noktaları)."""
    mask = t > 0
    x = np.sqrt(alpha_p * t[mask])
    denom = float(np.dot(x, x))
    return float(np.dot(s[mask], x) / denom) if denom > 0 else 0.0
