# HANDOFF (update at the end of every Claude session)

## Done (session 1, Claude A)
Step 0 skeleton, CLAUDE.md, docs/contracts.md, fixtures (SIMULATED weather, placeholder crops/soil),
src/watershift: water_balance (SEASONAL placeholder), rotations, scoring, scenarios (baseline + bad_year),
app/adapters.py + app/streamlit_app.py (DEMO DATA banner), 8 passing tests.

## NOT done / next, in this order
1. Step 2: src/watershift/data_fetch.py (NASA POWER, SoilGrids, NEX-GDDP-CMIP6) -> real data/processed files + docs/data_sources.md. Human must create NASA Earthdata and Google Earth Engine accounts.
2. Step 3: real crops.csv with a source per row (FAO-56, FAO-29/ECOCROP, BRRI/BARI). Human checks every ranking-driving value.
3. Step 4: replace the seasonal engine with a daily FAO-56 water balance; keep simulate_rotation output keys.
4. Step 7: future scenarios (NEX-GDDP-CMIP6) in run_scenarios; currently returns future=None.
5. Steps 8-9: feedback.py, scripts/make_simulated_outcomes.py, app/pages/researcher.py (is_simulated=True, SIMULATED banner).
6. Step 10 validation (MODIS NDVI, published local yields); Step 11 end-to-end test; Step 13 README/summary/AI-use note.

## Known problems
- Fixtures are not real data; rankings are not meaningful yet.
- Bad-year result is close to baseline because the fixture weather is synthetic.
- Streamlit app was not launched in the build sandbox, only adapters were tested.

## PROMPT TO PASTE INTO THE NEXT CLAUDE (Claude Code or chat)
Read CLAUDE.md, docs/contracts.md and HANDOFF.md, then make a short plan before changing any file. Project: WaterShift Agro, a NASA Space Apps tool ranking multi-season crop rotations for a smallholder field in Shyamnagar, Satkhira, Bangladesh, plus a blind-spot loop comparing predictions with farmer outcomes. Continue with the first item under "NOT done / next". Never invent data or citations; mark unknowns as assumption; label simulated data SIMULATED; run pytest before each commit. Work as far as your usage limit allows, finishing and testing each file. RELAY RULE: before your limit runs out, stop starting new work, save all files, update HANDOFF.md (done / not done / next / known problems), and write a ready-to-paste prompt like this one for the next Claude, so the chain continues. Give the human every finished file.
