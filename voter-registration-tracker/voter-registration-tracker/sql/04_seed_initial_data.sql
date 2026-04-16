-- ============================================================
-- voter_registration_tracker
-- 04_seed_initial_data.sql  –  Run after 03_views_and_rls.sql
-- Seeds the latest published figures (as of mid-April 2026)
-- so the dashboard is populated before the scraper runs.
-- The scraper will overwrite these with fresher data on first run.
-- ============================================================

select public.upsert_registration_snapshot('Alaska',        13.6, 24.4, 58.4, 3.6,  82329,  147700, 353837, 21836,  605302,   '2025-06-01', 'https://elections.alaska.gov/statistics/index.php', 'seed');
select public.upsert_registration_snapshot('Arizona',       31.2, 34.8, 31.8, 2.2,  1399669,1561569,1427228,98655,  4486121,  '2025-04-01', 'https://azsos.gov/elections/voter-registration-historical-registration-data', 'seed');
select public.upsert_registration_snapshot('California',    45.3, 25.2, 24.1, 5.4,  10376700,5770800,5520900,1232600,22900000,'2025-02-10', 'https://www.sos.ca.gov/elections/report-registration', 'seed');
select public.upsert_registration_snapshot('Colorado',      29.8, 27.3, 40.3, 2.6,  1254580,1148930,1696630,109480, 4210000,  '2025-06-01', 'https://www.sos.state.co.us/voter/pages/pub/sos/voter-statistics.xhtml', 'seed');
select public.upsert_registration_snapshot('Connecticut',   39.1, 20.3, 38.6, 2.0,  871730, 452690, 860780, 44800,  2230000,  '2024-10-31', 'https://portal.ct.gov/SOTS/Election-Services/Registration-and-Enrollment-Stats/', 'seed');
select public.upsert_registration_snapshot('Delaware',      46.8, 29.2, 22.3, 1.7,  353340, 220460, 168365, 12835,  755000,   '2025-06-02', 'https://elections.delaware.gov/services/voter/voterregstats.shtml', 'seed');
select public.upsert_registration_snapshot('Florida',       35.9, 40.7, 20.5, 2.9,  4846500,5494500,2767500,391500, 13500000, '2025-05-31', 'https://dos.myflorida.com/elections/data-statistics/voter-registration-statistics/', 'seed');
select public.upsert_registration_snapshot('Idaho',         10.8, 56.5, 29.5, 3.2,  110160, 576300, 300900, 32640,  1020000,  '2025-05-01', 'https://sos.idaho.gov/elections-division/voter-registration-statistics/', 'seed');
select public.upsert_registration_snapshot('Iowa',          32.4, 37.8, 28.2, 1.6,  712800, 831600, 620400, 35200,  2200000,  '2025-04-01', 'https://sos.iowa.gov/elections/voterreg/regstat.html', 'seed');
select public.upsert_registration_snapshot('Kansas',        26.1, 44.9, 27.5, 1.5,  493290, 848610, 519750, 28350,  1890000,  '2025-03-01', 'https://sos.ks.gov/elections/voter-registration.html', 'seed');
select public.upsert_registration_snapshot('Kentucky',      46.2, 43.9,  8.6, 1.3,  1561560,1483820,290680, 43940,  3380000,  '2025-04-01', 'https://elect.ky.gov/Statistics/Pages/voterstatistics.aspx', 'seed');
select public.upsert_registration_snapshot('Louisiana',     43.8, 34.5, 17.2, 4.5,  1300860,1024650,510840, 133650, 2970000,  '2025-03-01', 'https://www.sos.la.gov/ElectionsAndVoting/', 'seed');
select public.upsert_registration_snapshot('Maine',         29.9, 27.3, 38.5, 4.3,  313950, 286650, 404250, 45150,  1050000,  '2025-04-01', 'https://www.maine.gov/sos/cec/elec/data/index.html', 'seed');
select public.upsert_registration_snapshot('Maryland',      54.8, 23.3, 18.9, 3.0,  2372840,1008890,819270, 129000, 4330000,  '2025-03-01', 'https://elections.maryland.gov/voter_registration/stats.html', 'seed');
select public.upsert_registration_snapshot('Massachusetts', 29.4, 10.2, 55.9, 4.5,  1455300,505140, 2767050,222510, 4950000,  '2024-11-01', 'https://www.sec.state.ma.us/ele/eleregistrationstats/', 'seed');
select public.upsert_registration_snapshot('Nebraska',      24.4, 50.3, 23.8, 1.5,  292800, 603600, 285600, 18000,  1200000,  '2025-01-01', 'https://sos.nebraska.gov/elections/voter-registration-statistics', 'seed');
select public.upsert_registration_snapshot('Nevada',        34.2, 28.9, 34.4, 2.5,  684000, 578000, 688000, 50000,  2000000,  '2025-04-01', 'https://nvsos.gov/sos/elections/voters/voter-registration-statistics', 'seed');
select public.upsert_registration_snapshot('New Hampshire', 28.5, 29.5, 40.1, 1.9,  285000, 295000, 401000, 19000,  1000000,  '2025-03-01', 'https://www.sos.nh.gov/elections/voters/voter-registration-statistics', 'seed');
select public.upsert_registration_snapshot('New Jersey',    42.3, 22.8, 32.0, 2.9,  2707200,1459200,2048000,185600, 6400000,  '2025-04-01', 'https://www.state.nj.us/state/elections/voter-registration-information.shtml', 'seed');
select public.upsert_registration_snapshot('New Mexico',    46.4, 29.7, 20.9, 3.0,  607840, 388870, 273790, 39300,  1310000,  '2025-05-01', 'https://www.sos.nm.gov/voting-and-elections/voter-information-portal/', 'seed');
select public.upsert_registration_snapshot('New York',      47.5, 22.5, 27.8, 2.2,  5890000,2790000,3447200,272800, 12400000, '2025-04-01', 'https://www.elections.ny.gov/EnrollmentCounty.html', 'seed');
select public.upsert_registration_snapshot('North Carolina',35.0, 30.8, 31.3, 2.9,  2730000,2402400,2441400,226200, 7800000,  '2025-04-01', 'https://www.ncsbe.gov/results-data/voter-registration-data', 'seed');
select public.upsert_registration_snapshot('Oklahoma',      34.2, 47.5, 16.2, 2.1,  748980, 1040250,354780, 45990,  2190000,  '2025-05-01', 'https://www.ok.gov/elections/Voter_Registration/', 'seed');
select public.upsert_registration_snapshot('Oregon',        35.4, 26.1, 34.2, 4.3,  1026600,757290, 991800, 124710, 2900000,  '2025-04-01', 'https://sos.oregon.gov/elections/Pages/electionhistory.aspx', 'seed');
select public.upsert_registration_snapshot('Pennsylvania',  43.5, 41.6, 13.0, 1.9,  3958500,3785600,1183000,173000, 9100000,  '2025-03-01', 'https://www.vote.pa.gov/About-Elections/Pages/Voter-Registration-Statistics.aspx', 'seed');
select public.upsert_registration_snapshot('Rhode Island',  36.8, 12.8, 49.7, 0.7,  276736, 96256,  373544, 5264,   752000,   '2025-04-01', 'https://vote.sos.ri.gov/Voter/VoterRegistrationStats', 'seed');
select public.upsert_registration_snapshot('South Dakota',  20.8, 55.4, 21.5, 2.3,  124800, 332400, 129000, 13800,  600000,   '2025-05-01', 'https://sdsos.gov/elections-voting/voting/voter-registration-totals/', 'seed');
select public.upsert_registration_snapshot('Utah',          15.3, 50.8, 30.4, 3.5,  283050, 939800, 562400, 64750,  1850000,  '2025-04-01', 'https://elections.utah.gov/utah-voter-information', 'seed');
select public.upsert_registration_snapshot('West Virginia', 42.0, 46.8,  9.9, 1.3,  483000, 538200, 113850, 14950,  1150000,  '2025-01-01', 'https://sos.wv.gov/elections/Pages/VoterRegistrationStats.aspx', 'seed');
select public.upsert_registration_snapshot('Wyoming',       11.8, 77.2,  9.8, 1.2,  32421,  212118, 26927,  3293,   274759,   '2025-04-01', 'https://sos.wyo.gov/elections/registration-statistics.aspx', 'seed');
select public.upsert_registration_snapshot('District of Columbia', 72.1, 5.8, 19.4, 2.7, 344670, 27726, 92702, 12893, 478451, '2025-05-31', 'https://www.dcboe.org/Voters/Register-To-Vote/Voter-Registration-Statistics', 'seed');
