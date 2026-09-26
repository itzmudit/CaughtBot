# 🛡️ CaughtBot — Complete User Guide & Walkthrough
*Har feature, har button, har flow — click-by-click. Hinglish.*

> App chalao: `streamlit run app.py` → browser khudke `http://localhost:8501` pe khulega.
> App band karo: terminal mein `Ctrl + C`.

---

## 0. Screen ka map (kahan kya hai)

**Login se pehle:** sirf ek centered card — Log in / Sign up.

**Login ke baad, do hisse:**
- **Left sidebar** → account, Target, Auto-harden, Quick fixes, Customize, History.
- **Main area (right)** → greeting, (Admin dashboard agar admin), system prompt box, Run button, aur scan ke baad poori report.

---

## 1. Andar aana (Login / Sign up)

### Naya account banana
1. **✨ Sign up** tab pe click.
2. **Email** daalo (asli format, jaise `naam@gmail.com`).
3. **Password** daalo (kam se kam 6 characters).
4. **Create account** dabao.
5. ✅ Green balloons + ek floating message "Account created" + tumhara unique **Tester ID** dikhega. Seedhe andar aa jaoge.

### Pehle se account hai
1. **🔑 Log in** tab → email + password → **Log in**.

### Possible errors (aur matlab)
| Message | Matlab | Fix |
|---|---|---|
| "That doesn't look like a valid email" | Email format galat | `naam@domain.com` daalo |
| "Password must be at least 6 characters" | Chhota password | 6+ characters |
| "An account with this email already exists" | Email pehle se registered | Log in tab use karo |
| "No account with this email" | Registered nahi | Sign up karo |
| "Wrong password" | Password galat | Dobara sahi daalo |

> **Admin banna hai?** `.env` file mein `ADMIN_EMAILS=teri@email.com` honi chahiye, aur usi email se sign up/login karna. Tab sidebar mein **🛡️ ADMIN** badge aur Admin dashboard milega.

---

## 2. Sabse basic flow (pehli scan) — 3 click

1. Main area mein pehle se ek weak bot ka **system prompt** likha hai (ya apna paste karo).
2. **🚀 Run attack suite** dabao.
3. 1–2 min ruko → neeche poori **report** aa jayegi (score, chart, failed attacks).

Bas! Ye core hai. Baaki sab isi ke upar hai.

---

## 3. Report ko samajhna (scan ke baad kya-kya dikhta hai)

Upar se neeche:
1. **🧠 Generate AI summary** button → dabane pe 3-4 line ki plain-English summary.
2. **4 metric cards:**
   - **Security score** — kitne % attacks bot ne roke (0–100). Green delta pichhli scan se change dikhata hai.
   - **Weighted score** — critical breaches ko zyada weight (smart score).
   - **Blocked** — kitne attacks ruke.
   - **Broke through** — kitne attacks tod gaye.
3. **Progress bar** + risk line (LOW/MEDIUM/HIGH RISK).
4. **Score over time** — line chart (2+ scans ke baad dikhta hai).
5. **Do charts:** category-wise successful attacks + severity breakdown.
6. **⬇️ Download PDF report** — poori report ek PDF file mein.
7. **🚨 Successful attacks** — har fail hue attack ka expander → kholo to attack, bot ka reply, judge ka evidence, aur **🩹 Fix this one** button.

---

## 4. Saare features + flows (har combination)

### A) Auto-harden (khud sudhaar ke re-test) 🤖
*Sidebar mein, sirf demo-prompt mode mein.*
1. Sidebar → **🤖 Auto-harden** → **Rounds** slider set karo (1–3).
2. **🤖 Run auto-harden** dabao.
3. Main area mein live progress: baseline score → har round KEPT/REJECTED → best score.
4. Ant mein report best prompt ke saath update ho jayegi, score upar chala jayega.
> **Kaise kaam:** har round naya fix banata hai, poora suite dobara chalata hai, aur fix **tabhi rakhta hai jab score sach mein badhe**. Isliye score kabhi neeche nahi jaata.

### B) Quick fixes (ek-step suggestion) 🩹
*Sidebar. Sirf tab active jab kuch attacks tute ho.*
1. Ek scan chalao jisme kuch attacks tootein.
2. Sidebar → **🩹 Quick fixes** → **Generate fixes** dabao.
3. Report ke neeche **🩹 Suggested fixes** aayega: fixes ki list + ek **hardened system prompt**.
4. **✅ Apply fix** dabao → upar wala prompt badal jayega, results clear → phir **Run attack suite** dabao aur naya score dekho.

### C) Per-attack fix (ek attack ka targeted fix) 🩹
1. Report → **🚨 Successful attacks** → koi ek attack ka expander kholo.
2. Andar **🩹 Fix this one** dabao.
3. Us ek attack ka targeted fix wahin dikh jayega.

### D) AI-generated attacks (bot ke liye custom attacks) ✨
1. Sidebar → **🎛️ Customize** kholo.
2. **✨ Generate attacks with AI** ke neeche **How many** slider (3–8) set karo.
3. **✨ Generate attacks** dabao → AI us prompt ke hisaab se naye attacks banake list mein add kar dega.
4. Ab **Run attack suite** dabao → ye naye attacks bhi chalenge.

### E) Apna custom attack add karna ➕
1. Sidebar → **🎛️ Customize** → **Add a custom attack**.
2. **Category** chuno, **Attack prompt** likho.
3. **➕ Add attack** dabao.
4. **Clear custom attacks** se saare custom/AI attacks hata sakte ho.

### F) Kitne attacks chalein (speed control) 🎚️
1. Sidebar → **🎛️ Customize** → **Max attacks to run** slider.
2. Kam attacks = jaldi (free tier pe achha). 16 default hai; testing mein 8 rakho.

### G) Live chatbot test karna (asli bot ka API) 🎯
*Apne ya authorized bot pe hi.*
1. Sidebar → **🎯 Target** → **"Test a live chatbot API"** toggle ON karo.
2. Bharo:
   - **Bot API URL** (jaise `https://your-bot.com/chat`)
   - **Request field** (jis JSON field mein message jaata hai, default `message`)
   - **Response field** (jis field mein reply aata hai, default `reply`)
   - **Bearer token** (optional, agar bot ko chahiye)
3. Main area mein note aayega + button **🚀 Attack live bot** ban jayega.
4. Dabao → attacks tumhare asli bot ke API pe jaayenge, aur report banegi.
> Live mode mein Auto-harden nahi dikhega (asli bot ka prompt tum yahan se nahi badal sakte).

### H) AI summary 🧠
1. Kisi bhi report ke top pe **🧠 Generate AI summary** dabao.
2. Plain-English 3-4 line summary aa jayegi (PDF report mein bhi chali jayegi).

### I) PDF report download ⬇️
1. Report mein **⬇️ Download PDF report** dabao → structured PDF (score, category table, har breach, fixes, summary) download.

### J) Apni history 🕘
1. Sidebar → **🕘 Your history** kholo → tumhari saari pichhli scans (time, score, type).

### K) Log out
1. Sidebar top → **Log out** → wapas login screen.

---

## 5. Admin features (sirf admin ko dikhte hain) 🛡️

Admin ke liye main area mein **🛡️ Admin dashboard** expander hota hai.
1. Kholo → upar **stats**: total users, total scans, average score.
2. **All registered users** table: email, ID, admin status, scans, best/last score.
3. **Manage admins:**
   - **Grant admin by email** → kisi registered user ki email daalo → **➕ Make admin**.
   - **Revoke admin from** → dropdown se admin chuno → **➖ Revoke admin** (super-admins nahi hat sakte).
4. **Remove a user** → dropdown se user chuno → **🗑️ Delete user and their scans**.

> **Super-admin** = jo `.env` ke `ADMIN_EMAILS` mein hai (kabhi nahi hat sakta). **Normal admin** = jise app ke andar se banaya (hataya ja sakta hai).

---

## 6. Ek typical demo flow (poora combo, start-to-end)

1. **Sign up** (ya log in) karo.
2. Weak prompt already loaded hai → **🚀 Run attack suite** → score aayega (jaise 22/100).
3. Ek **critical** attack kholo → bot ne secret leak kiya, evidence dekho.
4. Sidebar → **🤖 Run auto-harden** → score upar (jaise 62/100), green delta.
5. **🧠 Generate AI summary** → summary padho.
6. **⬇️ Download PDF report** → report save.
7. (Optional) **🎛️ Customize → ✨ Generate attacks** → naye AI attacks → phir Run.
8. (Optional) **🎯 Target** toggle → apne asli bot ka URL → **Attack live bot**.

---

## 7. Common gotchas (yaad rakho)

| Problem | Fix |
|---|---|
| `.py` file badli, change nahi dikh raha | Streamlit restart: `Ctrl + C` → `streamlit run app.py` |
| `command not found: streamlit` | Pehle `source venv/bin/activate` (Windows: `venv\Scripts\activate`) |
| `File does not exist: app.py` | Galat folder — pehle project folder mein `cd` karo |
| RateLimitError (per-minute) | 1 min ruko, retry |
| RateLimitError (per-day) | Us model ka din ka budget khatam — `config.py` mein model badlo ya kal |
| Page light/white dikh raha | Streamlit `⋮ → Settings → Theme → Dark` |
| Auto-harden nahi dikh raha | Tum live-target mode mein ho — toggle OFF karo |

---

## 8. Zaroori note
Sirf apne ya authorized chatbots pe test karo. Built-in demo bot fake hai — uska "secret" aur "actions" asli nahi. 🛡️
