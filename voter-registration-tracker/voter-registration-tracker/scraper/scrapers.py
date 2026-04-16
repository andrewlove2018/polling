"""
scraper/scrapers.py
One scraper function per state. Each returns a RegistrationSnapshot.

SCRAPER MAP at bottom registers all 30 states.

Implementation notes:
- Florida, Colorado, Nevada, North Carolina: CSV downloads — most reliable
- Arizona, California, Maine, Kansas: PDF tables
- Most others: HTML table parsing
- All use the shared base.py helpers
"""

import csv
import io
import re
from datetime import date, datetime
from typing import Optional

from base import (
    fetch_html, fetch_csv_text, fetch_pdf_tables, fetch_pdf_text,
    parse_int, parse_float, safe_pct, parse_month_year
)
from models import RegistrationSnapshot


# ── HELPER ────────────────────────────────────────────────────────────────────

def _snap(state, dem_t, rep_t, ind_t, other_t, pub_date, url) -> RegistrationSnapshot:
    """Build and validate a snapshot from raw totals."""
    total = dem_t + rep_t + ind_t + other_t
    snap = RegistrationSnapshot(
        state_name=state,
        dem_pct=safe_pct(dem_t, total),
        rep_pct=safe_pct(rep_t, total),
        ind_pct=safe_pct(ind_t, total),
        other_pct=safe_pct(other_t, total),
        dem_total=dem_t,
        rep_total=rep_t,
        ind_total=ind_t,
        other_total=other_t,
        total_registered=total,
        state_published_date=pub_date,
        source_url=url,
    )
    snap.validate()
    return snap


# ── FLORIDA ───────────────────────────────────────────────────────────────────
# Monthly CSV: columns include Party, VoterCount

def scrape_florida() -> RegistrationSnapshot:
    url = "https://dos.myflorida.com/media/708493/book.csv"
    # FL publishes a summary book CSV; party totals are in rows labeled
    # 'Republican', 'Democratic', 'No Party Affiliation', and 'Other'
    text = fetch_csv_text(url)
    reader = csv.DictReader(io.StringIO(text))
    totals = {"DEM": 0, "REP": 0, "NPA": 0, "OTH": 0}
    pub_date = None

    for row in reader:
        party = (row.get("Party") or row.get("PARTY", "")).strip().upper()
        count_str = row.get("Book", row.get("Total", "0"))
        count = parse_int(count_str)
        if "DEMOCRAT" in party or party == "DEM":
            totals["DEM"] += count
        elif "REPUBLICAN" in party or party == "REP":
            totals["REP"] += count
        elif "NO PARTY" in party or "NPA" in party or "UNAFFILIATED" in party:
            totals["NPA"] += count
        elif party not in ("PARTY", "", "TOTAL"):
            totals["OTH"] += count

        if pub_date is None:
            date_str = row.get("BookDate") or row.get("Date") or row.get("AsOf", "")
            if date_str:
                pub_date = parse_month_year(date_str)

    return _snap("Florida", totals["DEM"], totals["REP"], totals["NPA"], totals["OTH"],
                 pub_date, "https://dos.myflorida.com/elections/data-statistics/voter-registration-statistics/voter-registration-reports/")


# ── NORTH CAROLINA ────────────────────────────────────────────────────────────
# Monthly CSV snapshot available for download

def scrape_north_carolina() -> RegistrationSnapshot:
    url = "https://s3.amazonaws.com/dl.ncsbe.gov/data/ncvoter_Statewide.zip"
    # NC publishes a full voter file which is large. For summary stats, use their
    # stats page HTML instead.
    stats_url = "https://vt.ncsbe.gov/RegStat/"
    soup = fetch_html(stats_url)

    totals = {"DEM": 0, "REP": 0, "UNA": 0, "OTH": 0}
    pub_date = None

    # NC stats page has a summary table; look for party breakdown rows
    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
            if len(cells) < 2:
                continue
            label = cells[0].upper()
            if "DEMOCRAT" in label:
                totals["DEM"] = parse_int(cells[-1])
            elif "REPUBLICAN" in label:
                totals["REP"] = parse_int(cells[-1])
            elif "UNAFFILIATED" in label or "UNA" in label:
                totals["UNA"] = parse_int(cells[-1])
            elif "LIBERTARIAN" in label or "GREEN" in label or "OTHER" in label:
                totals["OTH"] += parse_int(cells[-1])

    # Try to find published date
    date_text = soup.get_text()
    m = re.search(r"as of\s+([A-Za-z]+ \d{1,2},?\s*\d{4})", date_text, re.IGNORECASE)
    if m:
        pub_date = parse_month_year(m.group(1))

    return _snap("North Carolina", totals["DEM"], totals["REP"], totals["UNA"], totals["OTH"],
                 pub_date, stats_url)


# ── PENNSYLVANIA ──────────────────────────────────────────────────────────────
# Monthly stats page, HTML table

def scrape_pennsylvania() -> RegistrationSnapshot:
    url = "https://www.vote.pa.gov/About-Elections/Pages/Voter-Registration-Statistics.aspx"
    soup = fetch_html(url)

    totals = {"DEM": 0, "REP": 0, "IND": 0, "OTH": 0}
    pub_date = None

    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = [td.get_text(strip=True).replace(",", "") for td in row.find_all(["td", "th"])]
            if len(cells) < 2:
                continue
            label = cells[0].upper()
            if "DEMOCRAT" in label:
                totals["DEM"] = parse_int(cells[-1])
            elif "REPUBLICAN" in label:
                totals["REP"] = parse_int(cells[-1])
            elif "NO AFFILIATION" in label or "NON-AFFILIATED" in label or "INDEPENDENT" in label:
                totals["IND"] = parse_int(cells[-1])
            elif "OTHER" in label or "MINOR" in label:
                totals["OTH"] = parse_int(cells[-1])

    text = soup.get_text()
    m = re.search(r"(?:as of|updated)\s+([A-Za-z]+ \d{4})", text, re.IGNORECASE)
    if m:
        pub_date = parse_month_year(m.group(1))

    return _snap("Pennsylvania", totals["DEM"], totals["REP"], totals["IND"], totals["OTH"],
                 pub_date, url)


# ── ARIZONA ───────────────────────────────────────────────────────────────────
# Monthly PDF report

def scrape_arizona() -> RegistrationSnapshot:
    index_url = "https://azsos.gov/elections/voter-registration-historical-registration-data"
    soup = fetch_html(index_url)

    # Find most recent PDF link
    pdf_url = None
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if ".pdf" in href.lower() and ("registration" in href.lower() or "reg" in href.lower()):
            pdf_url = href if href.startswith("http") else "https://azsos.gov" + href
            break

    if not pdf_url:
        raise RuntimeError("Arizona: could not find registration PDF link")

    tables = fetch_pdf_tables(pdf_url)
    totals = {"DEM": 0, "REP": 0, "IND": 0, "OTH": 0}

    for table in tables:
        for row in table:
            if not row or len(row) < 2:
                continue
            label = str(row[0] or "").upper()
            value_str = str(row[-1] or "0")
            if "DEMOCRAT" in label:
                totals["DEM"] = parse_int(value_str)
            elif "REPUBLICAN" in label:
                totals["REP"] = parse_int(value_str)
            elif "OTHER" == label.strip() or "NO PARTY" in label or "INDEPENDENT" in label:
                totals["IND"] = parse_int(value_str)
            elif "LIBERTARIAN" in label or "GREEN" in label:
                totals["OTH"] += parse_int(value_str)

    pub_date = date.today().replace(day=1)
    return _snap("Arizona", totals["DEM"], totals["REP"], totals["IND"], totals["OTH"],
                 pub_date, index_url)


# ── COLORADO ──────────────────────────────────────────────────────────────────
# Monthly CSV download

def scrape_colorado() -> RegistrationSnapshot:
    url = "https://www.sos.state.co.us/voter/pages/pub/sos/voter-statistics.xhtml"
    soup = fetch_html(url)

    # Find CSV download link
    csv_url = None
    for a in soup.find_all("a", href=True):
        if ".csv" in a["href"].lower():
            csv_url = a["href"] if a["href"].startswith("http") else "https://www.sos.state.co.us" + a["href"]
            break

    totals = {"DEM": 0, "REP": 0, "UNA": 0, "OTH": 0}
    pub_date = date.today().replace(day=1)

    if csv_url:
        text = fetch_csv_text(csv_url)
        reader = csv.reader(io.StringIO(text))
        for row in reader:
            if len(row) < 2:
                continue
            label = row[0].upper().strip()
            if "DEMOCRAT" in label:
                totals["DEM"] = parse_int(row[-1])
            elif "REPUBLICAN" in label:
                totals["REP"] = parse_int(row[-1])
            elif "UNAFFILIATED" in label or "UNA" in label:
                totals["UNA"] = parse_int(row[-1])
            elif label not in ("", "PARTY", "TOTAL"):
                totals["OTH"] += parse_int(row[-1])
    else:
        # Fall back to HTML table
        for table in soup.find_all("table"):
            for row in table.find_all("tr"):
                cells = [td.get_text(strip=True) for td in row.find_all(["td","th"])]
                if len(cells) < 2:
                    continue
                label = cells[0].upper()
                if "DEMOCRAT" in label:
                    totals["DEM"] = parse_int(cells[-1])
                elif "REPUBLICAN" in label:
                    totals["REP"] = parse_int(cells[-1])
                elif "UNAFFILIATED" in label:
                    totals["UNA"] = parse_int(cells[-1])
                elif cells[0] not in ("", "Party", "Total"):
                    totals["OTH"] += parse_int(cells[-1])

    return _snap("Colorado", totals["DEM"], totals["REP"], totals["UNA"], totals["OTH"],
                 pub_date, url)


# ── NEVADA ────────────────────────────────────────────────────────────────────

def scrape_nevada() -> RegistrationSnapshot:
    url = "https://nvsos.gov/sos/elections/voters/voter-registration-statistics"
    soup = fetch_html(url)

    totals = {"DEM": 0, "REP": 0, "IND": 0, "OTH": 0}
    pub_date = date.today().replace(day=1)

    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = [td.get_text(strip=True) for td in row.find_all(["td","th"])]
            if len(cells) < 2:
                continue
            label = cells[0].upper()
            if "DEMOCRAT" in label:
                totals["DEM"] = parse_int(cells[-1])
            elif "REPUBLICAN" in label:
                totals["REP"] = parse_int(cells[-1])
            elif "NON-PARTISAN" in label or "INDEPENDENT" in label or "NO PARTY" in label:
                totals["IND"] = parse_int(cells[-1])
            elif label not in ("", "PARTY", "TOTAL", "COUNTY"):
                totals["OTH"] += parse_int(cells[-1])

    return _snap("Nevada", totals["DEM"], totals["REP"], totals["IND"], totals["OTH"],
                 pub_date, url)


# ── NEW YORK ──────────────────────────────────────────────────────────────────

def scrape_new_york() -> RegistrationSnapshot:
    url = "https://www.elections.ny.gov/EnrollmentCounty.html"
    soup = fetch_html(url)

    totals = {"DEM": 0, "REP": 0, "BLK": 0, "OTH": 0}
    pub_date = date.today().replace(day=1)

    # NY has a statewide summary row; look for the TOTAL or STATEWIDE row
    tables = soup.find_all("table")
    for table in tables:
        rows = table.find_all("tr")
        headers = []
        for row in rows:
            cells = [td.get_text(strip=True) for td in row.find_all(["td","th"])]
            if not cells:
                continue
            if any("DEM" in c.upper() for c in cells):
                headers = [c.upper() for c in cells]
            elif headers and ("TOTAL" in cells[0].upper() or "STATE" in cells[0].upper()):
                for i, h in enumerate(headers):
                    if i >= len(cells):
                        break
                    if "DEM" in h:
                        totals["DEM"] = parse_int(cells[i])
                    elif "REP" in h:
                        totals["REP"] = parse_int(cells[i])
                    elif "BLANK" in h or "BLK" in h or "UNAFFILIATED" in h:
                        totals["BLK"] = parse_int(cells[i])
                    elif h not in ("", "COUNTY", "TOTAL", "GRAND"):
                        totals["OTH"] += parse_int(cells[i])
                break

    return _snap("New York", totals["DEM"], totals["REP"], totals["BLK"], totals["OTH"],
                 pub_date, url)


# ── CALIFORNIA ────────────────────────────────────────────────────────────────

def scrape_california() -> RegistrationSnapshot:
    url = "https://www.sos.ca.gov/elections/report-registration"
    soup = fetch_html(url)

    # Find link to most recent Report of Registration PDF/HTML
    report_url = None
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "report-registration" in href.lower() and href != url:
            report_url = href if href.startswith("http") else "https://www.sos.ca.gov" + href
            break

    totals = {"DEM": 0, "REP": 0, "NPP": 0, "OTH": 0}
    pub_date = date.today().replace(day=1)

    target_soup = fetch_html(report_url) if report_url else soup

    for table in target_soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = [td.get_text(strip=True) for td in row.find_all(["td","th"])]
            if len(cells) < 2:
                continue
            label = cells[0].upper()
            if "DEMOCRAT" in label:
                totals["DEM"] = parse_int(cells[-1])
            elif "REPUBLICAN" in label:
                totals["REP"] = parse_int(cells[-1])
            elif "NO PARTY PREFERENCE" in label or "NPP" in label:
                totals["NPP"] = parse_int(cells[-1])
            elif label not in ("", "PARTY", "TOTAL", "GRAND TOTAL"):
                totals["OTH"] += parse_int(cells[-1])

    return _snap("California", totals["DEM"], totals["REP"], totals["NPP"], totals["OTH"],
                 pub_date, url)


# ── GENERIC HTML SCRAPER FACTORY ──────────────────────────────────────────────
# Most state HTML pages follow the same pattern: a table with party names
# and totals. This factory generates scrapers for them.

def _make_html_scraper(state_name: str, url: str,
                       dem_keys: list, rep_keys: list,
                       ind_keys: list, other_keys: list = None):
    """
    Factory for states with a simple HTML table: party name → total.
    Keys are uppercase substrings matched against the label cell.
    """
    def scraper() -> RegistrationSnapshot:
        soup = fetch_html(url)
        totals = {"DEM": 0, "REP": 0, "IND": 0, "OTH": 0}
        pub_date = date.today().replace(day=1)

        skip = {"", "PARTY", "TOTAL", "GRAND TOTAL", "COUNTY", "DISTRICT"}

        for table in soup.find_all("table"):
            for row in table.find_all("tr"):
                cells = [td.get_text(strip=True) for td in row.find_all(["td","th"])]
                if len(cells) < 2:
                    continue
                label = cells[0].upper().strip()
                val = parse_int(cells[-1])
                if any(k in label for k in dem_keys):
                    totals["DEM"] += val
                elif any(k in label for k in rep_keys):
                    totals["REP"] += val
                elif any(k in label for k in ind_keys):
                    totals["IND"] += val
                elif other_keys and any(k in label for k in other_keys):
                    totals["OTH"] += val
                elif label not in skip and not label.startswith("TOTAL"):
                    pass  # silently ignore unrecognized rows

        # Try to find a date in page text
        text = soup.get_text()
        m = re.search(r"(?:as of|updated|effective)\s+([A-Za-z]+\s+\d{1,2},?\s*\d{4}|[A-Za-z]+\s+\d{4})",
                      text, re.IGNORECASE)
        if m:
            parsed = parse_month_year(m.group(1))
            if parsed:
                pub_date = parsed

        return _snap(state_name, totals["DEM"], totals["REP"], totals["IND"], totals["OTH"],
                     pub_date, url)

    scraper.__name__ = f"scrape_{state_name.lower().replace(' ', '_')}"
    return scraper


# ── SCRAPER REGISTRY ──────────────────────────────────────────────────────────
# Map state name → scraper function

SCRAPERS = {
    # Custom scrapers (complex formats)
    "Florida":          scrape_florida,
    "North Carolina":   scrape_north_carolina,
    "Pennsylvania":     scrape_pennsylvania,
    "Arizona":          scrape_arizona,
    "Colorado":         scrape_colorado,
    "Nevada":           scrape_nevada,
    "New York":         scrape_new_york,
    "California":       scrape_california,

    # HTML table scrapers (generated)
    "Alaska": _make_html_scraper(
        "Alaska",
        "https://elections.alaska.gov/statistics/index.php",
        dem_keys=["DEMOCRAT"],
        rep_keys=["REPUBLICAN"],
        ind_keys=["UNDECLARED", "NONPARTISAN", "INDEPENDENT", "NO PARTY"],
    ),
    "Connecticut": _make_html_scraper(
        "Connecticut",
        "https://portal.ct.gov/SOTS/Election-Services/Registration-and-Enrollment-Stats/Registration-and-Enrollment-Statistics",
        dem_keys=["DEMOCRAT"],
        rep_keys=["REPUBLICAN"],
        ind_keys=["UNAFFILIATED"],
    ),
    "Delaware": _make_html_scraper(
        "Delaware",
        "https://elections.delaware.gov/services/voter/voterregstats.shtml",
        dem_keys=["DEMOCRAT"],
        rep_keys=["REPUBLICAN"],
        ind_keys=["INDEPENDENT", "UNAFFILIATED", "NO PARTY"],
    ),
    "Idaho": _make_html_scraper(
        "Idaho",
        "https://sos.idaho.gov/elections-division/voter-registration-statistics/",
        dem_keys=["DEMOCRAT"],
        rep_keys=["REPUBLICAN"],
        ind_keys=["UNAFFILIATED", "INDEPENDENT", "NO PARTY"],
    ),
    "Iowa": _make_html_scraper(
        "Iowa",
        "https://sos.iowa.gov/elections/voterreg/regstat.html",
        dem_keys=["DEMOCRAT"],
        rep_keys=["REPUBLICAN"],
        ind_keys=["NO PARTY", "OTHER", "UNAFFILIATED"],
    ),
    "Kansas": _make_html_scraper(
        "Kansas",
        "https://sos.ks.gov/elections/voter-registration.html",
        dem_keys=["DEMOCRAT"],
        rep_keys=["REPUBLICAN"],
        ind_keys=["LIBERTARIAN", "UNAFFILIATED", "INDEPENDENT"],
        other_keys=["OTHER"],
    ),
    "Kentucky": _make_html_scraper(
        "Kentucky",
        "https://elect.ky.gov/Statistics/Pages/voterstatistics.aspx",
        dem_keys=["DEMOCRAT"],
        rep_keys=["REPUBLICAN"],
        ind_keys=["OTHER", "NO PARTY", "INDEPENDENT"],
    ),
    "Louisiana": _make_html_scraper(
        "Louisiana",
        "https://www.sos.la.gov/ElectionsAndVoting/RegisterToVote/ReviewVoterRegistrationInformation/Pages/default.aspx",
        dem_keys=["DEMOCRAT"],
        rep_keys=["REPUBLICAN"],
        ind_keys=["OTHER", "NO PARTY"],
    ),
    "Maine": _make_html_scraper(
        "Maine",
        "https://www.maine.gov/sos/cec/elec/data/index.html",
        dem_keys=["DEMOCRAT"],
        rep_keys=["REPUBLICAN"],
        ind_keys=["UNENROLLED", "INDEPENDENT", "GREEN", "NO PARTY"],
    ),
    "Maryland": _make_html_scraper(
        "Maryland",
        "https://elections.maryland.gov/voter_registration/stats.html",
        dem_keys=["DEMOCRAT"],
        rep_keys=["REPUBLICAN"],
        ind_keys=["UNAFFILIATED", "INDEPENDENT", "NO PARTY"],
    ),
    "Massachusetts": _make_html_scraper(
        "Massachusetts",
        "https://www.sec.state.ma.us/ele/eleregistrationstats/registrationstats.htm",
        dem_keys=["DEMOCRAT"],
        rep_keys=["REPUBLICAN"],
        ind_keys=["UNENROLLED", "INDEPENDENT", "NO PARTY"],
    ),
    "Nebraska": _make_html_scraper(
        "Nebraska",
        "https://sos.nebraska.gov/elections/voter-registration-statistics",
        dem_keys=["DEMOCRAT"],
        rep_keys=["REPUBLICAN"],
        ind_keys=["INDEPENDENT", "NO PARTY", "NONPARTISAN"],
        other_keys=["OTHER", "LIBERTARIAN"],
    ),
    "New Hampshire": _make_html_scraper(
        "New Hampshire",
        "https://www.sos.nh.gov/elections/voters/voter-registration-statistics",
        dem_keys=["DEMOCRAT"],
        rep_keys=["REPUBLICAN"],
        ind_keys=["UNDECLARED", "INDEPENDENT", "NO PARTY"],
    ),
    "New Jersey": _make_html_scraper(
        "New Jersey",
        "https://www.state.nj.us/state/elections/voter-registration-information.shtml",
        dem_keys=["DEMOCRAT"],
        rep_keys=["REPUBLICAN"],
        ind_keys=["UNAFFILIATED", "INDEPENDENT", "NO PARTY"],
    ),
    "New Mexico": _make_html_scraper(
        "New Mexico",
        "https://www.sos.nm.gov/voting-and-elections/voter-information-portal/voter-registration-statistics/",
        dem_keys=["DEMOCRAT"],
        rep_keys=["REPUBLICAN"],
        ind_keys=["DECLINED", "NO PARTY", "INDEPENDENT", "LIBERTARIAN"],
    ),
    "Oklahoma": _make_html_scraper(
        "Oklahoma",
        "https://www.ok.gov/elections/Voter_Registration/Voter_Registration_Statistics/index.html",
        dem_keys=["DEMOCRAT"],
        rep_keys=["REPUBLICAN"],
        ind_keys=["INDEPENDENT", "NO PARTY", "LIBERTARIAN"],
        other_keys=["OTHER"],
    ),
    "Oregon": _make_html_scraper(
        "Oregon",
        "https://sos.oregon.gov/elections/Pages/electionhistory.aspx",
        dem_keys=["DEMOCRAT"],
        rep_keys=["REPUBLICAN"],
        ind_keys=["INDEPENDENT", "NAV", "NO PARTY", "NONAFFILIATED"],
        other_keys=["OTHER", "PACIFIC GREEN", "PROGRESSIVE", "LIBERTARIAN"],
    ),
    "Rhode Island": _make_html_scraper(
        "Rhode Island",
        "https://vote.sos.ri.gov/Voter/VoterRegistrationStats",
        dem_keys=["DEMOCRAT"],
        rep_keys=["REPUBLICAN"],
        ind_keys=["UNAFFILIATED", "INDEPENDENT", "NO PARTY"],
    ),
    "South Dakota": _make_html_scraper(
        "South Dakota",
        "https://sdsos.gov/elections-voting/voting/voter-registration-totals/default.aspx",
        dem_keys=["DEMOCRAT"],
        rep_keys=["REPUBLICAN"],
        ind_keys=["INDEPENDENT", "NO LABEL", "NO PARTY", "LIBERTARIAN"],
        other_keys=["OTHER"],
    ),
    "Utah": _make_html_scraper(
        "Utah",
        "https://elections.utah.gov/utah-voter-information",
        dem_keys=["DEMOCRAT"],
        rep_keys=["REPUBLICAN"],
        ind_keys=["UNAFFILIATED", "INDEPENDENT", "NO PARTY"],
        other_keys=["OTHER", "LIBERTARIAN", "CONSTITUTION"],
    ),
    "West Virginia": _make_html_scraper(
        "West Virginia",
        "https://sos.wv.gov/elections/Pages/VoterRegistrationStats.aspx",
        dem_keys=["DEMOCRAT"],
        rep_keys=["REPUBLICAN"],
        ind_keys=["INDEPENDENT", "NO PARTY", "LIBERTARIAN"],
        other_keys=["OTHER"],
    ),
    "Wyoming": _make_html_scraper(
        "Wyoming",
        "https://sos.wyo.gov/elections/registration-statistics.aspx",
        dem_keys=["DEMOCRAT"],
        rep_keys=["REPUBLICAN"],
        ind_keys=["INDEPENDENT", "NO PARTY", "LIBERTARIAN"],
        other_keys=["OTHER", "CONSTITUTION"],
    ),
    "District of Columbia": _make_html_scraper(
        "District of Columbia",
        "https://www.dcboe.org/Voters/Register-To-Vote/Voter-Registration-Statistics",
        dem_keys=["DEMOCRAT"],
        rep_keys=["REPUBLICAN"],
        ind_keys=["INDEPENDENT", "NO PARTY", "STATEHOOD GREEN"],
        other_keys=["OTHER", "LIBERTARIAN"],
    ),
}
