# Euro Marfi Futuristic Exchange Starter

Lightweight Flask starter website for a currency exchange business. The homepage keeps the exchange table first, editable content is stored locally in JSON, and the admin area can update the visible site content without a database.

## Project Structure

```text
app.py
requirements.txt
README.md
data/
  site_data.json
  admin_settings.json
templates/
  base.html
  index.html
  login.html
  admin.html
  lokacija.html
  galerija.html
static/
  css/style.css
  js/main.js
  images/
```

## Create a Virtual Environment

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## Install Requirements

```bash
pip install -r requirements.txt
```

## Run the Flask App

```bash
python app.py
```

Then open `http://127.0.0.1:5000/` in your browser.

## Admin Login

The starter admin username is still defined in [app.py](/d:/euro-marfi-futuristic-site/app.py:24) as `ADMIN_USERNAME = "admin"`.

The password is no longer stored in plain text during normal use:

- on first run, the starter password `changeme123` is converted into a secure hash
- the secure settings are stored in [data/admin_settings.json](/d:/euro-marfi-futuristic-site/data/admin_settings.json:1)
- you can change the password directly from the admin panel

If you ever need to reset the starter password manually, delete `data/admin_settings.json` and run the app again.

## Password Change

Inside the admin panel there is a separate security section for changing the password:

1. Enter the current password
2. Enter the new password
3. Confirm the new password
4. Save the change

The new password is stored with `werkzeug.security.generate_password_hash`.

## Two-Factor Authentication (2FA)

The admin panel also includes an optional TOTP-based 2FA section.

To enable 2FA:

1. Open the admin panel
2. Go to the security section
3. Scan the QR code with an authenticator app
4. Enter your current password
5. Enter the 6-digit code from the app
6. Activate 2FA

When 2FA is enabled:

- login requires username
- password
- a valid 6-digit authenticator code

To disable 2FA, use the disable button in the same security section and confirm with the current password.

## Where to Edit Site Content

- Main editable site data: [data/site_data.json](/d:/euro-marfi-futuristic-site/data/site_data.json:1)
- Secure admin settings: [data/admin_settings.json](/d:/euro-marfi-futuristic-site/data/admin_settings.json:1)
- Admin form and save logic: [app.py](/d:/euro-marfi-futuristic-site/app.py:1)
- Homepage layout: [templates/index.html](/d:/euro-marfi-futuristic-site/templates/index.html:1)
- Gallery layout: [templates/galerija.html](/d:/euro-marfi-futuristic-site/templates/galerija.html:1)
- Location layout: [templates/lokacija.html](/d:/euro-marfi-futuristic-site/templates/lokacija.html:1)
- Styles: [static/css/style.css](/d:/euro-marfi-futuristic-site/static/css/style.css:1)

The admin panel can now update:

- daily info in MK and EN
- working hours in MK and EN
- phone numbers
- address
- map link
- homepage notes in MK and EN
- currency buy/sell values and flag labels
- gallery titles in MK and EN
- gallery descriptions in MK and EN

## Where to Replace Images

Project images are stored in [static/images](/d:/euro-marfi-futuristic-site/static/images).

- Gallery photos: `static/images/gallery`
- Brand/logo assets: `static/images/brands`
- Flags: `static/images/flags`

If you rename files, update the matching paths in [data/site_data.json](/d:/euro-marfi-futuristic-site/data/site_data.json:1).

## Notes

- No database is used.
- Visitor count is stored locally in `data/site_data.json`.
- Admin password hash and optional 2FA secret are stored locally in `data/admin_settings.json`.
- The code is kept beginner-friendly so it is easy to extend later.
