# Voter Registration Tracker

Real-time US voter registration map. Tracks the 30 states that publicly publish party registration data, updated on each state's own publication schedule (most are monthly).

## Project structure

```
voter-registration-tracker/
├── sql/
│   ├── 01_schema.sql          # Tables, indexes
│   ├── 02_seed_states.sql     # states_ref lookup table (all 50 + DC)
│   ├── 03_views_and_rls.sql   # Views, stored function, RLS policies
│   └── 04_seed_initial_data.sql  # Bootstrap data (latest published figures)
├── scraper/
│   ├── main.py                # Orchestrator
│   ├── scrapers.py            # One scraper per state (30 total)
│   ├── base.py                # HTTP helpers, PDF/HTML utils
│   ├── models.py              # RegistrationSnapshot dataclass
│   ├── config.py              # Env config, Supabase client
│   └── requirements.txt
├── dashboard/
│   └── index.html             # Self-contained dashboard (D3 choropleth)
├── .github/
│   └── workflows/
│       └── scraper.yml        # Weekly cron + manual trigger
└── README.md
```

---

## Setup

### 1. Supabase

1. Create a new Supabase project at [supabase.com](https://supabase.com).
2. In the **SQL Editor**, run each file in order:
   - `sql/01_schema.sql`
   - `sql/02_seed_states.sql`
   - `sql/03_views_and_rls.sql`
   - `sql/04_seed_initial_data.sql`
3. Note your **Project URL** and both keys from **Settings → API**:
   - `anon` key → goes in `dashboard/index.html`
   - `service_role` key → goes in GitHub Secrets (never expose this)

### 2. Dashboard

Open `dashboard/index.html` and replace the two constants near the top:

```js
const SUPABASE_URL      = "https://YOUR_PROJECT_ID.supabase.co";
const SUPABASE_ANON_KEY = "YOUR_ANON_KEY";
```

The dashboard is a single static HTML file. Deploy to GitHub Pages, Netlify, Vercel, or any static host. No build step required.

**GitHub Pages quick deploy:**
- Push the repo to GitHub
- Go to Settings → Pages → Source → Deploy from a branch → `main` / `/dashboard`

### 3. Scraper

**Local test:**

```bash
cd scraper
pip install -r requirements.txt

# Create a .env file (never commit this)
echo "SUPABASE_URL=https://YOUR_PROJECT_ID.supabase.co" > .env
echo "SUPABASE_SERVICE_KEY=YOUR_SERVICE_ROLE_KEY" >> .env

# Test a single state without writing to DB
python main.py --states Florida --dry-run

# Run all states
python main.py
```

**GitHub Actions (automated):**

1. In your GitHub repo, go to **Settings → Secrets and variables → Actions**
2. Add two secrets:
   - `SUPABASE_URL` — your project URL
   - `SUPABASE_SERVICE_KEY` — the `service_role` key (not the anon key)
3. The workflow in `.github/workflows/scraper.yml` runs every Sunday at 06:00 UTC.
4. You can also trigger it manually from the **Actions** tab with optional state filtering.

---

## Data model

| Table / View | Purpose |
|---|---|
| `states_ref` | Static lookup: all 50 states + DC, source URLs, update frequency |
| `voter_registration` | Every scraper snapshot (append-only) |
| `registration_trend` | Computed directional trend per state |
| `scraper_run_log` | Run history with success/failure counts |
| `latest_registration` | View: most recent snapshot per state |
| `latest_trend` | View: most recent trend per state |
| `dashboard_view` | View: combined, single query for the frontend |
| `national_aggregate` | View: national totals and party split |
| `trend_series` | View: monthly historical series for charting |

Trend direction is computed by the `upsert_registration_snapshot` SQL function on every write. A shift < 0.5pp in the D−R lead margin is classified as `N` (stable); ≥ 0.5pp is `D` or `R` depending on direction. Magnitude buckets: `slight` (0.5–1pp), `moderate` (1–3pp), `strong` (3pp+).

---

## Scraper maintenance

State websites change their formats periodically. When a scraper breaks:

1. Run `python main.py --states "State Name" --dry-run` locally to see the error.
2. Inspect the state's current page/file format.
3. Update the relevant scraper function in `scrapers.py`.
4. For completely new formats, implement a custom function following the pattern of `scrape_florida()` or `scrape_pennsylvania()`.

The `_make_html_scraper()` factory handles ~22 states. The 8 custom scrapers handle CSV downloads (FL, NC, CO) and PDF tables (AZ, CA).

---

## Adding more data

The schema supports extensions without breaking existing queries:

- **County-level data**: Add a `county_registration` table with a `state_name` FK and county FIPS code.
- **Historical import**: Run `04_seed_initial_data.sql`-style inserts with older `scrape_timestamp` values.
- **Trend charts**: Query `trend_series` view, already grouped by state and month.

---

## Notes on the "30 states" figure

The 30 states that publish party registration data are concentrated in the Northeast and West, with fewer in the South and Midwest. Many large non-reporting states (TX, GA, VA, WI, MI, OH) use open primaries and do not register voters by party, so national totals from these 30 states skew more Democratic than the full electorate. The `national_aggregate` view notes this in the data — keep it in mind when interpreting the D lead figure.
