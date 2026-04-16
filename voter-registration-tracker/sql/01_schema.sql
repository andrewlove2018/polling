-- ============================================================
-- voter_registration_tracker
-- 01_schema.sql  –  Run this first in Supabase SQL Editor
-- ============================================================

-- Enable UUID extension (already enabled on most Supabase projects)
create extension if not exists "uuid-ossp";

-- ── STATES REFERENCE TABLE ───────────────────────────────────
-- Static lookup: all 50 states + DC, with metadata about whether
-- they publish party registration data and where to find it.
create table if not exists public.states_ref (
  state_name       text primary key,
  abbreviation     char(2) not null unique,
  fips_code        char(2) not null unique,
  publishes_party  boolean not null default false,
  source_url       text,
  source_format    text,   -- 'csv', 'pdf', 'html', 'api'
  update_frequency text,   -- 'monthly', 'quarterly', 'annual'
  notes            text
);

-- ── VOTER REGISTRATION TABLE ─────────────────────────────────
-- One row per state per snapshot. The scraper upserts into this.
-- latest_snapshot view (below) surfaces the most recent row per state.
create table if not exists public.voter_registration (
  id               uuid primary key default uuid_generate_v4(),
  state_name       text not null references public.states_ref(state_name),
  dem_pct          numeric(5,2),   -- % registered Democrat
  rep_pct          numeric(5,2),   -- % registered Republican
  ind_pct          numeric(5,2),   -- % independent / unaffiliated
  other_pct        numeric(5,2),   -- % other parties
  dem_total        bigint,
  rep_total        bigint,
  ind_total        bigint,
  other_total      bigint,
  total_registered bigint,
  party_lead       text generated always as (
    case
      when dem_pct > rep_pct then 'D'
      when rep_pct > dem_pct then 'R'
      else 'TIE'
    end
  ) stored,
  lead_margin_pp   numeric(5,2) generated always as (
    dem_pct - rep_pct
  ) stored,
  state_published_date  date,      -- date on the state's own report
  scrape_timestamp      timestamptz not null default now(),
  source_url            text,
  scraper_version       text
);

-- Index for fast latest-per-state queries
create index if not exists idx_vr_state_scrape
  on public.voter_registration (state_name, scrape_timestamp desc);

-- ── TREND TABLE ───────────────────────────────────────────────
-- Computed by the scraper after each run: compares current snapshot
-- to prior snapshot to determine directional shift.
create table if not exists public.registration_trend (
  id               uuid primary key default uuid_generate_v4(),
  state_name       text not null references public.states_ref(state_name),
  computed_at      timestamptz not null default now(),
  prior_snapshot_id  uuid references public.voter_registration(id),
  current_snapshot_id uuid references public.voter_registration(id),
  dem_delta_pp     numeric(5,2),   -- change in D% since prior snapshot
  rep_delta_pp     numeric(5,2),
  ind_delta_pp     numeric(5,2),
  trend_direction  text check (trend_direction in ('R','D','N')),
    -- R = shifting more Republican (R up, or D down)
    -- D = shifting more Democrat
    -- N = stable (< 0.5pp change in lead)
  magnitude        text check (magnitude in ('strong','moderate','slight','stable'))
);

create index if not exists idx_trend_state_time
  on public.registration_trend (state_name, computed_at desc);

-- ── SCRAPER RUN LOG ───────────────────────────────────────────
create table if not exists public.scraper_run_log (
  id               uuid primary key default uuid_generate_v4(),
  run_at           timestamptz not null default now(),
  states_attempted int,
  states_succeeded int,
  states_failed    int,
  failed_states    text[],
  run_duration_sec numeric(8,2),
  scraper_version  text,
  notes            text
);
