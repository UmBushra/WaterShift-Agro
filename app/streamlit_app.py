import streamlit as st
import adapters

st.set_page_config(page_title="WaterShift Agro", layout="centered")
st.title("WaterShift Agro")
st.warning("DEMO DATA: weather is SIMULATED and crop/soil values are unverified placeholders.")
st.sidebar.header("Priorities")
raw = {"soil": st.sidebar.slider("Soil recovery", 0, 10, 5), "water": st.sidebar.slider("Water saving", 0, 10, 5),
       "resilience": st.sidebar.slider("Low risk", 0, 10, 5), "feasibility": st.sidebar.slider("Easy and affordable", 0, 10, 5)}
cap = st.sidebar.slider("Irrigation water available per season (mm)", 0, 400, 150)
tot = sum(raw.values()) or 1
weights = {k: v / tot for k, v in raw.items()}
for i, r in enumerate(adapters.rank(weights, irrigation_cap_mm=float(cap))[:5], 1):
    path = " → ".join(x["crop_id"] for x in r["rotation"])
    with st.expander(f"#{i}  {path}   score {r['score']['total']:.2f}", expanded=(i == 1)):
        st.write({k: round(v, 2) for k, v in r["score"]["sub_scores"].items()})
        for t in r["score"]["top_reasons"]:
            st.write("• " + t)
        b, bad = r["scenarios"]["baseline"], r["scenarios"]["bad_year"]
        st.caption(f"Relative yield (SIMULATED) typical year p10/p50/p90: {b['p10']:.2f}/{b['p50']:.2f}/{b['p90']:.2f}; "
                   f"bad year: {bad['p10']:.2f}/{bad['p50']:.2f}/{bad['p90']:.2f}. Future climate: not built yet.")
