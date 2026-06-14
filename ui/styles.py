"""样式定义 — Offer捕手全局 CSS"""


def load_css():
    return """<style>
    :root {
        --bg: #f3f6f8;
        --panel: #ffffff;
        --panel-soft: #f8fafb;
        --ink: #172033;
        --muted: #667085;
        --line: #d9e2ec;
        --accent: #0f766e;
        --accent-dark: #115e59;
        --accent-soft: #e6f4f1;
        --warning: #b7791f;
    }

    [data-testid="stAppViewContainer"] {
        background:
            linear-gradient(180deg, rgba(15, 118, 110, 0.08), rgba(15, 118, 110, 0) 260px),
            var(--bg);
        color: var(--ink);
    }
    [data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"] {
        background: transparent;
        visibility: hidden;
        height: 0;
    }
    .block-container {
        max-width: 1040px;
        padding: 2rem 2rem 3rem;
    }
    p, li, label, span, div {
        letter-spacing: 0;
    }

    .app-header {
        display: flex;
        align-items: flex-end;
        justify-content: space-between;
        gap: 1.5rem;
        padding: 0.25rem 0 1.2rem;
        margin-bottom: 1.2rem;
        border-bottom: 1px solid rgba(23, 32, 51, 0.12);
    }
    .app-header.compact {
        margin-bottom: 0.6rem;
        padding-bottom: 0.75rem;
    }
    .brand-lockup {
        display: flex;
        align-items: center;
        gap: 0.85rem;
        min-width: 0;
    }
    .brand-mark {
        width: 42px;
        height: 42px;
        border-radius: 8px;
        display: grid;
        place-items: center;
        background: var(--accent);
        color: #fff;
        font-weight: 800;
        box-shadow: 0 10px 24px rgba(15, 118, 110, 0.18);
        flex: 0 0 auto;
    }
    .eyebrow {
        margin: 0 0 0.2rem;
        color: var(--accent-dark);
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
    }
    .app-header h1 {
        margin: 0;
        color: var(--ink);
        font-size: 1.85rem;
        line-height: 1.1;
        font-weight: 800;
    }
    .app-header.compact h1 {
        font-size: 1.35rem;
    }
    .subtitle {
        margin: 0.35rem 0 0;
        color: var(--muted);
        font-size: 0.95rem;
        line-height: 1.55;
    }
    .header-pills {
        display: flex;
        flex-wrap: wrap;
        justify-content: flex-end;
        gap: 0.5rem;
    }
    .header-pills span {
        border: 1px solid var(--line);
        border-radius: 999px;
        padding: 0.35rem 0.7rem;
        background: rgba(255, 255, 255, 0.72);
        color: #475467;
        font-size: 0.78rem;
        font-weight: 650;
        white-space: nowrap;
    }

    .form-heading,
    .chat-heading,
    .action-heading {
        display: flex;
        align-items: flex-end;
        justify-content: space-between;
        gap: 1rem;
        margin: 0.4rem 0 0.8rem;
    }
    .form-heading h2,
    .chat-heading h2,
    .action-heading h2 {
        margin: 0;
        color: var(--ink);
        font-size: 1.15rem;
        font-weight: 760;
    }
    .form-heading p,
    .chat-heading p,
    .action-heading p {
        margin: 0;
        color: var(--muted);
        font-size: 0.86rem;
        line-height: 1.5;
    }

    div[data-testid="stForm"] {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 1.35rem 1.45rem 1.15rem;
        box-shadow: 0 18px 45px rgba(16, 24, 40, 0.08);
    }
    .section-label {
        margin: 0.25rem 0 0.9rem;
        padding-left: 0.75rem;
        border-left: 3px solid var(--accent);
        color: var(--ink);
        font-size: 0.98rem;
        font-weight: 760;
        line-height: 1.2;
    }
    .section-divider {
        margin: 1.05rem 0 1.15rem;
        border: none;
        height: 1px;
        background: var(--line);
    }

    .stTextInput input,
    .stTextArea textarea,
    div[data-baseweb="select"] > div {
        border-radius: 8px !important;
        border: 1px solid var(--line) !important;
        background: var(--panel-soft) !important;
        box-shadow: none !important;
        transition: border-color 0.16s ease, box-shadow 0.16s ease, background 0.16s ease;
        font-size: 0.94rem !important;
    }
    .stTextInput input:focus,
    .stTextArea textarea:focus,
    div[data-baseweb="select"]:focus-within > div {
        border-color: var(--accent) !important;
        background: #fff !important;
        box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.13) !important;
    }
    .stTextInput input::placeholder,
    .stTextArea textarea::placeholder {
        color: #98a2b3 !important;
    }
    .stTextInput label,
    .stSelectbox label,
    .stTextArea label,
    .stMultiSelect label {
        color: #253044 !important;
        font-size: 0.9rem !important;
        font-weight: 650 !important;
    }
    .stMultiSelect div[data-baseweb="tag"] {
        border-radius: 999px !important;
        background: var(--accent-soft) !important;
        color: var(--accent-dark) !important;
        font-weight: 650 !important;
    }
    .stTextArea textarea {
        min-height: 118px !important;
    }

    .stButton button,
    .stFormSubmitButton button {
        min-height: 2.65rem;
        border-radius: 8px !important;
        border: 1px solid var(--line) !important;
        background: #fff !important;
        color: var(--ink) !important;
        font-weight: 720 !important;
        transition: transform 0.16s ease, box-shadow 0.16s ease, border-color 0.16s ease, background 0.16s ease;
    }
    .stButton button:hover,
    .stFormSubmitButton button:hover {
        border-color: rgba(15, 118, 110, 0.45) !important;
        box-shadow: 0 10px 24px rgba(16, 24, 40, 0.08) !important;
        transform: translateY(-1px);
    }
    .stButton button[kind="primary"],
    .stFormSubmitButton button[kind="primary"] {
        border-color: var(--accent) !important;
        background: var(--accent) !important;
        color: #fff !important;
        box-shadow: 0 12px 28px rgba(15, 118, 110, 0.2) !important;
    }
    .stButton button[kind="primary"]:hover,
    .stFormSubmitButton button[kind="primary"]:hover {
        background: var(--accent-dark) !important;
    }

    .profile-summary {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 0.95rem 1rem;
        box-shadow: 0 12px 30px rgba(16, 24, 40, 0.06);
        color: var(--ink);
        line-height: 1.8;
    }
    .match-board {
        margin: 1rem 0 0.9rem;
        display: grid;
        grid-template-columns: minmax(0, 1fr) minmax(220px, 0.38fr);
        gap: 0.85rem;
        align-items: stretch;
    }
    .top-match-panel,
    .signal-panel {
        border: 1px solid var(--line);
        border-radius: 8px;
        background: #fff;
        padding: 1rem;
        box-shadow: 0 12px 28px rgba(16, 24, 40, 0.06);
    }
    .top-match-panel h3,
    .signal-panel h3 {
        margin: 0 0 0.35rem;
        color: var(--ink);
        font-size: 1rem;
        font-weight: 760;
    }
    .score-line {
        display: flex;
        align-items: baseline;
        gap: 0.55rem;
        margin: 0.15rem 0 0.5rem;
    }
    .score-value {
        color: var(--accent-dark);
        font-size: 2rem;
        font-weight: 820;
        line-height: 1;
    }
    .score-label {
        color: var(--muted);
        font-size: 0.83rem;
        font-weight: 650;
    }
    .reason-list {
        margin: 0.55rem 0 0;
        padding-left: 1.05rem;
        color: #344054;
        font-size: 0.88rem;
        line-height: 1.65;
    }
    .signal-stack {
        display: grid;
        gap: 0.42rem;
        margin-top: 0.55rem;
    }
    .signal-row {
        display: flex;
        justify-content: space-between;
        gap: 0.7rem;
        border-bottom: 1px solid #edf2f7;
        padding-bottom: 0.4rem;
        color: var(--muted);
        font-size: 0.84rem;
    }
    .signal-row strong {
        color: var(--ink);
        text-align: right;
    }
    .match-note {
        margin: 0.4rem 0 0.8rem;
        color: var(--muted);
        font-size: 0.84rem;
        line-height: 1.55;
    }
    .summary-chip,
    .skill-chip {
        display: inline-flex;
        align-items: center;
        max-width: 100%;
        margin: 0.15rem 0.28rem 0.15rem 0;
        border-radius: 999px;
        padding: 0.16rem 0.55rem;
        background: #f1f5f9;
        color: #344054;
        font-size: 0.83rem;
        font-weight: 620;
        vertical-align: middle;
    }
    .summary-name,
    .skill-chip {
        background: var(--accent-soft);
        color: var(--accent-dark);
    }

    div[data-testid="chatMessage"] {
        padding: 0.25rem 0;
    }
    .chat-shell {
        margin-top: 1rem;
    }
    div[data-testid="chatMessage"] > div:last-child {
        border: 1px solid var(--line);
        border-radius: 8px !important;
        background: #fff;
        box-shadow: 0 10px 24px rgba(16, 24, 40, 0.05);
    }
    .stChatInputContainer {
        border-top: 1px solid var(--line) !important;
        background: rgba(243, 246, 248, 0.94) !important;
    }
    div[data-testid="stSpinner"] {
        color: var(--accent-dark) !important;
    }

    .action-heading {
        margin-top: 1.3rem;
        padding-top: 1.1rem;
        border-top: 1px solid var(--line);
    }
    .back-btn .stButton button {
        min-height: 2.25rem;
        background: transparent !important;
        color: var(--muted) !important;
        border-color: transparent !important;
        box-shadow: none !important;
    }
    .back-btn .stButton button:hover {
        background: rgba(15, 118, 110, 0.08) !important;
        color: var(--accent-dark) !important;
        transform: none;
    }

    table {
        width: 100%;
        border-collapse: collapse;
        overflow: hidden;
        border-radius: 8px;
        border: 1px solid var(--line);
        background: #fff;
    }
    th {
        background: #eff6f4 !important;
        color: var(--accent-dark) !important;
        font-size: 0.84rem !important;
        font-weight: 760 !important;
        padding: 0.65rem 0.75rem !important;
    }
    td {
        border-top: 1px solid #edf2f7 !important;
        color: #344054 !important;
        font-size: 0.84rem !important;
        padding: 0.62rem 0.75rem !important;
        vertical-align: top;
    }
    tr:nth-child(even) td {
        background: #fafcfc !important;
    }

    .footer {
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid rgba(23, 32, 51, 0.1);
        color: #8792a2;
        font-size: 0.78rem;
        text-align: center;
    }

    /* ── 简历解析新增样式 ── */
    .resume-upload-zone {
        border: 2px dashed var(--line);
        border-radius: 8px;
        padding: 1.5rem;
        text-align: center;
        background: var(--panel-soft);
        transition: border-color 0.2s ease, background 0.2s ease;
    }
    .resume-upload-zone:hover {
        border-color: var(--accent);
        background: var(--accent-soft);
    }
    .resume-review-panel {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: 0 12px 28px rgba(16, 24, 40, 0.06);
    }
    .resume-review-panel .coverage-bar {
        height: 6px;
        border-radius: 3px;
        background: #e5e7eb;
        margin: 0.5rem 0 1rem;
        overflow: hidden;
    }
    .resume-review-panel .coverage-fill {
        height: 100%;
        border-radius: 3px;
        background: var(--accent);
        transition: width 0.4s ease;
    }
    .field-missing {
        border-color: #f59e0b !important;
        box-shadow: 0 0 0 2px rgba(245, 158, 11, 0.18) !important;
    }
    .field-filled {
        border-color: #10b981 !important;
        box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.14) !important;
    }
    .error-card {
        background: #fef2f2;
        border: 1px solid #fecaca;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.75rem 0;
        color: #991b1b;
        font-size: 0.9rem;
    }
    .error-card button {
        margin-top: 0.5rem;
    }

    @media (max-width: 760px) {
        .block-container {
            padding: 1.25rem 1rem 2.25rem;
        }
        .app-header,
        .form-heading,
        .chat-heading,
        .action-heading {
            align-items: flex-start;
            flex-direction: column;
        }
        .header-pills {
            justify-content: flex-start;
        }
        .app-header h1 {
            font-size: 1.45rem;
        }
        div[data-testid="stForm"] {
            padding: 1rem;
        }
        .match-board {
            grid-template-columns: 1fr;
        }
    }
</style>"""
