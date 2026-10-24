"""D1–D11'i hesap sırasıyla birleştiren model. Girdi: SI değerli sözlük (anahtarlar symbols.PARAMS).

Spiralli tüp iki daldırma olarak modellenir:
* 1. daldırma: çıplak mandrel → s_1 (= s_kür).
* 2. daldırma: katmanlar içten dışa mandrel (T_m0,2), iç PVC katmanı s_1 (T_s1, plastisol
  özellikleri) ve tel halkası d (çelik tel + oluklara dolan plastisol; ρc_eff, Rayleigh k_eff,
  enerji dengesinden T_halka – bkz. wire.py). Plastisolle temas eden yüzey R + s_1 + d (tel tepesi).
* w = s_1 + d_tel + s_2.
Sürüklenen film, plastisolle temas eden yüzeyin üstündeki jel katmanına (R_s + s_jel) çekilir.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import film, gel, preheat, wall, wire


class ModelError(ValueError):
    """Kullanıcıya gösterilebilecek, sade Türkçe hata."""


@dataclass
class Options:
    spiral: bool = True
    T_m0_mode: str = "direct"        # "direct" (doğrudan) | "D1" (ön ısıtmadan hesapla)
    quality: str = "normal"          # gel.QUALITY anahtarı
    keep_details: bool = True        # D3 alanını (grafikler için) sakla


@dataclass
class DipResult:
    index: int
    T_m0: float
    t_wait: float
    R_s: float                # plastisolle temas eden yüzey yarıçapı
    s_max: float              # D2 (tam)
    s_max_thin: float | None  # D2 ince katman (yalnız dolu mandrel, 1. daldırma)
    s_jel: float              # D3
    C: float                  # D4
    eta_b: float              # D5
    film: film.FilmResult     # D6, D7
    h0: float                 # kullanılan çekme anı film kalınlığı
    h_stop: float             # D8 h_dur
    h: float                  # D8 boy boyunca ortalama
    h_top: float
    h_bottom: float
    s_toplam: float           # s_jel + h
    s_kur: float              # D9
    gel_result: gel.GelResult | None = None


@dataclass
class ModelResult:
    R: float
    T_m0: float
    preheat: dict | None
    dip1: DipResult
    dip2: DipResult | None
    w: float
    w_target: float
    w_tol: float
    deviation: float
    ok: bool
    warnings: list[str] = field(default_factory=list)
    wire: wire.WireResult | None = None

    def summary(self) -> dict[str, float]:
        """Tablolar için skaler sonuçlar (SI)."""
        d1, d2 = self.dip1, self.dip2
        out = {
            "T_m0": self.T_m0, "s_jel_1": d1.s_jel, "h_1": d1.h, "s_1": d1.s_kur,
            "s_toplam": d1.s_toplam, "w": self.w, "deviation": self.deviation,
            "ok": float(self.ok),
        }
        if d2 is not None:
            out.update({"s_jel_2": d2.s_jel, "h_2": d2.h, "s_2": d2.s_kur})
        return out


def check_inputs(p: dict) -> None:
    """Modelin çalışamayacağı durumlar (ayrıntılı doğrulama arayüzde yapılır)."""
    if p["T_g"] <= p["T_b"]:
        raise ModelError("T_g, T_b'den büyük olmalı: banyo jel sıcaklığındaysa banyo kendiliğinden "
                         "jelleşir. Plastisol veri sayfasındaki jel sıcaklığını ve banyo sıcaklığını "
                         "kontrol et.")
    if p["R_i"] >= p["ID"] / 2:
        raise ModelError("Mandrel iç yarıçapı R_i, dış yarıçaptan (ID/2) küçük olmalı.")


def run_model(p: dict, opt: Options | None = None) -> ModelResult:
    opt = opt or Options()
    check_inputs(p)
    R = p["ID"] / 2.0
    warnings: list[str] = []

    pre = None
    if opt.T_m0_mode == "D1":
        if p["R_i"] > 0:
            raise ModelError("D1 yalnızca dolu mandrel için tanımlı. İçi boş mandrelde T_m0'ı "
                             "doğrudan gir.")
        pre = preheat.preheat(p["rho_m"], p["c_m"], p["k_m"], R, p["R_i"], p["h_oven"],
                              p["T_oven"], p["T_0"], p["t_pre"])
        # fırın çıkışından banyoya taşımada havada soğuma
        T_m0, tau_t = preheat.transfer_cooling(pre["T_m_end"], p["T_amb"], p["rho_m"], p["c_m"], R,
                                               p["h_amb"], p["t_tr"])
        pre.update(T_exit=pre["T_m_end"], T_m0=T_m0, tau_t=tau_t)
        if not pre["biot_ok"]:
            warnings.append(f"Bi = {pre['Bi']:.3f} ≥ 0,1: toplu kütle modeli (D1) geçersiz.")
    else:
        T_m0 = p["T_m0"]
    if T_m0 <= p["T_g"]:
        warnings.append("T_m0 ≤ T_g: mandrel jel sıcaklığına ulaşmıyor, jel katmanı oluşmaz.")

    mandrel = gel.Layer(p["R_i"], R, p["rho_m"], p["c_m"], p["k_m"], T_m0, "mandrel")
    dip1 = _dip(1, [mandrel], p, T_m0, p["t_wait"], opt)

    dip2 = None
    wr = None
    d_wire = 0.0
    if opt.spiral:
        d_wire = p["d_wire"]
        if d_wire > 0 and p["p_wire"] < d_wire:
            raise ModelError("Hatve p, tel çapı d'den küçük olamaz.")
        T2, t2 = p["T_m0_2"], p["t_wait_2"]
        R1 = R + dip1.s_kur
        layers = [gel.Layer(p["R_i"], R, p["rho_m"], p["c_m"], p["k_m"], T2, "mandrel")]
        if R1 > R:
            layers.append(gel.Layer(R, R1, p["rho_p"], p["c_p"], p["k_p"], p["T_s1"], "iç PVC katmanı"))
        if d_wire > 0:
            wr = wire.analyze(p, T_m0)
            # tel halkası: ρc_eff tek sayı olarak verilir (rho = ρc_eff, c = 1)
            layers.append(gel.Layer(R1, R1 + d_wire, wr.rhoc_eff, 1.0, wr.k_eff, wr.T_ring, "tel halkası"))
        dip2 = _dip(2, layers, p, T2, t2, opt)
        w = wall.spiral_wall(dip1.s_kur, d_wire, dip2.s_kur)
    else:
        w = dip1.s_kur

    w_target, w_tol = wall.wall_target(p["ID"], p["OD"], p["OD_tol"])
    dev, ok = wall.check_target(w, w_target, w_tol)
    return ModelResult(R=R, T_m0=T_m0, preheat=pre, dip1=dip1, dip2=dip2, w=w, w_target=w_target,
                       w_tol=w_tol, deviation=dev, ok=ok, warnings=warnings, wire=wr)


def _dip(index: int, layers: list[gel.Layer], p: dict, T_m0: float, t_wait: float,
         opt: Options) -> DipResult:
    R_s = layers[-1].r_out
    if index == 1 and len(layers) == 1:
        _, s_max = gel.energy_ceiling(p["rho_m"], p["c_m"], R_s, p["R_i"], T_m0, p["T_g"],
                                      p["rho_p"], p["c_p"], p["T_b"])
        s_thin = (gel.energy_ceiling_thin(p["rho_m"], p["c_m"], R_s, T_m0, p["T_g"], p["rho_p"],
                                          p["c_p"], p["T_b"]) if p["R_i"] <= 0 else None)
    else:
        s_max = gel.energy_ceiling_layers(layers, p["T_g"], p["rho_p"], p["c_p"], p["T_b"])
        s_thin = None

    g_res = gel.gel_layer(layers, p["rho_p"], p["c_p"], p["k_p"], p["T_b"], p["T_g"], t_wait,
                          opt.quality)
    s_jel = g_res.s_final
    C = gel.fit_diffusion_coefficient(g_res.t, g_res.s_gel, g_res.alpha_p)

    eta_b = float(film.viscosity(p["eta_ref"], p["E_a"], p["T_b"], p["T_ref"]))
    try:
        choice = film.film_thickness(R_s + s_jel, eta_b, p["U"], p["gamma"],
                                     p["rho_p"], p["g"], p["C_lld"], p["C_fib"], p["C_grav"])
    except ValueError as exc:
        raise ModelError(str(exc)) from exc
    h0 = choice.h0
    h_stop = film.stop_thickness(p["tau_y"], p["rho_p"], p["g"], p["C_dur"])
    args = (p["t_drain"], h0, eta_b, p["rho_p"], p["g"], h_stop)
    h = film.drained_mean(p["L"], *args)
    h_top, h_bottom = film.drained_profile([0.0, p["L"]], *args)

    return DipResult(index=index, T_m0=T_m0, t_wait=t_wait, R_s=R_s, s_max=s_max,
                     s_max_thin=s_thin, s_jel=s_jel, C=C, eta_b=eta_b, film=choice, h0=h0,
                     h_stop=h_stop, h=h, h_top=float(h_top), h_bottom=float(h_bottom),
                     s_toplam=s_jel + h,
                     s_kur=wall.cured_thickness(s_jel, h, p["eps"], p.get("phi", 1.0)),
                     gel_result=g_res if opt.keep_details else None)
