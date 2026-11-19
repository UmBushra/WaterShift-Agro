# Cited water-balance parameters (Step 4b, constants part)
File: `data/processed/crop_water_params.csv`, read by `water_balance.simulate_rotation` (merged on crop_id when the crop table has no `root_depth_m` column). Blank cells fall back to the old defaults and are reported per season in `default_params`.

## Verified against the published tables (fetched 2026-11-19)
| Field | Source |
|---|---|
| root_depth_min_m / max_m, p_depletion | FAO-56 (Allen et al. 1998) Table 22, https://www.fao.org/4/X0490e/x0490e0e.htm |
| ky | FAO-56 Table 24 (seasonal Ky from FAO-33), same page. Tabulated only for: wheat 1.15 (spring), maize 1.25, groundnut 0.70, sunflower 0.95, tomato 1.05, pepper 1.10. Left blank for rice, mustard, mungbean (FAO-56: use Ky = 1 where unknown, which is the engine default). |
| l_ini, l_dev, l_mid, l_late | FAO-56 Table 11, https://www.fao.org/4/x0490e/x0490e0b.htm. Row chosen per crop (named in `source`); rows are from OTHER regions. Only the shares of the season are used, not the day counts. Blank for mustard (no rapeseed row). |

## Choices and assumptions
- `root_depth_m` (value actually used) = the Table 22 MINIMUM. Reason: Table 22 footnote 1 says the smaller value suits irrigation scheduling and the larger rainfed stress modelling; the minimum was picked as a conservative guess for a shallow water table and saline subsoil in the delta. That reason is an ASSUMPTION. Switch to max or midpoint by editing the column.
- Ky enters as FAO-56 Eq. 90: rel_yield water factor = 1 - Ky x (1 - ETa/ETc). The old placeholder was (ETa/ETc)^KY; identical at Ky = 1.
- Rice p = 0.20 is "of saturation" (Table 22 footnote 4). The bucket is relative to field capacity, so the rice p is a MISMATCH until paddy ponding exists. It makes rice trigger irrigation much earlier. Treat rice results as provisional.
- Not applied: p adjustment for ETc (p = p_table + 0.04 (5 - ETc), limited to 0.1-0.8); 5-10% p adjustment for soil texture; root depth growing through the season; Table 23 (salinity) is the same data as the crops_sourced.csv salinity columns, not re-used.
- Proxies carried over: mustard = rapeseed row, chilli = sweet pepper row.

## Effect (synthetic weather only, NOT your fixture)
On a synthetic 3-year weather series the new constants changed rel_yield by up to about 0.06 and irrigation by up to 106 mm per season (aman rice 44 -> 150 mm, mustard 87 -> 0 mm). Rankings WILL change; diff them against the previous run before trusting or presenting any ranking.
