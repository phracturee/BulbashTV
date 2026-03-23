# Cookie Files for Tracker Authorization

## How to Get Cookies

### Method 1: Via Browser (Recommended)

1. **Log in** to rutracker.org or nnmclub.to
2. **Open DevTools** (F12 or Ctrl+Shift+I)
3. Go to **Application** tab
4. In the left menu select **Storage** → **Cookies** → site
5. **Copy required cookies** (see list below)
6. **Paste into JSON file** in `cookies/` folder

### Method 2: Via Extension

1. Install extension **"Cookie-Editor"** or **"EditThisCookie"**
2. Log in to the tracker
3. Click on the extension icon
4. Click **Export**
5. Save to `cookies/[tracker]_cookies.json`

## Required Cookies

### For Rutracker (rutracker_cookies.json):
```json
[
  {
    "name": "bb_session",
    "value": "your_token",
    "domain": ".rutracker.org"
  },
  {
    "name": "bb_uid",
    "value": "your_id",
    "domain": ".rutracker.org"
  },
  {
    "name": "bb_hash",
    "value": "your_hash",
    "domain": ".rutracker.org"
  }
]
```

### For NnmClub (nnmclub_cookies.json):
```json
[
  {
    "name": "phpbb2mysql_4_sid",
    "value": "your_session_id",
    "domain": "nnmclub.to"
  },
  {
    "name": "opt_js_user_id",
    "value": "your_id",
    "domain": "nnmclub.to"
  },
  {
    "name": "opt_js_user_pass",
    "value": "your_pass_hash",
    "domain": "nnmclub.to"
  }
]
```

## Important!

- Cookies are valid for a **limited time** (usually several months)
- When you log out in the browser, cookies become **invalid**
- **Do not commit cookies to git!** Add to `.gitignore`:
  ```
  cookies/*_cookies.json
  ```

## How Automatic Authorization Works

1. Parser **first tries to load cookies** from file
2. If cookies are loaded, check their **validity** (look for "Logout" link)
3. If cookies are **valid** → use them for search
4. If cookies are **invalid or missing** → try to login with username/password
5. If no cookies and no login → display error message

## Verification

After adding cookies, run test:
```bash
python -c "from parsers.rutracker import RutrackerSpider; s = RutrackerSpider(); print('Cookies loaded:', len(s.session.cookies))"
```

### If you see: "[Rutracker] No login credentials provided and no valid cookies"

This means:
- Cookies are not loaded (file missing)
- Cookies are loaded but **invalid** (expired)
- No username/password in config.py

**Solution:** Update cookies via browser (see instructions above)

### If you see: "[Rutracker] Cookies are valid, already logged in"

Everything is working! Search will use cookies.
