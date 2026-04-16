#!/usr/bin/env python3
"""
voter_registration_tracker / scraper / main.py

Orchestrates all state scrapers, writes results to Supabase,
and logs each run. Run on a cron schedule (weekly recommended).

Usage:
    python main.py                    # scrape all states
    python main.py --states FL PA NC  # scrape specific states
    python main.py --dry-run          # scrape but don't write to DB
"""

import argparse
import time
import traceback
from datetime import datetime, timezone
from typing import Optional

from config import SCRAPER_VERSION, get_supabase_client
from models import RegistrationSnapshot
from scrapers import SCRAPERS


def run_scraper(
    state_name: str,
    dry_run: bool = False,
) -> Optional[RegistrationSnapshot]:
    """Run a single state scraper. Returns snapshot or None on failure."""
    scraper_fn = SCRAPERS.get(state_name)
    if not scraper_fn:
        print(f"  [SKIP] No scraper registered for {state_name}")
        return None

    try:
        snapshot = scraper_fn()
        if dry_run:
            print(f"  [DRY] {state_name}: D={snapshot.dem_pct}% R={snapshot.rep_pct}% I={snapshot.ind_pct}%  total={snapshot.total_registered:,}")
        return snapshot
    except Exception as e:
        print(f"  [FAIL] {state_name}: {e}")
        traceback.print_exc()
        return None


def write_snapshot(supabase, snapshot: RegistrationSnapshot) -> Optional[str]:
    """Call the Supabase upsert function and return the new row ID."""
    result = supabase.rpc("upsert_registration_snapshot", {
        "p_state_name":           snapshot.state_name,
        "p_dem_pct":              snapshot.dem_pct,
        "p_rep_pct":              snapshot.rep_pct,
        "p_ind_pct":              snapshot.ind_pct,
        "p_other_pct":            snapshot.other_pct,
        "p_dem_total":            snapshot.dem_total,
        "p_rep_total":            snapshot.rep_total,
        "p_ind_total":            snapshot.ind_total,
        "p_other_total":          snapshot.other_total,
        "p_total_registered":     snapshot.total_registered,
        "p_state_published_date": snapshot.state_published_date.isoformat() if snapshot.state_published_date else None,
        "p_source_url":           snapshot.source_url,
        "p_scraper_version":      SCRAPER_VERSION,
    }).execute()
    return result.data


def main():
    parser = argparse.ArgumentParser(description="Voter registration scraper")
    parser.add_argument("--states", nargs="+", help="Limit to specific state names")
    parser.add_argument("--dry-run", action="store_true", help="Scrape but skip DB writes")
    args = parser.parse_args()

    states_to_run = args.states if args.states else list(SCRAPERS.keys())
    supabase = None if args.dry_run else get_supabase_client()

    print(f"\n{'='*60}")
    print(f"Voter Registration Scraper v{SCRAPER_VERSION}")
    print(f"Started:  {datetime.now(timezone.utc).isoformat()}")
    print(f"States:   {len(states_to_run)}")
    print(f"Dry run:  {args.dry_run}")
    print(f"{'='*60}\n")

    run_start = time.time()
    succeeded, failed, failed_names = 0, 0, []

    for state in states_to_run:
        print(f"→ {state}")
        snapshot = run_scraper(state, dry_run=args.dry_run)

        if snapshot is None:
            failed += 1
            failed_names.append(state)
            continue

        if not args.dry_run:
            try:
                new_id = write_snapshot(supabase, snapshot)
                print(f"  [OK] {state} → id={new_id}")
                succeeded += 1
            except Exception as e:
                print(f"  [DB FAIL] {state}: {e}")
                failed += 1
                failed_names.append(state)
        else:
            succeeded += 1

        # Be polite to state servers
        time.sleep(1.5)

    run_duration = round(time.time() - run_start, 2)

    print(f"\n{'='*60}")
    print(f"Done. Succeeded: {succeeded}  Failed: {failed}  Duration: {run_duration}s")
    if failed_names:
        print(f"Failed states: {', '.join(failed_names)}")
    print(f"{'='*60}\n")

    # Log the run to Supabase
    if not args.dry_run and supabase:
        try:
            supabase.table("scraper_run_log").insert({
                "states_attempted": len(states_to_run),
                "states_succeeded": succeeded,
                "states_failed":    failed,
                "failed_states":    failed_names,
                "run_duration_sec": run_duration,
                "scraper_version":  SCRAPER_VERSION,
            }).execute()
        except Exception as e:
            print(f"Warning: could not write run log: {e}")


if __name__ == "__main__":
    main()
