"""All logic for the UI lives here so the real engine can replace fixtures later."""
import json, sys, pathlib
import pandas as pd
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from watershift.rotations import generate_rotations
from watershift.water_balance import simulate_rotation
from watershift.scoring import score_rotation
from watershift.scenarios import run_scenarios

D = ROOT / "data" / "processed"


def load():
    return (pd.read_csv(D / "weather_daily.csv"), json.load(open(D / "soil.json")), pd.read_csv(D / "crops.csv"))


def rank(weights, feasibility=0.7, irrigation_cap_mm=150.0):
    """Return ranked list of dicts: rotation, sim, score, scenarios."""
    w, soil, crops = load()
    rows = []
    for rot in generate_rotations(crops):
        sim = simulate_rotation(rot, w, soil, crops, irrigation_cap_mm=irrigation_cap_mm)
        rows.append({"rotation": rot, "sim": sim, "score": score_rotation(sim, weights, feasibility),
                     "scenarios": run_scenarios(rot, w, None, soil, crops)})
    return sorted(rows, key=lambda r: -r["score"]["total"])
