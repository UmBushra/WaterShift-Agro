"""Rotation generator: calendar fit, no same family back to back, >=1 legume or salt-tolerant crop."""
import itertools

SALT_TOLERANT_DSM = 4.0  # assumption: threshold at/above this counts as salt tolerant


def generate_rotations(crops, season_slots=("aman", "rabi", "kharif1"), max_n=40):
    """Return up to max_n rotations as lists of {crop_id, season, year_index}."""
    pools = [crops[crops.season == s].to_dict("records") for s in season_slots]
    result = []
    for combo in itertools.product(*pools):
        if any(a["family"] == b["family"] for a, b in zip(combo, combo[1:])):
            continue
        if not any(c["is_legume"] or c["salinity_threshold_dsm"] >= SALT_TOLERANT_DSM for c in combo):
            continue
        yi, prev, rot = 0, None, []
        for c, s in zip(combo, season_slots):  # next calendar year when the sow month wraps around
            if prev is not None and c["sow_month"] < prev:
                yi += 1
            rot.append({"crop_id": c["crop_id"], "season": s, "year_index": yi})
            prev = c["sow_month"]
        result.append(rot)
        if len(result) >= max_n:
            break
    return result
