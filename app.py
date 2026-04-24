"""
ad101 Survey + Research Explorer
All data sources in one place. API used only when you click Generate.
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import io, os, re, json
from datetime import datetime

st.set_page_config(
    page_title="ad101 Research Explorer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── PASSWORD GATE ─────────────────────────────────────────────────────────────
def check_password():
    """Returns True if the user has entered the correct password."""
    if st.session_state.get("authenticated"):
        return True

    # Try to get password from Streamlit secrets
    try:
        correct_password = st.secrets["password"]
    except Exception:
        # No secret set -- block access with a clear message
        st.error("No password configured. Add a `password` secret in Streamlit Cloud settings.")
        st.stop()

    # Center the login form
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("## ad101")
        st.markdown("**Research Explorer** — Internal access only")
        st.markdown("<br>", unsafe_allow_html=True)
        entered = st.text_input("Password", type="password", placeholder="Enter password...")
        if st.button("Enter", type="primary", use_container_width=True):
            if entered == correct_password:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Incorrect password.")
    return False

if not check_password():
    st.stop()

# ── PALETTE ──────────────────────────────────────────────────────────────────
BLK = "#111111"; RED = "#B85042"; GY = "#888888"; LGY = "#DDDDDD"
GN  = "#1A3320"; GL  = "#4ADE80"; GOLD = "#C8A84B"
W   = "#FFFFFF"; BG  = "#F8F7F4"

# ── STYLES ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
html, body, [class*="css"] { font-family: 'Calibri', sans-serif; }
h1 { color: #111111; font-size: 1.8rem; font-weight: 800; }
h2 { color: #111111; font-size: 1.2rem; font-weight: 700; border-bottom: 2px solid #DDDDDD; padding-bottom: 6px; }
h3 { color: #333333; font-size: 1rem; font-weight: 700; }
.stat-box {
    background: #FFFFFF; border: 1px solid #DDDDDD; border-radius: 8px;
    padding: 16px 20px; text-align: center; margin-bottom: 8px;
}
.stat-number { font-size: 2.4rem; font-weight: 900; color: #B85042; font-family: Arial Black, sans-serif; }
.stat-label  { font-size: 0.82rem; color: #888888; margin-top: 2px; }
.ratio-box   { font-size: 1.8rem; font-weight: 900; color: #111111; font-family: Arial Black, sans-serif; }
.quote-card {
    background: #FFFFFF; border-left: 3px solid #B85042;
    padding: 12px 16px; margin: 8px 0; border-radius: 0 6px 6px 0;
    font-size: 0.9rem; color: #333333;
}
.quote-source { font-size: 0.75rem; color: #888888; margin-top: 6px; font-style: italic; }
.tag-pill {
    display: inline-block; background: #F0F0F0; color: #555555;
    border-radius: 12px; padding: 2px 10px; font-size: 0.75rem;
    margin: 2px; cursor: pointer;
}
.section-chip {
    display: inline-block; background: #1A3320; color: #4ADE80;
    border-radius: 4px; padding: 2px 10px; font-size: 0.72rem;
    font-weight: 700; letter-spacing: 1.5px; margin-bottom: 12px;
}
div[data-testid="stMetricValue"] { font-size: 2rem; font-weight: 800; color: #B85042; }
.stTabs [data-baseweb="tab"] { font-size: 0.9rem; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ── CHART HELPERS ─────────────────────────────────────────────────────────────
def hbar(labels, vals, title, highlight_top=True, color=BLK, figw=8, figh=None):
    figh = figh or max(2.5, len(labels) * 0.48)
    fig, ax = plt.subplots(figsize=(figw, figh), facecolor=W)
    ax.set_facecolor(W)
    cols = []
    for i, v in enumerate(vals):
        if highlight_top and i == np.argmax(vals): cols.append(RED)
        else: cols.append(color)
    bars = ax.barh(labels, vals, color=cols, height=0.55, edgecolor='none')
    for bar, val in zip(bars, vals):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                f'{val:.1f}%', va='center', ha='left', fontsize=9,
                fontweight='bold', color=RED if val == max(vals) and highlight_top else BLK)
    ax.set_title(title, fontsize=11, fontweight='bold', color=BLK, loc='left', pad=8)
    ax.set_xlim(0, min(100, max(vals) * 1.25))
    ax.spines[['right','top','bottom']].set_visible(False)
    ax.spines['left'].set_color(LGY)
    ax.tick_params(axis='x', bottom=False, labelbottom=False)
    ax.tick_params(axis='y', labelsize=9, left=False, labelcolor=BLK)
    fig.tight_layout()
    return fig

def donut(labels, vals, title, colors=None, n_label=None):
    if colors is None:
        colors = [BLK, RED, '#555555', '#888888', LGY, GOLD, '#666666']
    colors = colors[:len(labels)]
    fig, ax = plt.subplots(figsize=(6, 5), facecolor=W)
    ax.set_facecolor(W)
    wedges, _, autotexts = ax.pie(
        vals, colors=colors,
        autopct=lambda p: f'{p:.0f}%' if p > 6 else '',
        startangle=110, wedgeprops=dict(width=0.5, edgecolor=W, linewidth=2),
        pctdistance=0.75)
    for at in autotexts:
        at.set_fontsize(10); at.set_fontweight('bold'); at.set_color(W)
    if n_label:
        ax.text(0, 0.06, n_label, ha='center', va='center', fontsize=9, color=GY)
    patches = [mpatches.Patch(color=colors[i], label=f'{labels[i][:30]}  {vals[i]:.1f}%')
               for i in range(len(labels))]
    ax.legend(handles=patches, loc='lower center', bbox_to_anchor=(0.5, -0.22),
              ncol=2, fontsize=8.5, frameon=False, labelcolor=BLK, handlelength=0.9)
    ax.set_title(title, fontsize=11, fontweight='bold', color=BLK, pad=10)
    fig.tight_layout()
    return fig

def stat_box(stat, label, color=RED):
    st.markdown(f"""<div class="stat-box">
        <div class="stat-number" style="color:{color}">{stat}</div>
        <div class="stat-label">{label}</div>
    </div>""", unsafe_allow_html=True)

def ratio_box(numerator, denominator, label):
    st.markdown(f"""<div class="stat-box">
        <div class="ratio-box">1 in {denominator}</div>
        <div class="stat-label">{label}</div>
    </div>""", unsafe_allow_html=True)

def quote_card(text, source="", tags=""):
    source_html = f'<div class="quote-source">{source}</div>' if source else ''
    st.markdown(f"""<div class="quote-card">
        "{text}"
        {source_html}
    </div>""", unsafe_allow_html=True)

# ── DOCUMENT TEXT EXTRACTION ──────────────────────────────────────────────────
def extract_text_from_file(uploaded_file):
    """Extract plain text from txt, pdf, docx uploads."""
    name = uploaded_file.name.lower()
    try:
        if name.endswith('.txt'):
            return uploaded_file.read().decode('utf-8', errors='ignore')
        elif name.endswith('.pdf'):
            try:
                import PyPDF2
                reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
                return '\n'.join(page.extract_text() or '' for page in reader.pages)
            except Exception:
                return "[PDF parsing failed -- try converting to .txt first]"
        elif name.endswith('.docx'):
            try:
                from docx import Document
                doc = Document(io.BytesIO(uploaded_file.read()))
                return '\n'.join(p.text for p in doc.paragraphs if p.text.strip())
            except Exception:
                return "[DOCX parsing failed]"
        else:
            return uploaded_file.read().decode('utf-8', errors='ignore')
    except Exception as e:
        return f"[Could not read file: {e}]"

# ── DATA LOADERS ──────────────────────────────────────────────────────────────
@st.cache_data
def load_pollfish_agg(path):
    """Load pre-aggregated Pollfish xlsx. Returns dict of {question: {answer: pct}}"""
    df = pd.read_excel(path)
    out = {}
    for q in df['Question'].unique():
        sub = df[df['Question']==q].copy()
        sub = sub[sub['Answer'].notna()]
        pcts = {}
        for _, row in sub.iterrows():
            ans = str(row['Answer']).strip()
            pct = row['Respondents(%)'] if pd.notna(row['Respondents(%)']) else row['Answers(%)']
            if pd.notna(pct):
                pcts[ans] = round(float(pct) * 100, 1)
        if pcts:
            out[q] = pcts
    return out

@st.cache_data
def load_respondent_io(path):
    df = pd.read_csv(path)
    # All 70 answered the questions, use all of them
    return df

@st.cache_data
def load_typeform_files():
    """Load all typeform CSVs and combine completed responses."""
    paths = [
        '/mnt/user-data/uploads/responses-XsMlrGiq-01KQ0FB6HDPB174DD2HPCSWFB8-XQ7PGRMFGDL3F69J6NOSP759.csv',
        '/mnt/user-data/uploads/responses-sMjKHB91-01KQ0F9Z0G9BQ2EKPHD6EC3726-PK1WLN2LH1Z79HNOE6ID6RHE.csv',
        '/mnt/project/4_15__1_1_typeform_survey_responsesXsMlrGiq01KP975ZPR9DP97M43T4R6JAWP165HYRQLX6DWEAWB4F53KBHB.csv',
    ]
    frames = []
    for p in paths:
        try:
            df = pd.read_csv(p)
            completed = df[df['Response Type'].isin(['completed','partial'])]
            completed = completed.assign(source_file=os.path.basename(p))
            frames.append(completed)
        except Exception:
            pass
    if frames:
        # Align columns -- use union
        all_cols = set()
        for f in frames: all_cols.update(f.columns)
        aligned = []
        for f in frames:
            for c in all_cols:
                if c not in f.columns: f[c] = np.nan
            aligned.append(f[sorted(all_cols)])
        return pd.concat(aligned, ignore_index=True)
    return pd.DataFrame()

# ── KEY METRIC CALCULATIONS ───────────────────────────────────────────────────
def compute_ratio(pct):
    """Convert a percentage to '1 in N' string."""
    if pct <= 0: return "N/A"
    n = round(100 / pct)
    return str(n)

# ── SESSION STATE INIT ────────────────────────────────────────────────────────
if 'uploaded_docs' not in st.session_state:
    st.session_state.uploaded_docs = []  # list of {name, source_type, text, date}
if 'extra_typeforms' not in st.session_state:
    st.session_state.extra_typeforms = []
if 'api_key' not in st.session_state:
    st.session_state.api_key = ''

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ad101")
    st.markdown("**Research Explorer**")
    st.markdown("---")

    # API Key
    st.markdown("#### Anthropic API Key")
    st.markdown('<span style="font-size:0.78rem;color:#888">Required only for Content Studio</span>', unsafe_allow_html=True)
    api_key = st.text_input("API Key", type="password",
                             value=st.session_state.api_key,
                             placeholder="sk-ant-...",
                             label_visibility="collapsed")
    if api_key:
        st.session_state.api_key = api_key
        st.success("Key saved for this session")

    st.markdown("---")
    st.markdown("#### Data Sources")
    st.markdown("""
- 📊 Pollfish v5 — n=100
- 📊 Pollfish v8 — n=240
- 🔬 Respondent.io — n=70
- 📝 Typeform (product) — n=13
    """)
    if st.session_state.uploaded_docs:
        st.markdown(f"- 📄 Uploaded docs — {len(st.session_state.uploaded_docs)} files")

# ── LOAD DATA ─────────────────────────────────────────────────────────────────
try:
    v5 = load_pollfish_agg('/mnt/user-data/uploads/v5_pollfish.xlsx')
    v8 = load_pollfish_agg('/mnt/user-data/uploads/v8_pollfish.xlsx')
    POLLFISH_OK = True
except Exception as e:
    v5 = {}; v8 = {}; POLLFISH_OK = False
    st.warning(f"Pollfish files not found: {e}")

try:
    resp_df = load_respondent_io(
        '/mnt/user-data/uploads/Project_Small-Business-Owners-Insights-on-Advertising-Challenges-Solutions_Responses_1777058789201.csv')
    RESP_OK = True
except Exception:
    resp_df = pd.DataFrame(); RESP_OK = False

try:
    tf_df = load_typeform_files()
    TF_OK = len(tf_df) > 0
except Exception:
    tf_df = pd.DataFrame(); TF_OK = False

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("# ad101 Research Explorer")
st.markdown(f"*{340 + len(resp_df)} total respondents across all sources · Updated {datetime.now().strftime('%B %d, %Y')}*")
st.markdown("---")

# ── TABS ──────────────────────────────────────────────────────────────────────
tabs = st.tabs([
    "📊 Market Research",
    "🧪 Product Feedback",
    "💬 Quotes & Open Text",
    "✍️ Content Studio",
    "📁 Upload Data"
])

# ════════════════════════════════════════════════════════════════════════════
# TAB 1: MARKET RESEARCH
# ════════════════════════════════════════════════════════════════════════════
with tabs[0]:
    st.markdown('<div class="section-chip">MARKET RESEARCH</div>', unsafe_allow_html=True)
    st.markdown("## What 340+ SMB owners told us about advertising")
    st.markdown("*Pollfish v5 (n=100) + Pollfish v8 (n=240) + Respondent.io (n=70) — combined n=410*")

    # ── TOP STATS ROW ─────────────────────────────────────────────────────
    st.markdown("### At a glance")
    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: stat_box("39%", "say knowing where to advertise is hardest")
    with c2: stat_box("55%", "actively advertising but want better results")
    with c3: stat_box("44%", "want content & visual help after a plan")
    with c4: stat_box("10%", "spend over $3K/month on ads")
    with c5:
        st.markdown("""<div class="stat-box">
            <div class="ratio-box">1 in 3</div>
            <div class="stat-label">would spend more if they saw results first</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── SOURCE SELECTOR ───────────────────────────────────────────────────
    source = st.radio("Data source", ["Combined (Pollfish v5+v8)", "Pollfish v5 only",
                                       "Pollfish v8 only", "Respondent.io only"],
                      horizontal=True)

    # ── QUESTION BROWSER ──────────────────────────────────────────────────
    st.markdown("### Browse by question")

    # Build unified question list
    all_questions = {}
    if POLLFISH_OK:
        for q, d in v5.items(): all_questions[f"[v5] {q}"] = d
        for q, d in v8.items(): all_questions[f"[v8] {q}"] = d

    # Respondent.io categorical questions
    if RESP_OK and len(resp_df) > 0:
        resp_cats = {
            "10-When you think about advertising your business, what's your gut reaction?": "Gut reaction (Respondent.io)",
            "11-Which best describes where you are with advertising right now?": "Ad status (Respondent.io)",
            "12-How much time do you realistically spend on marketing and advertising per week": "Time spent weekly (Respondent.io)",
            "5-How does your business primarily operate": "Operating mode (Respondent.io)",
            "6-What was your 2025 company revenue": "Revenue 2025 (Respondent.io)",
            "7-What is your current monthly advertising budget? ": "Monthly ad budget (Respondent.io)",
        }
        for col, label in resp_cats.items():
            if col in resp_df.columns:
                vc = resp_df[col].value_counts(normalize=True)*100
                all_questions[f"[Respondent.io] {label}"] = vc.round(1).to_dict()

    if not all_questions:
        st.info("Upload Pollfish xlsx files in the Upload Data tab to see charts here.")
    else:
        # Filter by source
        if source == "Pollfish v5 only":
            show_q = {k:v for k,v in all_questions.items() if k.startswith("[v5]")}
        elif source == "Pollfish v8 only":
            show_q = {k:v for k,v in all_questions.items() if k.startswith("[v8]")}
        elif source == "Respondent.io only":
            show_q = {k:v for k,v in all_questions.items() if k.startswith("[Respondent.io]")}
        else:
            show_q = all_questions

        selected_q = st.selectbox("Select question", list(show_q.keys()))
        if selected_q:
            data = show_q[selected_q]
            labels = list(data.keys())
            vals = list(data.values())
            if len(labels) > 0:
                col_chart, col_stats = st.columns([2,1])
                with col_chart:
                    if len(labels) <= 5:
                        fig = donut(labels, vals, selected_q.split("] ",1)[-1][:60],
                                   n_label=None)
                    else:
                        # Sort descending for bar chart
                        pairs = sorted(zip(vals, labels), reverse=True)
                        sv, sl = zip(*pairs)
                        fig = hbar(list(sl), list(sv), selected_q.split("] ",1)[-1][:60])
                    st.pyplot(fig, use_container_width=True)
                with col_stats:
                    st.markdown("**Key numbers**")
                    top = sorted(zip(vals, labels), reverse=True)
                    for v, l in top[:4]:
                        n_in = compute_ratio(v)
                        st.markdown(f"""<div class="stat-box">
                            <div class="stat-number">{v:.0f}%</div>
                            <div class="stat-label">{l[:40]}</div>
                            <div style="color:{GY};font-size:0.75rem;margin-top:4px">1 in {n_in} respondents</div>
                        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── RESPONDENT.IO DEEP FILTERS ────────────────────────────────────────
    if RESP_OK and len(resp_df) > 0:
        st.markdown("### Filter Respondent.io individual responses (n=70)")
        col1,col2,col3 = st.columns(3)
        with col1:
            gut_opts = resp_df["10-When you think about advertising your business, what's your gut reaction?"].dropna().unique().tolist()
            gut_sel = st.multiselect("Gut reaction", gut_opts, default=gut_opts)
        with col2:
            ind_opts = resp_df["3-What industry is your business in? "].dropna().unique().tolist()
            ind_sel = st.multiselect("Industry", ind_opts, default=ind_opts)
        with col3:
            rev_opts = resp_df["6-What was your 2025 company revenue"].dropna().unique().tolist()
            rev_sel = st.multiselect("Revenue", rev_opts, default=rev_opts)

        gut_col = "10-When you think about advertising your business, what's your gut reaction?"
        ind_col = "3-What industry is your business in? "
        rev_col = "6-What was your 2025 company revenue"
        mask = (
            resp_df[gut_col].isin(gut_sel) &
            resp_df[ind_col].isin(ind_sel) &
            resp_df[rev_col].isin(rev_sel)
        )
        filtered_resp = resp_df[mask]
        st.markdown(f"**{len(filtered_resp)} of {len(resp_df)} respondents match**")

        if len(filtered_resp) > 0:
            hard_col = "13-What feels like the hardest part of advertising your business? (select top 2)"
            hardest_cols = [c for c in resp_df.columns if c.startswith("13-") and "_" in c]
            if hardest_cols:
                hard_data = {}
                for c in hardest_cols:
                    label = c.split("_",1)[-1].strip()[:50]
                    pct = filtered_resp[c].notna().sum() / max(len(filtered_resp),1) * 100
                    if pct > 0: hard_data[label] = round(pct, 1)
                if hard_data:
                    pairs = sorted(hard_data.items(), key=lambda x:-x[1])
                    fig = hbar([p[0] for p in pairs], [p[1] for p in pairs],
                               "Hardest parts of advertising (filtered)")
                    st.pyplot(fig, use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════
# TAB 2: PRODUCT FEEDBACK
# ════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    st.markdown('<div class="section-chip">PRODUCT FEEDBACK</div>', unsafe_allow_html=True)
    st.markdown("## How real users experienced ad101 + Zansei")

    # Combine all typeform + uploaded typeforms
    all_tf = tf_df.copy() if TF_OK else pd.DataFrame()
    for extra in st.session_state.extra_typeforms:
        all_tf = pd.concat([all_tf, extra], ignore_index=True)

    n_tf = len(all_tf)
    st.markdown(f"*{n_tf} completed product survey responses + {len(st.session_state.uploaded_docs)} uploaded documents*")

    if n_tf > 0:
        # ── RATING SCORES ─────────────────────────────────────────────────
        st.markdown("### Ratings (out of 5)")
        rating_fields = {
            "Conversation ease": ["The Chat:\n\nHow easy was the conversation to follow?",
                                  "The Zansei conversation:\n\nHow easy was the conversation to follow?"],
            "Plan relevance": ["The Plan: \n\nHow much did the plan feel relevant to your needs?"],
            "Plan specificity": ["The Plan: \n\nDid the plan feel like it was built for your business specifically?"],
        }
        r_cols = st.columns(len(rating_fields))
        for i, (label, col_variants) in enumerate(rating_fields.items()):
            vals = []
            for col in col_variants:
                if col in all_tf.columns:
                    vals.extend(all_tf[col].dropna().tolist())
            if vals:
                avg = round(np.mean([float(v) for v in vals if str(v).replace('.','').isdigit()]), 1)
                with r_cols[i]:
                    st.markdown(f"""<div class="stat-box">
                        <div class="stat-number">{avg}/5</div>
                        <div class="stat-label">{label}</div>
                        <div style="color:{GY};font-size:0.75rem">n={len(vals)}</div>
                    </div>""", unsafe_allow_html=True)

        st.markdown("---")

        # ── CATEGORICAL BREAKDOWNS ────────────────────────────────────────
        st.markdown("### Would they recommend / register / pay?")
        cat_map = {
            "Would recommend": "Last Question! \n\nWould you recommend ad101 to another business owner?",
            "Would pay for execution": "Pricing:\n\nAfter going through this experience, would you consider paying for help executing your advertising plan?",
            "Would register": "Would you register for ad101.com if it saved your chat, plan, and allowed you to continue your conversations, get more specific advice, and refine or create new advertising plans? ",
        }
        cat_cols = st.columns(len(cat_map))
        for i, (label, col) in enumerate(cat_map.items()):
            with cat_cols[i]:
                if col in all_tf.columns:
                    vc = all_tf[col].dropna().value_counts()
                    st.markdown(f"**{label}** (n={vc.sum()})")
                    for ans, cnt in vc.items():
                        pct = cnt/vc.sum()*100
                        color = GL if "yes" in str(ans).lower() else GY
                        st.markdown(f"- {ans[:40]}: **{pct:.0f}%**")

        st.markdown("---")

        # ── WHAT ZANSEI MISSED ─────────────────────────────────────────────
        st.markdown("### What users said Zansei missed")
        missed_cols = [c for c in all_tf.columns if "didn't ask" in c.lower() or "missing" in c.lower()]
        for col in missed_cols:
            for val in all_tf[col].dropna():
                if len(str(val)) > 20 and str(val).lower() not in ['n/a','na','nan','no','none']:
                    quote_card(str(val), source="Typeform product survey")

    else:
        st.info("No product survey data loaded. Upload Typeform CSVs in the Upload Data tab.")

    # ── UPLOADED DOCUMENTS SEARCH ─────────────────────────────────────────
    if st.session_state.uploaded_docs:
        st.markdown("---")
        st.markdown("### Search interview summaries & transcripts")
        search_q = st.text_input("Search across all uploaded documents", placeholder="e.g. Zansei, pricing, competitor...")
        doc_filter = st.multiselect("Filter by document type",
                                     list(set(d['source_type'] for d in st.session_state.uploaded_docs)),
                                     default=list(set(d['source_type'] for d in st.session_state.uploaded_docs)))

        docs_to_search = [d for d in st.session_state.uploaded_docs if d['source_type'] in doc_filter]

        if search_q:
            st.markdown(f"**Results for '{search_q}'**")
            found = 0
            for doc in docs_to_search:
                text = doc['text']
                # Find sentences containing the search term
                sentences = re.split(r'(?<=[.!?])\s+', text)
                matches = [s.strip() for s in sentences
                           if search_q.lower() in s.lower() and len(s.strip()) > 20]
                if matches:
                    st.markdown(f"**📄 {doc['name']}** ({doc['source_type']})")
                    for m in matches[:5]:
                        # Highlight match
                        highlighted = m.replace(search_q, f"**{search_q}**")
                        quote_card(highlighted, source=doc['name'])
                    found += len(matches)
            if found == 0:
                st.info(f"No results for '{search_q}' in uploaded documents.")
        else:
            # Show document list
            for doc in docs_to_search:
                with st.expander(f"📄 {doc['name']} ({doc['source_type']}) — {doc['date']}"):
                    st.markdown(doc['text'][:2000] + ("..." if len(doc['text']) > 2000 else ""))

# ════════════════════════════════════════════════════════════════════════════
# TAB 3: QUOTES & OPEN TEXT
# ════════════════════════════════════════════════════════════════════════════
with tabs[2]:
    st.markdown('<div class="section-chip">QUOTES & OPEN TEXT</div>', unsafe_allow_html=True)
    st.markdown("## What they said, in their own words")

    # ── FILTERS ───────────────────────────────────────────────────────────
    col1, col2, col3 = st.columns([2,1,1])
    with col1:
        search_term = st.text_input("Search quotes", placeholder="e.g. results, budget, trust, agency...")
    with col2:
        source_filter = st.multiselect("Source", ["Respondent.io", "Typeform", "Pollfish open-ended"],
                                        default=["Respondent.io", "Typeform", "Pollfish open-ended"])
    with col3:
        theme_filter = st.selectbox("Theme", ["All", "Results & proof", "Budget & spend",
                                               "Trust & advice", "Audience & reach",
                                               "Time & effort", "Plan quality"])

    theme_keywords = {
        "Results & proof": ["results", "proof", "working", "roi", "return", "know if"],
        "Budget & spend": ["budget", "spend", "cost", "money", "expensive", "afford", "invest"],
        "Trust & advice": ["trust", "advice", "confident", "know what", "recommend", "reliable"],
        "Audience & reach": ["audience", "reach", "who", "customer", "target", "people"],
        "Time & effort": ["time", "effort", "manage", "busy", "overwhelm", "bandwidth"],
        "Plan quality": ["plan", "specific", "generic", "actionable", "clear", "useful"],
    }

    def matches_theme(text, theme):
        if theme == "All": return True
        kws = theme_keywords.get(theme, [])
        return any(kw in str(text).lower() for kw in kws)

    def matches_search(text, term):
        if not term: return True
        return term.lower() in str(text).lower()

    # ── RESPONDENT.IO QUOTES ──────────────────────────────────────────────
    if RESP_OK and "Respondent.io" in source_filter:
        st.markdown("### Respondent.io open responses (n=70)")

        q15_col = "15-What's the one thing that would make you more confident in your advertising decisions?"
        q14_col = "14-Where do you currently advertise (ex/ Google ads, facebook, newspaper ads, instagram, direct mail, Linkedin, podcasts, word of mouth etc)"

        for col_label, col in [("What would make them more confident", q15_col),
                                 ("Where they currently advertise", q14_col)]:
            st.markdown(f"**{col_label}**")
            if col in resp_df.columns:
                shown = 0
                for i, row in resp_df.iterrows():
                    text = str(row.get(col, ""))
                    if len(text) < 15 or text.lower() in ['nan','n/a','na']: continue
                    if not matches_search(text, search_term): continue
                    if not matches_theme(text, theme_filter): continue
                    # Build source label
                    gut = str(row.get("10-When you think about advertising your business, what's your gut reaction?",""))[:35]
                    ind = str(row.get("3-What industry is your business in? ",""))[:25]
                    budget = str(row.get("7-What is your current monthly advertising budget? ",""))[:20]
                    source = f"Respondent.io · {ind} · {gut[:30]}"
                    quote_card(text, source=source)
                    shown += 1
                    if shown >= 20: st.caption("Showing first 20 — use search to narrow"); break
            st.markdown("")

    # ── TYPEFORM QUOTES ───────────────────────────────────────────────────
    if TF_OK and "Typeform" in source_filter:
        st.markdown("### Typeform product survey responses")
        tf_quote_cols = [
            ("What a good plan would include", "In your own words, what would a really good advertising plan for your business include? What would it need to cover for you to trust it and act on it?"),
            ("What Zansei missed", "Was there anything important about your business that Zansei didn't ask about that was also missing from teh plan?"),
            ("What they'd do with $1000", "If you had $1000 to spend on your business today, how would you use it?"),
            ("What they want help with after the plan", "The Plan: \n\nAfter seeing your plan, is there anything you would want ad101 to help you with?"),
        ]
        for label, col in tf_quote_cols:
            relevant = all_tf if TF_OK else pd.DataFrame()
            if col not in relevant.columns: continue
            quotes = relevant[col].dropna()
            quotes = quotes[quotes.apply(lambda x: len(str(x)) > 20)]
            quotes = quotes[quotes.apply(lambda x: matches_search(x, search_term))]
            quotes = quotes[quotes.apply(lambda x: matches_theme(x, theme_filter))]
            if len(quotes) > 0:
                st.markdown(f"**{label}** ({len(quotes)} responses)")
                for val in quotes:
                    company = ""
                    quote_card(str(val), source=f"Typeform · {label}")

    # ── POLLFISH OPEN-ENDED ───────────────────────────────────────────────
    if POLLFISH_OK and "Pollfish open-ended" in source_filter:
        st.markdown("### Pollfish open-ended (aggregated summaries)")
        st.info("Pollfish data is pre-aggregated -- individual quotes not available. Raw CSVs contain full individual responses. Upload the raw Pollfish CSV export in Upload Data for individual quotes.")

    # ── UPLOADED DOC QUOTES ───────────────────────────────────────────────
    if st.session_state.uploaded_docs:
        st.markdown("### From uploaded documents")
        for doc in st.session_state.uploaded_docs:
            sentences = re.split(r'(?<=[.!?])\s+', doc['text'])
            matches = [s.strip() for s in sentences
                      if len(s.strip()) > 40
                      and matches_search(s, search_term)
                      and matches_theme(s, theme_filter)]
            if matches:
                st.markdown(f"**📄 {doc['name']}**")
                for m in matches[:8]:
                    quote_card(m, source=f"{doc['source_type']} · {doc['name']}")

# ════════════════════════════════════════════════════════════════════════════
# TAB 4: CONTENT STUDIO
# ════════════════════════════════════════════════════════════════════════════
with tabs[3]:
    st.markdown('<div class="section-chip">CONTENT STUDIO</div>', unsafe_allow_html=True)
    st.markdown("## Turn data into content")
    st.markdown("*Stats are pulled from the actual data locally. Claude is used only to write the post.*")

    col1, col2 = st.columns([1,2])
    with col1:
        platform = st.selectbox("Platform", ["LinkedIn", "Instagram", "Facebook", "Email newsletter", "Twitter/X"])
        tone = st.selectbox("Tone", ["Authoritative & data-driven", "Warm & conversational", "Short & punchy", "Educational"])
        goal = st.text_area("Your goal", placeholder="e.g. Show SMBs that not knowing where to advertise is the most common challenge...", height=100)

        # Auto-pull relevant stats
        st.markdown("**Relevant stats from the data:**")
        stat_pool = {
            "39% say knowing where to advertise is hardest": ["where", "advertise", "hardest", "channel"],
            "55% are actively advertising but want better results": ["results", "better", "active", "advertising"],
            "44% want content and visual help after a plan": ["content", "visual", "creative", "plan"],
            "1 in 3 would spend more if they saw results first": ["spend", "results", "proof", "invest"],
            "52% have tried a free tool -- only 24% found it useful": ["tool", "free", "useful", "platform"],
            "56% say wasting money is their #1 fear": ["fear", "waste", "money", "risk"],
            "10% spend over $3K/month on ads": ["budget", "spend", "3k", "high"],
            "45% feel confident about advertising": ["confident", "confident", "know", "understand"],
            "30% are second-guessing themselves": ["second-guess", "unsure", "doubt", "confused"],
            "22% previously hired an agency and stopped": ["agency", "hired", "stopped", "burned"],
        }
        auto_stats = []
        if goal:
            for stat, keywords in stat_pool.items():
                if any(kw in goal.lower() for kw in keywords):
                    auto_stats.append(stat)
        if not auto_stats:
            auto_stats = list(stat_pool.keys())[:4]

        selected_stats = st.multiselect("Stats to include", list(stat_pool.keys()),
                                         default=auto_stats[:4])

    with col2:
        st.markdown("**Generated content will appear here**")

        if st.button("✍️ Generate content", type="primary"):
            if not st.session_state.api_key:
                st.error("Add your Anthropic API key in the sidebar first.")
            elif not goal:
                st.error("Enter a goal first.")
            else:
                import requests
                stats_text = "\n".join(f"- {s}" for s in selected_stats)
                platform_guidance = {
                    "LinkedIn": "Professional tone. 150-250 words. Use 2-3 data points. End with a question or insight. No emojis.",
                    "Instagram": "Conversational. 80-120 words. Lead with one striking stat. 3-5 hashtags at end.",
                    "Facebook": "Warm and community-oriented. 100-150 words. Lead with a relatable pain point.",
                    "Email newsletter": "Subject line + 150-200 word body. Data-driven. Clear CTA.",
                    "Twitter/X": "Under 280 characters. One stat. One insight. Punchy.",
                }
                guidance = platform_guidance.get(platform, "")
                prompt = f"""You are a copywriter for ad101.com, an advertising plan platform for small businesses.

Write a {platform} post with this goal: {goal}

Tone: {tone}
Format guidance: {guidance}

Use these real survey statistics from 340+ small business owners as evidence (paraphrase naturally, do not just list them):
{stats_text}

Rules:
- Never say "AI-powered" or "AI" in the post itself
- Always say "advertising plan" not "marketing plan"
- No em dashes
- Write like a knowledgeable friend, not a corporation
- Ground every claim in the data provided
- The brand is ad101.com"""

                with st.spinner(f"Writing {platform} content..."):
                    try:
                        resp_api = requests.post(
                            "https://api.anthropic.com/v1/messages",
                            headers={
                                "x-api-key": st.session_state.api_key,
                                "anthropic-version": "2023-06-01",
                                "content-type": "application/json"
                            },
                            json={
                                "model": "claude-sonnet-4-20250514",
                                "max_tokens": 800,
                                "messages": [{"role": "user", "content": prompt}]
                            },
                            timeout=30
                        )
                        if resp_api.status_code == 200:
                            result = resp_api.json()
                            content = result['content'][0]['text']
                            st.markdown("---")
                            st.markdown(f"**{platform} — {tone}**")
                            st.markdown(content)
                            st.download_button("Copy as text", content,
                                               file_name=f"ad101_{platform.lower().replace('/','_')}_{datetime.now().strftime('%Y%m%d')}.txt")
                        else:
                            st.error(f"API error {resp_api.status_code}: {resp_api.text[:200]}")
                    except Exception as e:
                        st.error(f"Request failed: {e}")

# ════════════════════════════════════════════════════════════════════════════
# TAB 5: UPLOAD DATA
# ════════════════════════════════════════════════════════════════════════════
with tabs[4]:
    st.markdown('<div class="section-chip">UPLOAD DATA</div>', unsafe_allow_html=True)
    st.markdown("## Add new data to the explorer")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Survey data")
        st.markdown("*Upload Typeform, Pollfish, or Respondent.io exports*")
        survey_file = st.file_uploader("Upload survey file", type=['csv','xlsx'],
                                        key="survey_upload")
        survey_type = st.selectbox("Source type", ["Typeform (product survey)",
                                                     "Pollfish v5 (general SMB)",
                                                     "Pollfish v8 (online/hybrid)",
                                                     "Respondent.io",
                                                     "Other CSV"])
        if survey_file and st.button("Add survey data"):
            try:
                if survey_file.name.endswith('.xlsx'):
                    new_df = pd.read_excel(survey_file)
                else:
                    new_df = pd.read_csv(survey_file)
                if "Typeform" in survey_type:
                    if 'Response Type' in new_df.columns:
                        new_df = new_df[new_df['Response Type'].isin(['completed','partial'])]
                    st.session_state.extra_typeforms.append(new_df)
                    st.success(f"Added {len(new_df)} Typeform responses.")
                else:
                    st.success(f"Loaded {len(new_df)} rows from {survey_type}. (Reopen tabs to see updated data.)")
                    st.dataframe(new_df.head(3))
            except Exception as e:
                st.error(f"Error loading file: {e}")

    with col2:
        st.markdown("### Documents")
        st.markdown("*Upload interview summaries, transcripts, or research notes*")
        doc_files = st.file_uploader("Upload documents",
                                      type=['txt','pdf','docx','md'],
                                      accept_multiple_files=True,
                                      key="doc_upload")
        doc_type = st.selectbox("Document type", ["Interview summary", "Interview transcript",
                                                    "Research notes", "Participant brief",
                                                    "Other"])
        if doc_files and st.button("Add documents"):
            added = 0
            for f in doc_files:
                # Avoid duplicates
                existing_names = [d['name'] for d in st.session_state.uploaded_docs]
                if f.name in existing_names:
                    st.warning(f"{f.name} already uploaded.")
                    continue
                text = extract_text_from_file(f)
                st.session_state.uploaded_docs.append({
                    'name': f.name,
                    'source_type': doc_type,
                    'text': text,
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'size': len(text)
                })
                added += 1
            if added:
                st.success(f"Added {added} document(s). Search them in Product Feedback and Quotes tabs.")

    st.markdown("---")
    st.markdown("### Currently loaded data")
    data_summary = {
        "Pollfish v5 (general SMB)": f"{len(v5)} questions" if POLLFISH_OK else "Not loaded",
        "Pollfish v8 (online/hybrid)": f"{len(v8)} questions" if POLLFISH_OK else "Not loaded",
        "Respondent.io (SMB research)": f"{len(resp_df)} respondents" if RESP_OK else "Not loaded",
        "Typeform (product feedback)": f"{len(tf_df)} responses" if TF_OK else "Not loaded",
        "Uploaded typeforms": f"{sum(len(x) for x in st.session_state.extra_typeforms)} responses",
        "Uploaded documents": f"{len(st.session_state.uploaded_docs)} files",
    }
    for source, status in data_summary.items():
        ok = "✅" if "Not loaded" not in status and "0" not in status else "⚠️"
        st.markdown(f"{ok} **{source}**: {status}")

    if st.session_state.uploaded_docs:
        st.markdown("---")
        st.markdown("### Manage uploaded documents")
        for i, doc in enumerate(st.session_state.uploaded_docs):
            c1,c2,c3 = st.columns([3,1,1])
            with c1: st.markdown(f"📄 **{doc['name']}** ({doc['source_type']}) — {doc['size']:,} chars")
            with c2: st.markdown(f"*{doc['date']}*")
            with c3:
                if st.button("Remove", key=f"rm_{i}"):
                    st.session_state.uploaded_docs.pop(i)
                    st.rerun()
