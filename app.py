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
from ui.presenters import build_match_table_rows, build_top_match_insights
from ui.components import (
    render_brand_header,
    render_match_overview,
    render_action_buttons,
)


# ─── 页面配置 ──────────────────────────────────────
st.set_page_config(
    page_title="Offer捕手 - AI 智能体",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="collapsed",
)


from ui.styles import load_css


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
        submitted = st.form_submit_button("🚀 开始匹配", type="primary", width="stretch")

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

    render_action_buttons(
        on_analysis=lambda: _handle_analysis(profile, matched_jobs),
        on_optimization=lambda: _handle_optimization(profile, matched_jobs),
        on_refresh=lambda: _refresh_recommendations(),
    )

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


def _refresh_recommendations():
    """清空聊天历史并重新渲染，触发新一轮匹配。"""
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
