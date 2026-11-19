# Crop parameter sources (Step 3)
File: `data/processed/crops_sourced.csv` (11 crops). Provenance per cell is in the `source`, `assumed_fields`, `missing_fields` and `notes` columns.
It is deliberately NOT named `crops.csv`: the current fixture crops.csv keeps the engine and the 20 old tests working. Rename it only after Step 4 (daily engine) can handle the blank fields below.

## Verified against the published tables (fetched 2026-11-19)
| Field | Source |
|---|---|
| kc_ini, kc_mid, kc_end | FAO Irrigation and Drainage Paper 56 (Allen et al. 1998), Table 12, https://www.fao.org/4/x0490e/x0490e0b.htm. Kc ini is the group value shown in the table header row (cereals 0.3, legumes 0.4, oil crops 0.35, Solanaceae 0.6, rice 1.05). |
| salinity_threshold_dsm, salinity_slope_pct_per_dsm | FAO Irrigation and Drainage Paper 29 Rev.1 (Ayers and Westcot 1985), Annex 1 Table A1.1 (Maas and Grattan 1999 update), https://www.fao.org/3/Y4263E/y4263e0e.htm. ECe in dS/m, slope in % per dS/m. Relative yield = 100 - slope x (ECe - threshold). |

Choices made inside a table range (all written in each row's `notes`): rice Kc end = 0.60 (range 0.90-0.60); wheat Kc end = 0.40 (hand-harvested); maize Kc end = 0.35 (dry harvest); mustard and sunflower Kc mid = 1.075 (midpoint of 1.0-1.15); tomato Kc end = 0.80 (midpoint of 0.70-0.90); mungbean Kc end = 0.35 (dry harvest).

## Proxies (not the exact local crop)
- Mustard uses the Rapeseed/Canola row (Kc) and canola *B. campestris* (salinity). Local mustard species and variety not confirmed.
- Chilli uses Sweet Peppers (bell) for Kc; salinity row is *Capsicum annuum* "Pepper".
- Mungbean uses the "Green gram and cowpeas" Kc row.
- Aus, aman and boro rice share one Kc and salinity row (O. sativa). Saline-tolerant BRRI/BINA varieties are not represented, so rice salinity loss is probably overstated for those.

## ASSUMPTIONS (values present, no source)
`season`, `sow_month`, `harvest_month`, `duration_days` for every crop: typical Bangladesh calendar, written from general knowledge, NOT checked against BRRI/BARI/DAE. They are needed for the engine to place crops in seasons. Human to replace with a cited local source. FAO-56 Table 11 durations are for other regions and were not used.

## MISSING (left blank on purpose, not invented)
`tmax_stress_c`, `rain_need_mm`, `residue_t_ha`, `n_credit_kg_ha`, `cost_bdt_ha`, `yield_t_ha`, `price_bdt_t`.
Suggested sources: BRRI/BARI crop production guides and BBS yearbook for yield, cost, price; published heat-stress thresholds per crop; legume N-credit and residue figures from cited agronomy papers. `rain_need_mm` should probably be computed in Step 4 from Kc x ET0 instead of being a table value.

## Crops considered but not included (no numeric salinity data in FAO-29 Table A1.1)
Watermelon (MS*, estimate only), chickpea (MS, no numbers), sesame (S, no numbers), lentil and khesari (not listed). Add them once a cited salinity source is found.

## Caveats to state in the write-up
- FAO tables are for non-stressed, well-managed crops in sub-humid conditions (RHmin about 45%, wind 2 m/s). Coastal Bangladesh is more humid, so Kc mid is probably a little lower than the table (FAO-56 Eq. 62 adjusts this; not applied yet).
- Kc ini is an approximation. With frequent monsoon rain it can be much higher (FAO-56 Fig. 29/30).
- FAO-29 thresholds assume chloride-dominated soils and a uniform ECe from late seedling to maturity. Germination and seedling stages are more sensitive (wheat, rice, mungbean).
- Paddy rice ECe values refer to the soil water while submerged, not saturated paste. Check how `salinity_end_dsm` is defined in the engine before comparing.
