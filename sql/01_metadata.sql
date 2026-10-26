-- Additive, transactional; no records, policies, or existing columns are removed.
begin;
alter table public.anime add column if not exists category text;
alter table public.anime add column if not exists genre text;
alter table public.anime add column if not exists status text;
alter table public.anime add column if not exists studio text;
alter table public.anime add column if not exists rating numeric;
alter table public.anime add column if not exists is_trending boolean not null default false;
create index if not exists tc_anime_created_id on public.anime(created_at desc, id desc);
create index if not exists tc_seasons_anime_number on public.seasons(anime_id, season_number, id);
create index if not exists tc_episodes_season_number on public.episodes(season_id, episode_number, id);
commit;
-- Existing titles remain Uncategorized; set category and Trending in Admin → Add Anime/Edit.
-- No fake categories, studios, ratings, or popularity figures are inferred.
