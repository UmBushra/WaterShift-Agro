# WaterShift Agro (formerly "Field Shift"): project rules for Claude Code

Goal: a NASA Space Apps decision-support tool that ranks multi-season crop rotations for a smallholder field in Shyamnagar, Satkhira, Bangladesh on soil health, water use, climate resilience and feasibility. A second module compares predictions with farmer outcomes to flag possible local model blind spots.

## Rules
1. Read docs/contracts.md and HANDOFF.md before touching any shared file or function. Never change a contract silently; update the doc and tell the human.
2. Never invent data, parameters or citations. If a value is unknown, mark it as assumption in the data and in docs/assumptions.md.
3. Anything simulated carries is_simulated=True and is labelled SIMULATED in the UI and docs.
4. Every parameter has a source (URL or paper) in its sources file.
5. Python 3.11+ with pandas, numpy, streamlit, folium. Add other dependencies only when needed and list them in requirements.txt.
6. Small functions, docstrings, one pytest test each. Run pytest before every commit.
7. Work directly on main. Run pytest, then commit after each working step. Push at the end of each session.
8. If a download needs a login or the network is blocked, write the script, say exactly what the human must do, and use a fixture meanwhile.
9. At the end of every task report: what changed, what is assumed, what a human must check.
10. RELAY RULE: when your usage limit is close, stop starting new work. Finish and test what is in progress, save every file, update HANDOFF.md (done / not done / next step / known problems), and give the human a ready-to-paste prompt for the next Claude. Every Claude does this, so the chain never loses context.
