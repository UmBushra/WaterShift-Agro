"""Simplified seasonal water/salinity engine (PLACEHOLDER for the daily FAO-56 bucket, see HANDOFF.md)."""
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


def _window(w, year, sow_month, dur):
    start = pd.Timestamp(year=int(year), month=int(sow_month), day=1)
    return w[(w.date >= start) & (w.date < start + pd.Timedelta(days=int(dur)))]


def simulate_season(win, crop, ec_start, ec_water, irrigation_cap_mm=IRRIGATION_CAP_MM):
    """Simulate one crop season on a weather window; returns the contract fields."""
    rain, et0 = float(win.rain_mm.sum()), float(win.et0_mm.sum())
    kc = (crop.kc_ini + crop.kc_mid + crop.kc_end) / 3.0
    etc = kc * et0
    eff = EFF_RAIN * rain
    irr = min(max(0.0, etc - eff), irrigation_cap_mm)
    ks = min(1.0, (eff + irr) / etc) if etc > 0 else 1.0
    deficit = max(0.0, etc - rain)
    ec_end = ec_start * (1 - LEACH_PER_100MM_RAIN * rain / 100.0)
    ec_end += SALT_BUILD_PER_100MM_IRR * irr / 100.0 * ec_water + SALT_BUILD_PER_100MM_DEFICIT * deficit / 100.0
    ec_end = max(MIN_EC, ec_end)
    ec_mean = (ec_start + ec_end) / 2
    fs = min(1.0, max(0.0, 1 - crop.salinity_slope_pct_per_dsm / 100 * max(0.0, ec_mean - crop.salinity_threshold_dsm)))
    hot = int((win.tmax_c > crop.tmax_stress_c).sum())
    fh = max(0.5, 1 - HEAT_LOSS_PER_DAY * hot)
    wl = int((win.rain_mm > WATERLOG_RAIN_MM).sum())
    fw = max(0.5, 1 - WATERLOG_LOSS_PER_DAY * wl)
    return dict(rel_yield=ks * fs * fh * fw, water_use_mm=etc, irrigation_mm=irr,
                salinity_start_dsm=ec_start, salinity_end_dsm=ec_end,
                soc_change_pct=SOC_GAIN_PER_T_RESIDUE * crop.residue_t_ha - SOC_LOSS_PER_SEASON,
                n_credit_kg_ha=float(crop.n_credit_kg_ha), cover_days=int(crop.duration_days),
                waterlogging_days=wl)


def simulate_rotation(rotation, weather, soil, crops, year=None, irrigation_cap_mm=IRRIGATION_CAP_MM):
    """Simulate a rotation (list of {crop_id, season, year_index}); see docs/contracts.md."""
    w = weather.copy()
    w["date"] = pd.to_datetime(w["date"])
    year = int(year) if year is not None else int(w.date.dt.year.max()) - 3
    lib = crops.set_index("crop_id")
    ec, out = float(soil["ec_soil_dsm"]), []
    for r in rotation:
        c = lib.loc[r["crop_id"]]
        win = _window(w, year + r["year_index"], c.sow_month, c.duration_days)
        s = simulate_season(win, c, ec, float(soil["ec_water_dsm"]), irrigation_cap_mm)
        ec = s["salinity_end_dsm"]
        out.append({"crop_id": r["crop_id"], "season": r["season"], "year_index": r["year_index"], **s})
    return {"seasons": out}
