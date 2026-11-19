"""Daily FAO-56 single-coefficient soil water bucket + salinity/heat/waterlogging penalties. NaN crop inputs are skipped and reported."""
import pathlib
import numpy as np
import pandas as pd

# Named constants: ALL are assumptions, listed in docs/assumptions.md
EFF_RAIN = 0.8              # fraction of rain that is effective
IRRIGATION_CAP_MM = 150.0   # default irrigation a farmer can access per season
SALT_BUILD_PER_100MM_IRR = 0.15   # dS/m added per 100 mm irrigation per dS/m of water EC
SALT_BUILD_PER_100MM_DEFICIT = 0.10  # dS/m added per 100 mm of dry-season ET not met by rain
LEACH_PER_100MM_RAIN = 0.12       # fraction of soil EC removed per 100 mm rain
HEAT_LOSS_PER_DAY = 0.01    # relative yield lost per day above crop tmax_stress_c
WATERLOG_RAIN_MM = 40.0     # daily rain above this counts as a waterlogging day
WATERLOG_LOSS_PER_DAY = 0.02
SOC_GAIN_PER_T_RESIDUE = 0.01   # % SOC per t/ha residue
SOC_LOSS_PER_SEASON = 0.005     # % SOC lost per season (oxidation)
MIN_EC = 0.2


# DEFAULTS, used only where a crop has no cited value in data/processed/crop_water_params.csv (reported in `default_params`).
ROOT_DEPTH_M = 0.5          # assumption: default root depth (m)
P_DEPLETION = 0.5           # assumption: default allowable depletion fraction (FAO-56 says 0.5 is commonly used, Ch. 8)
STAGE_FRACTIONS = (0.2, 0.3, 0.3, 0.2)  # assumption: default ini/dev/mid/late share of duration
KY = 1.0                    # assumption: default yield response factor (FAO-56 Ch. 8: use 1 where Ky is unknown)

# Crop-specific values from FAO-56 Table 22 (root depth Zr, depletion fraction p), Table 24 (Ky), Table 11 (stage lengths).
# Not applied: the ETc adjustment of p (p = p_table + 0.04 (5 - ETc)), the 5-10% soil texture adjustment of p, growing root depth.
WATER_PARAMS_PATH = pathlib.Path(__file__).resolve().parents[2] / "data" / "processed" / "crop_water_params.csv"
_PARAM_COLS = ["root_depth_m", "p_depletion", "ky", "l_ini", "l_dev", "l_mid", "l_late"]


def load_water_params(path=None):
    """crop_water_params.csv indexed by crop_id, or None if the file is not there."""
    p = pathlib.Path(path) if path else WATER_PARAMS_PATH
    return pd.read_csv(p).set_index("crop_id")[_PARAM_COLS] if p.exists() else None


def _param(crop, name, default, used_default):
    v = crop.get(name, np.nan)
    if v is None or pd.isna(v):
        used_default.append(name)
        return default
    return float(v)


def _stage_fractions(crop, used_default):
    ls = [crop.get(k, np.nan) for k in ("l_ini", "l_dev", "l_mid", "l_late")]
    if any(v is None or pd.isna(v) for v in ls) or sum(ls) <= 0:
        used_default.append("stage_fractions")
        return STAGE_FRACTIONS
    tot = float(sum(ls))
    return tuple(float(v) / tot for v in ls)


def _window(w, year, sow_month, dur):
    start = pd.Timestamp(year=int(year), month=int(sow_month), day=1)
    return w[(w.date >= start) & (w.date < start + pd.Timedelta(days=int(dur)))]


def _kc(i, n, c, fractions=STAGE_FRACTIONS):
    """Piecewise-linear Kc over the four stages (lengths = fractions of the season)."""
    f = i / max(1, n - 1)
    a, b, m = fractions[0], fractions[0] + fractions[1], fractions[0] + fractions[1] + fractions[2]
    if f < a: return c.kc_ini
    if f < b: return c.kc_ini + (c.kc_mid - c.kc_ini) * (f - a) / (b - a)
    if f < m: return c.kc_mid
    return c.kc_mid + (c.kc_end - c.kc_mid) * (f - m) / (1 - m)


def simulate_season(win, crop, ec_start, ec_water, irrigation_cap_mm=IRRIGATION_CAP_MM, fc=0.35, wp=0.18):
    """Daily bucket for one season; returns the contract fields plus missing_inputs and the water-balance terms.

    Balance per season (start at field capacity): rain_mm + irrigation_mm = eta_mm + runoff_mm + drainage_mm + storage_change_mm.
    water_use_mm is the POTENTIAL crop ET (ETc); eta_mm is the actual ET that the balance uses.
    """
    used_default = []
    zr = _param(crop, "root_depth_m", ROOT_DEPTH_M, used_default)
    p_dep = _param(crop, "p_depletion", P_DEPLETION, used_default)
    ky = _param(crop, "ky", KY, used_default)
    fractions = _stage_fractions(crop, used_default)
    taw = 1000.0 * (fc - wp) * zr
    raw = p_dep * taw
    dr, left, irr, etc_t, eta_t, ec, wl, n = 0.0, irrigation_cap_mm, 0.0, 0.0, 0.0, float(ec_start), 0, len(win)
    ec_sum, rain_t, runoff_t, drain_t = 0.0, 0.0, 0.0, 0.0
    for i, (rain, et0) in enumerate(zip(win.rain_mm.values, win.et0_mm.values)):
        etc = _kc(i, n, crop, fractions) * et0
        ks = 1.0 if dr <= raw else max(0.0, (taw - dr) / (taw - raw))
        eta = ks * etc
        dr_new = dr - EFF_RAIN * rain + eta      # depletion after effective rain and crop use
        if dr_new < 0.0:                         # root zone above field capacity: the surplus drains below the roots
            drain_t += -dr_new
            dr_new = 0.0
        elif dr_new > taw:                       # crop cannot take more water than the root zone holds
            eta -= dr_new - taw
            dr_new = taw
        dr = dr_new
        rain_t += rain
        runoff_t += (1.0 - EFF_RAIN) * rain      # non-effective rain leaves the field as runoff
        if dr >= raw and left > 0:
            a = min(dr, left); dr -= a; left -= a; irr += a
            ec += SALT_BUILD_PER_100MM_IRR * a / 100.0 * ec_water
        ec = max(MIN_EC, ec * (1 - LEACH_PER_100MM_RAIN * rain / 100.0) + SALT_BUILD_PER_100MM_DEFICIT * max(0.0, etc - rain) / 100.0)
        ec_sum += ec
        etc_t += etc; eta_t += eta; wl += int(rain > WATERLOG_RAIN_MM)
    ec_mean = ec_sum / max(1, n)
    # FAO-56 Eq. 90: 1 - Ya/Ym = Ky (1 - ETa/ETc)
    kw = min(1.0, max(0.0, 1.0 - ky * (1.0 - eta_t / etc_t))) if etc_t > 0 else 1.0
    fs = min(1.0, max(0.0, 1 - crop.salinity_slope_pct_per_dsm / 100 * max(0.0, ec_mean - crop.salinity_threshold_dsm)))
    missing = []
    if pd.isna(crop.tmax_stress_c):
        fh = 1.0; missing.append("tmax_stress_c")
    else:
        fh = max(0.5, 1 - HEAT_LOSS_PER_DAY * int((win.tmax_c > crop.tmax_stress_c).sum()))
    fw = max(0.5, 1 - WATERLOG_LOSS_PER_DAY * wl)
    nan = float("nan")
    if pd.isna(crop.residue_t_ha): missing.append("residue_t_ha")
    if pd.isna(crop.n_credit_kg_ha): missing.append("n_credit_kg_ha")
    return dict(rel_yield=kw * fs * fh * fw, water_use_mm=etc_t, irrigation_mm=irr,
                eta_mm=eta_t, rain_mm=rain_t, runoff_mm=runoff_t, drainage_mm=drain_t, storage_change_mm=-dr,
                salinity_start_dsm=float(ec_start), salinity_end_dsm=float(ec),
                soc_change_pct=nan if pd.isna(crop.residue_t_ha) else SOC_GAIN_PER_T_RESIDUE * crop.residue_t_ha - SOC_LOSS_PER_SEASON,
                n_credit_kg_ha=nan if pd.isna(crop.n_credit_kg_ha) else float(crop.n_credit_kg_ha),
                cover_days=int(crop.duration_days), waterlogging_days=wl, missing_inputs=missing, default_params=used_default)


def simulate_rotation(rotation, weather, soil, crops, year=None, irrigation_cap_mm=IRRIGATION_CAP_MM):
    """Simulate a rotation (list of {crop_id, season, year_index}); see docs/contracts.md."""
    w = weather.copy()
    w["date"] = pd.to_datetime(w["date"])
    year = int(year) if year is not None else int(w.date.dt.year.max()) - 3
    lib = crops.set_index("crop_id")
    if "root_depth_m" not in lib.columns:           # merge the cited water parameters if the crop table has none
        params = load_water_params()
        if params is not None:
            lib = lib.join(params, how="left")
    ec, out = float(soil["ec_soil_dsm"]), []
    for r in rotation:
        c = lib.loc[r["crop_id"]]
        win = _window(w, year + r["year_index"], c.sow_month, c.duration_days)
        s = simulate_season(win, c, ec, float(soil["ec_water_dsm"]), irrigation_cap_mm,
                            float(soil.get("field_capacity", 0.35)), float(soil.get("wilting_point", 0.18)))
        ec = s["salinity_end_dsm"]
        out.append({"crop_id": r["crop_id"], "season": r["season"], "year_index": r["year_index"], **s})
    return {"seasons": out}
