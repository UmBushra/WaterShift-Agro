"""Four sub-scores (0-1), weighted total, plain-language reasons. All weights/constants are assumptions."""
import numpy as np

SALT_PENALTY = 0.15      # soil score lost per dS/m of salinity rise
SOC_BONUS = 20.0         # soil score gained per % SOC gained
N_BONUS_PER_KG = 1 / 200  # soil score gained per kg/ha N credit
WATER_REF_MM = 300.0     # irrigation per season that scores 0 on water
DEFAULT_WEIGHTS = {"soil": 0.25, "water": 0.25, "resilience": 0.25, "feasibility": 0.25}


def _clip(x):
    return float(np.clip(x, 0.0, 1.0))


def score_rotation(sim, weights, feasibility):
    """sim from simulate_rotation; weights sum to 1; feasibility = value 0-1. See docs/contracts.md."""
    s = sim["seasons"]
    if abs(sum(weights.values()) - 1) > 1e-6:
        raise ValueError("weights must sum to 1")
    d_ec = s[-1]["salinity_end_dsm"] - s[0]["salinity_start_dsm"]
    soc = float(np.nansum([x["soc_change_pct"] for x in s]))
    n = float(np.nansum([x["n_credit_kg_ha"] for x in s]))
    missing = sorted({m for x in s for m in x.get("missing_inputs", [])})
    subs = {"soil": _clip(0.5 - SALT_PENALTY * d_ec + SOC_BONUS * soc + N_BONUS_PER_KG * n),
            "water": _clip(1 - np.mean([x["irrigation_mm"] for x in s]) / WATER_REF_MM),
            "resilience": _clip(min(x["rel_yield"] for x in s)),
            "feasibility": _clip(feasibility)}
    total = sum(weights[k] * subs[k] for k in subs)
    reasons = []
    reasons.append("Salinity rises %.1f dS/m over the rotation" % d_ec if d_ec > 0.2 else "Salinity stays stable or falls")
    if n > 0:
        reasons.append("Legumes add about %d kg/ha nitrogen" % n)
    worst = min(s, key=lambda x: x["rel_yield"])
    reasons.append("Weakest season: %s (relative yield %.2f)" % (worst["crop_id"], worst["rel_yield"]))
    reasons.append("Average irrigation %.0f mm per season" % np.mean([x["irrigation_mm"] for x in s]))
    if missing:
        reasons.append("Missing crop data (treated as no effect): " + ", ".join(missing))
    return {"sub_scores": subs, "total": float(total), "top_reasons": reasons}
