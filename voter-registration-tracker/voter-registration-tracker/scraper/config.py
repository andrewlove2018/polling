"""
scraper/config.py
Environment config and shared Supabase client factory.
"""

import os
from supabase import create_client, Client

SCRAPER_VERSION = "1.0.0"

# Load from environment (set in .env or GitHub Actions secrets)
SUPABASE_URL         = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]  # NOT the anon key


def get_supabase_client() -> Client:
    """Return a Supabase client using the service role key.
    The service key bypasses RLS so the scraper can write."""
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


# HTTP request defaults used by all scrapers
REQUEST_TIMEOUT  = 30       # seconds
REQUEST_HEADERS  = {
    "User-Agent": (
        "VoterRegistrationTracker/1.0 "
        "(public data aggregator; contact via GitHub issues)"
    )
}
MAX_RETRIES      = 3
RETRY_BACKOFF    = 2.0      # seconds, doubles each retry
