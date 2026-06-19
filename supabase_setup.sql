-- Run this in Supabase SQL Editor before deploying to Vercel.
-- Keep SUPABASE_SERVICE_ROLE_KEY only in Vercel environment variables.

create table if not exists public.site_settings (
  key text primary key,
  value jsonb not null,
  updated_at timestamptz not null default now()
);

create or replace function public.set_site_settings_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists set_site_settings_updated_at on public.site_settings;
create trigger set_site_settings_updated_at
before update on public.site_settings
for each row execute function public.set_site_settings_updated_at();

alter table public.site_settings enable row level security;

-- The Flask server uses the service role key, which bypasses RLS.
-- Do not expose that key in browser JavaScript.

insert into storage.buckets (id, name, public)
values ('site-media', 'site-media', true)
on conflict (id) do update set public = excluded.public;

-- Public read access for uploaded media.
create policy "Public read site media"
on storage.objects for select
to public
using (bucket_id = 'site-media');