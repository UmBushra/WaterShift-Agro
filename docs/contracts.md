# WaterShift Agro data contracts
Package name: `watershift` (src/watershift). If something must change, agree on it, edit this file, tell the other person.

```text
FILES (data/processed/)
weather_daily.csv   date, rain_mm, tmax_c, tmin_c, solar_mj_m2, rh_pct, wind_ms, et0_mm
future_climate.csv  date, model, scenario, rain_mm, tmax_c, tmin_c
soil.json           field_capacity, wilting_point, soc_pct, ph, clay_pct, sand_pct, silt_pct,
                    nitrogen, ec_soil_dsm, ec_water_dsm, source
crops.csv           crop_id, name, family, is_legume, season, sow_month, harvest_month,
                    duration_days, kc_ini, kc_mid, kc_end, tmax_stress_c, rain_need_mm,
                    salinity_threshold_dsm, salinity_slope_pct_per_dsm, residue_t_ha,
                    n_credit_kg_ha, cost_bdt_ha, yield_t_ha, price_bdt_t, source
predictions_log.csv prediction_id, farm_id, season, area, crop, predicted_rel_yield,
                    p_success, uncertainty, model_version, created_at
outcomes.csv        farm_id, season, crop, observed_rel_yield, success, water_ec_dsm,
                    observation_quality, notes, is_simulated

FUNCTIONS
simulate_rotation(rotation, weather, soil, crops) -> dict
   rotation = list of {crop_id, season, year_index}
   returns per season: rel_yield, water_use_mm, irrigation_mm, salinity_end_dsm,
   soc_change_pct, n_credit_kg_ha, cover_days, waterlogging_days
score_rotation(sim, weights, feasibility) -> dict
   weights = {soil, water, resilience, feasibility}, sum to 1
   returns sub_scores, total, top_reasons (list of plain-language strings)
run_scenarios(rotation, weather, future_climate, soil, crops) -> dict
   returns baseline, bad_year, future (per scenario) each with p10, p50, p90
```
## Clarifications added (compatible extensions, not breaking changes)
- simulate_rotation accepts optional `year=` (first weather year) and `irrigation_cap_mm=`.
- It returns `{"seasons": [ {crop_id, season, year_index, <fields above>, salinity_start_dsm} ]}`.
- Fixture files carry a SIMULATED/DEMO notice in data/processed/FIXTURE_NOTICE.txt.
- (Step 2) soil.json gains an optional `assumed_fields` list; `source` now says which fields are fetched vs assumed. Existing keys unchanged.
- (Step 2) Sidecar `weather_daily.meta.json` records source, coordinates, period, access date. Not read by any code.
- (Step 2) `soil.json.nitrogen` unit is % N (was unspecified). `weather_daily.et0_mm` is FAO-56 Penman-Monteith computed from POWER variables.
- (Step 2) future_climate.csv has no solar/humidity/wind, so ET0 for future scenarios is open (Step 7).
- (Step 3) crops_sourced.csv has the contract columns plus three optional trailing columns: `assumed_fields` (value present, unsourced), `missing_fields` (left blank), `notes`. Blank numeric cells are allowed only for fields named in `missing_fields`. Code reading it must handle NaN. The fixture crops.csv is unchanged.
- (Step 4) Each per-season dict in simulate_rotation also has `missing_inputs` (list of blank crop fields that were skipped). soc_change_pct and n_credit_kg_ha are NaN when their crop inputs are blank. generate_rotations default slots are now (aman, rabi, kharif1); year_index follows sow-month order.
- (Step 4b) Each per-season dict also has water-balance terms in mm: `eta_mm` (actual ET), `rain_mm`, `runoff_mm`, `drainage_mm`, `storage_change_mm` (<= 0, season starts at field capacity). Closure: rain_mm + irrigation_mm = eta_mm + runoff_mm + drainage_mm + storage_change_mm (tested to 1 mm). `water_use_mm` is unchanged and still means POTENTIAL crop ET (ETc); `eta_mm` is the actual ET.
- (Step 4b-constants) New optional file data/processed/crop_water_params.csv (crop_id, root_depth_min_m, root_depth_max_m, root_depth_m, p_depletion, ky, l_ini, l_dev, l_mid, l_late, source, assumed_fields, missing_fields, notes). simulate_rotation merges it into the crop table on crop_id when the crop table has no `root_depth_m` column. simulate_season reads optional crop fields root_depth_m, p_depletion, ky, l_ini..l_late and falls back to the module defaults when blank.
- (Step 4b-constants) Each per-season dict also has `default_params` (list of names that fell back to defaults: root_depth_m, p_depletion, ky, stage_fractions). rel_yield water factor is now 1 - Ky(1 - ETa/ETc) (FAO-56 Eq. 90).
