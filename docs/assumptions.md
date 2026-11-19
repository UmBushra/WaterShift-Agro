# Assumptions log (every value below is an UNVERIFIED placeholder until a source is added)
- water_balance.py: EFF_RAIN, IRRIGATION_CAP_MM, SALT_BUILD_PER_100MM_IRR, SALT_BUILD_PER_100MM_DEFICIT, LEACH_PER_100MM_RAIN, HEAT_LOSS_PER_DAY, WATERLOG_RAIN_MM, WATERLOG_LOSS_PER_DAY, SOC_GAIN_PER_T_RESIDUE, SOC_LOSS_PER_SEASON, MIN_EC
- Engine is SEASONAL and uses a mean Kc, not the daily FAO-56 bucket. Placeholder.
- rotations.py: SALT_TOLERANT_DSM = 4.0; season order rabi -> kharif1 -> aman.
- scoring.py: SALT_PENALTY, SOC_BONUS, N_BONUS_PER_KG, WATER_REF_MM, default equal weights.
- scenarios.py: BAD_YEAR_QUANTILE = 0.10 (worst 10% by annual rain). Future climate not built.
- data/processed/weather_daily.csv is SIMULATED synthetic data. crops.csv and soil.json values are placeholders (source = assumption).
- NEX-GDDP-CMIP6 cannot represent sea-level rise or salinity intrusion (to state when future runs are added).
