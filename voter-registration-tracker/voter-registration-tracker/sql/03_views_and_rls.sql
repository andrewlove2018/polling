-- ============================================================
-- voter_registration_tracker
-- 03_views_and_rls.sql  –  Run after 02_seed_states.sql
-- ============================================================

-- ── VIEW: latest snapshot per state ───────────────────────────
-- Used by the dashboard to get current numbers without pagination.
create or replace view public.latest_registration as
select distinct on (vr.state_name)
  vr.id,
  vr.state_name,
  sr.abbreviation,
  sr.fips_code,
  vr.dem_pct,
  vr.rep_pct,
  vr.ind_pct,
  vr.other_pct,
  vr.dem_total,
  vr.rep_total,
  vr.ind_total,
  vr.other_total,
  vr.total_registered,
  vr.party_lead,
  vr.lead_margin_pp,
  vr.state_published_date,
  vr.scrape_timestamp,
  vr.source_url,
  sr.source_format,
  sr.update_frequency
from public.voter_registration vr
join public.states_ref sr on sr.state_name = vr.state_name
order by vr.state_name, vr.scrape_timestamp desc;

-- ── VIEW: latest trend per state ──────────────────────────────
create or replace view public.latest_trend as
select distinct on (state_name)
  state_name,
  computed_at,
  dem_delta_pp,
  rep_delta_pp,
  ind_delta_pp,
  trend_direction,
  magnitude
from public.registration_trend
order by state_name, computed_at desc;

-- ── VIEW: dashboard combined view ─────────────────────────────
-- Single query for the frontend: registration + trend + state meta.
create or replace view public.dashboard_view as
select
  lr.state_name,
  lr.abbreviation,
  lr.fips_code,
  lr.dem_pct,
  lr.rep_pct,
  lr.ind_pct,
  lr.other_pct,
  lr.total_registered,
  lr.party_lead,
  lr.lead_margin_pp,
  lr.state_published_date,
  lr.scrape_timestamp,
  lr.source_url,
  lr.update_frequency,
  coalesce(lt.trend_direction, 'N') as trend_direction,
  lt.magnitude,
  lt.dem_delta_pp,
  lt.rep_delta_pp,
  lt.ind_delta_pp,
  lt.computed_at as trend_computed_at
from public.latest_registration lr
left join public.latest_trend lt on lt.state_name = lr.state_name;

-- ── VIEW: national aggregate ──────────────────────────────────
create or replace view public.national_aggregate as
select
  sum(total_registered)                                    as total_registered,
  sum(dem_total)                                           as total_dem,
  sum(rep_total)                                           as total_rep,
  sum(ind_total)                                           as total_ind,
  round(sum(dem_total)::numeric / sum(total_registered) * 100, 2) as national_dem_pct,
  round(sum(rep_total)::numeric / sum(total_registered) * 100, 2) as national_rep_pct,
  round(sum(ind_total)::numeric / sum(total_registered) * 100, 2) as national_ind_pct,
  count(*) filter (where party_lead = 'R')                as states_r_lead,
  count(*) filter (where party_lead = 'D')                as states_d_lead,
  count(*) filter (where party_lead = 'TIE')              as states_tied,
  max(scrape_timestamp)                                    as last_updated
from public.latest_registration;

-- ── VIEW: historical trend series (for charts) ────────────────
create or replace view public.trend_series as
select
  vr.state_name,
  sr.abbreviation,
  date_trunc('month', vr.scrape_timestamp) as month,
  avg(vr.dem_pct)   as dem_pct,
  avg(vr.rep_pct)   as rep_pct,
  avg(vr.ind_pct)   as ind_pct,
  avg(vr.lead_margin_pp) as lead_margin_pp,
  count(*)          as snapshots_in_month
from public.voter_registration vr
join public.states_ref sr on sr.state_name = vr.state_name
group by vr.state_name, sr.abbreviation, date_trunc('month', vr.scrape_timestamp)
order by vr.state_name, month;

-- ── FUNCTION: upsert snapshot ─────────────────────────────────
-- Called by the Python scraper for each state. Inserts a new row,
-- then recomputes the trend by comparing to the prior snapshot.
create or replace function public.upsert_registration_snapshot(
  p_state_name          text,
  p_dem_pct             numeric,
  p_rep_pct             numeric,
  p_ind_pct             numeric,
  p_other_pct           numeric,
  p_dem_total           bigint,
  p_rep_total           bigint,
  p_ind_total           bigint,
  p_other_total         bigint,
  p_total_registered    bigint,
  p_state_published_date date,
  p_source_url          text,
  p_scraper_version     text default '1.0'
)
returns uuid
language plpgsql
security definer
as $$
declare
  v_new_id        uuid;
  v_prior_id      uuid;
  v_prior_dem_pct numeric;
  v_prior_rep_pct numeric;
  v_prior_ind_pct numeric;
  v_dem_delta     numeric;
  v_rep_delta     numeric;
  v_ind_delta     numeric;
  v_lead_delta    numeric;
  v_direction     text;
  v_magnitude     text;
begin
  -- Insert new snapshot
  insert into public.voter_registration (
    state_name, dem_pct, rep_pct, ind_pct, other_pct,
    dem_total, rep_total, ind_total, other_total, total_registered,
    state_published_date, source_url, scraper_version
  ) values (
    p_state_name, p_dem_pct, p_rep_pct, p_ind_pct, p_other_pct,
    p_dem_total, p_rep_total, p_ind_total, p_other_total, p_total_registered,
    p_state_published_date, p_source_url, p_scraper_version
  ) returning id into v_new_id;

  -- Find the most recent prior snapshot for this state
  select id, dem_pct, rep_pct, ind_pct
    into v_prior_id, v_prior_dem_pct, v_prior_rep_pct, v_prior_ind_pct
  from public.voter_registration
  where state_name = p_state_name
    and id <> v_new_id
  order by scrape_timestamp desc
  limit 1;

  -- Compute trend if prior snapshot exists
  if v_prior_id is not null then
    v_dem_delta  := p_dem_pct  - v_prior_dem_pct;
    v_rep_delta  := p_rep_pct  - v_prior_rep_pct;
    v_ind_delta  := p_ind_pct  - v_prior_ind_pct;
    -- Lead delta: positive = D gaining, negative = R gaining
    v_lead_delta := (p_dem_pct - p_rep_pct) - (v_prior_dem_pct - v_prior_rep_pct);

    if abs(v_lead_delta) < 0.5 then
      v_direction := 'N';
      v_magnitude := 'stable';
    elsif v_lead_delta > 0 then
      v_direction := 'D';
      v_magnitude := case
        when v_lead_delta >= 3  then 'strong'
        when v_lead_delta >= 1  then 'moderate'
        else 'slight'
      end;
    else
      v_direction := 'R';
      v_magnitude := case
        when abs(v_lead_delta) >= 3  then 'strong'
        when abs(v_lead_delta) >= 1  then 'moderate'
        else 'slight'
      end;
    end if;

    insert into public.registration_trend (
      state_name, prior_snapshot_id, current_snapshot_id,
      dem_delta_pp, rep_delta_pp, ind_delta_pp,
      trend_direction, magnitude
    ) values (
      p_state_name, v_prior_id, v_new_id,
      v_dem_delta, v_rep_delta, v_ind_delta,
      v_direction, v_magnitude
    );
  end if;

  return v_new_id;
end;
$$;

-- ── ROW LEVEL SECURITY ────────────────────────────────────────
-- All tables are public read. Only the service role (scraper) can write.

alter table public.states_ref           enable row level security;
alter table public.voter_registration   enable row level security;
alter table public.registration_trend   enable row level security;
alter table public.scraper_run_log      enable row level security;

-- Public read on all tables
create policy "public read states_ref"
  on public.states_ref for select using (true);

create policy "public read voter_registration"
  on public.voter_registration for select using (true);

create policy "public read registration_trend"
  on public.registration_trend for select using (true);

create policy "public read scraper_run_log"
  on public.scraper_run_log for select using (true);

-- Service role writes only (scraper uses SUPABASE_SERVICE_KEY)
create policy "service insert voter_registration"
  on public.voter_registration for insert
  to service_role with check (true);

create policy "service insert registration_trend"
  on public.registration_trend for insert
  to service_role with check (true);

create policy "service insert scraper_run_log"
  on public.scraper_run_log for insert
  to service_role with check (true);

-- Grant read access to anon role (used by the frontend with anon key)
grant select on public.states_ref           to anon;
grant select on public.voter_registration   to anon;
grant select on public.registration_trend   to anon;
grant select on public.scraper_run_log      to anon;
grant select on public.latest_registration  to anon;
grant select on public.latest_trend         to anon;
grant select on public.dashboard_view       to anon;
grant select on public.national_aggregate   to anon;
grant select on public.trend_series         to anon;
grant execute on function public.upsert_registration_snapshot to service_role;
