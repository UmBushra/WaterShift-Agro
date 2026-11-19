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
