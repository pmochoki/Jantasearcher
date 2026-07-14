# ProjectEagle — Scan & apply frequency

With **URGENCY_MODE=true**, **HUNGARY_FOCUS=true**, and **PERMIT_DEADLINE** set:

| What | How often | Notes |
|------|-----------|--------|
| **Automation check** | Every **15 min** | Decides what is due |
| **Hungary deep scan (LinkedIn)** | Every **1 h** | Hungary + Budapest × up to 6 titles |
| **LinkedIn Europe** | Every **2 h** | **Hungary always included** + 4 other countries |
| **LinkedIn scholarships** | Every **3 h** | **Hungary + Budapest only** |
| **EURES (EU official)** | Every **4 h** | **Hungary (hu) in every batch** |
| **Arbeitnow + RemoteOK + scholarship RSS** | Every **4 h** | API feeds |
| **profession.hu (Hungary)** | Every **3 h** | 4 job titles per run |
| **Indeed** | Every **12 h** | Hungary + Germany when focus on |
| **Auto-apply** | Up to **10/day** | Hungary jobs **prioritized** in queue |

Normal mode (urgency off): slower — 30 min checks, Hungary every 4 h, profession.hu every 6 h.

## Hungary focus

When `HUNGARY_FOCUS=true` (default):

- Every LinkedIn EU batch starts with **Hungary + Budapest**
- Dedicated **Hungary-only** LinkedIn pass on its own schedule
- EURES always queries **hu**
- Scholarships searched in **Hungary only** (while EU jobs still rotate)
- Apply queue **boosts** Hungary and profession.hu listings

## Telegram

- `/scan hungary` — force Hungary deep scan now
- `/scan profession` — profession.hu now
- `/urgency` — countdown + full schedule
- `/pending` — applications waiting for **Approve**

Keep the **local backend running 24/7** on your Mac (Vercel cannot run Playwright scrapers).
