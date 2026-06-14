"""Offer捕手 - AI 智能体主应用"""
import html
import streamlit as st
from data.loader import load_skills
from services.matcher import match_jobs
from services.ai_service import chat_with_ai_stream
from services.resume_parser import parse_resume, ResumeParseError
from ui.components import (
    render_brand_header,
    render_match_overview,
    render_action_buttons,
    render_resume_review_panel,
)
from ui.styles import load_css


# ——— 页面配置 ——————————————————————————————————————
st.set_page_config(
    page_title="Offer捕手 - AI 智能体",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# ——— Session State —————————————————————————————————

def init_session_state(state):
    defaults = {
        "page": "form",
        "profile": {},
        "profile_source": "manual",
        "resume_raw_text": None,
        "resume_file_name": None,
        "parsed_profile": None,
        "chat_history": [],
        "matched_jobs": [],
        "processing": False,
    }
    for key, default in defaults.items():
        if key not in state:
            state[key] = default


def reset_session(state):
    for key in list(state.keys()):
        del state[key]
    init_session_state(state)


# ——— 工具函数 ——————————————————————————————————————

def get_default_skills() -> list:
    skills_data = load_skills()
    return skills_data.get("skills", [])


def format_profile_for_display(profile: dict) -> str:
    def esc(value) -> str:
        return html.escape(str(value), quote=True)

    parts = []
    if profile.get("name"):
        parts.append(f'<span class="summary-chip summary-name">候选人 · <strong>{esc(profile["name"])}</strong></span>')
    if profile.get("education"):
        edu_text = esc(profile["education"])
        if profile.get("school"):
            edu_text += f" · {esc(profile['school'])}"
        parts.append(f'<span class="summary-chip">学历 · {edu_text}</span>')
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


# ——— 表单提交处理 ——————————————————————————————————

def handle_manual_submit(education, school, major, grad_year, city,
                         selected_skills, custom_skill, experience,
                         target_position, custom_target, name):
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
        return False

    if custom_target and target_position not in ("", "🤷 我不确定，帮我推荐"):
        final_target = custom_target
    else:
        final_target = target_position if target_position != "🤷 我不确定，帮我推荐" else ""

    all_skills = list(selected_skills)
    if custom_skill:
        extra = [s.strip() for s in custom_skill.split(",") if s.strip()]
        all_skills.extend(extra)

    st.session_state["profile"] = {
        "name": name or "同学",
        "education": education,
        "school": school,
        "major": major,
        "grad_year": grad_year,
        "city": city,
        "skills": all_skills,
        "experience": experience,
        "target_position": final_target,
    }
    st.session_state["profile_source"] = "manual"

    with st.spinner("🔍 AI 正在分析你的背景，匹配最佳岗位..."):
        matched = match_jobs(st.session_state["profile"], top_n=10)
        st.session_state["matched_jobs"] = matched

    st.session_state["page"] = "chat"
    return True


def handle_resume_confirm(profile: dict):
    st.session_state["profile"] = profile
    st.session_state["profile_source"] = "resume"
    st.session_state["parsed_profile"] = None

    with st.spinner("🔍 AI 正在分析你的背景，匹配最佳岗位..."):
        matched = match_jobs(st.session_state["profile"], top_n=10)
        st.session_state["matched_jobs"] = matched

    st.session_state["page"] = "chat"


# ——— AI 对话事件处理 ——————————————————————————————

def _append_ai_stream(reply_generator):
    content = st.write_stream(reply_generator)
    st.session_state["chat_history"].append({"role": "assistant", "content": content})
    return content


def handle_first_matching(profile: dict, matched_jobs: list):
    reply_gen = chat_with_ai_stream(
        profile,
        job_context={"matched_jobs": [r.job for r in matched_jobs]},
        query_type="matching",
    )
    _append_ai_stream(reply_gen)


def handle_analysis(profile: dict, matched_jobs: list):
    if st.session_state.get("processing"):
        return
    if not matched_jobs:
        st.warning("暂无匹配的岗位数据")
        return
    st.session_state["processing"] = True
    try:
        top_job = matched_jobs[0].job
        reply_gen = chat_with_ai_stream(
            profile, job_context={"job": top_job}, query_type="analysis",
        )
        _append_ai_stream(reply_gen)
    finally:
        st.session_state["processing"] = False


def handle_optimization(profile: dict, matched_jobs: list):
    if st.session_state.get("processing"):
        return
    if not matched_jobs:
        st.warning("暂无匹配的岗位数据")
        return
    st.session_state["processing"] = True
    try:
        top_job = matched_jobs[0].job
        reply_gen = chat_with_ai_stream(
            profile, job_context={"job": top_job}, query_type="optimization",
        )
        _append_ai_stream(reply_gen)
    finally:
        st.session_state["processing"] = False


def handle_chat_message(prompt: str, profile: dict, matched_jobs: list):
    if st.session_state.get("processing"):
        st.info("AI 正在回复中，请稍候...")
        return
    st.session_state["chat_history"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state["processing"] = True
    try:
        with st.chat_message("assistant"):
            reply_gen = chat_with_ai_stream(
                profile,
                job_context={"matched_jobs": [r.job for r in matched_jobs]},
                query_type="chat",
                user_message=prompt,
            )
            _append_ai_stream(reply_gen)
    finally:
        st.session_state["processing"] = False


# ——— 页面渲染 ——————————————————————————————————————

def render_form_page():
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
        st.markdown('<div class="section-label">基本信息</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("姓名（选填）", placeholder="可匿名")
            education = st.selectbox("学历 *", options=["", "专科", "本科", "硕士", "博士"], index=0)
            school = st.text_input("学校 *", placeholder="如：北京大学")
            major = st.text_input("专业 *", placeholder="如：计算机科学与技术")

        with col2:
            grad_year = st.selectbox("毕业年份 *", options=["", "2025", "2026", "2027", "2028", "2029", "2030"], index=0)
            city = st.text_input("目标城市（选填）", placeholder="如：北京、上海")

            all_skills = get_default_skills()
            selected_skills = st.multiselect("技能标签 *", options=all_skills, placeholder="选择你的技能...")
            custom_skill = st.text_input("其他技能（选填，用逗号分隔）", placeholder="如：Figma, Scrum")

        st.markdown('<div class="section-label">经历与目标</div>', unsafe_allow_html=True)
        experience = st.text_area(
            "实习/项目经历（选填）",
            placeholder="简述你的实习经历或项目经验，如：在XX公司实习X个月，参与XX项目...",
            height=100,
        )

        target_options = [
            "", "产品经理", "前端开发", "后端开发", "数据分析师", "UI/UX 设计师",
            "运营", "测试工程师", "算法工程师", "数据工程师", "运维工程师",
            "产品运营", "新媒体运营", "HR/人力资源", "🤷 我不确定，帮我推荐",
        ]
        target_position = st.selectbox("目标岗位方向 *", options=target_options, index=0)
        custom_target = ""
        if target_position not in ("", "🤷 我不确定，帮我推荐"):
            custom_target = st.text_input("如果上面没有你的目标岗位，请自行输入", placeholder="输入其他岗位名称")

        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        submitted = st.form_submit_button("🚀 开始匹配", type="primary", width="stretch")

    if submitted:
        if handle_manual_submit(
            education=education, school=school, major=major, grad_year=grad_year,
            city=city, selected_skills=selected_skills, custom_skill=custom_skill,
            experience=experience, target_position=target_position,
            custom_target=custom_target, name=name,
        ):
            st.rerun()

    # ── 简历上传 ──
    with st.expander("📄 上传简历自动填写", expanded=False):
        st.markdown(
            '<p style="color:#667085;font-size:0.88rem;margin-bottom:0.75rem;">'
            '支持 PDF / DOCX 格式，AI 将自动提取你的信息并回填表单。</p>',
            unsafe_allow_html=True,
        )
        uploaded_file = st.file_uploader("选择简历文件", type=["pdf", "docx"], label_visibility="collapsed")

        if uploaded_file is not None:
            if uploaded_file.size > 10 * 1024 * 1024:
                st.error("文件大小不能超过 10MB，请压缩后重新上传。")
            elif st.session_state.get("processing"):
                st.info("正在解析中，请稍候...")
            else:
                st.session_state["processing"] = True
                with st.spinner("📄 AI 正在解析你的简历..."):
                    try:
                        file_bytes = uploaded_file.getvalue()
                        parsed = parse_resume(file_bytes, uploaded_file.name)
                        st.session_state["resume_raw_text"] = parsed.get("_raw_text", "")
                        st.session_state["resume_file_name"] = uploaded_file.name
                        st.session_state["parsed_profile"] = parsed
                        st.session_state["processing"] = False
                        st.rerun()
                    except ResumeParseError as e:
                        st.session_state["processing"] = False
                        st.error(f"❌ 解析失败：{e.message}")
                    except Exception as e:
                        st.session_state["processing"] = False
                        st.error(f"❌ 文件读取失败：{str(e)}，请尝试手动填写或更换文件格式。")

        if st.session_state.get("parsed_profile"):
            render_resume_review_panel(
                raw_text=st.session_state.get("resume_raw_text", ""),
                parsed_profile=st.session_state["parsed_profile"],
                on_confirm=handle_resume_confirm,
            )

    st.markdown('<div class="footer">Offer捕手 · AI 驱动求职助手</div>', unsafe_allow_html=True)


def render_chat_page():
    st.markdown(load_css(), unsafe_allow_html=True)

    profile = st.session_state.get("profile", {})
    matched_jobs = st.session_state.get("matched_jobs", [])

    col1, col2 = st.columns([1, 5])
    with col1:
        st.markdown('<div class="back-btn">', unsafe_allow_html=True)
        if st.button("← 返回修改"):
            reset_session(st.session_state)
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        render_brand_header(subtitle=False)

    formatted = format_profile_for_display(profile)
    st.markdown(f'<div class="profile-summary">{formatted}</div>', unsafe_allow_html=True)

    render_match_overview(matched_jobs)

    st.markdown(
        """
        <section class="chat-heading">
            <div>
                <h2>AI 深入解读</h2>
                <p>上方是确定性匹配结果；这里继续用 HR 视角解释面试重点、补短板方向或简历表达。</p>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="chat-shell">', unsafe_allow_html=True)

    for msg in st.session_state.get("chat_history", []):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if not st.session_state.get("chat_history"):
        with st.chat_message("assistant"):
            with st.spinner("🔍 AI 正在为你分析匹配..."):
                handle_first_matching(profile, matched_jobs)

    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.get("processing"):
        st.info("AI 正在处理中，请稍候...")

    render_action_buttons(
        on_analysis=lambda: handle_analysis(profile, matched_jobs),
        on_optimization=lambda: handle_optimization(profile, matched_jobs),
        on_refresh=lambda: _refresh(),
    )

    prompt = st.chat_input("💬 追问 AI 相关问题...（如：这个岗位面试重点是什么？）")
    if prompt:
        handle_chat_message(prompt, profile, matched_jobs)

    st.markdown('<div class="footer">Offer捕手 · AI 驱动求职助手</div>', unsafe_allow_html=True)


def _refresh():
    st.session_state["chat_history"] = []
    st.rerun()


# ——— 主入口 ———————————————————————————————————————

def main():
    init_session_state(st.session_state)
    if st.session_state["page"] == "form":
        render_form_page()
    else:
        render_chat_page()


if __name__ == "__main__":
    main()
