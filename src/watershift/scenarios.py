"""Stress tests. baseline + bad_year are implemented; future (NEX-GDDP-CMIP6) is a TODO in HANDOFF.md."""
import numpy as np
import pandas as pd
from .water_balance import simulate_rotation

BAD_YEAR_QUANTILE = 0.10  # worst 10% of years by total annual rain (assumption, documented rule)


def _stats(vals):
    return {"p10": float(np.percentile(vals, 10)), "p50": float(np.percentile(vals, 50)),
            "p90": float(np.percentile(vals, 90))}


def _run(rotation, w, soil, crops, years):
    y = [np.mean([s["rel_yield"] for s in simulate_rotation(rotation, w, soil, crops, year=yr)["seasons"]])
         for yr in years]
    return _stats(y)


def run_scenarios(rotation, weather, future_climate, soil, crops):
    """Return baseline, bad_year and future (future not implemented yet -> None). See docs/contracts.md."""
    w = weather.copy()
    w["date"] = pd.to_datetime(w["date"])
    yearly = w.groupby(w.date.dt.year).rain_mm.sum()
    years = [y for y in yearly.index if y + 2 <= yearly.index.max()]
    cut = yearly.loc[years].quantile(BAD_YEAR_QUANTILE)
    bad = [y for y in years if yearly[y] <= cut] or [min(years, key=lambda y: yearly[y])]
    return {"baseline": _run(rotation, w, soil, crops, years),
            "bad_year": _run(rotation, w, soil, crops, bad), "future": None}
