# Vercel + Supabase Launch Checklist

## 1. Supabase

Run `supabase_setup.sql` in the Supabase SQL Editor.

Use these Vercel environment variables:

- `SECRET_KEY`: long random value for Flask sessions
- `SITE_URL`: `https://menuvacnica.mk`
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY`: Supabase legacy service_role API key, server-side only
- `SUPABASE_TABLE`: `site_settings`
- `SUPABASE_STORAGE_BUCKET`: `site-media`
- `SUPABASE_MEDIA_PREFIX`: `uploads`

On first production run, the app seeds Supabase from the existing local files if rows do not exist:

- `data/site_data.json` -> `site_settings.key = 'site_data'`
- `data/admin_settings.json` -> `site_settings.key = 'admin_settings'`

## 2. Vercel

Import or connect this repository in Vercel.

The included `vercel.json` routes all requests through `app.py` using Vercel's Python runtime.

Before connecting DNS, verify the Vercel preview URL:

- `/`
- `/lokacija`
- `/galerija`
- `/index.html` -> 301 to `/`
- `/lokacija.html` -> 301 to `/lokacija`
- `/sliki.html` -> 301 to `/galerija`
- `/kursna-lista` -> 301 to `/`
- `/robots.txt`
- `/sitemap.xml`
- `/admin`

## 3. DNS Cutover

Only change web records after the Vercel preview works.

Add both domains in Vercel:

- `menuvacnica.mk`
- `www.menuvacnica.mk`

At the DNS provider, change only the records Vercel asks for. Do not delete mail-related records unless you have copied them first:

- `MX`
- `TXT`
- SPF
- DKIM
- DMARC

After DNS propagates, verify HTTPS and submit `https://menuvacnica.mk/sitemap.xml` in Google Search Console.