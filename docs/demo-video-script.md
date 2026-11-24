# LeaseGuard — final 2-minute demo script

**Team:** Techbeez  
**Team members:** Amritanshu Mishra, Kaushiki Upadhaya  
**Project:** LeaseGuard — evidence-first lease charge audit

Do **not** record from a broken laptop install. Record the already-running app in the Arena browser preview.

---

## 1. How to open the live preview in Arena

1. Keep this Arena session open — the Vite dev server is running on **port 5173** and the API on **port 8000**.
2. In the Arena interface, open the **Live Preview** panel (it is shown for the running “Website” process and labelled with port **5173**).
3. Click **Open in new tab** / the external-link icon so the app fills a normal browser tab. This makes screen recording much cleaner than recording inside the Arena panel.
4. You should see **“Check your rent before you pay.”** and a **Load sample case** button. The header badge will say **Demo mode** — that is correct for the video.
5. If the panel is missing or blank, message in the Arena chat and ask for the preview to be restarted. Do **not** open `http://localhost:5173` on your laptop — that points to your laptop, not this sandbox.

**Direct fallback URL** (use while this session is live):

**https://5173-iq00wejk649icn06cmrof.e2b.app**

Only port **5173** is the app. Port **8000** is the API; do not open it in the video.

---

## 2. How to record

| Tool | Windows steps |
| --- | --- |
| **Xbox Game Bar** (fastest) | Focus the browser tab → `Win + Alt + R` to start → `Win + Alt + M` for mic → speak the script → `Win + Alt + S` to stop. Video saves in `Videos\Captures`. |
| **Loom** (browser extension) | Choose **Screen + webcam**, select the browser tab, press Record. Easy pause and re-record. |
| **OBS Studio** (free) | Add **Window Capture** → select Chrome/Edge → Record. |
| **PowerPoint** | Insert → Screen Recording → select the browser window. |
| **Phone** | Open the preview URL on the phone and use its built-in screen recorder. |

Tips: 1280×720 or higher, close notifications, set browser zoom to 125% if text is small, and click slowly enough for the judges to read. If a WhatsApp tab opens at the end, leave it visible for 3 seconds, then switch back.

---

## 3. Final 2-minute voiceover and click path

Suggested lower-third on the opening frame:

> **Techbeez** · Amritanshu Mishra · Kaushiki Upadhaya · LeaseGuard

### 0:00–0:10 — Intro

**Show:** full dashboard, hero, the six scenario cards and the footer credit “Techbeez · Amritanshu Mishra · Kaushiki Upadhaya”.

**Say:**
> “I’m Amritanshu Mishra from **Techbeez**, presenting LeaseGuard with my teammate **Kaushiki Upadhaya**. A tenant uploads a lease, its amendment and this month’s invoice, and the app checks the bill before payment — running right here in the browser, no installation needed.”

### 0:10–0:22 — Load the case

**Click:** **Load sample case**.

**Say:**
> “I’m loading a synthetic case: a lease, a January amendment and an April invoice — through the same upload path a real document uses.”

### 0:22–0:38 — Show the controlling amendment

**Show:** lease detail page — document list and terms table.

**Say:**
> “Here is why the amendment matters. The lease says ten percent escalation. The January amendment caps it at five percent. The app marks the new clause **In force** and the older one **Superseded** by effective date. No guessing.”

### 0:38–0:48 — Run the audit

**Click:** **Run invoice audit**.

**Say:**
> “Now I recompute the April bill from the controlling terms. The arithmetic is done in code, in integer paise — the model only reads and quotes.”

### 0:48–1:12 — Evidence for one finding

**Show:** invoice summary (billed ₹44,000) and rent finding (expected ₹42,000, excess ₹2,000). Expand **Show calculation**.

**Say:**
> “The shopkeeper billed forty-four thousand. From the controlling amendment, the correct rent is forty-two thousand — a two-thousand-rupee excess. Every finding shows the exact clause quote, the source document, the page, the effective date and the full calculation. If a quote cannot be verified or a clause is vague, it says **Needs your input** — no amount is invented.”

### 1:12–1:26 — Impact numbers

**Show:** impact strip.

**Say:**
> “Across the case: ₹3,200 excess detected, ₹3,200 awaiting my review, and an estimated time saving. These are review numbers. We do **not** claim money recovered, and nothing is sent automatically.”

### 1:26–1:38 — Decide

**Click:** **Approve** on both findings.

**Say:**
> “I approve the two confirmed differences. Until then they stay pending — the tenant is in control.”

### 1:38–1:50 — Generate the letter

**Click:** **Generate letter (2)**.

**Say:**
> “The letter includes only the findings I approved, and it can be read in English or Hindi.”

### 1:50–2:00 — Share and close

**Show:** letter preview. **Click हिंदी** once, then **Share on WhatsApp**. If a draft opens, show it for 3 seconds. If not, use **More share options → Copy link**.

**Say:**
> “**Share on WhatsApp** opens a draft with the letter text so the shopkeeper can forward it. I decide whether to send. I’m Amritanshu Mishra, with Kaushiki Upadhaya, from **Techbeez** — LeaseGuard: evidence first, tenant in control. Thank you.”

---

## 4. One-minute fallback

Keep only: intro, controlling amendment, evidence finding, impact numbers, and share/close. Say the team names in the intro and again in the last 5 seconds.

## 5. If the preview fails

`http://localhost:5173` is **not** needed. Use the `e2b.app` URL or the Arena Live Preview panel. If both fail, message in the chat to restart the preview — do not try to repair it with `npm install` on the laptop.
