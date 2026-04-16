# Polling Repo — Claude Notes

## Project
Voter registration tracker. Scrapes 30 US states that publish party registration data, stores snapshots in Supabase, displays on a D3 choropleth dashboard.

## Repo structure
```
voter-registration-tracker/
├── scraper/          # Python scraper (run via GitHub Actions or locally)
├── dashboard/        # Single static HTML file (D3 + Supabase JS)
└── sql/              # Supabase schema, seeds, views, RLS
.github/workflows/
└── scraper.yml       # Weekly cron (Sundays 06:00 UTC) + manual trigger
```

## Supabase
- Project URL: `https://kycccxmbjqidwvyfpols.supabase.co`
- Anon key is hardcoded in `dashboard/index.html` (safe — public read only)
- Service role key is in GitHub Secrets (`SUPABASE_SERVICE_KEY`) — never commit it
- RLS: all tables are public-read, service role writes only
- Main function: `upsert_registration_snapshot()` — inserts snapshot + auto-computes trend

## Key tables / views
| Name | Purpose |
|---|---|
| `voter_registration` | Append-only snapshot per state per scrape |
| `registration_trend` | Directional trend (D/R/N) computed on each insert |
| `dashboard_view` | What the frontend queries — latest reg + trend joined |
| `scraper_run_log` | Run history |

## Scraper
- Entry point: `scraper/main.py`
- `--dry-run` flag scrapes but skips DB writes (useful for testing)
- `--states "Florida" "Pennsylvania"` to target specific states
- 30 states total: 8 custom scrapers (CSV/PDF), 22 via `_make_html_scraper()` factory
- 1.5s sleep between states to be polite to state servers
- Validation in `models.py`: percentages must sum to ~100%, totals within 2%

## Dashboard
- `dashboard/index.html` — fully self-contained, no build step
- 4 map modes: Party Lead, % Democrat, % Republican, % Independent
- Click a state → detail panel with bar chart + trend badge + delta since prior scrape
- Deploy to GitHub Pages: Settings → Pages → `main` branch, `/voter-registration-tracker/dashboard` folder

## When scraper breaks
State websites change formats. Debug flow:
1. `python main.py --states "State Name" --dry-run` to see the error
2. Inspect current state page format
3. Update the scraper function in `scrapers.py`
