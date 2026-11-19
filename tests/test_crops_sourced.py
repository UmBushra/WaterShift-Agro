"""Offline tests for data/processed/crops_sourced.csv (Step 3).
They check shape and provenance bookkeeping, plus a few spot checks against the FAO tables."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
import numpy as np, pandas as pd

PATH = pathlib.Path(__file__).resolve().parents[1] / "data" / "processed" / "crops_sourced.csv"
CONTRACT_COLS = ["crop_id", "name", "family", "is_legume", "season", "sow_month", "harvest_month",
                 "duration_days", "kc_ini", "kc_mid", "kc_end", "tmax_stress_c", "rain_need_mm",
                 "salinity_threshold_dsm", "salinity_slope_pct_per_dsm", "residue_t_ha",
                 "n_credit_kg_ha", "cost_bdt_ha", "yield_t_ha", "price_bdt_t", "source"]
EXTRA_COLS = ["assumed_fields", "missing_fields", "notes"]
NUMERIC = ["sow_month", "harvest_month", "duration_days", "kc_ini", "kc_mid", "kc_end", "tmax_stress_c",
           "rain_need_mm", "salinity_threshold_dsm", "salinity_slope_pct_per_dsm", "residue_t_ha",
           "n_credit_kg_ha", "cost_bdt_ha", "yield_t_ha", "price_bdt_t"]


def _load():
    return pd.read_csv(PATH)


def _split(cell):
    return set() if pd.isna(cell) or str(cell).strip() == "" else set(str(cell).split(";"))


def test_columns_follow_contract():
    df = _load()
    assert list(df.columns) == CONTRACT_COLS + EXTRA_COLS


def test_ids_unique_and_seasons_valid():
    df = _load()
    assert df.crop_id.is_unique
    assert set(df.season) <= {"rabi", "kharif1", "aman"}
    assert set(df.season) == {"rabi", "kharif1", "aman"}        # every season has at least one crop
    assert set(df.is_legume) <= {0, 1}


def test_blank_cells_are_declared_missing_and_assumed_cells_are_filled():
    df = _load()
    for _, r in df.iterrows():
        missing, assumed = _split(r.missing_fields), _split(r.assumed_fields)
        assert not (missing & assumed), r.crop_id
        for col in NUMERIC:
            if pd.isna(r[col]):
                assert col in missing, f"{r.crop_id}.{col} is blank but not listed in missing_fields"
        for col in missing:
            assert pd.isna(r[col]), f"{r.crop_id}.{col} listed missing but has a value"
        for col in assumed:
            assert not pd.isna(r[col]), f"{r.crop_id}.{col} listed assumed but is blank"


def test_every_row_cites_a_source_for_fao_values():
    df = _load()
    for _, r in df.iterrows():
        assert "FAO-56" in r.source and "Table 12" in r.source, r.crop_id
        assert "FAO-29" in r.source and "A1.1" in r.source, r.crop_id
        for col in ["kc_ini", "kc_mid", "kc_end", "salinity_threshold_dsm", "salinity_slope_pct_per_dsm"]:
            assert col not in _split(r.assumed_fields) | _split(r.missing_fields), (r.crop_id, col)


def test_value_ranges():
    df = _load()
    assert df[["kc_ini", "kc_mid", "kc_end"]].apply(lambda s: s.between(0.1, 1.4)).all().all()
    assert (df.kc_mid >= df.kc_ini).all()
    assert df.salinity_threshold_dsm.between(0.5, 12).all()
    assert df.salinity_slope_pct_per_dsm.between(1, 40).all()
    assert df.sow_month.between(1, 12).all() and df.harvest_month.between(1, 12).all()


def test_month_window_roughly_matches_duration():
    """Sow month + duration should land in the stated harvest month (+/- 1 month). Both are ASSUMPTIONS."""
    df = _load()
    for _, r in df.iterrows():
        start = (r.sow_month - 1) * 30.4 + 15                     # middle of the sow month
        end_month = int(((start + r.duration_days) / 30.4) % 12) + 1
        diff = min((end_month - r.harvest_month) % 12, (r.harvest_month - end_month) % 12)
        assert diff <= 1, f"{r.crop_id}: sow {r.sow_month} + {r.duration_days} d -> month {end_month}, stated {r.harvest_month}"


def test_spot_checks_against_fao_tables():
    df = _load().set_index("crop_id")
    r = df.loc["aman_rice"]                                       # FAO-56 T12 rice 1.05/1.20/0.90-0.60; FAO-29 3.0/12
    assert (r.kc_ini, r.kc_mid) == (1.05, 1.20) and 0.60 <= r.kc_end <= 0.90
    assert (r.salinity_threshold_dsm, r.salinity_slope_pct_per_dsm) == (3.0, 12)
    m = df.loc["maize"]                                           # corn 1.7/12; Kc 0.30/1.20
    assert (m.salinity_threshold_dsm, m.salinity_slope_pct_per_dsm, m.kc_ini, m.kc_mid) == (1.7, 12, 0.30, 1.20)
    w = df.loc["wheat"]                                           # 6.0/7.1
    assert (w.salinity_threshold_dsm, w.salinity_slope_pct_per_dsm) == (6.0, 7.1)
    g = df.loc["groundnut"]                                       # peanut 3.2/29
    assert (g.salinity_threshold_dsm, g.salinity_slope_pct_per_dsm) == (3.2, 29)


def test_legume_flag_matches_family():
    df = _load()
    assert ((df.family == "Fabaceae") == (df.is_legume == 1)).all()
