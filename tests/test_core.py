import sys, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
import pandas as pd, pytest
from watershift.water_balance import simulate_rotation
from watershift.rotations import generate_rotations
from watershift.scoring import score_rotation
from watershift.scenarios import run_scenarios
D = pathlib.Path(__file__).resolve().parents[1] / "data" / "processed"
W, C, S = pd.read_csv(D / "weather_daily.csv"), pd.read_csv(D / "crops.csv"), json.load(open(D / "soil.json"))
def rot(*ids): return [{"crop_id": c, "season": s, "year_index": y} for c, s, y in zip(ids, ["rabi", "kharif1", "aman"], [0, 1, 1])]
EQ = {"soil": .25, "water": .25, "resilience": .25, "feasibility": .25}

def test_contract_fields():
    s = simulate_rotation(rot("sunflower", "mungbean", "aman_rice"), W, S, C)["seasons"][0]
    for k in "rel_yield water_use_mm irrigation_mm salinity_end_dsm soc_change_pct n_credit_kg_ha cover_days waterlogging_days".split():
        assert k in s

def test_dry_year_lowers_yield():
    dry = W.copy(); dry["rain_mm"] *= 0.2
    r = rot("sunflower", "mungbean", "aman_rice")
    assert simulate_rotation(r, dry, S, C)["seasons"][2]["rel_yield"] < simulate_rotation(r, W, S, C)["seasons"][2]["rel_yield"]

def test_salinity_hurts_sensitive_more():
    hi = dict(S, ec_soil_dsm=8.0)
    a = simulate_rotation(rot("sunflower", "mungbean", "aman_rice"), W, hi, C)["seasons"][2]["rel_yield"]
    b = simulate_rotation(rot("sunflower", "mungbean", "aman_rice_salttol"), W, hi, C)["seasons"][2]["rel_yield"]
    assert b > a

def test_legume_n_credit():
    s = simulate_rotation(rot("sunflower", "mungbean", "aman_rice"), W, S, C)["seasons"]
    assert s[1]["n_credit_kg_ha"] > 0 and s[0]["n_credit_kg_ha"] == 0

def test_generator_rules():
    for r in generate_rotations(C):
        fam = [C.set_index("crop_id").loc[x["crop_id"], "family"] for x in r]
        assert all(a != b for a, b in zip(fam, fam[1:]))

def test_weights_and_determinism():
    sim = simulate_rotation(rot("sunflower", "mungbean", "aman_rice"), W, S, C)
    assert score_rotation(sim, EQ, 0.7) == score_rotation(sim, EQ, 0.7)
    with pytest.raises(ValueError): score_rotation(sim, {"soil": 1, "water": 1, "resilience": 0, "feasibility": 0}, 0.7)

def test_water_weight_favours_low_irrigation():
    lo = simulate_rotation(rot("sunflower", "mungbean", "aman_rice"), W, S, C, irrigation_cap_mm=0)
    hi = simulate_rotation(rot("sunflower", "mungbean", "aman_rice"), W, S, C, irrigation_cap_mm=400)
    ww = {"soil": 0, "water": 1, "resilience": 0, "feasibility": 0}
    assert score_rotation(lo, ww, .7)["total"] >= score_rotation(hi, ww, .7)["total"]

def test_scenarios_ordered():
    r = run_scenarios(rot("sunflower", "mungbean", "aman_rice"), W, None, S, C)
    assert r["bad_year"]["p50"] <= r["baseline"]["p90"] and r["baseline"]["p10"] <= r["baseline"]["p90"]
