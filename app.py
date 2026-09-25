from datetime import datetime

import pandas as pd
import streamlit as st

import auth
from attacks import ATTACKS
from fixer import suggest_fixes
from harden import auto_harden
from report import category_breakdown
from report_pdf import build_pdf_report
from runner import compute_score, run_all
from target_bot import WEAK_PROMPT

CATEGORIES = ["Prompt leakage", "Instruction override", "Role-play jailbreak", "Off-limits action"]
SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "none": 4}
SEVERITY_COLOR = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵", "none": "⚪"}


def logo(size: int = 44) -> str:
    return f"""<svg width="{size}" height="{size}" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="5" y="5" width="54" height="54" rx="15" fill="url(#cbg)"/>
    <path d="M32 4v6M32 54v6M4 32h6M54 32h6" stroke="#04122b" stroke-width="3.4" stroke-linecap="round"/>
    <rect x="20" y="23" width="24" height="19" rx="6" fill="#04122b"/>
    <rect x="30.2" y="14" width="3.6" height="7" rx="1.8" fill="#04122b"/>
    <circle cx="32" cy="12.4" r="3" fill="#04122b"/>
    <circle cx="27" cy="32.5" r="3.2" fill="#7dd3fc"/>
    <circle cx="37" cy="32.5" r="3.2" fill="#7dd3fc"/>
    <rect x="27" y="37" width="10" height="2.4" rx="1.2" fill="#38bdf8"/>
    <defs><linearGradient id="cbg" x1="5" y1="5" x2="59" y2="59" gradientUnits="userSpaceOnUse">
    <stop stop-color="#38bdf8"/><stop offset="1" stop-color="#7dd3fc"/></linearGradient></defs></svg>"""


st.set_page_config(page_title="CaughtBot", page_icon="🎯", layout="wide")


# ── Styling: same palette (dark blue + light-blue/white), animated ───
def inject_css(accent: str = "#38bdf8") -> None:
    st.markdown(f"""
    <style>
    :root {{ --accent: {accent}; }}
    /* animated "scanning code" background — dark blue with faint scrolling lines */
    .stApp {{
      background-color:#070b1e;
      background-image:
        repeating-linear-gradient(0deg, rgba(56,189,248,.05) 0 1px, transparent 1px 26px),
        radial-gradient(1100px 560px at 18% -12%, #16264f 0%, #0b1636 46%, #070b1e 82%);
      background-attachment: fixed;
      animation: bgscroll 16s linear infinite;
    }}
    @keyframes bgscroll {{ from{{background-position:0 0, 0 0;}} to{{background-position:0 -260px, 0 0;}} }}
    .block-container {{ padding-top: 2rem; max-width: 1180px; }}

    @keyframes fadeUp  {{ from{{opacity:0; transform:translateY(20px);}} to{{opacity:1; transform:none;}} }}
    @keyframes floatIn {{ from{{opacity:0; transform:translateY(40px) scale(.96);}} to{{opacity:1; transform:none;}} }}
    @keyframes shimmer {{ 0%{{background-position:0% 50%}} 50%{{background-position:100% 50%}} 100%{{background-position:0% 50%}} }}
    @keyframes pulse   {{ 0%,100%{{transform:scale(1);}} 50%{{transform:scale(1.04);}} }}
    @keyframes riseIn  {{ from{{opacity:0; transform:translateY(28px);}} to{{opacity:1; transform:none;}} }}

    /* Claude-style centered landing */
    .landing {{ text-align:center; margin: 5vh 0 1.5rem; animation: fadeUp .6s ease; }}
    .landing .mark {{ display:flex; justify-content:center; margin-bottom:14px; }}
    .landing h1 {{ font-size:2.5rem; font-weight:800; color:#eaf2ff; margin:0; letter-spacing:-.6px; }}
    .landing h1 span {{ color: var(--accent); }}
    .landing p {{ color:#9fb4d6; font-size:1.05rem; margin:.5rem 0 0; }}

    .brand {{ display:flex; align-items:center; gap:10px; margin-bottom:6px; }}
    .brand b {{ font-size:1.25rem; color:#eaf2ff; letter-spacing:-.3px; }}
    .brand small {{ color:#7f93b8; }}

    div[data-testid="stMetric"] {{
      background: rgba(15,22,51,.72); border:1px solid #1e2a52; border-radius:16px; padding:16px 18px;
      animation: riseIn .6s ease both;
    }}
    div[data-testid="stMetricValue"] {{ font-size:1.9rem; font-weight:800; color:#fff; }}
    .stButton > button {{ border-radius:12px; font-weight:700; padding:.6rem 1.1rem; border:1px solid #24345f; }}
    .stButton > button[kind="primary"] {{ background:var(--accent); color:#04122b; border:0; }}
    .stDownloadButton > button {{
      border-radius:12px; font-weight:800; background:linear-gradient(120deg,var(--accent),#7dd3fc);
      color:#04122b; border:0; animation: pulse 2.6s ease infinite;
    }}
    div[data-testid="stExpander"] {{ border:1px solid #1e2a52; border-radius:13px; background:rgba(15,22,51,.55); }}
    section[data-testid="stSidebar"] {{ background:#0a1029; border-right:1px solid #16224a; }}

    /* animated reveal for the whole report block */
    #report-anchor ~ div [data-testid="stMetric"],
    [data-testid="stAlert"], [data-testid="stDataFrame"], .stProgress, .stDownloadButton {{
      animation: riseIn .6s ease both;
    }}
    .stApp textarea {{ background:rgba(9,14,34,.85)!important; border-radius:12px!important; }}

    .flash {{
      position: fixed; right: 26px; bottom: 26px; z-index: 9999;
      background: linear-gradient(120deg, var(--accent), #7dd3fc); color:#04122b;
      padding: 16px 22px; border-radius: 14px; font-weight:800; min-width: 240px;
      box-shadow: 0 16px 44px rgba(56,189,248,.45); animation: floatIn .5s ease, pulse 2.4s ease infinite;
    }}
    .flash small {{ display:block; font-weight:600; opacity:.85; }}
    </style>
    """, unsafe_allow_html=True)


def score_color(score: int) -> str:
    return "🟢" if score >= 80 else "🟡" if score >= 50 else "🔴"


def risk_label(score: int) -> str:
    return "LOW RISK" if score >= 80 else "MEDIUM RISK" if score >= 50 else "HIGH RISK"


def greeting() -> str:
    h = datetime.now().hour
    return "Good morning" if h < 12 else "Good afternoon" if h < 18 else "Good evening"


# ── Session defaults ─────────────────────────────────────────────────
ss = st.session_state
ss.setdefault("user", None)
ss.setdefault("accent", "#38bdf8")
ss.setdefault("prompt", WEAK_PROMPT)
ss.setdefault("results", None)
ss.setdefault("fix", None)
ss.setdefault("history", [])
ss.setdefault("trajectory", None)
ss.setdefault("custom_attacks", [])
ss.setdefault("flash", None)

inject_css(ss.accent)


# ── LOGIN GATE (Claude-style opening) ────────────────────────────────
def login_screen() -> None:
    st.markdown(f"""
    <div class="landing">
      <div class="mark">{logo(60)}</div>
      <h1>Caught<span>Bot</span></h1>
      <p>Catch your chatbot's weaknesses before attackers do.</p>
    </div>""", unsafe_allow_html=True)

    _, mid, _ = st.columns([1, 1.6, 1])
    with mid:
        with st.container(border=True):
            tab_login, tab_signup = st.tabs(["🔑 Log in", "✨ Sign up"])
            with tab_login:
                email = st.text_input("Email", key="li_email")
                pw = st.text_input("Password", type="password", key="li_pw")
                if st.button("Log in", type="primary", use_container_width=True):
                    ok, msg, user = auth.log_in(email, pw)
                    if ok:
                        ss.user = user
                        ss.flash = {"title": "Logged in", "sub": f"ID {user['id']}"}
                        st.rerun()
                    else:
                        st.error(msg)
            with tab_signup:
                email2 = st.text_input("Email", key="su_email")
                pw2 = st.text_input("Password (min 6 chars)", type="password", key="su_pw")
                if st.button("Create account", type="primary", use_container_width=True):
                    ok, msg, user = auth.sign_up(email2, pw2)
                    if ok:
                        ss.user = user
                        ss.flash = {"title": "Account created 🎉", "sub": f"Your ID: {user['id']}"}
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(msg)
            st.caption("One account per email · passwords stored hashed, never in plain text.")


if ss.user is None:
    login_screen()
    st.stop()


# ── LOGGED IN ────────────────────────────────────────────────────────
user = ss.user
breached_now = [r for r in ss.results if r["succeeded"]] if ss.results else []

with st.sidebar:
    st.markdown(f'<div class="brand">{logo(30)}<b>CaughtBot</b></div>', unsafe_allow_html=True)
    admin_badge = " · 🛡️ ADMIN" if user.get("is_admin") else ""
    st.caption(f"👤 {user['email'].split('@')[0]}{admin_badge}  ·  ID `{user['id']}`")
    if st.button("Log out", use_container_width=True):
        for k in ["user", "results", "fix", "history", "trajectory", "custom_attacks", "flash"]:
            ss.pop(k, None)
        st.rerun()
    st.divider()

    # Auto-harden lives in the sidebar now
    st.subheader("🤖 Auto-harden")
    rounds = st.slider("Rounds", 1, 3, 2,
                       help="Each round re-runs the whole suite and keeps the fix only if the score improves.")
    auto_clicked = st.button("🤖 Run auto-harden", use_container_width=True)

    # Quick fixes gets its own bar in the sidebar
    st.subheader("🩹 Quick fixes")
    if breached_now:
        fixes_clicked = st.button("Generate fixes", use_container_width=True)
    else:
        fixes_clicked = False
        st.caption("Run a scan with failing attacks first.")

    with st.expander("🎛️ Customize", expanded=False):
        chosen_cats = st.multiselect("Attack categories", CATEGORIES, default=CATEGORIES)
        max_attacks = st.slider("Max attacks to run", 4, len(ATTACKS) + len(ss.custom_attacks), 16,
                                help="On the free tier, fewer attacks finish faster. 32 works too but is slower.")
        ss.accent = st.color_picker("Accent color", ss.accent)
        st.markdown("**Add a custom attack**")
        ca_cat = st.selectbox("Category", CATEGORIES, key="ca_cat")
        ca_prompt = st.text_input("Attack prompt", key="ca_prompt")
        if st.button("➕ Add attack") and ca_prompt.strip():
            ss.custom_attacks.append({"id": f"CUSTOM-{len(ss.custom_attacks)+1:02d}",
                                      "category": ca_cat, "prompt": ca_prompt.strip()})
            st.success("Added.")
        if ss.custom_attacks:
            st.caption(f"{len(ss.custom_attacks)} custom attack(s) added.")

    with st.expander("🕘 Your history", expanded=False):
        hist = auth.scan_history(user["id"])
        if hist:
            st.dataframe(pd.DataFrame(hist)[["ts", "score", "label"]].rename(
                columns={"ts": "When", "score": "Score", "label": "Run"}).assign(
                When=lambda d: d["When"].str.slice(5, 16).str.replace("T", " ")),
                hide_index=True, use_container_width=True)
        else:
            st.caption("No scans yet. Run one!")

    if user.get("is_admin"):
        with st.expander("🛡️ Admin", expanded=False):
            stats = auth.platform_stats()
            st.metric("Users", stats["users"])
            st.metric("Scans", stats["scans"])
            st.metric("Avg score", f"{stats['avg_score']}/100")
            udf = pd.DataFrame(auth.all_users())
            if not udf.empty:
                st.dataframe(udf.rename(columns={"email": "Email", "id": "ID", "scans": "Scans",
                                                 "best_score": "Best", "last_score": "Last"})[
                    ["Email", "ID", "Scans", "Best", "Last"]], hide_index=True, use_container_width=True)
                others = [u for u in auth.all_users() if u["id"] != user["id"]]
                if others:
                    pick = st.selectbox("Remove user", [f"{u['email']} ({u['id']})" for u in others])
                    if st.button("🗑️ Delete user"):
                        auth.delete_user(pick.split("(")[-1].rstrip(")"))
                        st.success("Removed.")
                        st.rerun()
            st.caption("Set via ADMIN_EMAILS in .env. Passwords never shown.")

# Active attack list from customization
active_attacks = [a for a in ATTACKS if a["category"] in chosen_cats]
active_attacks = active_attacks[:max(1, max_attacks - len(ss.custom_attacks))] + \
    [a for a in ss.custom_attacks if a["category"] in chosen_cats]

# ── Floating completion message ──────────────────────────────────────
if ss.flash:
    st.markdown(f'<div class="flash">{ss.flash["title"]}<small>{ss.flash["sub"]}</small></div>',
                unsafe_allow_html=True)
    ss.flash = None

# ── Claude-style centered landing ────────────────────────────────────
name = user["email"].split("@")[0].capitalize()
st.markdown(f"""
<div class="landing">
  <div class="mark">{logo(52)}</div>
  <h1>{greeting()}, {name}</h1>
  <p>Point CaughtBot at a system prompt and it will try {len(active_attacks)} ways to break it.</p>
</div>""", unsafe_allow_html=True)

_, mid, _ = st.columns([1, 2.4, 1])
with mid:
    prompt = st.text_area("System prompt", ss.prompt, height=180, label_visibility="collapsed",
                          placeholder="Paste the chatbot's system prompt here…")
    run_clicked = st.button("🚀 Run attack suite", type="primary", use_container_width=True)


def finish(results, label):
    ss.prompt = prompt
    ss.results = results
    score = compute_score(results)
    ss.history.append(score)
    blocked = sum(1 for r in results if not r["succeeded"])
    auth.record_scan(user["id"], score, blocked, len(results), label)
    ss.flash = {"title": f"{label} complete · {score}/100", "sub": f"{blocked}/{len(results)} attacks blocked"}


if run_clicked:
    with st.spinner(f"Firing {len(active_attacks)} attacks and judging every reply..."):
        results = run_all(prompt, active_attacks)
    ss.fix = None
    ss.trajectory = None
    finish(results, "Scan")
    st.toast("Scan complete!", icon="✅")
    st.rerun()

if auto_clicked:
    st.subheader("🤖 Auto-harden progress")
    live = st.container()
    progress = st.progress(0.0)
    trajectory = []
    best_prompt, best_results = prompt, ss.results
    with st.spinner("Hardening… runs the full suite once per round."):
        for step in auto_harden(prompt, active_attacks, base_results=ss.results, max_rounds=rounds):
            if step["round"] == 0:
                live.markdown(f"**Baseline:** {score_color(step['score'])} **{step['score']}/100**")
            else:
                badge = "✅ **KEPT**" if step["accepted"] else "↩️ **REJECTED** (did not beat best)"
                live.markdown(f"**Round {step['round']}:** candidate {score_color(step['score'])} "
                              f"{step['score']}/100 → {badge} · best **{step['best_score']}/100**")
                progress.progress(step["round"] / rounds)
            if step["accepted"]:
                best_prompt, best_results = step["prompt"], step["results"]
            trajectory.append(step)
    progress.progress(1.0)
    prompt = best_prompt
    ss.fix = None
    ss.trajectory = trajectory
    finish(best_results, "Auto-harden")
    st.balloons()
    st.rerun()

if fixes_clicked and ss.results:
    with st.spinner("Analyzing failures and hardening the prompt..."):
        ss.fix = suggest_fixes(ss.prompt, [r for r in ss.results if r["succeeded"]])

if ss.trajectory:
    scores = [s["score"] if s["round"] == 0 else s["best_score"] for s in ss.trajectory]
    kept = sum(1 for s in ss.trajectory if s["round"] and s["accepted"])
    st.info("**Auto-harden:** " + " → ".join(str(s) for s in scores) +
            f"/100  ·  kept {kept} of {len(ss.trajectory) - 1} attempted fixes.")

# ── Report ───────────────────────────────────────────────────────────
results = ss.results
if results:
    st.markdown('<span id="report-anchor"></span>', unsafe_allow_html=True)
    st.subheader("📊 Vulnerability report")
    history = ss.history
    breached = [r for r in results if r["succeeded"]]
    score = history[-1]
    delta = history[-1] - history[-2] if len(history) > 1 else None

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Security score", f"{score}/100", delta=delta)
    c2.metric("Risk level", f"{score_color(score)} {risk_label(score)}")
    c3.metric("Blocked", len(results) - len(breached))
    c4.metric("Broke through", len(breached))
    st.progress(score / 100)
    if len(history) > 1:
        st.caption("Score history: " + " → ".join(str(s) for s in history))

    chart_col, table_col = st.columns(2)
    df = pd.DataFrame(results)
    chart_col.markdown("**Successful attacks by category**")
    chart_col.bar_chart(df.groupby("category")["succeeded"].sum())
    table_col.markdown("**Category breakdown**")
    table_col.dataframe(pd.DataFrame([{"Category": c, "Broke in": f"{s} / {t}", "Blocked": t - s}
                                      for c, (s, t) in category_breakdown(results).items()]),
                        hide_index=True, use_container_width=True)

    report_fixes = ss.fix.fixes if ss.fix else None
    st.download_button("⬇️ Download PDF report",
                       data=build_pdf_report(prompt, results, fixes=report_fixes),
                       file_name=f"caughtbot_report_{user['id']}.pdf", mime="application/pdf")

    st.subheader("🚨 Successful attacks")
    if not breached:
        st.success("No attacks succeeded. The bot passed the full suite.")
    for r in sorted(breached, key=lambda r: SEVERITY_ORDER[r["severity"]]):
        with st.expander(f"{SEVERITY_COLOR[r['severity']]} [{r['severity'].upper()}] {r['id']} · {r['category']}"):
            st.markdown("**Attack**")
            st.code(r["prompt"], language=None)
            st.markdown("**Bot reply**")
            st.code(r["response"], language=None)
            st.markdown(f"**Judge's evidence:** {r['evidence']}")

    if ss.fix:
        st.subheader("🩹 Suggested fixes")
        for item in ss.fix.fixes:
            st.markdown(f"- {item}")
        st.markdown("**Hardened system prompt**")
        st.code(ss.fix.hardened_prompt, language=None)
        if st.button("✅ Apply fix (updates the prompt above)"):
            ss.prompt = ss.fix.hardened_prompt
            ss.results = None
            ss.fix = None
            ss.trajectory = None
            st.rerun()
