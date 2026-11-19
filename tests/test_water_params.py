"""Step 4b (cited constants): crop_water_params.csv shape/provenance, spot checks against FAO-56 tables, engine use.
Self-contained: builds its own synthetic weather, so it does not depend on the fixture weather file."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
import numpy as np, pandas as pd
from watershift import water_balance as wb

D = pathlib.Path(__file__).resolve().parents[1] / "data" / "processed"
P = pd.read_csv(D / "crop_water_params.csv")
C = pd.read_csv(D / "crops_sourced.csv")
NUM = ["root_depth_min_m", "root_depth_max_m", "root_depth_m", "p_depletion", "ky", "l_ini", "l_dev", "l_mid", "l_late"]
TOL_MM = 1.0


def _split(cell):
    return set() if pd.isna(cell) or str(cell).strip() == "" else set(str(cell).split(";"))


def _weather(rain_factor=1.0, years=(2015, 2016, 2017)):
    d = pd.date_range(f"{years[0]}-01-01", f"{years[-1]}-12-31")
    rng = np.random.default_rng(0)
    wet = (np.sin((d.dayofyear.values - 120) / 365 * 2 * np.pi) > 0.3)
    rain = np.where(rng.random(len(d)) < np.where(wet, 0.5, 0.05), rng.gamma(1.5, 12, len(d)), 0.0) * rain_factor
    return pd.DataFrame({"date": d, "rain_mm": rain, "et0_mm": 3.5 + 1.5 * np.sin((d.dayofyear.values - 80) / 365 * 2 * np.pi),
                         "tmax_c": 31 + 4 * np.sin((d.dayofyear.values - 90) / 365 * 2 * np.pi)})


SOIL = {"field_capacity": 0.35, "wilting_point": 0.18, "ec_soil_dsm": 3.0, "ec_water_dsm": 2.0}


def test_params_file_covers_every_crop_and_follows_provenance_rules():
    assert list(P.columns) == ["crop_id", "root_depth_min_m", "root_depth_max_m", "root_depth_m", "p_depletion", "ky",
                               "l_ini", "l_dev", "l_mid", "l_late", "source", "assumed_fields", "missing_fields", "notes"]
    assert set(P.crop_id) == set(C.crop_id) and P.crop_id.is_unique
    for _, r in P.iterrows():
        missing, assumed = _split(r.missing_fields), _split(r.assumed_fields)
        for col in NUM:
            if pd.isna(r[col]):
                assert col in missing, f"{r.crop_id}.{col} blank but not listed"
        for col in missing:
            assert pd.isna(r[col]), f"{r.crop_id}.{col}"
        for col in assumed:
            assert not pd.isna(r[col])
        assert "FAO-56 Table 22" in r.source


def test_ranges_and_chosen_root_depth():
    assert (P.root_depth_min_m <= P.root_depth_m).all() and (P.root_depth_m <= P.root_depth_max_m).all()
    assert P.p_depletion.between(0.1, 0.8).all()
    assert P.ky.dropna().between(0.5, 1.5).all()


def test_spot_checks_against_fao56_tables():
    t = P.set_index("crop_id")
    assert (t.loc["tomato", "root_depth_min_m"], t.loc["tomato", "root_depth_max_m"], t.loc["tomato", "p_depletion"], t.loc["tomato", "ky"]) == (0.7, 1.5, 0.40, 1.05)
    assert (t.loc["maize", "p_depletion"], t.loc["maize", "ky"]) == (0.55, 1.25)
    assert (t.loc["groundnut", "ky"], t.loc["groundnut", "p_depletion"]) == (0.70, 0.50)
    assert (t.loc["wheat", "ky"], t.loc["wheat", "root_depth_max_m"]) == (1.15, 1.5)
    assert t.loc["aman_rice", "p_depletion"] == 0.20
    assert t.loc["sunflower", "ky"] == 0.95 and t.loc["chilli", "ky"] == 1.10
    assert tuple(t.loc["tomato", ["l_ini", "l_dev", "l_mid", "l_late"]]) == (35, 45, 70, 30)   # Table 11, Oct/Nov, Arid Region


def test_engine_merges_params_for_a_rotation_and_reports_defaults():
    rot = [{"crop_id": "aman_rice", "season": "aman", "year_index": 0}, {"crop_id": "mustard", "season": "rabi", "year_index": 0}]
    out = wb.simulate_rotation(rot, _weather(), SOIL, C, year=2015)["seasons"]
    assert out[0]["default_params"] == ["ky"]                                    # rice: only Ky is missing
    assert set(out[1]["default_params"]) == {"ky", "stage_fractions"}            # mustard proxy: Ky and stage shares missing


def test_root_depth_sets_taw():
    crop = C.set_index("crop_id").loc["wheat"].copy()
    win = _weather(0.0).iloc[:110]
    crop["root_depth_m"] = 1.0
    s1 = wb.simulate_season(win, crop, 2.0, 2.0, irrigation_cap_mm=0.0)
    crop["root_depth_m"] = 0.5
    s2 = wb.simulate_season(win, crop, 2.0, 2.0, irrigation_cap_mm=0.0)
    assert s1["storage_change_mm"] < s2["storage_change_mm"] <= 0.0             # deeper roots can draw down a bigger store
    assert -1000 * 0.17 * 1.0 - 1e-9 <= s1["storage_change_mm"]
    assert s1["eta_mm"] > s2["eta_mm"]


def test_p_depletion_changes_stress_onset():
    crop = C.set_index("crop_id").loc["tomato"].copy()
    win = _weather(0.0).iloc[300:420]
    crop["root_depth_m"] = 0.7
    out = {}
    for p in (0.2, 0.7):
        crop["p_depletion"] = p
        out[p] = wb.simulate_season(win, crop, 2.0, 2.0, irrigation_cap_mm=0.0)["eta_mm"]
    assert out[0.7] > out[0.2]                                                  # higher p -> stress starts later -> more actual ET


def test_ky_follows_fao56_eq90_and_ky_one_matches_old_behaviour():
    crop = C.set_index("crop_id").loc["groundnut"].copy()
    crop["root_depth_m"], crop["p_depletion"] = 0.5, 0.5
    win = _weather(0.0).iloc[60:190]
    ys = {}
    for ky in (0.5, 1.0, 1.5):
        crop["ky"] = ky
        ys[ky] = wb.simulate_season(win, crop, 0.2, 0.2, irrigation_cap_mm=0.0)
    r = ys[1.0]["eta_mm"] / ys[1.0]["water_use_mm"]
    assert r < 0.95                                                             # the window really is water-stressed
    # salinity factor is the same for all three, so ratios of rel_yield isolate the water factor
    f = lambda ky: max(0.0, 1 - ky * (1 - r))
    assert abs(ys[0.5]["rel_yield"] / ys[1.0]["rel_yield"] - f(0.5) / f(1.0)) < 1e-9
    assert abs(ys[1.5]["rel_yield"] / ys[1.0]["rel_yield"] - f(1.5) / f(1.0)) < 1e-9
    assert ys[0.5]["rel_yield"] > ys[1.0]["rel_yield"] > ys[1.5]["rel_yield"]


def test_stage_fractions_from_table11_lengths():
    c = pd.Series(dict(kc_ini=0.4, kc_mid=1.2, kc_end=0.3, l_ini=10, l_dev=20, l_mid=40, l_late=30))
    used = []
    fr = wb._stage_fractions(c, used)
    assert used == [] and abs(sum(fr) - 1.0) < 1e-12 and fr == (0.1, 0.2, 0.4, 0.3)
    n = 100
    assert wb._kc(5, n, c, fr) == 0.4                                            # initial stage
    assert wb._kc(50, n, c, fr) == 1.2                                           # mid stage
    assert abs(wb._kc(99, n, c, fr) - 0.3) < 1e-9                                # end of late stage
    used = []
    assert wb._stage_fractions(pd.Series(dict(kc_ini=1)), used) == wb.STAGE_FRACTIONS and used == ["stage_fractions"]


def test_water_balance_closes_with_cited_parameters_for_every_crop():
    for factor in (1.0, 3.0, 0.1):
        w = _weather(factor)
        for cap in (0.0, 150.0, 400.0):
            for _, c in C.iterrows():
                rot = [{"crop_id": c.crop_id, "season": c.season, "year_index": 0}]
                s = wb.simulate_rotation(rot, w, SOIL, C, year=2015, irrigation_cap_mm=cap)["seasons"][0]
                res = s["rain_mm"] + s["irrigation_mm"] - (s["eta_mm"] + s["runoff_mm"] + s["drainage_mm"] + s["storage_change_mm"])
                assert abs(res) <= TOL_MM, f"{c.crop_id} x{factor} cap {cap}: {res:.3f}"
                assert 0.0 <= s["rel_yield"] <= 1.0 and s["eta_mm"] <= s["water_use_mm"] + 1e-9


def test_crop_table_that_already_has_params_is_not_overwritten():
    c2 = C.merge(P[["crop_id", "root_depth_m", "p_depletion"]].assign(root_depth_m=0.3, p_depletion=0.3), on="crop_id")
    rot = [{"crop_id": "wheat", "season": "rabi", "year_index": 0}]
    a = wb.simulate_rotation(rot, _weather(), SOIL, c2, year=2015, irrigation_cap_mm=0.0)["seasons"][0]
    b = wb.simulate_rotation(rot, _weather(), SOIL, C, year=2015, irrigation_cap_mm=0.0)["seasons"][0]
    assert a["storage_change_mm"] != b["storage_change_mm"]
