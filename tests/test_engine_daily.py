import sys, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
import numpy as np, pandas as pd
from watershift.water_balance import simulate_rotation
from watershift.rotations import generate_rotations
from watershift.scoring import score_rotation
D = pathlib.Path(__file__).resolve().parents[1] / "data" / "processed"
W, S, C = pd.read_csv(D / "weather_daily.csv"), json.load(open(D / "soil.json")), pd.read_csv(D / "crops_sourced.csv")
EQ = {"soil": .25, "water": .25, "resilience": .25, "feasibility": .25}

def test_sourced_crops_run_with_nan_and_report_missing():
    for r in generate_rotations(C):
        sim = simulate_rotation(r, W, S, C)
        assert all("tmax_stress_c" in x["missing_inputs"] for x in sim["seasons"])
        out = score_rotation(sim, EQ, 0.7)
        assert 0 <= out["total"] <= 1 and np.isfinite(out["total"])

def test_year_index_never_goes_backwards_and_generator_nonempty():
    rots = generate_rotations(C)
    assert len(rots) > 0
    for r in rots:
        yi = [x["year_index"] for x in r]
        assert yi == sorted(yi)

def test_irrigation_never_exceeds_cap_and_dry_year_hurts():
    r = generate_rotations(C)[0]
    a = simulate_rotation(r, W, S, C, irrigation_cap_mm=100)["seasons"]
    assert all(x["irrigation_mm"] <= 100 + 1e-9 for x in a)
    dry = W.copy(); dry["rain_mm"] *= 0.1
    b = simulate_rotation(r, dry, S, C, irrigation_cap_mm=100)["seasons"]
    assert np.mean([x["rel_yield"] for x in b]) <= np.mean([x["rel_yield"] for x in a])
