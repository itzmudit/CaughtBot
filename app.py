import pandas as pd
import streamlit as st

from fixer import suggest_fixes
from runner import compute_score, run_all
from target_bot import WEAK_PROMPT

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "none": 4}

st.set_page_config(page_title="Chatbot Red-Teamer", page_icon="🛡️", layout="wide")
st.title("🛡️ Chatbot Red-Teamer")
st.caption("Automated prompt-injection and jailbreak testing for LLM chatbots")

# session_state survives Streamlit's re-runs (every button click re-runs the script)
if "prompt" not in st.session_state:
    st.session_state.prompt = WEAK_PROMPT
    st.session_state.results = None
    st.session_state.fix = None
    st.session_state.history = []

# ── 1. Target ────────────────────────────────────────────────────────
st.subheader("1. Target bot's system prompt")
prompt = st.text_area("System prompt", st.session_state.prompt, height=180)

if st.button("🚀 Run attack suite", type="primary"):
    with st.spinner("Firing 32 attacks and judging every reply..."):
        st.session_state.results = run_all(prompt)
    st.session_state.prompt = prompt
    st.session_state.fix = None
    st.session_state.history.append(compute_score(st.session_state.results))

results = st.session_state.results
if results:
    # ── 2. Scorecard ─────────────────────────────────────────────────
    st.subheader("2. Vulnerability report")
    history = st.session_state.history
    breached = [r for r in results if r["succeeded"]]
    delta = history[-1] - history[-2] if len(history) > 1 else None

    c1, c2, c3 = st.columns(3)
    c1.metric("Security score", f"{history[-1]}/100", delta=delta)
    c2.metric("Attacks blocked", len(results) - len(breached))
    c3.metric("Attacks succeeded", len(breached))
    if len(history) > 1:
        st.caption("Score history: " + " → ".join(str(s) for s in history))

    df = pd.DataFrame(results)
    st.markdown("**Successful attacks by category**")
    st.bar_chart(df.groupby("category")["succeeded"].sum())

    # ── 3. Failed attacks ────────────────────────────────────────────
    st.subheader("3. Successful attacks")
    for r in sorted(breached, key=lambda r: SEVERITY_ORDER[r["severity"]]):
        with st.expander(f"[{r['severity'].upper()}] {r['id']} · {r['category']}"):
            st.markdown("**Attack**")
            st.code(r["prompt"], language=None)
            st.markdown("**Bot reply**")
            st.code(r["response"], language=None)
            st.markdown(f"**Judge's evidence:** {r['evidence']}")

    # ── 4. Fixes ─────────────────────────────────────────────────────
    if breached:
        st.subheader("4. Suggested fixes")
        if st.button("🩹 Generate fixes"):
            with st.spinner("Analyzing failures and hardening the prompt..."):
                st.session_state.fix = suggest_fixes(prompt, breached)

        fix = st.session_state.fix
        if fix:
            for item in fix.fixes:
                st.markdown(f"- {item}")
            st.markdown("**Hardened system prompt**")
            st.code(fix.hardened_prompt, language=None)
            if st.button("✅ Apply fix, then click Run again"):
                st.session_state.prompt = fix.hardened_prompt
                st.session_state.results = None
                st.session_state.fix = None
                st.rerun()
    else:
        st.success("No attacks succeeded. The bot passed the full suite.")