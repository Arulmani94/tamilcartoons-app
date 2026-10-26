-- Read-only. Run first in Supabase SQL Editor and retain results privately.
select table_name, column_name, data_type from information_schema.columns
where table_schema = 'public' and table_name in ('anime','seasons','episodes','app_admins')
order by table_name, ordinal_position;
select tablename, policyname, permissive, roles, cmd, qual, with_check
from pg_policies where schemaname='public' and tablename in ('anime','seasons','episodes','app_admins');
select pg_get_functiondef('public.is_app_admin()'::regprocedure);
select relname, relrowsecurity from pg_class where oid in ('public.anime'::regclass,'public.seasons'::regclass,'public.episodes'::regclass,'public.app_admins'::regclass);
-- Verify is_app_admin() checks auth.uid() membership, not a user-editable metadata field.
-- Inspect FK delete rules before deleting anime/seasons in Admin; existing constraints decide cascading.
select conname, pg_get_constraintdef(oid) from pg_constraint
where conrelid in ('public.seasons'::regclass,'public.episodes'::regclass) and contype='f';
