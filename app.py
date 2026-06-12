"""Offer捕手 - AI 智能体主应用 (UI 增强版)

交互流程:
1. 学生填写个人信息表单
2. 系统进行岗位匹配
3. AI 以 HR 口吻输出推荐结果
4. 学生可选择进一步分析或优化
"""
import html

import streamlit as st
from data.loader import load_skills
from services.matcher import match_jobs
from services.ai_service import chat_with_ai


# ─── 页面配置 ──────────────────────────────────────
st.set_page_config(
    page_title="Offer捕手 - AI 智能体",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# ─── CSS 样式 ──────────────────────────────────────
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
    }
</style>"""


# ─── 工具函数 ──────────────────────────────────────

def get_default_skills():
    """获取预设技能列表"""
    skills_data = load_skills()
    return skills_data.get("skills", [])


def get_skill_categories():
    """获取技能分类"""
    skills_data = load_skills()
    return skills_data.get("categories", {})


def format_profile_for_display(profile: dict) -> str:
    """格式化学生信息为可读文本（HTML 版）"""
    parts = []

    def esc(value) -> str:
        return html.escape(str(value), quote=True)

    if profile.get("name"):
        parts.append(f'<span class="summary-chip summary-name">候选人 · <strong>{esc(profile["name"])}</strong></span>')
    if profile.get("education"):
        education_text = esc(profile["education"])
        if profile.get("school"):
            education_text += f" · {esc(profile['school'])}"
        parts.append(f'<span class="summary-chip">学历 · {education_text}</span>')
    if profile.get("major"):
        parts.append(f'<span class="summary-chip">专业 · {esc(profile["major"])}</span>')
    if profile.get("grad_year"):
        parts.append(f'<span class="summary-chip">毕业 · {esc(profile["grad_year"])}届</span>')
    if profile.get("skills"):
        skills_html = "".join(f'<span class="skill-chip">{esc(s)}</span>' for s in profile["skills"])
        parts.append(skills_html)
    if profile.get("experience"):
        exp = profile["experience"]
        if len(exp) > 60:
            exp = exp[:60] + "..."
        parts.append(f'<span class="summary-chip">经历 · {esc(exp)}</span>')
    if profile.get("target_position"):
        parts.append(f'<span class="summary-chip summary-name">目标 · <strong>{esc(profile["target_position"])}</strong></span>')
    if profile.get("city"):
        parts.append(f'<span class="summary-chip">城市 · {esc(profile["city"])}</span>')
    return "".join(parts) if parts else "暂无信息"


def init_session_state(state):
    """初始化会话状态"""
    if "page" not in state:
        state["page"] = "form"
    if "profile" not in state:
        state["profile"] = {}
    if "chat_history" not in state:
        state["chat_history"] = []
    if "matched_jobs" not in state:
        state["matched_jobs"] = []


def reset_session(state):
    """重置会话"""
    state["page"] = "form"
    state["profile"] = {}
    state["chat_history"] = []
    if "matched_jobs" in state:
        del state["matched_jobs"]
    if "selected_job" in state:
        del state["selected_job"]


# ─── 页面组件 ──────────────────────────────────────

def render_brand_header(subtitle=True):
    """品牌头部"""
    compact = " compact" if not subtitle else ""
    header_html = f'<header class="app-header{compact}">'
    header_html += '<div class="brand-lockup">'
    header_html += '<div class="brand-mark">OC</div>'
    header_html += '<div class="brand-copy">'
    header_html += '<p class="eyebrow">Offer Catcher</p>'
    header_html += '<h1>Offer捕手</h1>'
    if subtitle:
        header_html += '<p class="subtitle">AI 智能匹配岗位，拆解岗位要求，给出可执行的求职建议。</p>'
    header_html += '</div></div>'
    if subtitle:
        header_html += '<div class="header-pills"><span>岗位匹配</span><span>简历分析</span><span>HR 视角</span></div>'
    header_html += '</header>'
    st.html(header_html)


def render_form_page():
    """表单页面 - 收集学生信息"""
    # 注入 CSS
    st.markdown(load_css(), unsafe_allow_html=True)

    render_brand_header()

    st.markdown(
        """
        <section class="form-heading">
            <div>
                <h2>填写你的信息</h2>
                <p>完成基础背景、技能和目标方向后，系统会先做岗位匹配，再进入 AI 对话分析。</p>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    with st.form("student_form"):
        # 基本信息
        st.markdown('<div class="section-label">基本信息</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("姓名（选填）", placeholder="可匿名")
            education = st.selectbox(
                "学历 *",
                options=["", "专科", "本科", "硕士", "博士"],
                index=0,
            )
            school = st.text_input("学校 *", placeholder="如：北京大学")
            major = st.text_input("专业 *", placeholder="如：计算机科学与技术")

        with col2:
            grad_year = st.selectbox(
                "毕业年份 *",
                options=["", "2025", "2026", "2027", "2028", "2029", "2030"],
                index=0,
            )
            city = st.text_input("目标城市（选填）", placeholder="如：北京、上海")

            # 技能多选
            all_skills = get_default_skills()
            selected_skills = st.multiselect(
                "技能标签 *",
                options=all_skills,
                placeholder="选择你的技能...",
            )
            custom_skill = st.text_input(
                "其他技能（选填，用逗号分隔）",
                placeholder="如：Figma, Scrum",
            )

        # 经历
        st.markdown('<div class="section-label">经历与目标</div>', unsafe_allow_html=True)
        experience = st.text_area(
            "实习/项目经历（选填）",
            placeholder="简述你的实习经历或项目经验，如：在XX公司实习X个月，参与XX项目...",
            height=100,
        )

        # 岗位目标
        target_options = [
            "",
            "产品经理",
            "前端开发",
            "后端开发",
            "数据分析师",
            "UI/UX 设计师",
            "运营",
            "测试工程师",
            "算法工程师",
            "数据工程师",
            "运维工程师",
            "产品运营",
            "新媒体运营",
            "HR/人力资源",
            "🤷 我不确定，帮我推荐",
        ]
        target_position = st.selectbox(
            "目标岗位方向 *",
            options=target_options,
            index=0,
            help="选择具体岗位，或选「我不确定」让 AI 帮你推荐",
        )
        custom_target = ""
        if target_position not in ("", "🤷 我不确定，帮我推荐"):
            custom_target = st.text_input(
                "如果上面没有你的目标岗位，请自行输入",
                placeholder="输入其他岗位名称",
            )

        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

        # 提交按钮
        submitted = st.form_submit_button("🚀 开始匹配", type="primary", use_container_width=True)

    if submitted:
        # 表单验证
        errors = []
        if not education:
            errors.append("请选择学历")
        if not school:
            errors.append("请填写学校")
        if not major:
            errors.append("请填写专业")
        if not grad_year:
            errors.append("请选择毕业年份")
        if not selected_skills and not custom_skill:
            errors.append("请至少选择或填写一个技能")

        if errors:
            for e in errors:
                st.error(f"❌ {e}")
        else:
            # 处理目标岗位
            if custom_target and target_position not in ("", "🤷 我不确定，帮我推荐"):
                final_target = custom_target
            else:
                final_target = target_position if target_position != "🤷 我不确定，帮我推荐" else ""

            # 合并自定义技能
            all_user_skills = list(selected_skills)
            if custom_skill:
                extra = [s.strip() for s in custom_skill.split(",") if s.strip()]
                all_user_skills.extend(extra)

            # 保存到 session state
            st.session_state["profile"] = {
                "name": name or "同学",
                "education": education,
                "school": school,
                "major": major,
                "grad_year": grad_year,
                "city": city,
                "skills": all_user_skills,
                "experience": experience,
                "target_position": final_target,
            }

            # 执行匹配
            with st.spinner("🔍 AI 正在分析你的背景，匹配最佳岗位..."):
                matched = match_jobs(
                    st.session_state["profile"],
                    top_n=10,
                )
                st.session_state["matched_jobs"] = matched

            # 跳转到聊天页
            st.session_state["page"] = "chat"
            st.rerun()

    # Footer
    st.markdown('<div class="footer">Offer捕手 · AI 驱动求职助手</div>', unsafe_allow_html=True)


def render_chat_page():
    """聊天页面 - AI 交互"""
    # 注入 CSS
    st.markdown(load_css(), unsafe_allow_html=True)

    profile = st.session_state.get("profile", {})
    matched_jobs = st.session_state.get("matched_jobs", [])

    # 顶部导航
    col1, col2 = st.columns([1, 5])
    with col1:
        st.markdown('<div class="back-btn">', unsafe_allow_html=True)
        st.button("← 返回修改", on_click=reset_session, args=[st.session_state])
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        render_brand_header(subtitle=False)

    # 学生信息摘要
    formatted = format_profile_for_display(profile)
    st.markdown(
        f'<div class="profile-summary">{formatted}</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <section class="chat-heading">
            <div>
                <h2>岗位推荐与追问</h2>
                <p>AI 会基于当前资料解释推荐理由，你也可以继续追问面试重点、补短板方向或简历表达。</p>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    # 聊天区域
    st.markdown('<div class="chat-shell">', unsafe_allow_html=True)

    # 显示聊天历史
    for msg in st.session_state.get("chat_history", []):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 如果没有聊天历史，自动触发首次推荐
    if not st.session_state.get("chat_history"):
        _handle_first_matching(profile, matched_jobs)

    st.markdown("</div>", unsafe_allow_html=True)

    render_action_buttons(profile, matched_jobs)

    # 输入框
    prompt = st.chat_input("💬 追问 AI 相关问题...（如：这个岗位面试重点是什么？）")
    if prompt:
        st.session_state["chat_history"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("🤔 AI 正在思考..."):
                reply = chat_with_ai(
                    profile,
                    job_context={"matched_jobs": [r.job for r in matched_jobs]},
                    query_type="chat",
                    user_message=prompt,
                )
                st.markdown(reply)
                st.session_state["chat_history"].append({"role": "assistant", "content": reply})

    # Footer
    st.markdown('<div class="footer">Offer捕手 · AI 驱动求职助手</div>', unsafe_allow_html=True)


def _handle_first_matching(profile: dict, matched_jobs: list):
    """首次进入聊天页时自动触发岗位匹配推荐"""
    with st.chat_message("assistant"):
        with st.spinner("🔍 AI 正在为你分析匹配..."):
            reply = chat_with_ai(
                profile,
                job_context={"matched_jobs": [r.job for r in matched_jobs]},
                query_type="matching",
            )
            st.markdown(reply)
            st.session_state["chat_history"].append({"role": "assistant", "content": reply})


def render_action_buttons(profile: dict, matched_jobs: list):
    """渲染聊天页快捷操作。"""
    # 快速操作
    st.markdown(
        """
        <section class="action-heading">
            <div>
                <h2>继续深入</h2>
                <p>选择一个方向，AI 会基于当前匹配岗位继续分析。</p>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📊 简历匹配度分析", use_container_width=True):
            _handle_analysis(profile, matched_jobs)

    with col2:
        if st.button("✏️ 简历优化建议", use_container_width=True):
            _handle_optimization(profile, matched_jobs)

    with col3:
        if st.button("🔄 换一批推荐", use_container_width=True):
            st.session_state["chat_history"] = []
            st.rerun()


def _handle_analysis(profile: dict, matched_jobs: list):
    """处理匹配度分析请求"""
    if not matched_jobs:
        st.warning("暂无匹配的岗位数据")
        return

    top_job = matched_jobs[0].job

    with st.chat_message("assistant"):
        with st.spinner("📊 AI 正在分析简历匹配度..."):
            reply = chat_with_ai(
                profile,
                job_context={"job": top_job},
                query_type="analysis",
            )
            st.markdown(reply)
            st.session_state["chat_history"].append({"role": "assistant", "content": reply})


def _handle_optimization(profile: dict, matched_jobs: list):
    """处理简历优化建议请求"""
    if not matched_jobs:
        st.warning("暂无匹配的岗位数据")
        return

    top_job = matched_jobs[0].job

    with st.chat_message("assistant"):
        with st.spinner("✏️ AI 正在为你生成优化建议..."):
            reply = chat_with_ai(
                profile,
                job_context={"job": top_job},
                query_type="optimization",
            )
            st.markdown(reply)
            st.session_state["chat_history"].append({"role": "assistant", "content": reply})


# ─── 主入口 ───────────────────────────────────────

def main():
    """应用主入口"""
    init_session_state(st.session_state)

    if st.session_state["page"] == "form":
        render_form_page()
    else:
        render_chat_page()


if __name__ == "__main__":
    main()
