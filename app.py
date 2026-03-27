"""
ad101 Survey Data Explorer
Combines v5 (general SMB) and v8 (online/hybrid) Pollfish survey data.
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io, os
from datetime import datetime

st.set_page_config(page_title="ad101 Survey Explorer", page_icon="📊",
                   layout="wide", initial_sidebar_state="expanded")

INDIGO="#5046E5"; INDIGO_L="#8B82F0"; GRAY="#9CA3AF"
GREEN="#10B981"; RED="#EF4444"; AMBER="#F59E0B"; DARK="#1E1B4B"

# ── PASSWORD ─────────────────────────────────────────────────────────────────
def check_password():
    if st.session_state.get("auth"): return True
    try:
        pwd = st.secrets["password"]
    except Exception:
        st.session_state["auth"] = True; return True
    st.markdown("## ad101 Survey Explorer")
    entered = st.text_input("Password", type="password")
    if st.button("Enter"):
        if entered == pwd: st.session_state["auth"] = True; st.rerun()
        else: st.error("Incorrect password.")
    return False

# ── HELPERS ───────────────────────────────────────────────────────────────────
def sel(df, col):
    if col not in df.columns: return pd.Series(0, index=df.index)
    return (df[col] == "Selected").astype(int)

def vcpct(df, col):
    return (df[col].value_counts(normalize=True)*100).round(1).to_dict()

def mpct(df, prefix):
    cols = [c for c in df.columns if c.startswith(prefix)]
    n = max(len(df), 1)
    return {c.replace(prefix,"").replace("_"," "): round(df[c].sum()/n*100,1) for c in cols}

# ── NORMALIZATION ─────────────────────────────────────────────────────────────
def normalize_v5(df):
    o = pd.DataFrame(index=df.index)
    o["survey"]       = "v5 — General SMB"
    o["respondent_id"]= df.get("ID", pd.RangeIndex(len(df))).astype(str)+"_v5"
    o["age"]          = pd.to_numeric(df["Age"], errors="coerce")
    o["gender"]       = df["Gender"]
    o["region"]       = df["US Region"]
    o["state"]        = df.get("US State", np.nan)
    o["industry_demo"]= np.nan
    o["industry"]     = df["Q1: What industry is your business in?"]
    o["tenure"]       = df["Q2: How long have you been running your business?"]
    o["operation"]    = df["Q3: How does your business primarily operate?"]
    o["revenue"]      = df["Q4: Roughly what was your business's annual revenue last year?"]
    o["gut_reaction"] = df["Q5: When you think about advertising your business, what's your gut reaction?"]
    o["ad_status"]    = df["Q6: Which best describes where you are with advertising right now?"]
    o["time_spent"]   = df["Q7: How much time do you realistically spend on marketing and advertising per week?"]
    o["budget"]       = df["Q9: How much do you currently spend on advertising per month, or if you haven't advertised yet, what would you be comfortable spending?"]
    o["free_tool"]    = df["Q11: Have you ever used a free tool, quiz, or resource to help with your marketing or advertising?"]
    o["involvement"]  = df["Q13: If someone was running your ads for you, how involved would you want to be day to day?"]
    o["ai_attitude"]  = df["Q15: How do you feel about using AI tools to help with your business marketing?"]
    o["nature_affects"]= np.nan
    o["success_def"]  = np.nan

    P8 = "Q8: What feels like the hardest part of advertising for your business? Pick your top two._"
    o["hard_knowing_where"]  = sel(df, P8+"Knowing where to advertise")
    o["hard_who_to_reach"]   = sel(df, P8+"Figuring out who to reach")
    o["hard_how_much"]       = sel(df, P8+"Deciding how much to spend")
    o["hard_creating_ads"]   = sel(df, P8+"Creating the actual ads")
    o["hard_finding_time"]   = sel(df, P8+"Finding the time to manage it")
    o["hard_understanding"]  = sel(df, P8+"Understanding whether it's working")
    o["hard_trusting_advice"]= sel(df, P8+"Trusting that the advice I'm getting is actually right")

    P10 = "Q10: If you had a clear advertising plan built specifically for your business, what would you most want help with after that? Pick your top two._"
    o["help_running_ads"]    = sel(df, P10+"Actually running the ads. I'd want someone to handle it.")
    o["help_content_visuals"]= sel(df, P10+"Creating the content and visuals for the ads")
    o["help_social_media"]   = sel(df, P10+"Managing my social media")
    o["help_email"]          = sel(df, P10+"Setting up and managing email marketing")
    o["help_measuring"]      = sel(df, P10+"Figuring out whether it's working and what to change")
    o["help_try_myself"]     = sel(df, P10+"I'd want to try it myself first before getting help.")
    o["help_nothing"]        = sel(df, P10+"Nothing. I'd handle everything on my own.")

    P14 = "Q14: If you were paying a service to run your ads, what would worry you most? Pick your top two._"
    o["worry_wasting_money"] = sel(df, P14+"Wasting money on ads that don't work")
    o["worry_unexpected"]    = sel(df, P14+"Unexpected charges or fees")
    o["worry_brand_fit"]     = sel(df, P14+"Ads that don't look or sound like my business")
    o["worry_not_knowing"]   = sel(df, P14+"Not knowing what's actually being done with my money")
    o["worry_cant_pause"]    = sel(df, P14+"Not being able to pause or stop quickly if needed")
    o["worry_bad_reports"]   = sel(df, P14+"Getting reports that don't tell me if it's actually working")

    P16 = "Q16: Which online tools or channels do you currently use for marketing or advertising? Select all that apply._"
    o["ch_fb_organic"] = sel(df, P16+"Facebook or Instagram (organic posts)")
    o["ch_fb_ads"]     = sel(df, P16+"Facebook or Instagram ads")
    o["ch_google_ads"] = sel(df, P16+"Google Ads")
    o["ch_email"]      = sel(df, P16+"Email marketing (Mailchimp, Klaviyo, etc.)")
    o["ch_tiktok"]     = sel(df, P16+"TikTok")
    o["ch_yelp_gbp"]   = sel(df, P16+"Yelp or Google Business Profile")
    o["ch_ai_tool"]    = sel(df, P16+"ChatGPT or another AI tool")
    o["ch_no_online"]  = sel(df, P16+"I don't use any online marketing currently.")

    P18 = "Q18: Where do you typically go when looking for business or marketing advice? Select all that apply._"
    o["adv_google"]   = sel(df, P18+"Google search")
    o["adv_youtube"]  = sel(df, P18+"YouTube")
    o["adv_social"]   = sel(df, P18+"Instagram or TikTok")
    o["adv_reddit"]   = sel(df, P18+"Reddit")
    o["adv_fb_groups"]= sel(df, P18+"Facebook groups or online communities")
    o["adv_linkedin"] = sel(df, P18+"LinkedIn")
    o["adv_ai"]       = sel(df, P18+"AI (Claude, ChatGPT, Gemini, etc)")
    o["adv_peers"]    = sel(df, P18+"Other business owners I know ")
    o["adv_dont_look"]= sel(df, P18+"I don't really look for this kind of advice.")

    jarg_map = {"Target Audience":"jarg_target","Paid media":"jarg_paid",
                "Organic reach":"jarg_organic","Programmatic advertising":"jarg_programmatic",
                "Channel strategy":"jarg_channel"}
    jval = {"Extremely familiar":3,"Kind of familiar":2,"I have a rough idea":2,"I'm not sure":1,"Never heard of it":0}
    for col in [c for c in df.columns if "Q12:" in c and "::" in c]:
        term = col.split("::")[-1].strip().rstrip(":")
        key = jarg_map.get(term)
        if key: o[key] = df[col].map(jval)

    o["open_ended"] = df.get("Q19: In your own words, what would make advertising feel less overwhelming for you? (This answer is very important, however, if you do not wish to respond, type N/A)", np.nan)
    o["tried_channels_raw"] = np.nan
    return o


def normalize_v8(df):
    o = pd.DataFrame(index=df.index)
    o["survey"]       = "v8 — Online/Hybrid"
    o["respondent_id"]= df.get("ID", pd.RangeIndex(len(df))).astype(str)+"_v8"
    o["age"]          = pd.to_numeric(df["Age"], errors="coerce")
    o["gender"]       = df["Gender"]
    o["region"]       = df["US Region"]
    o["state"]        = df.get("US State", np.nan)
    o["industry_demo"]= df.get("Industry Work In", np.nan)
    o["industry"]     = df["Q1: What industry is your business in?"]
    o["tenure"]       = df["Q2: How long have you been running your business?"]
    o["operation"]    = df["SQ3: How does your business primarily operate?"]
    o["revenue"]      = df["Q3: Roughly what was your business's annual revenue last year?"]
    o["gut_reaction"] = df["Q4: When you think about advertising your business, what's your gut reaction?"]
    o["ad_status"]    = df["Q5: Which best describes where you are with advertising right now?"]
    o["time_spent"]   = df["Q8: How much time do you realistically spend on marketing and advertising per week?"]
    o["budget"]       = df["Q10: How much do you currently spend on advertising per month, or if you haven't advertised yet, what would you be comfortable spending?"]
    o["free_tool"]    = df["Q12: Have you ever used a free tool, quiz, or resource to help with your marketing or advertising?"]
    o["involvement"]  = df["Q15: If someone was running your ads for you, how involved would you want to be day to day?"]
    o["ai_attitude"]  = df["Q17: How do you feel about using AI tools to help with your business marketing?"]
    o["nature_affects"]= df["Q13: Does the nature of your business affect how you think about advertising?"]

    q7_cols = [c for c in df.columns if c.startswith("Q7:") and "_" in c and "_oe" not in c]
    o["success_def"] = df.apply(lambda row: ", ".join(
        [c.split("_")[-1].strip() for c in q7_cols if str(row.get(c,""))=="Selected"]
    ) or np.nan, axis=1)

    P9 = "Q9: What feels like the hardest part of advertising for your business? Pick your top two._"
    o["hard_knowing_where"]  = sel(df, P9+"Knowing where to advertise")
    o["hard_who_to_reach"]   = sel(df, P9+"Figuring out who to reach")
    o["hard_how_much"]       = sel(df, P9+"Deciding how much to spend")
    o["hard_creating_ads"]   = sel(df, P9+"Creating the actual ads")
    o["hard_finding_time"]   = sel(df, P9+"Finding the time to manage it")
    o["hard_understanding"]  = sel(df, P9+"Understanding whether it's working")
    o["hard_trusting_advice"]= sel(df, P9+"Trusting that the advice I'm getting is actually right")

    P11 = "Q11: If you had a clear advertising plan built specifically for your business, what would you most want help with after that? Pick your top two._"
    o["help_running_ads"]    = sel(df, P11+"Actually running the ads. I'd want someone to handle it.")
    o["help_content_visuals"]= sel(df, P11+"Creating the content and visuals for the ads")
    o["help_social_media"]   = sel(df, P11+"Managing my social media")
    o["help_email"]          = sel(df, P11+"Setting up and managing email marketing")
    o["help_measuring"]      = sel(df, P11+"Figuring out whether it's working and what to change")
    o["help_try_myself"]     = sel(df, P11+"I'd want to try it myself first before getting help.")
    o["help_nothing"]        = sel(df, P11+"Nothing. I'd handle everything on my own.")

    P16 = "Q16: If you were paying a service to run your ads, what would worry you most? Pick your top two._"
    o["worry_wasting_money"] = sel(df, P16+"Wasting money on ads that don't work")
    o["worry_unexpected"]    = sel(df, P16+"Unexpected charges or fees")
    o["worry_brand_fit"]     = sel(df, P16+"Ads that don't look or sound like my business")
    o["worry_not_knowing"]   = sel(df, P16+"Not knowing what's actually being done with my money")
    o["worry_cant_pause"]    = sel(df, P16+"Not being able to pause or stop quickly if needed")
    o["worry_bad_reports"]   = sel(df, P16+"Getting reports that don't tell me if it's actually working")

    P18 = "Q18: Which online tools or channels do you CURRENTLY use for marketing or advertising? Select all that apply._"
    o["ch_fb_organic"] = sel(df, P18+"Facebook or Instagram (organic posts)")
    o["ch_fb_ads"]     = sel(df, P18+"Facebook or Instagram ads")
    o["ch_google_ads"] = sel(df, P18+"Google Ads")
    o["ch_email"]      = sel(df, P18+"Email marketing (Mailchimp, Klaviyo, etc.)")
    o["ch_tiktok"]     = sel(df, P18+"TikTok")
    o["ch_yelp_gbp"]   = sel(df, P18+"Yelp or Google Business Profile")
    o["ch_ai_tool"]    = pd.Series(0, index=df.index)
    o["ch_no_online"]  = sel(df, P18+"I don't use any online marketing currently.")

    P19 = "Q19: Where do you typically go when looking for business or marketing advice? Select all that apply._"
    o["adv_google"]   = sel(df, P19+"Google search")
    o["adv_youtube"]  = sel(df, P19+"YouTube")
    o["adv_social"]   = sel(df, P19+"Instagram or TikTok")
    o["adv_reddit"]   = sel(df, P19+"Reddit")
    o["adv_fb_groups"]= sel(df, P19+"Facebook groups or online communities")
    o["adv_linkedin"] = sel(df, P19+"LinkedIn")
    o["adv_ai"]       = sel(df, P19+"AI (Claude, ChatGPT, Gemini, etc)")
    o["adv_peers"]    = sel(df, P19+"Other business owners I know")
    o["adv_dont_look"]= sel(df, P19+"I don't really look for this kind of advice.")

    jarg_map = {"Target Audience":"jarg_target","Paid media":"jarg_paid",
                "Organic reach":"jarg_organic","Programmatic advertising":"jarg_programmatic",
                "Channel strategy":"jarg_channel"}
    jval = {"Extremely familiar":3,"Kind of familiar":2,"I have a rough idea":2,"I'm not sure":1,"Never heard of it":0}
    for col in [c for c in df.columns if "Q14:" in c and "::" in c]:
        term = col.split("::")[-1].strip().rstrip(":")
        key = jarg_map.get(term)
        if key: o[key] = df[col].map(jval)

    q6_cols = [c for c in df.columns if c.startswith("Q6:") and "_" in c and "_oe" not in c]
    o["tried_channels_raw"] = df.apply(lambda row: ", ".join(
        [c.split("_")[-1].strip() for c in q6_cols if str(row.get(c,""))=="Selected"]
    ) or np.nan, axis=1)

    q20_cols = [c for c in df.columns if c.startswith("Q20:")]
    o["open_ended"] = df[q20_cols[0]] if q20_cols else np.nan
    return o


@st.cache_data(show_spinner="Loading survey data...")
def load_default():
    dfs = []
    for path, fn in [("data/v5_pollfish.xlsx", normalize_v5),
                     ("data/v8_pollfish.xlsx", normalize_v8)]:
        if os.path.exists(path):
            raw = pd.read_excel(path, sheet_name="Individuals")
            dfs.append(fn(raw))
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


def load_uploaded(file, version):
    raw = pd.read_excel(file, sheet_name="Individuals")
    return normalize_v5(raw) if version == "v5" else normalize_v8(raw)


# ── CHARTS ────────────────────────────────────────────────────────────────────
def make_pie(labels, values, title, colors=None):
    colors = (colors or [INDIGO,INDIGO_L,RED,GRAY,"#DC2626",AMBER,GREEN,"#7C3AED","#A78BFA","#4C1D95"])[:len(values)]
    fig = plt.figure(figsize=(5,6)); fig.patch.set_facecolor("white")
    ax = fig.add_axes([0.05,0.28,0.90,0.65])
    wedges,_,autos = ax.pie(values, colors=colors, autopct=lambda p: f"{p:.0f}%" if p>=5 else "",
                             startangle=90, pctdistance=0.72)
    for at in autos: at.set_fontsize(11); at.set_fontweight("bold"); at.set_color("white")
    ax.set_aspect("equal")
    ax.set_title(title, fontsize=11, fontweight="bold", pad=10)
    la = fig.add_axes([0.0,0.0,1.0,0.26]); la.set_axis_off()
    la.legend(wedges, labels, fontsize=9, loc="center", ncol=2, frameon=False,
              handlelength=1.2, handletextpad=0.4)
    return fig


def make_hbar(labels, vals, title, cvals=None, clabel=None, blabel=None):
    n = len(labels)
    fig, ax = plt.subplots(figsize=(7, max(3.5, n*0.52)))
    fig.patch.set_facecolor("white"); ax.set_facecolor("white")
    y = np.arange(n)
    if cvals is not None:
        h = 0.35
        b1 = ax.barh(y+h/2, vals, h, color=INDIGO, alpha=0.92, label=blabel or "Group A")
        b2 = ax.barh(y-h/2, cvals, h, color=INDIGO_L, alpha=0.75, label=clabel or "Group B")
        xmax = max(max(vals), max(cvals)) if vals and cvals else 1
        for bar,v in zip(b1,vals):
            ax.text(bar.get_width()+0.8, bar.get_y()+bar.get_height()/2, f"{v:.0f}%",
                    va="center", fontsize=9, fontweight="bold", color=INDIGO)
        for bar,v in zip(b2,cvals):
            ax.text(bar.get_width()+0.8, bar.get_y()+bar.get_height()/2, f"{v:.0f}%",
                    va="center", fontsize=9, color="#6B7280")
        ax.legend(fontsize=9, loc="upper center", bbox_to_anchor=(0.5,-0.08), ncol=2, frameon=False)
    else:
        xmax = max(vals) if vals else 1
        cs = [INDIGO if v==max(vals) else INDIGO_L if v>=25 else GRAY for v in vals]
        bars = ax.barh(y, vals, color=cs, height=0.55)
        for bar,v in zip(bars,vals):
            ax.text(bar.get_width()+0.8, bar.get_y()+bar.get_height()/2, f"{v:.0f}%",
                    va="center", fontsize=10, fontweight="bold", color="#1F2937")
    ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=10)
    ax.set_xlim(0, xmax+16); ax.set_xlabel("% of Respondents", fontsize=10)
    ax.set_title(title, fontsize=11, fontweight="bold", pad=10)
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    plt.tight_layout(); return fig


# ── SIDEBAR FILTERS ───────────────────────────────────────────────────────────
def sidebar_filters(df):
    st.sidebar.markdown("## 🔍 Filters")
    f = {}
    def ms(label, col, key):
        opts = sorted(df[col].dropna().unique().tolist())
        return st.sidebar.multiselect(label, opts, default=opts, key=key)

    f["survey"]       = ms("Survey", "survey", "f_surv")
    f["operation"]    = ms("Business operation", "operation", "f_op")
    f["industry"]     = ms("Industry (self-reported)", "industry", "f_ind")

    demo_opts = sorted(df["industry_demo"].dropna().unique().tolist())
    if demo_opts:
        sel_d = st.sidebar.multiselect("Industry (Pollfish demographic)", ["All"]+demo_opts, default=["All"], key="f_demo")
        f["industry_demo"] = sel_d

    f["gut_reaction"] = ms("Gut reaction", "gut_reaction", "f_gut")
    f["ad_status"]    = ms("Advertising status", "ad_status", "f_stat")
    f["budget"]       = ms("Monthly budget", "budget", "f_bud")
    f["region"]       = ms("Region", "region", "f_reg")
    f["gender"]       = ms("Gender", "gender", "f_gen")
    f["tenure"]       = ms("Business tenure", "tenure", "f_ten")
    f["revenue"]      = ms("Annual revenue", "revenue", "f_rev")

    mn = int(df["age"].dropna().min()) if df["age"].notna().any() else 18
    mx = int(df["age"].dropna().max()) if df["age"].notna().any() else 70
    f["age"] = st.sidebar.slider("Age range", mn, mx, (mn, mx), key="f_age")

    nat_opts = sorted(df["nature_affects"].dropna().unique().tolist())
    if nat_opts:
        sel_n = st.sidebar.multiselect("Nature affects advertising (v8)", ["All"]+nat_opts, default=["All"], key="f_nat")
        f["nature_affects"] = sel_n

    return f


def apply_filters(df, f):
    m = pd.Series(True, index=df.index)
    for col, val in f.items():
        if col == "age":
            m &= df["age"].between(val[0], val[1])
        elif col == "industry_demo" and val != ["All"]:
            m &= df["industry_demo"].isin(val)
        elif col == "nature_affects" and val != ["All"]:
            m &= df["nature_affects"].isin(val)
        elif isinstance(val, list) and val:
            m &= df[col].isin(val)
    return df[m].copy()


# ── TABS ──────────────────────────────────────────────────────────────────────
def tab_overview(df):
    n = len(df)
    st.markdown(f"### Overview — **{n} respondents** match current filters")
    if n == 0: st.warning("No respondents match the current filters."); return

    sv = df["survey"].value_counts()
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Total", n)
    c2.metric("v5 General", int(sv.get("v5 — General SMB",0)))
    c3.metric("v8 Online/Hybrid", int(sv.get("v8 — Online/Hybrid",0)))
    c4.metric("Median age", int(df["age"].median()) if df["age"].notna().any() else "—")
    conf = round(df["gut_reaction"].str.contains("confident",case=False,na=False).sum()/n*100)
    c5.metric("Feel confident", f"{conf}%")

    st.divider()
    c1,c2 = st.columns(2)
    with c1:
        vc = vcpct(df,"gut_reaction")
        if vc: st.pyplot(make_pie(list(vc.keys()),[round(v,1) for v in vc.values()],"Gut Reaction",
                                   colors=[INDIGO,INDIGO_L,RED,GRAY,"#DC2626"]))
    with c2:
        vc = vcpct(df,"ad_status")
        if vc: st.pyplot(make_pie(list(vc.keys()),[round(v,1) for v in vc.values()],"Advertising Status",
                                   colors=[INDIGO,RED,INDIGO_L,GRAY]))
    c1,c2 = st.columns(2)
    with c1:
        vc = vcpct(df,"budget")
        if vc: st.pyplot(make_pie(list(vc.keys()),[round(v,1) for v in vc.values()],"Monthly Budget",
                                   colors=[INDIGO,GRAY,INDIGO_L,"#7C3AED","#9CA3AF","#A78BFA","#4C1D95"]))
    with c2:
        vc = vcpct(df,"ai_attitude")
        if vc: st.pyplot(make_pie(list(vc.keys()),[round(v,1) for v in vc.values()],"AI Attitudes",
                                   colors=[INDIGO,GREEN,GRAY,AMBER,RED]))


def tab_questions(df):
    n = len(df)
    if n == 0: st.warning("No respondents match the current filters."); return
    st.markdown(f"### All Questions — **{n} respondents**")

    sec = st.selectbox("Section", ["Gut reaction & status","Hardest parts","Success metrics (v8)",
                                    "Budget & help wanted","Worries & involvement",
                                    "Online channels","AI & jargon","Regulation (v8)","Advice sources"])

    if sec == "Gut reaction & status":
        c1,c2 = st.columns(2)
        with c1:
            vc = vcpct(df,"gut_reaction")
            if vc: st.pyplot(make_hbar([k[:35] for k in vc],[round(v,1) for v in vc.values()],"Gut reaction"))
        with c2:
            vc = vcpct(df,"ad_status")
            if vc: st.pyplot(make_hbar([k[:35] for k in vc],[round(v,1) for v in vc.values()],"Advertising status"))
        vc = vcpct(df,"tenure")
        if vc: st.pyplot(make_hbar([k[:35] for k in vc],[round(v,1) for v in vc.values()],"Business tenure"))

    elif sec == "Hardest parts":
        mp = mpct(df,"hard_")
        labels = {"hard knowing where":"Where to advertise","hard who to reach":"Who to reach",
                  "hard how much":"How much to spend","hard creating ads":"Creating actual ads",
                  "hard finding time":"Finding time","hard understanding":"Understanding results",
                  "hard trusting advice":"Trusting the advice"}
        d = {labels.get(k,k):v for k,v in sorted(mp.items(), key=lambda x:x[1],reverse=True)}
        if d: st.pyplot(make_hbar(list(d.keys()),list(d.values()),"Hardest parts of advertising (pick 2)"))

    elif sec == "Success metrics (v8)":
        v8 = df[df["survey"]=="v8 — Online/Hybrid"]
        if len(v8)==0: st.info("v8 only — adjust filters."); return
        from collections import Counter
        items = []
        for val in v8["success_def"].dropna():
            items.extend([x.strip() for x in str(val).split(",") if x.strip()])
        cnt = Counter(items)
        total = len(v8)
        pairs = sorted([(k,round(v/total*100,1)) for k,v in cnt.items()],key=lambda x:x[1],reverse=True)
        if pairs:
            ls,vs = zip(*pairs)
            st.pyplot(make_hbar(list(ls),list(vs),f"What does 'working' mean? (v8, n={total})"))

    elif sec == "Budget & help wanted":
        c1,c2 = st.columns(2)
        with c1:
            vc = vcpct(df,"budget")
            if vc: st.pyplot(make_hbar([k[:30] for k in vc],[round(v,1) for v in vc.values()],"Monthly budget"))
        with c2:
            mp = mpct(df,"help_")
            d = {k.replace("_"," ")[:35]:v for k,v in sorted(mp.items(),key=lambda x:x[1],reverse=True)}
            if d: st.pyplot(make_hbar(list(d.keys()),list(d.values()),"Help wanted after a plan"))

    elif sec == "Worries & involvement":
        c1,c2 = st.columns(2)
        with c1:
            mp = mpct(df,"worry_")
            wl = {"worry wasting money":"Wasting money","worry unexpected":"Unexpected charges",
                  "worry brand fit":"Brand fit","worry not knowing":"Not knowing",
                  "worry cant pause":"Can't pause","worry bad reports":"Bad reports"}
            d = {wl.get(k,k):v for k,v in sorted(mp.items(),key=lambda x:x[1],reverse=True)}
            if d: st.pyplot(make_hbar(list(d.keys()),list(d.values()),"Worries about paid execution"))
        with c2:
            vc = vcpct(df,"involvement")
            if vc: st.pyplot(make_hbar([k[:35] for k in vc],[round(v,1) for v in vc.values()],"Desired involvement"))

    elif sec == "Online channels":
        mp = mpct(df,"ch_")
        cl = {"ch fb organic":"FB/IG organic","ch fb ads":"FB/IG ads","ch google ads":"Google Ads",
              "ch email":"Email","ch tiktok":"TikTok","ch yelp gbp":"Yelp/GBP","ch ai tool":"AI tool"}
        d = {cl.get(k,k):v for k,v in sorted(mp.items(),key=lambda x:x[1],reverse=True) if "no online" not in k}
        if d: st.pyplot(make_hbar(list(d.keys()),list(d.values()),"Current online channels"))

    elif sec == "AI & jargon":
        c1,c2 = st.columns(2)
        with c1:
            vc = vcpct(df,"ai_attitude")
            if vc: st.pyplot(make_hbar([k[:35] for k in vc],[round(v,1) for v in vc.values()],"AI attitudes"))
        with c2:
            jcols = ["jarg_target","jarg_paid","jarg_organic","jarg_programmatic","jarg_channel"]
            jnames = ["Target Audience","Paid media","Organic reach","Programmatic adv.","Channel strategy"]
            pcts = [round((df[c].dropna()>=2).sum()/max(df[c].notna().sum(),1)*100,1) if c in df.columns else 0 for c in jcols]
            st.pyplot(make_hbar(jnames,pcts,"Jargon familiarity (familiar or rough idea)"))

    elif sec == "Regulation (v8)":
        v8 = df[df["survey"]=="v8 — Online/Hybrid"]
        if len(v8)==0: st.info("v8 only."); return
        vc = vcpct(v8,"nature_affects")
        if vc: st.pyplot(make_hbar([k[:50] for k in vc],[round(v,1) for v in vc.values()],
                                    f"Nature affects advertising (v8, n={len(v8)})"))

    elif sec == "Advice sources":
        mp = mpct(df,"adv_")
        al = {"adv google":"Google","adv youtube":"YouTube","adv social":"Instagram/TikTok",
              "adv reddit":"Reddit","adv fb groups":"Facebook groups","adv linkedin":"LinkedIn",
              "adv ai":"AI tools","adv peers":"Other business owners"}
        d = {al.get(k,k):v for k,v in sorted(mp.items(),key=lambda x:x[1],reverse=True) if "dont look" not in k}
        if d: st.pyplot(make_hbar(list(d.keys()),list(d.values()),"Where do you look for advice?"))


def tab_compare(df):
    st.markdown("### Compare Two Segments Side by Side")
    st.info("Sidebar filters apply to both groups. Use controls below to split within that population.")
    c1,c2 = st.columns(2)
    def grp_controls(label, suffix):
        with (c1 if suffix=="a" else c2):
            st.markdown(f"**{label}**")
            gut = st.multiselect("Gut reaction", df["gut_reaction"].dropna().unique().tolist(),
                                  default=df["gut_reaction"].dropna().unique().tolist(), key=f"cg_{suffix}")
            surv = st.multiselect("Survey", df["survey"].dropna().unique().tolist(),
                                   default=df["survey"].dropna().unique().tolist(), key=f"cs_{suffix}")
            bud = st.multiselect("Budget", df["budget"].dropna().unique().tolist(),
                                  default=df["budget"].dropna().unique().tolist(), key=f"cb_{suffix}")
        return df[df["gut_reaction"].isin(gut) & df["survey"].isin(surv) & df["budget"].isin(bud)]

    ga = grp_controls("Group A","a")
    gb = grp_controls("Group B","b")
    st.markdown(f"**Group A:** {len(ga)} &nbsp; **Group B:** {len(gb)}")
    st.divider()
    if len(ga)==0 or len(gb)==0: st.warning("One or both groups are empty."); return

    metric = st.selectbox("Compare on",["Hardest parts","Worries","Help wanted","Online channels",
                                         "AI attitudes","Ad status","Involvement"])
    def gv(grp, prefix, rn):
        return {rn.get(k.replace("_"," "),k):v for k,v in mpct(grp,prefix).items()}

    if metric=="Hardest parts":
        rn={"hard knowing where":"Where to advertise","hard who to reach":"Who to reach",
            "hard how much":"How much","hard creating ads":"Creating ads","hard finding time":"Time",
            "hard understanding":"Understanding","hard trusting advice":"Trusting advice"}
        va=gv(ga,"hard_",rn); vb=gv(gb,"hard_",rn)
    elif metric=="Worries":
        rn={"worry wasting money":"Wasting money","worry unexpected":"Unexpected",
            "worry brand fit":"Brand fit","worry not knowing":"Not knowing",
            "worry cant pause":"Can't pause","worry bad reports":"Bad reports"}
        va=gv(ga,"worry_",rn); vb=gv(gb,"worry_",rn)
    elif metric=="Help wanted":
        rn={"help running ads":"Running ads","help content visuals":"Content",
            "help social media":"Social","help email":"Email","help measuring":"Measuring",
            "help try myself":"Try myself","help nothing":"Nothing"}
        va=gv(ga,"help_",rn); vb=gv(gb,"help_",rn)
    elif metric=="Online channels":
        rn={"ch fb organic":"FB organic","ch fb ads":"FB ads","ch google ads":"Google",
            "ch email":"Email","ch tiktok":"TikTok","ch yelp gbp":"Yelp/GBP"}
        va=gv(ga,"ch_",rn); vb=gv(gb,"ch_",rn)
    elif metric=="AI attitudes":
        va=vcpct(ga,"ai_attitude"); vb=vcpct(gb,"ai_attitude")
    elif metric=="Ad status":
        va=vcpct(ga,"ad_status"); vb=vcpct(gb,"ad_status")
    elif metric=="Involvement":
        va=vcpct(ga,"involvement"); vb=vcpct(gb,"involvement")

    keys = sorted(set(list(va.keys())+list(vb.keys())))
    fig = make_hbar([k[:40] for k in keys],[round(va.get(k,0),1) for k in keys],
                    f"{metric} — A vs B",
                    cvals=[round(vb.get(k,0),1) for k in keys],
                    blabel=f"Group A (n={len(ga)})", clabel=f"Group B (n={len(gb)})")
    st.pyplot(fig, use_container_width=False)


def tab_open_ended(df):
    st.markdown("### Open-Ended Responses")
    rs = df["open_ended"].dropna()
    rs = rs[~rs.astype(str).str.strip().str.lower().isin(["n/a","na","nan","","nothing"])]
    st.markdown(f"**{len(rs)} responses** match current filters.")
    q = st.text_input("Search", placeholder="Filter by keyword...")
    if q: rs = rs[rs.astype(str).str.contains(q,case=False,na=False)]
    for i,(idx,resp) in enumerate(rs.items()):
        if i>=200: st.info("Showing first 200. Use search to narrow down."); break
        row = df.loc[idx]
        tag = "v5" if "v5" in str(row.get("survey","")) else "v8"
        ind = str(row.get("industry",""))[:22]
        gut = str(row.get("gut_reaction",""))[:22]
        st.markdown(f"**[{tag} · {ind} · {gut}]** {resp}")


def tab_upload(df):
    st.markdown("### Add New Survey Data")
    col1,col2 = st.columns([2,1])
    with col1:
        up = st.file_uploader("Upload Pollfish Excel (.xlsx)", type=["xlsx"])
    with col2:
        ver = st.radio("Survey version", ["v5","v8"], index=1)
    if up:
        try:
            nd = load_uploaded(up, ver)
            st.success(f"Loaded {len(nd)} respondents.")
            st.session_state["uploaded"] = nd
            st.dataframe(nd[["survey","industry","gut_reaction","ad_status","budget","region","age","gender"]].head())
        except Exception as e:
            st.error(f"Error: {e}")
    if "uploaded" in st.session_state:
        st.info(f"📎 {len(st.session_state['uploaded'])} uploaded respondents included in this session.")
    st.divider()
    st.markdown("""
**Adding data permanently:** Commit the new `.xlsx` to `data/` in your GitHub repo and update `load_default()` in `app.py` to include it. Streamlit redeploys automatically.

**Adding a new survey version:** Ask Claude to write a `normalize_vX()` function — provide the column structure from the Pollfish export and it takes ~10 minutes.
""")


def tab_raw(df):
    st.markdown(f"### Raw Data — {len(df)} respondents")
    cols = [c for c in ["survey","respondent_id","age","gender","region","state","industry",
                         "industry_demo","tenure","revenue","operation","gut_reaction",
                         "ad_status","budget","ai_attitude","involvement","nature_affects"] if c in df.columns]
    st.dataframe(df[cols], use_container_width=True)
    csv = df[cols].to_csv(index=False)
    st.download_button("Download CSV", csv,
                       file_name=f"ad101_filtered_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                       mime="text/csv")


# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    if not check_password(): return

    st.markdown(f'<h1 style="color:{INDIGO};margin-bottom:2px">ad101 Survey Explorer</h1>'
                f'<p style="color:{GRAY};margin-top:0">v5 General SMB · v8 Online/Hybrid · Any filter, any lens</p>',
                unsafe_allow_html=True)

    base = load_default()
    if "uploaded" in st.session_state:
        base = pd.concat([base, st.session_state["uploaded"]], ignore_index=True)

    if base.empty:
        st.error("No data found. Use the Add Data tab to upload survey files.")
        tab_upload(base); return

    filters = sidebar_filters(base)
    filtered = apply_filters(base, filters)

    st.sidebar.divider()
    st.sidebar.markdown(f"**{len(filtered)} of {len(base)}** respondents match")
    if st.sidebar.button("Reset all filters"): st.rerun()

    tabs = st.tabs(["📊 Overview","📋 All Questions","⚖️ Compare Segments",
                    "💬 Open-Ended","📁 Add Data","🗃️ Raw Data"])
    with tabs[0]: tab_overview(filtered)
    with tabs[1]: tab_questions(filtered)
    with tabs[2]: tab_compare(filtered)
    with tabs[3]: tab_open_ended(filtered)
    with tabs[4]: tab_upload(filtered)
    with tabs[5]: tab_raw(filtered)

if __name__ == "__main__":
    main()
