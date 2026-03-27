# ad101 Survey Explorer

Interactive dashboard for exploring ad101 SMB survey data across any filter combination.

## What it does

- Combines v5 (general SMB) and v8 (online/hybrid) Pollfish surveys in one place
- Filter by any combination: survey version, region, industry, gut reaction, ad status, budget, gender, tenure, age, and more
- Six tabs: Overview, All Questions, Compare Segments, Open-Ended responses, Add Data, Raw Data
- Upload new Pollfish exports directly in the app — no code changes needed
- Password-protected for internal use

---

## Deploying to Streamlit Community Cloud (free, takes ~5 minutes)

### Step 1 — Put the survey files in the repo

Create a `data/` folder and add both Pollfish exports:
```
data/
  v5_pollfish.xlsx    ← rename your v5 Pollfish export to this
  v8_pollfish.xlsx    ← rename your v8 Pollfish export to this
```

The app loads these automatically on startup. Future surveys are uploaded directly in the app.

### Step 2 — Create a GitHub repo

1. Go to github.com and create a new **private** repository called `ad101-survey-explorer`
2. Upload these files:
   - `app.py`
   - `requirements.txt`
   - `README.md`
   - `data/v5_pollfish.xlsx`
   - `data/v8_pollfish.xlsx`

### Step 3 — Deploy on Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click **New app**
4. Select your `ad101-survey-explorer` repo
5. Main file path: `app.py`
6. Click **Deploy**

Streamlit gives you a public URL like `https://ad101-survey-explorer.streamlit.app`

### Step 4 — Set the password (optional but recommended)

In Streamlit Cloud, go to your app → **Settings** → **Secrets** and add:

```toml
password = "your-password-here"
```

Share the URL and password with the team. Anyone with both can access it.

---

## Adding new survey data

**Option A — Upload in the app:**
1. Export the `Individuals` tab from Pollfish as `.xlsx`
2. Open the app → **Add Data** tab
3. Upload the file and select the survey version (v5 or v8)
4. Data merges instantly for your session

**Option B — Add to the repo (permanent):**
1. Save the new export as `data/v9_pollfish.xlsx` (or any name)
2. Open `app.py` and add a loader for it in the `load_default_data()` function
3. Commit to GitHub — Streamlit redeploys automatically

---

## Adding a new survey version

If you run a v9 survey with different questions:
1. Upload via the app using the v8 structure (if question numbers are similar)
2. Or ask Claude to add a `normalize_v9()` function to `app.py` — provide the column mapping and it takes ~10 minutes

---

## Filter combinations that work well

- **Confident + $1K+ budget** → your highest-value acquisition segment
- **v8 only + health/care industry** → healthcare segment
- **Burned + never advertised** → hardest-to-reach group
- **v5 vs v8** → side-by-side to see how the online/hybrid audience differs
- **South region + under $100K revenue** → small Southern operators

---

## Team access

Share the Streamlit URL and password with anyone at ad101. No install required — works in any browser.
