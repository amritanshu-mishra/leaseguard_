# 2-minute demo video — no local setup needed

If the laptop setup is failing, **do not record from the laptop install**. Record the already-running app in the browser instead.

## The app to record

Open this URL in Chrome or Edge on the machine you are recording from:

**https://5173-iq00wejk649icn06cmrof.e2b.app**

This is the live Arena preview of the current branch. It proxies `/api` to the API, so nothing on the laptop needs installing. The URL is temporary — use it while this session is live. You can also use the **Live Preview** button in Arena and record that tab.

Confirm it loaded: you should see **“Check your rent before you pay.”** and a **Load sample case** button. The header badge should say **Demo mode** — that is expected and fine for the video.

## How to record (pick one)

| Tool | Windows steps |
| --- | --- |
| **Xbox Game Bar** (fastest) | Open the browser tab above → press `Win + Alt + R` to start → `Win + Alt + M` to turn on mic → speak the script → `Win + Alt + S` to stop. Video lands in `Videos\Captures`. |
| **Loom** (browser extension) | Install Loom, choose **Screen + webcam**, select the browser tab, press Record. Easy pause/re-record. |
| **OBS Studio** (free, most control) | Add **Window Capture** → select Chrome/Edge → Record. Good if Game Bar is blocked by policy. |
| **PowerPoint** | Insert → Screen Recording → select the browser window. |
| **Phone** | Open the URL on the phone and use its built-in screen recorder. |

Tips: use 1280×720 or higher, close notifications, zoom the browser to 125% if text looks small, and keep each click slow enough to read. If a WhatsApp tab opens at the end, leave it open for 3 seconds, then switch back.

---

## Exact 2-minute script

### 0:00–0:10 — Intro

**Show:** full dashboard, including the hero and the six scenario cards.

**Say:**
> “This is LeaseGuard. A tenant uploads a lease, its amendment, and this month's invoice. The app checks the bill before payment — and it runs right here in the browser, no installation needed.”

### 0:10–0:22 — Load the case

**Click:** **Load sample case**.

**Say:**
> “I'm loading a synthetic case: a lease, a January amendment, and an April invoice. These go through the same upload and extraction path as a real document.”

### 0:22–0:38 — Show the controlling amendment

**Show:** lease detail page — document list and the terms table.

**Say:**
> “Here is why the amendment matters. The original lease says ten percent escalation. The January amendment caps it at five percent. The app marks the new clause **In force** and the older one **Superseded** by effective date. No guessing.”

### 0:38–0:48 — Run the audit

**Click:** **Run invoice audit**.

**Say:**
> “Now I recompute the April bill from the controlling terms. The arithmetic is done in code, in integer paise — the model only reads and quotes.”

### 0:48–1:12 — Show one finding's evidence

**Show:** invoice summary (billed ₹44,000) and the rent finding (expected ₹42,000, excess ₹2,000). Expand **Show calculation** on the first finding.

**Say:**
> “The shopkeeper billed forty-four thousand. From the controlling amendment, the correct rent is forty-two thousand — a two-thousand-rupee excess. Every finding shows the exact clause quote, the source document, the page, the effective date, and the full calculation. If a quote can't be verified or a clause is vague, it is marked **Needs your input** and no amount is invented.”

### 1:12–1:26 — Impact numbers

**Show:** the impact strip.

**Say:**
> “Across the case: ₹3,200 excess detected, ₹3,200 awaiting my review, and an estimated time saving. These are review numbers. We do **not** claim any money recovered, and nothing is sent automatically.”

### 1:26–1:38 — Decide

**Click:** **Approve** on both findings.

**Say:**
> “I approve the two confirmed differences. Until I do this, they stay pending — the tenant is in control.”

### 1:38–1:50 — Generate the letter

**Click:** **Generate letter (2)**.

**Say:**
> “The letter includes only the findings I approved, and it can be read in English or Hindi.”

### 1:50–2:00 — Share and close

**Show:** letter preview. **Click हिंदी** once, then click **Share on WhatsApp**. If a draft/tab opens, show it for 3 seconds. If nothing opens, click **More share options → Copy link** and show the copied confirmation.

**Say:**
> “Finally, **Share on WhatsApp** opens a draft with the letter text — the shopkeeper can forward it from there. I decide whether to send. That's LeaseGuard: evidence first, tenant in control. Thank you.”

---

## One-minute fallback

If you only get 60 seconds, keep steps 0:00–0:10, 0:22–0:38, 0:48–1:12, 1:12–1:26 and 1:50–2:00. Skip creating a new lease, uploads from disk, the six scenario cards, and the key setup — those are in the README, not the video.

## If the preview itself fails

Check <http://localhost:5173> is not required — it is not. Use the `e2b.app` URL above. If it is blank, message in the chat and I will restart the preview; do not try to fix it with `npm install` on the laptop.
