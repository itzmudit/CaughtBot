# 🛡️ CaughtBot — Setup Guide (Windows / Linux / Mac)

**CaughtBot** automatically tests an LLM chatbot for prompt-injection and jailbreak weaknesses.
It fires a library of attacks at a target bot, uses an LLM judge to score every reply, shows a
vulnerability report, and can **auto-harden** the bot's prompt until the score improves. It has
a login system, per-user scan history, an admin dashboard, and downloadable PDF reports.

This guide gets it running on a fresh laptop. It takes about 10 minutes. **No credit card needed.**

---

## What you need

- **Python 3.10 or newer** — check with `python --version` (Windows) or `python3 --version` (Linux/Mac).
  Get it from [python.org/downloads](https://www.python.org/downloads/). On Windows, tick
  **"Add Python to PATH"** during install.
- A **free Groq API key** (step 4 below). No card required.
- The project files (you should have received a folder called `CaughtBot`).

---

## Step 1 — Open a terminal in the project folder

Put the `CaughtBot` folder somewhere easy (e.g. Desktop), then open a terminal **inside it**:

- **Windows:** open the folder in File Explorer → click the address bar → type `cmd` → Enter.
- **Linux/Mac:** open Terminal → `cd` into the folder, e.g. `cd ~/Desktop/CaughtBot`.

Everything below runs from inside this folder.

---

## Step 2 — Create a virtual environment

This keeps the project's packages separate from the rest of your system.

**Windows:**
```bat
python -m venv venv
```

**Linux / Mac:**
```bash
python3 -m venv venv
```

---

## Step 3 — Activate it, then install the packages

**Windows (Command Prompt):**
```bat
venv\Scripts\activate
```
**Linux / Mac:**
```bash
source venv/bin/activate
```

Your prompt should now start with `(venv)`. Now install everything:

```bash
pip install -r requirements.txt
```

> On Windows, if `pip` isn't found, use `python -m pip install -r requirements.txt`.

---

## Step 4 — Get a free Groq API key

1. Go to **[console.groq.com](https://console.groq.com)** and sign in (Google/GitHub works, no card).
2. Open **API Keys → Create API Key**.
3. Copy the key — it starts with `gsk_`.

---

## Step 5 — Create your `.env` file

In the project folder, create a new file named exactly **`.env`** (nothing before the dot) and put:

```
GROQ_API_KEY=gsk_paste_your_key_here
```

Optional — to give yourself the **admin dashboard**, add a second line with your login email:

```
ADMIN_EMAILS=your_email@example.com
```

(You can list more than one, separated by commas.)

> **Never share your `.env` file or your key** — it's private to you.

---

## Step 6 — Run it

```bash
streamlit run app.py
```

Your browser opens automatically at `http://localhost:8501`. If it doesn't, open that link yourself.
To stop the app later, press **Ctrl + C** in the terminal.

---

## First time using it

1. Click **Sign up**, enter an email + password (min 6 characters) → you get a unique Tester ID.
   (If you added your email to `ADMIN_EMAILS`, sign up with that exact email to get admin.)
2. A demo "weak" chatbot prompt is already loaded. Click **🚀 Run attack suite**.
3. Wait ~1–2 minutes — you'll see a **security score**, a chart, and every attack that got through.
4. Open the sidebar **🤖 Run auto-harden** to let it rewrite the prompt and re-test until the score climbs.
5. Click **⬇️ Download PDF report** to save a shareable report.

You can paste **any** chatbot's system prompt into the box and test that instead.

---

## Features

- **32 attacks** in 4 categories: prompt leakage, instruction override, role-play jailbreaks, off-limits actions.
- **LLM judge** scores each reply against a fixed security policy (structured JSON, validated).
- **Auto-harden:** only keeps a fix if a real re-run scores higher (so the score never drops).
- **Login + history:** each user gets an ID; past scans are saved.
- **Admin dashboard:** see all users/scans, grant or revoke admin, remove users.
- **PDF reports** and full **customization** (choose attacks, add your own, accent color).

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `streamlit: command not found` | Activate the venv first (Step 3); prompt must show `(venv)`. |
| `ModuleNotFoundError` | venv not active, or packages not installed → redo Step 3. |
| `AuthenticationError` / 401 | The key in `.env` is wrong. Recheck it (no quotes, no spaces around `=`). |
| `model ... does not exist` | Groq changed a model name. Open `config.py` and update `TARGET_MODEL` / `JUDGE_MODEL` to a model listed at [console.groq.com/docs/models](https://console.groq.com/docs/models). |
| `RateLimitError` (per-minute) | Wait ~1 minute and try again. The app auto-retries; it just needs to pace out. |
| `RateLimitError` (per-day / TPD) | The free daily token budget for that model is used up. Switch `JUDGE_MODEL` in `config.py` to another model, or wait for the daily reset. |
| Runs feel slow | In the sidebar **🎛️ Customize**, lower "Max attacks to run" (e.g. 8) while testing. |
| Page looks light/white | In Streamlit's **⋮ → Settings → Theme**, choose **Dark**. |

---

## Notes

- **Free tier limits:** Groq caps tokens **per minute** and **per day**. For a smooth run, use 8–16 attacks
  and don't do many full runs back-to-back.
- **Only test chatbots you own or are authorized to test.** The built-in demo bot's "secret" and "refunds"
  are fake — nothing real is touched.
- The login database (`redteam.db`) is created automatically on first run and stays on your laptop.

That's it — enjoy breaking some bots. 🛡️
