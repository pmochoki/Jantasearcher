# ProjectEagle — Scan & apply frequency

With **URGENCY_MODE=true** and **PERMIT_DEADLINE** set (default for your 3-month window):

| What | How often | Notes |
|------|-----------|--------|
| **Automation check** | Every **15 min** | Decides what is due |
| **LinkedIn jobs** | Every **2 h** | 4 countries × 2 titles per batch → full Europe in ~6 days |
| **LinkedIn scholarships** | Every **3 h** | Keywords rotate across Hungary + all Europe |
| **EURES (EU official)** | Every **4 h** | 3 countries per batch |
| **Arbeitnow + RemoteOK + scholarship RSS** | Every **4 h** | API feeds, no login |
| **profession.hu (Hungary)** | Every **6 h** | Playwright |
| **Indeed EU** | Every **12 h** | Every 3rd extra cycle; may hit CAPTCHA |
| **Auto-apply** | Up to **10/day** | Min **25 min** apart; Greenhouse/Lever only; **Approve** button on Telegram |

Normal mode (urgency off): slower — 30 min checks, 6 h LinkedIn, 6 applies/day.

## All sources

**Jobs:** LinkedIn (46 countries), EURES, Arbeitnow, RemoteOK, profession.hu, Indeed  
**Scholarships:** LinkedIn keywords, ScholarshipDB RSS, OpportunityDesk RSS  

## Telegram

- `/urgency` — countdown + full schedule
- `/pending` — applications waiting for your **Approve** button
- `/automation run` — force everything now

Keep the **local backend running 24/7** on your Mac (Vercel cannot run Playwright scrapers).
