-- ============================================================
-- voter_registration_tracker
-- 02_seed_states.sql  –  Run after 01_schema.sql
-- ============================================================

insert into public.states_ref
  (state_name, abbreviation, fips_code, publishes_party, source_url, source_format, update_frequency, notes)
values
  -- ── STATES THAT PUBLISH PARTY DATA ────────────────────────
  ('Alaska',         'AK', '02', true,
   'https://elections.alaska.gov/statistics/index.php',
   'html', 'monthly', 'Voters Count by Party and Precinct'),

  ('Arizona',        'AZ', '04', true,
   'https://azsos.gov/elections/voter-registration-historical-registration-data',
   'pdf', 'monthly', 'State of Arizona Registration Report'),

  ('California',     'CA', '06', true,
   'https://www.sos.ca.gov/elections/report-registration',
   'pdf', 'quarterly', 'Report of Registration – active voters only'),

  ('Colorado',       'CO', '08', true,
   'https://www.sos.state.co.us/voter/pages/pub/sos/voter-statistics.xhtml',
   'csv', 'monthly', 'Voter Registration Statistics – downloadable CSV'),

  ('Connecticut',    'CT', '09', true,
   'https://portal.ct.gov/SOTS/Election-Services/Registration-and-Enrollment-Stats/Registration-and-Enrollment-Statistics',
   'html', 'annual', 'Registration and Party Enrollment Statistics'),

  ('Delaware',       'DE', '10', true,
   'https://elections.delaware.gov/services/voter/voterregstats.shtml',
   'html', 'monthly', 'Voter Registration Totals By Political Party'),

  ('Florida',        'FL', '12', true,
   'https://dos.myflorida.com/elections/data-statistics/voter-registration-statistics/voter-registration-reports/',
   'csv', 'monthly', 'Voter Registration by Party Affiliation – monthly CSV'),

  ('Idaho',          'ID', '16', true,
   'https://sos.idaho.gov/elections-division/voter-registration-statistics/',
   'html', 'monthly', NULL),

  ('Iowa',           'IA', '19', true,
   'https://sos.iowa.gov/elections/voterreg/regstat.html',
   'html', 'monthly', NULL),

  ('Kansas',         'KS', '20', true,
   'https://sos.ks.gov/elections/voter-registration.html',
   'csv', 'quarterly', NULL),

  ('Kentucky',       'KY', '21', true,
   'https://elect.ky.gov/Statistics/Pages/voterstatistics.aspx',
   'html', 'monthly', NULL),

  ('Louisiana',      'LA', '22', true,
   'https://www.sos.la.gov/ElectionsAndVoting/RegisterToVote/ReviewVoterRegistrationInformation/Pages/default.aspx',
   'html', 'monthly', NULL),

  ('Maine',          'ME', '23', true,
   'https://www.maine.gov/sos/cec/elec/data/index.html',
   'csv', 'quarterly', NULL),

  ('Maryland',       'MD', '24', true,
   'https://elections.maryland.gov/voter_registration/stats.html',
   'html', 'monthly', NULL),

  ('Massachusetts',  'MA', '25', true,
   'https://www.sec.state.ma.us/ele/eleregistrationstats/registrationstats.htm',
   'html', 'annual', NULL),

  ('Nebraska',       'NE', '31', true,
   'https://sos.nebraska.gov/elections/voter-registration-statistics',
   'html', 'quarterly', NULL),

  ('Nevada',         'NV', '32', true,
   'https://nvsos.gov/sos/elections/voters/voter-registration-statistics',
   'csv', 'monthly', NULL),

  ('New Hampshire',  'NH', '33', true,
   'https://www.sos.nh.gov/elections/voters/voter-registration-statistics',
   'html', 'monthly', NULL),

  ('New Jersey',     'NJ', '34', true,
   'https://www.state.nj.us/state/elections/voter-registration-information.shtml',
   'html', 'monthly', NULL),

  ('New Mexico',     'NM', '35', true,
   'https://www.sos.nm.gov/voting-and-elections/voter-information-portal/voter-registration-statistics/',
   'html', 'monthly', NULL),

  ('New York',       'NY', '36', true,
   'https://www.elections.ny.gov/EnrollmentCounty.html',
   'html', 'monthly', NULL),

  ('North Carolina', 'NC', '37', true,
   'https://www.ncsbe.gov/results-data/voter-registration-data',
   'csv', 'monthly', 'Downloadable voter registration snapshot'),

  ('Oklahoma',       'OK', '40', true,
   'https://www.ok.gov/elections/Voter_Registration/Voter_Registration_Statistics/index.html',
   'html', 'monthly', NULL),

  ('Oregon',         'OR', '41', true,
   'https://sos.oregon.gov/elections/Pages/electionhistory.aspx',
   'html', 'monthly', NULL),

  ('Pennsylvania',   'PA', '42', true,
   'https://www.vote.pa.gov/About-Elections/Pages/Voter-Registration-Statistics.aspx',
   'html', 'monthly', 'Active voters only'),

  ('Rhode Island',   'RI', '44', true,
   'https://vote.sos.ri.gov/Voter/VoterRegistrationStats',
   'html', 'monthly', NULL),

  ('South Dakota',   'SD', '46', true,
   'https://sdsos.gov/elections-voting/voting/voter-registration-totals/default.aspx',
   'html', 'monthly', NULL),

  ('Utah',           'UT', '49', true,
   'https://elections.utah.gov/utah-voter-information',
   'html', 'monthly', NULL),

  ('West Virginia',  'WV', '54', true,
   'https://sos.wv.gov/elections/Pages/VoterRegistrationStats.aspx',
   'html', 'quarterly', NULL),

  ('Wyoming',        'WY', '56', true,
   'https://sos.wyo.gov/elections/registration-statistics.aspx',
   'html', 'monthly', NULL),

  -- ── STATES THAT DO NOT PUBLISH PARTY DATA ─────────────────
  ('Alabama',        'AL', '01', false, NULL, NULL, NULL, 'No party registration'),
  ('Arkansas',       'AR', '05', false, NULL, NULL, NULL, 'No party registration'),
  ('Georgia',        'GA', '13', false, NULL, NULL, NULL, 'No party registration'),
  ('Hawaii',         'HI', '15', false, NULL, NULL, NULL, 'No party registration'),
  ('Illinois',       'IL', '17', false, NULL, NULL, NULL, 'Requires request + fee'),
  ('Indiana',        'IN', '18', false, NULL, NULL, NULL, 'No party registration'),
  ('Michigan',       'MI', '26', false, NULL, NULL, NULL, 'No party registration'),
  ('Minnesota',      'MN', '27', false, NULL, NULL, NULL, 'No party registration'),
  ('Mississippi',    'MS', '28', false, NULL, NULL, NULL, 'No party registration'),
  ('Missouri',       'MO', '29', false, NULL, NULL, NULL, 'No party registration'),
  ('Montana',        'MT', '30', false, NULL, NULL, NULL, 'No party registration'),
  ('North Dakota',   'ND', '38', false, NULL, NULL, NULL, 'No voter registration required'),
  ('Ohio',           'OH', '39', false, NULL, NULL, NULL, 'No party registration'),
  ('South Carolina', 'SC', '45', false, NULL, NULL, NULL, 'No party registration'),
  ('Tennessee',      'TN', '47', false, NULL, NULL, NULL, 'No party registration'),
  ('Texas',          'TX', '48', false, NULL, NULL, NULL, 'No party registration; primary ballot tracked'),
  ('Virginia',       'VA', '51', false, NULL, NULL, NULL, 'No party registration'),
  ('Washington',     'WA', '53', false, NULL, NULL, NULL, 'No party registration'),
  ('Wisconsin',      'WI', '55', false, NULL, NULL, NULL, 'No party registration'),
  ('District of Columbia', 'DC', '11', true,
   'https://www.dcboe.org/Voters/Register-To-Vote/Voter-Registration-Statistics',
   'html', 'monthly', 'DC Board of Elections – included in national aggregates')

on conflict (state_name) do update
  set abbreviation     = excluded.abbreviation,
      fips_code        = excluded.fips_code,
      publishes_party  = excluded.publishes_party,
      source_url       = excluded.source_url,
      source_format    = excluded.source_format,
      update_frequency = excluded.update_frequency,
      notes            = excluded.notes;
