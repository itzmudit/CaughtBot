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
    <rect x="5" y="5" width="54" height="54" rx="16" fill="url(#cbg)"/>
    <rect x="5.6" y="5.6" width="52.8" height="52.8" rx="15.4" fill="none" stroke="rgba(255,255,255,.18)" stroke-width="1.1"/>
    <path d="M32 4v6M32 54v6M4 32h6M54 32h6" stroke="#0b0b18" stroke-width="3.4" stroke-linecap="round"/>
    <rect x="20" y="23" width="24" height="19" rx="6" fill="#0b0b18"/>
    <rect x="30.2" y="14" width="3.6" height="7" rx="1.8" fill="#0b0b18"/>
    <circle cx="32" cy="12.4" r="3" fill="#0b0b18"/>
    <circle cx="27" cy="32.5" r="3.2" fill="#e0e7ff"/>
    <circle cx="37" cy="32.5" r="3.2" fill="#e0e7ff"/>
    <rect x="27" y="37" width="10" height="2.4" rx="1.2" fill="#c7d2fe"/>
    <defs><linearGradient id="cbg" x1="5" y1="5" x2="59" y2="59" gradientUnits="userSpaceOnUse">
    <stop stop-color="#6366f1"/><stop offset="1" stop-color="#a855f7"/></linearGradient></defs></svg>"""


st.set_page_config(page_title="CaughtBot", page_icon="🎯", layout="wide")


# ── Styling: premium classy dark — Inter, aurora glow, glass panels ──
def inject_css(accent: str = "#6366f1") -> None:
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    :root {{ --accent:{accent}; --muted:#8b93ad; --line:rgba(255,255,255,.08); --glass:rgba(255,255,255,.035); }}
    html, body, .stApp, [class*="css"], button, input, textarea {{ font-family:'Inter',system-ui,sans-serif !important; }}

    /* drifting aurora over near-black — dynamic but classy */
    .stApp {{
      background:
        radial-gradient(620px 620px at 12% 6%, rgba(99,102,241,.20), transparent 60%),
        radial-gradient(560px 560px at 88% 94%, rgba(168,85,247,.16), transparent 62%),
        radial-gradient(520px 520px at 82% 10%, rgba(59,130,246,.12), transparent 60%),
        #08090f;
      background-attachment: fixed;
      animation: aurora 26s ease-in-out infinite;
    }}
    @keyframes aurora {{
      0%,100% {{ background-position: 12% 6%, 88% 94%, 82% 10%, 0 0; }}
      50%     {{ background-position: 20% 14%, 80% 86%, 72% 18%, 0 0; }}
    }}
    .block-container {{ padding-top: 2.4rem; max-width: 1100px; }}

    @keyframes fadeUp  {{ from{{opacity:0; transform:translateY(16px);}} to{{opacity:1; transform:none;}} }}
    @keyframes floatIn {{ from{{opacity:0; transform:translateY(22px);}} to{{opacity:1; transform:none;}} }}

    /* minimalist centered landing */
    .landing {{ text-align:center; margin: 6vh 0 1.7rem; animation: fadeUp .7s cubic-bezier(.2,.7,.2,1); }}
    .landing .mark {{ display:flex; justify-content:center; margin-bottom:20px; }}
    .landing .mark svg {{ filter: drop-shadow(0 8px 26px rgba(99,102,241,.55)); }}
    .landing h1 {{ font-size:2.6rem; font-weight:700; color:#f4f5fb; margin:0; letter-spacing:-1px; }}
    .landing h1 span {{ background:linear-gradient(120deg,#818cf8,#c084fc); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }}
    .landing p {{ color:var(--muted); font-size:1.04rem; margin:.7rem 0 0; font-weight:400; }}

    .brand {{ display:flex; align-items:center; gap:10px; margin-bottom:4px; }}
    .brand b {{ font-size:1.18rem; color:#f4f5fb; letter-spacing:-.3px; font-weight:700; }}

    /* glass panels */
    div[data-testid="stMetric"] {{
      background:var(--glass); border:1px solid var(--line); border-radius:16px; padding:18px 20px;
      backdrop-filter: blur(10px); animation: fadeUp .5s ease both;
    }}
    div[data-testid="stMetricValue"] {{ font-size:1.85rem; font-weight:700; color:#f4f5fb; letter-spacing:-.5px; }}
    div[data-testid="stMetricLabel"] {{ color:var(--muted); font-weight:500; }}

    /* buttons */
    .stButton > button {{
      border-radius:12px; font-weight:600; padding:.6rem 1.15rem; transition:all .18s ease;
      background:var(--glass); color:#e8eaf2; border:1px solid var(--line); backdrop-filter: blur(8px);
    }}
    .stButton > button:hover {{ border-color:rgba(129,140,248,.6); transform:translateY(-1px); }}
    .stButton > button[kind="primary"] {{
      background:linear-gradient(180deg,#7275f6,#5b5ee8); color:#fff; border:0;
      box-shadow:0 10px 26px -10px rgba(99,102,241,.85);
    }}
    .stButton > button[kind="primary"]:hover {{ transform:translateY(-1px); box-shadow:0 14px 32px -10px rgba(99,102,241,1); }}
    .stDownloadButton > button {{
      border-radius:12px; font-weight:700; background:var(--glass);
      color:#c7d2fe; border:1px solid rgba(129,140,248,.45); backdrop-filter: blur(8px);
    }}
    .stDownloadButton > button:hover {{ border-color:rgba(129,140,248,.9); color:#fff; }}

    div[data-testid="stExpander"] {{ border:1px solid var(--line); border-radius:14px; background:var(--glass); backdrop-filter: blur(8px); }}
    section[data-testid="stSidebar"] {{ background:rgba(8,9,15,.72); border-right:1px solid var(--line); backdrop-filter: blur(14px); }}
    .stApp textarea {{ background:rgba(255,255,255,.03)!important; border:1px solid var(--line)!important; border-radius:14px!important; color:#e8eaf2!important; }}
    [data-testid="stDataFrame"] {{ border:1px solid var(--line); border-radius:12px; overflow:hidden; }}
    hr {{ border-color:var(--line)!important; }}

    [data-testid="stAlert"], [data-testid="stDataFrame"], .stProgress, .stDownloadButton {{ animation: fadeUp .6s ease both; }}

    /* floating completion toast — glass card with accent edge */
    .flash {{
      position: fixed; right: 24px; bottom: 24px; z-index: 9999;
      background: rgba(15,17,26,.92); color:#f4f5fb; border:1px solid var(--line);
      border-left:3px solid #818cf8; backdrop-filter: blur(16px);
      padding: 15px 20px; border-radius: 14px; font-weight:600; min-width: 234px;
      box-shadow: 0 24px 60px rgba(0,0,0,.6); animation: floatIn .5s ease;
    }}
    .flash small {{ display:block; font-weight:400; color:var(--muted); margin-top:3px; }}
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
ss.setdefault("accent", "#6366f1")
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
        st.caption("🛡️ You're an admin — the Admin dashboard is on the main page.")

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

# ── Admin dashboard (admins only) ────────────────────────────────────
if user.get("is_admin"):
    with st.expander("🛡️ Admin dashboard", expanded=False):
        stats = auth.platform_stats()
        a1, a2, a3 = st.columns(3)
        a1.metric("Total users", stats["users"])
        a2.metric("Total scans", stats["scans"])
        a3.metric("Avg score", f"{stats['avg_score']}/100")

        users = auth.all_users()
        if not users:
            st.caption("No users registered yet.")
        else:
            udf = pd.DataFrame(users)
            show = udf.assign(
                Admin=udf["admin"].map(lambda x: "✅" if x else "—"),
                Type=udf["super_admin"].map(lambda x: "super (.env)" if x else ""),
            ).rename(columns={"email": "Email", "id": "ID", "scans": "Scans",
                              "best_score": "Best", "last_score": "Last"})
            st.markdown("**All registered users**")
            st.dataframe(show[["Email", "ID", "Admin", "Type", "Scans", "Best", "Last"]],
                         hide_index=True, use_container_width=True)

            st.markdown("**Manage admins**")
            g1, g2 = st.columns(2)
            with g1:
                new_admin = st.text_input("Grant admin by email", key="grant_email",
                                          placeholder="friend@example.com")
                if st.button("➕ Make admin", use_container_width=True) and new_admin.strip():
                    ok, msg = auth.grant_admin_by_email(new_admin)
                    (st.success if ok else st.error)(msg)
                    if ok:
                        st.rerun()
            with g2:
                revocable = [u for u in users if u["db_admin"] and not u["super_admin"] and u["id"] != user["id"]]
                if revocable:
                    rev = st.selectbox("Revoke admin from", [f"{u['email']} ({u['id']})" for u in revocable], key="rev")
                    if st.button("➖ Revoke admin", use_container_width=True):
                        auth.set_admin(rev.split("(")[-1].rstrip(")"), False)
                        st.success("Admin revoked.")
                        st.rerun()
                else:
                    st.caption("No revocable admins. Super-admins (from .env) can't be revoked here.")

            st.markdown("**Remove a user**")
            others = [u for u in users if u["id"] != user["id"]]
            if others:
                pick = st.selectbox("Select a user", [f"{u['email']} ({u['id']})" for u in others], key="delpick")
                if st.button("🗑️ Delete user and their scans"):
                    auth.delete_user(pick.split("(")[-1].rstrip(")"))
                    st.success("User removed.")
                    st.rerun()
        st.caption("Super-admins are set via ADMIN_EMAILS in .env and always stay admin. "
                   "Any admin can promote others here. Passwords are never shown.")

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
