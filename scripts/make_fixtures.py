"""Make SYNTHETIC demo weather (not real NASA data). Replace with data_fetch.py output."""
import numpy as np, pandas as pd
rng = np.random.default_rng(42)
d = pd.date_range("2010-01-01", "2024-12-31")
doy, mon = d.dayofyear.values, d.month.values
wet = np.where(np.isin(mon, [6, 7, 8, 9]), 0.6, np.where(np.isin(mon, [5, 10]), 0.3, 0.05))
mean = np.where(np.isin(mon, [6, 7, 8, 9]), 18, np.where(np.isin(mon, [5, 10]), 12, 6))
yf = dict(zip(range(2010, 2025), rng.lognormal(0, 0.25, 15)))
f = np.array([yf[y] for y in d.year])
rain = (rng.random(len(d)) < wet) * rng.gamma(0.7, mean / 0.7 * f)
tmax = 30 + 5 * np.sin(2 * np.pi * (doy - 60) / 365) + rng.normal(0, 1.5, len(d))
tmin = tmax - 8 - rng.normal(0, 1, len(d))
et0 = np.clip(3.5 + 1.5 * np.sin(2 * np.pi * (doy - 60) / 365) - 0.02 * rain, 1.0, None)
pd.DataFrame(dict(date=d.date, rain_mm=rain.round(1), tmax_c=tmax.round(1), tmin_c=tmin.round(1),
                  solar_mj_m2=18.0, rh_pct=75.0, wind_ms=2.0, et0_mm=et0.round(2))).to_csv(
    "data/processed/weather_daily.csv", index=False)
