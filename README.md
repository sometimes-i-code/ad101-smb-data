# ad101 Research Explorer

An internal research dashboard for exploring SMB advertising survey data, product feedback, and open-ended responses. Combines data from Pollfish, Respondent.io, and Typeform in one place.

Built with Streamlit. Deployable to Streamlit Community Cloud in about five minutes.

---

## What it does

**Market Research tab**
Browse all survey questions as interactive charts -- gut reaction, hardest parts, ad status, budget, channels, AI attitudes, and more. Filter Respondent.io respondents by gut reaction, industry, and revenue. Every chart shows percentage breakdowns and auto-calculated "1 in X" ratios.

**Product Feedback tab**
Ratings and open text from real users who went through the ad101 and Zansei experience. Upload interview transcripts, summaries, and research notes -- keyword search works across all uploaded documents without touching the API.

**Quotes and Open Text tab**
A searchable quote wall pulling from all data sources. Filter by theme (Results, Budget, Trust, Audience, Time, Plan quality) or keyword. Every quote is labeled with its source.

**Content Studio tab**
Enter a goal ("write a LinkedIn post about why SMBs struggle with advertising"), pick a platform and tone, and the app pulls relevant stats from the actual data. Claude writes the post. The API is only called when you click Generate -- everything else is local.

**Upload Data tab**
Add new survey exports (Pollfish, Typeform, Respondent.io) or documents (transcripts, summaries, notes in .txt, .pdf, or .docx). No code changes needed.

---

## Data sources currently loaded

| Source | Type | Respondents |
|---|---|---|
| Pollfish v5 | General SMB survey | n=100 |
| Pollfish v8 | Online/hybrid SMB survey | n=240 |
| Respondent.io | SMB research panel | n=70 |
| Typeform | Product feedback (Zansei experience) | n=13 completed |

Combined market research: 410 respondents across all sources.

---

## Deploying to Streamlit Community Cloud

### Step 1 -- Set up the data folder

Create a `data/` folder in the repo and add these files:

```
data/
  v5_pollfish.xlsx
  v8_pollfish.xlsx
  Project_Small-Business-Owners-Insights-on-Advertising-Challenges-Solutions_Responses_1777058789201.csv
  responses-XsMlrGiq-01KQ0FB6HDPB174DD2HPCSWFB8-XQ7PGRMFGDL3F69J6NOSP759.csv
  responses-sMjKHB91-01KQ0F9Z0G9BQ2EKPHD6EC3726-PK1WLN2LH1Z79HNOE6ID6RHE.csv
```

The app loads these automatically. If any file is missing, the app will tell you which tab is affected and prompt you to upload via the Upload Data tab instead.

Note: the Pollfish v5 and v8 files are pre-aggregated exports (the Summary tab from Pollfish, not the Individuals tab). If you have individual-level exports, they can be uploaded separately in the Upload Data tab for additional filtering.

### Step 2 -- Create a GitHub repo

Create a new private repository (suggested name: `ad101-survey-explorer`) and upload:

```
app.py
requirements.txt
README.md
data/  (folder with all data files above)
```

### Step 3 -- Deploy

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click New app
4. Select the `ad101-survey-explorer` repo
5. Main file path: `app.py`
6. Click Deploy

Streamlit will give you a URL. It redeploys automatically whenever you push changes to the repo.

### Step 4 -- Share with the team

Share the Streamlit URL. The app is not password-protected by default. If you want to add a password, go to your app in Streamlit Cloud, open Settings, then Secrets, and add:

```toml
password = "your-password-here"
```

Then add password checking logic to `app.py` if needed.

---

## Anthropic API key

The API key is entered by each user in the sidebar at the start of their session. It is stored only in session state and never written to disk or sent anywhere other than the Anthropic API.

The key is required only for the Content Studio tab. Every other tab works without it.

If a team member does not have an Anthropic API key, they can still use all four other tabs fully.

---

## Adding new survey data

**Option A -- Upload in the app (session only):**
Go to the Upload Data tab. Upload a Typeform CSV, Pollfish xlsx, or Respondent.io CSV. Select the source type. Data is available for the rest of that session.

**Option B -- Add to the repo (permanent):**
Add the file to the `data/` folder in the GitHub repo. Update `app.py` to load it in the relevant loader function. Streamlit redeploys automatically on the next push.

---

## Adding interview transcripts and research notes

Go to the Upload Data tab and upload any `.txt`, `.pdf`, or `.docx` file. Select the document type (interview summary, transcript, research notes, etc.). The document becomes searchable in the Product Feedback tab and the Quotes tab immediately.

Documents are stored in session state and do not persist between sessions. If you want documents to be permanently available, convert them to `.txt` and add them to the `data/` folder, then load them in `app.py`.

---

## Adding a new survey version

If a future survey has a different structure:

1. Export from Pollfish or Typeform as `.xlsx` or `.csv`
2. Upload via the Upload Data tab to test whether the column mapping works
3. If the questions align with existing ones, it will merge automatically
4. If not, ask Claude to write a `normalize_vX()` function -- provide the column names from the new export and it takes about ten minutes

---

## File structure

```
ad101-survey-explorer/
  app.py                 -- main Streamlit application
  requirements.txt       -- Python dependencies
  README.md              -- this file
  data/
    v5_pollfish.xlsx
    v8_pollfish.xlsx
    [respondent.io csv]
    [typeform csvs]
```

---

## Dependencies

```
streamlit>=1.32.0
pandas>=2.0.0
numpy>=1.24.0
matplotlib>=3.7.0
openpyxl>=3.1.0
xlrd>=2.0.1
python-docx>=0.8.11
PyPDF2>=3.0.0
requests>=2.28.0
```

`python-docx` and `PyPDF2` are required for parsing uploaded Word and PDF documents. If you only need CSV and text uploads, they are optional.

---

## Team access

Share the Streamlit URL with anyone at ad101. No install required -- works in any browser. Each person enters their own Anthropic API key if they want to use Content Studio.

For questions about the data or the app, contact Lisa.
