"""Visual system for the Offer Catcher career studio."""


def load_css() -> str:
    return """<style>
    :root {
        --oc-bg: #f6f7f3;
        --oc-surface: #ffffff;
        --oc-surface-soft: #eef3ee;
        --oc-ink: #172a28;
        --oc-muted: #526660;
        --oc-line: #dbe5df;
        --oc-teal: #0f766e;
        --oc-teal-deep: #095a55;
        --oc-mint: #e8f3ee;
        --oc-signal: #ef7d45;
        --oc-shadow: 0 18px 50px rgba(24, 57, 50, .08);
    }

    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(circle at 92% 4%, rgba(239, 125, 69, .12), transparent 23rem),
            radial-gradient(circle at 7% 18%, rgba(15, 118, 110, .1), transparent 26rem),
            var(--oc-bg);
        color: var(--oc-ink);
    }
    [data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"] { visibility: hidden; height: 0; background: transparent; }
    .block-container { max-width: 1240px; padding: 2.1rem 2.25rem 3.8rem; }
    p, li, label, span, div { letter-spacing: 0; }
    h1, h2, h3, h4 { font-family: "Source Han Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif; letter-spacing: -.025em; }

    .app-header { display: flex; align-items: flex-end; justify-content: space-between; gap: 1.5rem; padding: .25rem 0 1.35rem; margin-bottom: 1.35rem; border-bottom: 1px solid rgba(23, 42, 40, .13); }
    .app-header.compact { margin-bottom: .65rem; padding-bottom: .8rem; }
    .brand-lockup { display: flex; align-items: center; gap: .9rem; min-width: 0; }
    .brand-mark { width: 46px; height: 46px; display: grid; place-items: center; flex: 0 0 auto; border-radius: 14px 14px 14px 4px; background: var(--oc-teal); color: #fff; font-weight: 850; font-size: .88rem; letter-spacing: .06em; box-shadow: 8px 9px 0 rgba(239, 125, 69, .25); }
    .brand-copy { min-width: 0; }
    .eyebrow, .card-kicker { margin: 0 0 .22rem; color: var(--oc-teal-deep); font-size: .68rem; font-weight: 800; letter-spacing: .14em; text-transform: uppercase; }
    .app-header h1 { margin: 0; color: var(--oc-ink); font-size: 1.75rem; line-height: 1; font-weight: 850; }
    .app-header.compact h1 { font-size: 1.3rem; }
    .subtitle { margin: .45rem 0 0; color: var(--oc-muted); font-size: .93rem; line-height: 1.55; }
    .header-pills { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: .45rem; }
    .header-pills span, .status-pill { border: 1px solid var(--oc-line); border-radius: 999px; padding: .38rem .7rem; background: rgba(255,255,255,.75); color: var(--oc-muted); font-size: .75rem; font-weight: 750; white-space: nowrap; }

    .stepper { display: flex; align-items: center; gap: .62rem; margin: .2rem 0 2.3rem; }
    .step-item { display: flex; align-items: center; gap: .42rem; color: #87958f; font-size: .76rem; font-weight: 750; white-space: nowrap; }
    .step-item span { display: grid; place-items: center; width: 25px; height: 25px; border: 1px solid #ccd9d2; border-radius: 50%; color: #87958f; font-size: .66rem; }
    .step-item.is-active { color: var(--oc-teal-deep); }
    .step-item.is-active span, .step-item.is-done span { border-color: var(--oc-teal); background: var(--oc-teal); color: #fff; }
    .step-line { height: 1px; flex: 1; max-width: 90px; background: #d5e0da; }
    .step-line.is-done { background: var(--oc-teal); }

    .hero-copy { max-width: 710px; margin-bottom: 1.25rem; }
    .hero-kicker { margin-bottom: .55rem; color: var(--oc-signal); font-size: .72rem; font-weight: 850; letter-spacing: .18em; }
    .hero-copy h2 { margin: 0; color: var(--oc-ink); font-size: clamp(2rem, 5vw, 3.35rem); line-height: 1.06; font-weight: 850; }
    .hero-copy p { max-width: 600px; margin: .95rem 0 0; color: var(--oc-muted); font-size: 1rem; line-height: 1.72; }
    .oc-reveal { animation: oc-rise .42s ease both; }
    @keyframes oc-rise { from { opacity: 0; transform: translateY(7px); } to { opacity: 1; transform: translateY(0); } }

    .upload-card { display: flex; align-items: center; gap: 1rem; margin: 1.2rem 0 .85rem; padding: 1.15rem 1.25rem; border: 1px solid rgba(15,118,110,.2); border-radius: 18px; background: linear-gradient(112deg, rgba(232,243,238,.88), rgba(255,255,255,.9)); box-shadow: var(--oc-shadow); }
    .upload-mark { display: grid; place-items: center; width: 45px; height: 45px; flex: 0 0 auto; border-radius: 13px; background: var(--oc-teal); color: #fff; font-size: 1.55rem; font-weight: 300; }
    .upload-card h3 { margin: 0; color: var(--oc-ink); font-size: 1rem; font-weight: 820; }
    .upload-card p { margin: .22rem 0 0; color: var(--oc-muted); font-size: .82rem; line-height: 1.5; }
    .upload-meta { display: flex; flex-wrap: wrap; gap: .4rem; margin-left: auto; }
    .upload-meta span, .job-tags span { border-radius: 999px; padding: .28rem .52rem; background: rgba(15,118,110,.1); color: var(--oc-teal-deep); font-size: .68rem; font-weight: 800; }
    .privacy-note { margin: .45rem 0 1rem; color: #75837d; font-size: .73rem; }
    .entry-actions-label { margin: 1.15rem 0 .5rem; color: var(--oc-muted); font-size: .76rem; font-weight: 760; }
    .file-pill { display: flex; align-items: center; gap: .7rem; margin: .65rem 0; padding: .7rem .8rem; border: 1px solid var(--oc-line); border-radius: 12px; background: var(--oc-surface); }
    .file-icon { display: grid; place-items: center; width: 35px; height: 35px; border-radius: 9px; background: var(--oc-mint); color: var(--oc-teal-deep); font-size: .62rem; font-weight: 850; }
    .file-pill strong, .file-pill small { display: block; }
    .file-pill strong { color: var(--oc-ink); font-size: .83rem; }
    .file-pill small { margin-top: .15rem; color: var(--oc-muted); font-size: .71rem; }

    div[data-testid="stExpander"] { border: 1px solid var(--oc-line); border-radius: 15px; background: rgba(255,255,255,.54); }
    div[data-testid="stForm"] { border: 1px solid var(--oc-line); border-radius: 15px; background: var(--oc-surface); padding: 1.2rem 1.25rem 1rem; box-shadow: var(--oc-shadow); }
    .section-label { margin: .3rem 0 .82rem; padding-left: .7rem; border-left: 3px solid var(--oc-signal); color: var(--oc-ink); font-size: .93rem; font-weight: 820; line-height: 1.2; }
    .stTextInput input, .stTextArea textarea, div[data-baseweb="select"] > div { min-height: 2.75rem; border: 1px solid var(--oc-line) !important; border-radius: 10px !important; background: #fbfcfa !important; box-shadow: none !important; font-size: .9rem !important; }
    .stTextInput input:focus, .stTextArea textarea:focus, div[data-baseweb="select"]:focus-within > div { border-color: var(--oc-teal) !important; background: #fff !important; box-shadow: 0 0 0 3px rgba(15,118,110,.13) !important; }
    .stTextInput label, .stSelectbox label, .stTextArea label, .stMultiSelect label { color: var(--oc-ink) !important; font-size: .82rem !important; font-weight: 700 !important; }
    .stMultiSelect div[data-baseweb="tag"] { border-radius: 999px !important; background: var(--oc-mint) !important; color: var(--oc-teal-deep) !important; font-weight: 700 !important; }
    .stButton button, .stFormSubmitButton button { min-height: 2.75rem; border: 1px solid var(--oc-line) !important; border-radius: 10px !important; background: #fff !important; color: var(--oc-ink) !important; font-weight: 760 !important; transition: transform .16s ease, box-shadow .16s ease, border-color .16s ease; }
    .stButton button:hover, .stFormSubmitButton button:hover { border-color: rgba(15,118,110,.5) !important; box-shadow: 0 8px 20px rgba(23,42,40,.1) !important; transform: translateY(-1px); }
    .stButton button[kind="primary"], .stFormSubmitButton button[kind="primary"] { border-color: var(--oc-teal) !important; background: var(--oc-teal) !important; color: #fff !important; box-shadow: 0 10px 22px rgba(15,118,110,.2) !important; }
    .stButton button[kind="primary"]:hover, .stFormSubmitButton button[kind="primary"]:hover { background: var(--oc-teal-deep) !important; }
    button:focus-visible, input:focus-visible, textarea:focus-visible { outline: 3px solid rgba(239,125,69,.55) !important; outline-offset: 2px; }

    .profile-summary { margin: .2rem 0 1.2rem; padding: 1.15rem 1.25rem; border: 1px solid var(--oc-line); border-radius: 16px; background: rgba(255,255,255,.86); box-shadow: var(--oc-shadow); }
    .summary-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem; }
    .summary-head h2 { margin: 0; color: var(--oc-ink); font-size: 1.25rem; }
    .summary-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: .7rem; margin-top: .95rem; }
    .summary-grid div { padding: .65rem .72rem; border-radius: 10px; background: var(--oc-surface-soft); }
    .summary-grid span, .summary-grid strong { display: block; }
    .summary-grid span { color: var(--oc-muted); font-size: .68rem; }
    .summary-grid strong { margin-top: .28rem; color: var(--oc-ink); font-size: .8rem; line-height: 1.35; }
    .summary-skills { margin-top: .7rem; }
    .summary-chip, .skill-chip { display: inline-flex; align-items: center; max-width: 100%; margin: .15rem .25rem .15rem 0; border-radius: 999px; padding: .22rem .58rem; background: #edf2ef; color: var(--oc-muted); font-size: .75rem; font-weight: 700; vertical-align: middle; }
    .summary-name, .skill-chip { background: var(--oc-mint); color: var(--oc-teal-deep); }
    .muted { color: var(--oc-muted); font-size: .8rem; }

    .workspace-heading { margin-bottom: .9rem; }
    .workspace-heading h2 { margin: 0; color: var(--oc-ink); font-size: 1.35rem; }
    .workspace-heading p { margin: .35rem 0 0; color: var(--oc-muted); font-size: .8rem; line-height: 1.5; }
    .job-card { margin: 0 0 .45rem; padding: .9rem .95rem .82rem; border: 1px solid var(--oc-line); border-radius: 14px; background: rgba(255,255,255,.84); transition: border-color .16s ease, transform .16s ease, box-shadow .16s ease; }
    .job-card.selected { border-color: var(--oc-teal); box-shadow: 0 0 0 2px rgba(15,118,110,.12), var(--oc-shadow); }
    .job-card:hover { border-color: rgba(15,118,110,.5); transform: translateY(-1px); box-shadow: var(--oc-shadow); }
    .job-card-top { display: flex; justify-content: space-between; align-items: center; }
    .rank-badge { color: #81918a; font-size: .68rem; font-weight: 850; letter-spacing: .08em; }
    .score-badge { color: var(--oc-teal-deep); font-size: .94rem; font-weight: 850; }
    .job-card h3 { margin: .42rem 0 .14rem; color: var(--oc-ink); font-size: .98rem; }
    .job-company { margin: 0; color: var(--oc-muted); font-size: .78rem; }
    .job-meta { display: flex; flex-wrap: wrap; gap: .55rem; margin-top: .5rem; color: #6b7b74; font-size: .71rem; }
    .job-reason { margin: .52rem 0 .4rem; color: var(--oc-ink); font-size: .75rem; line-height: 1.45; }
    .job-tags { display: flex; flex-wrap: wrap; gap: .28rem; }
    .job-tags span { padding: .22rem .45rem; font-size: .64rem; }
    .job-detail { padding: 1.25rem 1.35rem; border: 1px solid var(--oc-line); border-radius: 16px; background: var(--oc-surface); box-shadow: var(--oc-shadow); }
    .job-detail h2 { margin: .15rem 0 .2rem; color: var(--oc-ink); font-size: 1.55rem; }
    .detail-company { margin: 0; color: var(--oc-muted); font-size: .82rem; }
    .detail-meta-grid { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: .45rem; margin-top: .85rem; }
    .detail-meta-grid div { min-width: 0; padding: .55rem .62rem; border-radius: 10px; background: var(--oc-surface-soft); }
    .detail-meta-grid span, .detail-meta-grid strong { display: block; overflow-wrap: anywhere; }
    .detail-meta-grid span { color: var(--oc-muted); font-size: .63rem; }
    .detail-meta-grid strong { margin-top: .2rem; color: var(--oc-ink); font-size: .74rem; line-height: 1.35; }
    .detail-score { display: flex; align-items: center; gap: .65rem; margin: 1rem 0; padding: .78rem .85rem; border-radius: 12px; background: var(--oc-mint); color: var(--oc-teal-deep); }
    .detail-score strong { font-size: 2.15rem; line-height: 1; }
    .detail-score span { font-size: .75rem; line-height: 1.35; }
    .detail-score small { font-weight: 800; }
    .detail-columns { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
    .detail-columns h4, .detail-description h4 { margin: 0 0 .42rem; color: var(--oc-ink); font-size: .83rem; }
    .detail-columns p, .detail-columns li, .detail-description p { color: var(--oc-muted); font-size: .78rem; line-height: 1.6; }
    .detail-columns ul { margin: 0; padding-left: 1rem; }
    .detail-description { margin-top: 1rem; padding-top: .85rem; border-top: 1px solid var(--oc-line); }
    .jd-section { margin-top: 1rem; padding-top: .85rem; border-top: 1px solid var(--oc-line); }
    .jd-section h4 { margin: 0 0 .42rem; color: var(--oc-ink); font-size: .83rem; }
    .jd-copy { margin: 0; white-space: pre-wrap; overflow-wrap: anywhere; }
    .jd-list { margin: 0; padding-left: 1.1rem; }
    .jd-list li { margin: .25rem 0; }
    .jd-tags { display: flex; flex-wrap: wrap; gap: .35rem; }
    .jd-tags span { border-radius: 999px; padding: .28rem .55rem; background: var(--oc-mint); color: var(--oc-teal-deep); font-size: .7rem; font-weight: 700; }
    .jd-tags em { color: var(--oc-muted); font-size: .76rem; font-style: normal; }
    .match-board { display: grid; grid-template-columns: minmax(0, 1fr) minmax(220px, .6fr); gap: .8rem; margin: 1rem 0 .9rem; }
    .top-match-panel, .signal-panel { padding: 1rem; border: 1px solid var(--oc-line); border-radius: 14px; background: #fff; }
    .top-match-panel h3, .signal-panel h3 { margin: 0 0 .3rem; color: var(--oc-ink); font-size: 1rem; }
    .score-line { display: flex; align-items: baseline; gap: .5rem; margin: .35rem 0 .55rem; }
    .score-value { color: var(--oc-teal-deep); font-size: 2rem; font-weight: 850; line-height: 1; }
    .score-label { color: var(--oc-muted); font-size: .72rem; font-weight: 700; }
    .reason-list { margin: .45rem 0 0; padding-left: 1rem; color: var(--oc-muted); font-size: .78rem; line-height: 1.65; }
    .signal-stack { display: grid; gap: .4rem; margin-top: .55rem; }
    .signal-row { display: flex; justify-content: space-between; gap: .7rem; padding-bottom: .42rem; border-bottom: 1px solid #edf2ef; color: var(--oc-muted); font-size: .73rem; }
    .signal-row strong { color: var(--oc-ink); text-align: right; }
    .match-note { margin: .35rem 0 .7rem; color: var(--oc-muted); font-size: .76rem; }
    .action-heading { margin-top: 1.2rem; padding-top: 1.05rem; border-top: 1px solid var(--oc-line); }
    .action-heading h2 { margin: 0; color: var(--oc-ink); font-size: 1.08rem; }
    .action-heading p { margin: .28rem 0 .75rem; color: var(--oc-muted); font-size: .78rem; }
    .review-shell { margin: .9rem 0; padding: 1rem; border: 1px solid var(--oc-line); border-radius: 16px; background: rgba(255,255,255,.9); box-shadow: var(--oc-shadow); }
    .review-page-intro { max-width: 760px; margin: .2rem 0 1.1rem; }
    .review-page-intro h2 { margin: 0; color: var(--oc-ink); font-size: clamp(1.45rem, 3vw, 2.1rem); }
    .review-page-intro p { margin: .45rem 0 0; color: var(--oc-muted); font-size: .88rem; line-height: 1.6; }
    .review-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem; }
    .review-header h2 { margin: 0; color: var(--oc-ink); font-size: 1.25rem; }
    .review-header p { margin: .28rem 0 0; color: var(--oc-muted); font-size: .76rem; }
    .coverage-number { color: var(--oc-teal-deep); font-size: 1.55rem; font-weight: 850; }
    .coverage-bar { height: 7px; margin: .72rem 0 1rem; overflow: hidden; border-radius: 999px; background: #e4ece7; }
    .coverage-fill { height: 100%; border-radius: inherit; background: linear-gradient(90deg, var(--oc-teal), #47a68e); }
    .source-panel { padding: .75rem; border-radius: 11px; background: var(--oc-surface-soft); }
    .source-caption { margin: .3rem 0 0; color: var(--oc-muted); font-size: .72rem; line-height: 1.5; }
    .footer { margin-top: 2rem; padding-top: .95rem; border-top: 1px solid rgba(23,42,40,.1); color: #87958f; font-size: .7rem; text-align: center; }

    @media (prefers-reduced-motion: reduce) { .oc-reveal, .job-card, .stButton button, .stFormSubmitButton button { animation: none; transition: none; } }
    @media (max-width: 900px) { .block-container { padding: 1.35rem 1.2rem 2.8rem; } .summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } .upload-card { align-items: flex-start; flex-wrap: wrap; } .upload-meta { margin-left: 0; } }
    @media (max-width: 900px) { .detail-meta-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
    @media (max-width: 680px) { .app-header, .header-pills { align-items: flex-start; flex-direction: column; } .header-pills { justify-content: flex-start; } .stepper { gap: .35rem; margin-bottom: 1.5rem; } .step-item { font-size: .68rem; } .step-item strong { display: none; } .step-line { max-width: none; } .hero-copy h2 { font-size: 2.1rem; } .upload-card { padding: .95rem; } .summary-grid, .detail-columns, .match-board, .detail-meta-grid { grid-template-columns: 1fr; } .job-detail { padding: 1rem; } .stButton button, .stFormSubmitButton button { min-height: 2.9rem; } }
    @media (max-width: 390px) { .block-container { padding-left: .8rem; padding-right: .8rem; } .brand-mark { width: 40px; height: 40px; } .app-header h1 { font-size: 1.45rem; } }
</style>"""
