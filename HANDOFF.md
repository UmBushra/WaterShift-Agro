# HANDOFF (update at the end of every Claude session)

## Done (session 1, Claude A)
Step 0 skeleton, CLAUDE.md, docs/contracts.md, fixtures (SIMULATED weather, placeholder crops/soil),
src/watershift: water_balance (SEASONAL placeholder), rotations, scoring, scenarios (baseline + bad_year),
app/adapters.py + app/streamlit_app.py (DEMO DATA banner), 8 passing tests.

## Done (session 2, Claude B, chat)
Step 2 code: src/watershift/data_fetch.py (NASA POWER + FAO-56 ET0, SoilGrids, NEX-GDDP-CMIP6 via Earth Engine), tests/test_data_fetch.py (12 offline tests), docs/data_sources.md, assumptions/contracts addenda, requirements.txt. 20 tests passed with a stand-in runner (pytest not installable in the sandbox). Live downloads never run (no network).

## Done (session 3, Claude C, chat) - Step 3 first pass
- data/processed/crops_sourced.csv: 11 crops (boro, aus, aman rice, wheat, maize, mustard, sunflower, mungbean, groundnut, tomato, chilli).
  Kc (ini/mid/end) VERIFIED against FAO-56 Table 12; salinity threshold/slope VERIFIED against FAO-29 Rev.1 Annex 1 Table A1.1. Both pages were fetched this session; URLs are in the `source` column.
- Calendar fields (season, sow/harvest month, duration) are ASSUMPTIONS (flagged). Seven fields are BLANK on purpose (flagged in `missing_fields`).
- docs/crop_sources.md (sources, proxies, table-range choices, caveats), tests/test_crops_sourced.py (8 offline tests, all pass with a stand-in runner), assumptions.md and contracts.md addenda.
- NOT renamed to crops.csv: the fixture still drives the engine. src/, data/ and CLAUDE.md were not shared with this session, so nothing was run against the real code.

## Done (session 4, Claude D, chat) - Step 4 first pass
- Merged sessions 1+3 files; ran REAL pytest: 16 passed, then 19 passed after the changes below. data_fetch.py (session 2) was NOT in this session's repo, so it was not merged or run; re-add it from session 2's files.
- src/watershift/water_balance.py: now a DAILY FAO-56 single-Kc bucket (stage-wise Kc, depletion, irrigation up to a seasonal cap, daily salt build-up/leaching, heat/waterlogging penalties, rel_yield = ETa/ETc x salinity x heat x waterlog). NaN crop fields are skipped and listed in `missing_inputs` per season (soc/N become NaN).
- scoring.py is NaN-safe and adds a reason line when crop data are missing. rotations.py: default slots now (aman, rabi, kharif1); year_index follows the calendar (increments when the sow month wraps). adapters.py prefers crops_sourced.csv. New tests/test_engine_daily.py (3 tests).
- Contract clarification (docs/contracts.md): per-season dict also has `missing_inputs` (list).

## Done (session 5, Claude B again, chat) - Step 4b first part
- Merged sessions 1-4 + my Step 2 files (data_fetch.py, test_data_fetch.py, data_sources.md): 31 tests pass.
- water_balance.py: daily bucket now tracks rain, runoff (non-effective rain), drainage (above field capacity), actual ET `eta_mm` and `storage_change_mm` per season; ETa is capped at what the root zone holds. New tests/test_water_closure.py (7 tests): balance closes within 1 mm for every generated rotation under normal / 3x wet / 0.1x dry rain and irrigation caps 0/150/400; mutation-checked (breaking drainage or the cap makes tests fail).
- Total 38 tests pass using a stand-in runner (pytest not installable in the chat sandbox); RUN REAL pytest locally. Ranking and scores are unchanged by this step (bookkeeping only).
- Contract/assumption addenda for the new keys in docs/contracts.md and docs/assumptions.md.

## Done (session 6, Claude, chat) - Step 4b cited constants
- NEW data/processed/crop_water_params.csv: root depth (Zr), depletion fraction p (FAO-56 Table 22), Ky (Table 24), stage lengths (Table 11) per crop, with source/assumed/missing columns. All values were fetched and checked this session; URLs in `source`.
- water_balance.py reads it (merged in simulate_rotation; defaults kept as fallback, reported in `default_params`). rel_yield water factor now uses FAO-56 Eq. 90 (same as before at Ky = 1). New tests/test_water_params.py: 10 tests, mutation-checked (ignoring root depth, or the wrong Ky form, makes them fail). Closure holds for every crop x rain x irrigation cap in these tests, and the old forced-cap edge case still closes.
- Only this session's files plus the engine/tests were uploaded: rotations.py, scoring.py, adapters, fixtures and the older tests were NOT available, so the full suite (38 tests) was NOT re-run. RUN REAL pytest locally; tests/test_water_closure.py must still pass, but RANKINGS WILL CHANGE (rice irrigation and root zones changed). Diff rankings before/after.
- Not applied: ETc adjustment of p, soil-texture adjustment of p, growing root depth.

## Done (session 7, Claude E, chat) - merge + real pytest
- Merged session 5-6 files (water_balance.py with closure terms, crop_water_params.csv, test_water_params.py, docs) into the session 1-4 repo. REAL pytest: 29 passed (8 core + 8 crops + 3 daily + 10 water params).
- Still NOT in this repo: data_fetch.py, tests/test_data_fetch.py, docs/data_sources.md (session 2) and tests/test_water_closure.py (session 5). Re-add them, then run pytest again.
- Ranking diff on SIMULATED fixture weather, equal weights: top 2 unchanged (aman_rice>mustard>aus_rice, >groundnut); the mungbean rotation fell from 3rd to 4th; all scores dropped about 0.04; aman rice irrigation went 0 -> 108 mm (rice p=0.20 mismatch, see Known problems).

## NOT done / next, in this order
1a. HUMAN: run `python -m watershift.data_fetch weather` and `soil` (no login), then `future` after Earth Engine setup; check outputs per docs/data_sources.md; run real pytest; commit. Set real field lat/lon.
1b. HUMAN: replace field_capacity, wilting_point, ec_soil_dsm, ec_water_dsm in soil.json (SRDI / farmer readings / cited pedotransfer).
1c. HUMAN: review crops_sourced.csv. Check the rice Kc end choice and the calendar fields; supply BRRI/BARI sources for duration and calendar, and for yield, cost, price.
2. Step 3b: fill the blank fields from cited sources (tmax_stress_c, residue_t_ha, n_credit_kg_ha, cost, yield, price). Do not invent. rain_need_mm to be computed from Kc x ET0 in Step 4. Then check whether watermelon, chickpea, sesame, lentil can be added with a salinity source.
3. Step 4b (rest): (DONE s5: closure test; DONE s6: cited Zr, p, Ky, stage lengths). Still to do: decide Kc-mid climate adjustment (FAO-56 Eq. 62); handle paddy rice ponding properly (bunds, standing water, percolation; rice p=0.20 is 'of saturation'); link salt leaching to drainage instead of total rain; decide whether to apply the ETc adjustment of p; confirm root-depth choice (min vs max) with a local source.
4. Step 7: future scenarios (NEX-GDDP-CMIP6) in run_scenarios; currently returns future=None; decide future-ET0 rule.
5. Steps 8-9: feedback.py, scripts/make_simulated_outcomes.py, app/pages/researcher.py (is_simulated=True, SIMULATED banner).
6. Step 10 validation (MODIS NDVI, published local yields); Step 11 end-to-end test; Step 13 README/summary/AI-use note.

## Known problems
- (s6) Rice p = 0.20 (of saturation) is applied to a field-capacity bucket: rice irrigation demand jumps (aman rice 44 -> 150 mm on synthetic weather). Rice results are provisional until ponding is built.
- (s6) Root depth used = Table 22 minimum, for an assumed reason (shallow water table). Stage-length rows are from other regions. Ky is blank (default 1) for rice, mustard, mungbean.
- (s5) `water_use_mm` is still POTENTIAL ETc (kept for contract compatibility); use `eta_mm` for actual ET. Runoff uses the unsourced EFF_RAIN, so runoff and drainage totals are not real estimates yet. Paddy rice has no ponding: its runoff and drainage are not meaningful.
- (s5) Closure holds by construction of the accounting; the tests guard against clamp/ordering bugs but do not validate the physics.
- (s4) Engine constants ROOT_DEPTH_M=0.5, P_DEPLETION=0.5, STAGE_FRACTIONS=(0.2,0.3,0.3,0.2), KY=1 are unsourced assumptions. Paddy rice is treated like an upland crop in the bucket. Only 10 rotations pass the rules on the 11-crop library.
- (s4) With tmax_stress_c, residue and N credit blank, heat stress is off and soil/N effects are ignored, so soil scores are not meaningful. Rankings still run on SIMULATED weather and placeholder soil.
- data_fetch.py live calls (POWER, SoilGrids, Earth Engine) untested; API field names written from documentation memory.
- Future climate has no solar/RH/wind: Step 7 must decide the future-ET0 rule.
- app banner: FIXTURE_NOTICE.txt is rewritten by data_fetch; check app/streamlit_app.py still shows DEMO/SIMULATED correctly.
- Fixtures are not real data; rankings are not meaningful yet. Bad-year result is close to baseline because fixture weather is synthetic.
- crops_sourced.csv: mustard and chilli use proxy rows; rice varieties are lumped and saline-tolerant varieties are not modelled; paddy-rice salinity is defined for submerged soil water, check the engine's salinity_end_dsm definition.
- Salt-sensitive crops (mungbean 1.8 dS/m, groundnut 3.2 with slope 29, maize 1.7) will rank low at the placeholder EC values; do not read this as a result until ec_soil_dsm is real.
- Streamlit app was not launched in any sandbox, only adapters were tested.

## PROMPT TO PASTE INTO THE NEXT CLAUDE (Claude Code or chat)
Read CLAUDE.md, docs/contracts.md, docs/crop_sources.md, docs/water_params_sources.md and HANDOFF.md, then make a short plan before changing any file. Project: WaterShift Agro, a NASA Space Apps tool ranking multi-season crop rotations for a smallholder field in Shyamnagar, Satkhira, Bangladesh, plus a blind-spot loop comparing predictions with farmer outcomes. Continue with the first item under "NOT done / next" that does not need the human (session 5 finished the closure test, session 6 the cited constants; next is paddy ponding + salt leaching linked to drainage in Step 4b, or Step 3b): if 1a-1c are not confirmed done, do Step 3b (fill blank fields in data/processed/crops_sourced.csv only from sources you actually retrieve; cite the URL per value; otherwise leave blank) or Step 4 (daily FAO-56 water balance) if the human has supplied the repo. Never invent data or citations; mark unknowns as assumption; label simulated data SIMULATED; run real pytest before each commit. Work as far as your usage limit allows, finishing and testing each file. RELAY RULE: before your limit runs out, stop starting new work, save all files, update HANDOFF.md (done / not done / next / known problems), and write a ready-to-paste prompt like this one for the next Claude, so the chain continues. Give the human every finished file.
