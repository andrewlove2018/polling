#!/usr/bin/env python3
"""
check_urls.py  —  Probe all state voter-registration URLs.
Run this locally: python check_urls.py
Paste the output back to Claude to fix the scrapers.
"""

import requests
import time

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# (state, label, url)
URLS_TO_CHECK = [
    # ── FLORIDA ──────────────────────────────────────────────────────────────
    ("Florida", "old CSV",        "https://dos.myflorida.com/media/708493/book.csv"),
    ("Florida", "new domain CSV", "https://dos.fl.gov/media/708493/book.csv"),
    ("Florida", "stats page",     "https://dos.fl.gov/elections/data-statistics/voter-registration-statistics/voter-registration-reports/"),
    ("Florida", "stats page old", "https://dos.myflorida.com/elections/data-statistics/voter-registration-statistics/voter-registration-reports/"),

    # ── ARIZONA ──────────────────────────────────────────────────────────────
    ("Arizona", "old",     "https://azsos.gov/elections/voter-registration-historical-registration-data"),
    ("Arizona", "cand1",   "https://azsos.gov/elections/voter-registration/voter-registration-reports"),
    ("Arizona", "cand2",   "https://azsos.gov/elections/historical-election-data"),
    ("Arizona", "cand3",   "https://azsos.gov/elections/voter-registration"),

    # ── IDAHO ────────────────────────────────────────────────────────────────
    ("Idaho", "old",   "https://sos.idaho.gov/elections-division/voter-registration-statistics/"),
    ("Idaho", "cand1", "https://sos.idaho.gov/elections/voter-registration/"),
    ("Idaho", "cand2", "https://voteidaho.gov/voter-registration-statistics/"),
    ("Idaho", "cand3", "https://sos.idaho.gov/elections-division/voter-registration/"),

    # ── KENTUCKY ─────────────────────────────────────────────────────────────
    ("Kentucky", "old",   "https://elect.ky.gov/Statistics/Pages/voterstatistics.aspx"),
    ("Kentucky", "cand1", "https://elect.ky.gov/statistics/voter-statistics"),
    ("Kentucky", "cand2", "https://elect.ky.gov/voter-statistics"),
    ("Kentucky", "cand3", "https://elect.ky.gov/resources/statistics"),

    # ── LOUISIANA ────────────────────────────────────────────────────────────
    ("Louisiana", "old",   "https://www.sos.la.gov/ElectionsAndVoting/RegisterToVote/ReviewVoterRegistrationInformation/Pages/default.aspx"),
    ("Louisiana", "cand1", "https://www.sos.la.gov/ElectionsAndVoting/Pages/default.aspx"),
    ("Louisiana", "cand2", "https://www.sos.la.gov/ElectionsAndVoting/VoterInformation/Pages/default.aspx"),
    ("Louisiana", "cand3", "https://sos.la.gov/elections/voter-registration/"),

    # ── NEW JERSEY ───────────────────────────────────────────────────────────
    ("New Jersey", "old",   "https://www.state.nj.us/state/elections/voter-registration-information.shtml"),
    ("New Jersey", "cand1", "https://www.nj.gov/state/elections/voter-registration-information.shtml"),
    ("New Jersey", "cand2", "https://nj.gov/state/elections/voter-registration-information.shtml"),
    ("New Jersey", "cand3", "https://www.state.nj.us/state/elections/results/pdf/"),

    # ── UTAH ─────────────────────────────────────────────────────────────────
    ("Utah", "old",   "https://elections.utah.gov/utah-voter-information"),
    ("Utah", "cand1", "https://elections.utah.gov/voter-registration-statistics"),
    ("Utah", "cand2", "https://elections.utah.gov/data-and-statistics/voter-registration-statistics"),
    ("Utah", "cand3", "https://elections.utah.gov/voter-statistics"),

    # ── WEST VIRGINIA ────────────────────────────────────────────────────────
    ("West Virginia", "old",   "https://sos.wv.gov/elections/Pages/VoterRegistrationStats.aspx"),
    ("West Virginia", "cand1", "https://sos.wv.gov/elections/voter-registration/"),
    ("West Virginia", "cand2", "https://sos.wv.gov/elections/pages/voterregistrationstats.aspx"),
    ("West Virginia", "cand3", "https://apps.sos.wv.gov/elections/voterregistrationstats"),

    # ── WYOMING ──────────────────────────────────────────────────────────────
    ("Wyoming", "old",   "https://sos.wyo.gov/elections/registration-statistics.aspx"),
    ("Wyoming", "cand1", "https://sos.wyo.gov/elections/voter-registration-statistics/"),
    ("Wyoming", "cand2", "https://sos.wyo.gov/elections/registration/"),
    ("Wyoming", "cand3", "https://sos.wyo.gov/elections/"),

    # ── DISTRICT OF COLUMBIA ─────────────────────────────────────────────────
    ("DC", "old",   "https://www.dcboe.org/Voters/Register-To-Vote/Voter-Registration-Statistics"),
    ("DC", "cand1", "https://dcboe.org/election-data/voter-registration-statistics"),
    ("DC", "cand2", "https://www.dcboe.org/election-data/voter-registration-statistics"),
    ("DC", "cand3", "https://www.dcboe.org/voters/register-to-vote/voter-registration-statistics"),

    # ── 403 STATES (check if browser UA fixes it) ────────────────────────────
    ("Colorado",      "old",   "https://www.sos.state.co.us/voter/pages/pub/sos/voter-statistics.xhtml"),
    ("Colorado",      "cand1", "https://www.coloradosos.gov/voter/pages/pub/sos/voter-statistics.xhtml"),
    ("Colorado",      "cand2", "https://www.sos.state.co.us/voter/pages/pub/sos/VoterRegistrationStatistics.xhtml"),
    ("Nevada",        "old",   "https://nvsos.gov/sos/elections/voters/voter-registration-statistics"),
    ("Nevada",        "cand1", "https://www.nvsos.gov/sos/elections/voters/voter-registration-statistics"),
    ("New York",      "old",   "https://www.elections.ny.gov/EnrollmentCounty.html"),
    ("New York",      "cand1", "https://elections.ny.gov/EnrollmentCounty.html"),
    ("Delaware",      "old",   "https://elections.delaware.gov/services/voter/voterregstats.shtml"),
    ("Delaware",      "cand1", "https://elections.delaware.gov/voter-registration/voter-statistics/"),
    ("Iowa",          "old",   "https://sos.iowa.gov/elections/voterreg/regstat.html"),
    ("Iowa",          "cand1", "https://sos.iowa.gov/elections/voter-registration/"),
    ("New Hampshire", "old",   "https://www.sos.nh.gov/elections/voters/voter-registration-statistics"),
    ("New Hampshire", "cand1", "https://sos.nh.gov/elections/voters/voter-registration-statistics"),
    ("Rhode Island",  "old",   "https://vote.sos.ri.gov/Voter/VoterRegistrationStats"),
    ("Rhode Island",  "cand1", "https://www.sos.ri.gov/divisions/elections/data/voter-statistics"),

    # ── 0% SUM STATES (page loads but parsing fails) ──────────────────────────
    ("North Carolina",  "current", "https://vt.ncsbe.gov/RegStat/"),
    ("Pennsylvania",    "current", "https://www.vote.pa.gov/About-Elections/Pages/Voter-Registration-Statistics.aspx"),
    ("California",      "current", "https://www.sos.ca.gov/elections/report-registration"),
    ("Connecticut",     "current", "https://portal.ct.gov/SOTS/Election-Services/Registration-and-Enrollment-Stats/Registration-and-Enrollment-Statistics"),
    ("Kansas",          "current", "https://sos.ks.gov/elections/voter-registration.html"),
    ("Maine",           "current", "https://www.maine.gov/sos/cec/elec/data/index.html"),
    ("Maryland",        "current", "https://elections.maryland.gov/voter_registration/stats.html"),
    ("Massachusetts",   "current", "https://www.sec.state.ma.us/ele/eleregistrationstats/registrationstats.htm"),
    ("New Mexico",      "current", "https://www.sos.nm.gov/voting-and-elections/voter-information-portal/voter-registration-statistics/"),
    ("Oklahoma",        "current", "https://www.ok.gov/elections/Voter_Registration/Voter_Registration_Statistics/index.html"),
    ("Oregon",          "current", "https://sos.oregon.gov/elections/Pages/electionhistory.aspx"),
    ("South Dakota",    "current", "https://sdsos.gov/elections-voting/voting/voter-registration-totals/default.aspx"),

    # ── ALASKA SSL ───────────────────────────────────────────────────────────
    ("Alaska", "old",   "https://elections.alaska.gov/statistics/index.php"),
    ("Alaska", "cand1", "https://elections.alaska.gov/statistics/"),
]


def check(state, label, url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        body = r.text.lower()
        has_dem = "democrat" in body or "democratic" in body
        has_rep = "republican" in body
        final_url = r.url if r.url != url else ""
        redirect_note = f" → {final_url}" if final_url else ""
        party_note = ""
        if has_dem and has_rep:
            party_note = " ✓ HAS D+R DATA"
        elif has_dem or has_rep:
            party_note = " ~ partial party data"
        print(f"  [{r.status_code}]{party_note} {label}{redirect_note}")
        return r.status_code, has_dem and has_rep, r.url
    except Exception as e:
        print(f"  [ERR] {label}: {e}")
        return 0, False, ""


current_state = None
for state, label, url in URLS_TO_CHECK:
    if state != current_state:
        print(f"\n{'─'*60}")
        print(f"  {state.upper()}")
        current_state = state
    check(state, label, url)
    time.sleep(0.5)

print("\nDone.")
