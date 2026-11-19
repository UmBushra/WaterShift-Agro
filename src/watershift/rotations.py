"""Rotation generator: calendar fit, no same family back to back, >=1 legume or salt-tolerant crop."""
import itertools

SALT_TOLERANT_DSM = 4.0  # assumption: threshold at/above this counts as salt tolerant
YEAR_INDEX = {"rabi": 0, "kharif1": 1, "aman": 1}  # rabi starts the cycle; the rest fall in the next calendar year


def generate_rotations(crops, season_slots=("rabi", "kharif1", "aman"), max_n=12):
    """Return up to max_n rotations as lists of {crop_id, season, year_index}."""
    pools = [crops[crops.season == s].to_dict("records") for s in season_slots]
    result = []
    for combo in itertools.product(*pools):
        if any(a["family"] == b["family"] for a, b in zip(combo, combo[1:])):
            continue
        if not any(c["is_legume"] or c["salinity_threshold_dsm"] >= SALT_TOLERANT_DSM for c in combo):
            continue
        result.append([{"crop_id": c["crop_id"], "season": s, "year_index": YEAR_INDEX[s]}
                       for c, s in zip(combo, season_slots)])
        if len(result) >= max_n:
            break
    return result
