# Vercel + Supabase Launch Checklist

## 1. Supabase

Run `supabase_setup.sql` in the Supabase SQL Editor.

Use these Vercel environment variables:

- `SECRET_KEY`: long random value for Flask sessions
- `SITE_URL`: `https://menuvacnica.com.mk`
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

- `menuvacnica.com.mk`
- `www.menuvacnica.com.mk`

At the DNS provider, change only the web records Vercel asks for. Do not delete mail-related records unless you have copied them first:

- Apex/root web record: `A` -> `76.76.21.21`
- `www`: `CNAME` -> `cname.vercel-dns.com`

If email is active on this domain, keep mail pointed at the old mail server instead of the new Vercel web record:

- `mail`: `A` -> `216.24.57.1` if this is still the active mail server
- `MX`: `mail.menuvacnica.com.mk`

- `MX`
- `TXT`
- SPF
- DKIM
- DMARC

After DNS propagates, verify HTTPS and submit `https://menuvacnica.com.mk/sitemap.xml` in Google Search Console.
