-- OPTIONAL: only if 00_inspect confirms existing permissive admin-write policies
-- are missing. First verify the existing is_app_admin() function is trustworthy.
-- Keeps all policies and records. Does not grant app_admins membership-management.
begin;
do $$
declare t text; action text; policy_name text; clause text; seq text;
begin
  if to_regprocedure('public.is_app_admin()') is null then
    raise exception 'Missing existing is_app_admin() function';
  end if;
  foreach t in array array['anime','seasons','episodes'] loop
    execute format('grant select, insert, update, delete on public.%I to authenticated', t);
    seq := pg_get_serial_sequence('public.' || t, 'id');
    if seq is not null then
      execute format('grant usage on sequence %s to authenticated', seq);
    end if;
    foreach action in array array['INSERT','UPDATE','DELETE'] loop
      policy_name := 'tc_allow_admin_' || lower(action);
      clause := case when action='INSERT' then 'with check ((select public.is_app_admin()))'
        when action='UPDATE' then 'using ((select public.is_app_admin())) with check ((select public.is_app_admin()))'
        else 'using ((select public.is_app_admin()))' end;
      if not exists(select 1 from pg_policies where schemaname='public' and tablename=t and policyname=policy_name) then
        execute format('create policy %I on public.%I as permissive for %s to authenticated %s', policy_name,t,action,clause);
      end if;
    end loop;
  end loop;
end $$;
commit;
