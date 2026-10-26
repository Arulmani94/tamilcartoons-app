-- Run 00_inspect first. Requires existing trusted public.is_app_admin() boolean function.
-- Adds restrictive write guards; retains existing public SELECT and write policies.
-- Existing permissive admin-write policies are still required to allow writes.
-- Atomic/idempotent: policies with these new names are created only if missing.
begin;
do $$
declare t text; action text; policy_name text; clause text;
begin
  if to_regprocedure('public.is_app_admin()') is null then
    raise exception 'Existing is_app_admin() function is missing. Stop and inspect setup.';
  end if;
  foreach t in array array['anime','seasons','episodes','app_admins'] loop
    execute format('alter table public.%I enable row level security', t);
    foreach action in array array['INSERT','UPDATE','DELETE'] loop
      policy_name := 'tc_guard_' || lower(action);
      clause := case when action='INSERT' then 'with check ((select public.is_app_admin()))'
        when action='UPDATE' then 'using ((select public.is_app_admin())) with check ((select public.is_app_admin()))'
        else 'using ((select public.is_app_admin()))' end;
      if not exists(select 1 from pg_policies where schemaname='public' and tablename=t and policyname=policy_name) then
        execute format('create policy %I on public.%I as restrictive for %s to authenticated %s', policy_name,t,action,clause);
      end if;
      policy_name := 'tc_deny_anon_' || lower(action);
      clause := case when action='INSERT' then 'with check (false)' when action='UPDATE' then 'using (false) with check (false)' else 'using (false)' end;
      if not exists(select 1 from pg_policies where schemaname='public' and tablename=t and policyname=policy_name) then
        execute format('create policy %I on public.%I as restrictive for %s to anon %s', policy_name,t,action,clause);
      end if;
    end loop;
  end loop;
end $$;
commit;
-- The first administrator is provisioned privately by project owner in SQL Editor.
-- This file intentionally does not insert users or change the existing membership function.
