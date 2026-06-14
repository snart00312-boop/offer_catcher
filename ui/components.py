"""Offer捕手 - UI 组件渲染函数"""

import html
import streamlit as st
from ui.presenters import build_match_table_rows, build_top_match_insights


def render_brand_header(subtitle: bool = True):
    """品牌头部。"""
    compact = " compact" if not subtitle else ""
    header_html = (
        f'<header class="app-header{compact}">'
        '<div class="brand-lockup">'
        '<div class="brand-mark">OC</div>'
        '<div class="brand-copy">'
        '<p class="eyebrow">Offer Catcher</p>'
        '<h1>Offer捕手</h1>'
    )
    if subtitle:
        header_html += '<p class="subtitle">AI 智能匹配岗位，拆解岗位要求，给出可执行的求职建议。</p>'
    header_html += '</div></div>'
    if subtitle:
        header_html += '<div class="header-pills"><span>岗位匹配</span><span>简历分析</span><span>HR 视角</span></div>'
    header_html += '</header>'
    st.html(header_html)


def render_match_overview(matched_jobs: list):
    """渲染可解释岗位推荐概览。"""
    if not matched_jobs:
        st.info("暂无匹配结果，请返回修改资料后重新匹配。")
        return

    top = build_top_match_insights(matched_jobs[0])
    reasons = "".join(f"<li>{html.escape(reason)}</li>" for reason in top["reasons"])
    matched_skill_text = "、".join(top["matched_skills"][:3]) or "待补充"
    missing_skill_text = "、".join(top["missing_skills"][:3]) or "暂无明显缺口"
    st.markdown(
        f"""
        <section class="match-board">
            <div class="top-match-panel">
                <h3>{html.escape(top['title'])}</h3>
                <p class="match-note">{html.escape(top['company'])} · {html.escape(top['level'])}</p>
                <div class="score-line"><span class="score-value">{top['score']}</span><span class="score-label">综合匹配度</span></div>
                <ul class="reason-list">{reasons}</ul>
            </div>
            <div class="signal-panel">
                <h3>关键判断</h3>
                <div class="signal-stack">
                    <div class="signal-row"><span>命中技能</span><strong>{html.escape(matched_skill_text)}</strong></div>
                    <div class="signal-row"><span>关键缺口</span><strong>{html.escape(missing_skill_text)}</strong></div>
                    <div class="signal-row"><span>学历状态</span><strong>{html.escape(top['education_status'])}</strong></div>
                    <div class="signal-row"><span>城市偏好</span><strong>{html.escape(top['city_status'])}</strong></div>
                </div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    rows = build_match_table_rows(matched_jobs, limit=5)
    st.dataframe(rows, hide_index=True, width="stretch")


def render_action_buttons(on_analysis, on_optimization, on_refresh):
    """渲染聊天页快捷操作按钮。"""
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
        if st.button("📊 简历匹配度分析", width="stretch"):
            on_analysis()
    with col2:
        if st.button("✏️ 简历优化建议", width="stretch"):
            on_optimization()
    with col3:
        if st.button("🔄 换一批推荐", width="stretch"):
            on_refresh()


# ── 简历解析 UI ─────────────────────────────────────

def render_resume_review_panel(raw_text: str, parsed_profile: dict, on_confirm):
    """渲染简历解析审核面板。

    Args:
        raw_text: 原始简历文本
        parsed_profile: AI 解析后的 Profile dict（含 _missing_fields）
        on_confirm: 确认回调，接收 parsed_profile 作为参数
    """
    total_fields = 7
    missing = parsed_profile.get("_missing_fields", [])
    coverage = int((total_fields - len(missing)) / total_fields * 100)

    st.markdown('<div class="resume-review-panel">', unsafe_allow_html=True)
    st.markdown(f"### 📋 简历解析结果（覆盖度 {coverage}%）")
    st.markdown(
        f'<div class="coverage-bar"><div class="coverage-fill" style="width:{coverage}%;"></div></div>',
        unsafe_allow_html=True,
    )

    if raw_text:
        with st.expander("📄 查看原始简历文本"):
            st.text(raw_text[:3000])

    profile = dict(parsed_profile)

    col1, col2 = st.columns(2)
    with col1:
        profile["name"] = st.text_input("姓名", value=profile.get("name") or "", key="review_name")
        profile["education"] = st.selectbox(
            "学历", options=["", "专科", "本科", "硕士", "博士"],
            index=_edu_index(profile.get("education", "")), key="review_education",
        )
        profile["school"] = st.text_input("学校", value=profile.get("school") or "", key="review_school")
        profile["major"] = st.text_input("专业", value=profile.get("major") or "", key="review_major")

    with col2:
        profile["grad_year"] = st.text_input(
            "毕业年份", value=str(profile.get("grad_year") or ""), key="review_grad_year",
        )
        profile["skills"] = st.multiselect(
            "技能标签", options=_all_skill_options(),
            default=[s for s in profile.get("skills", []) if s in _all_skill_options()],
            key="review_skills",
        )
        profile["experience"] = st.text_area(
            "实习/项目经历", value=profile.get("experience") or "", key="review_experience", height=100,
        )

    profile["target_position"] = st.text_input(
        "目标岗位方向（选填）", value="", key="review_target", placeholder="如：后端开发工程师",
    )
    profile["city"] = st.text_input(
        "目标城市（选填）", value="", key="review_city", placeholder="如：北京",
    )

    profile.pop("_raw_text", None)
    profile.pop("_missing_fields", None)

    if st.button("✅ 确认并开始匹配", type="primary", width="stretch"):
        on_confirm(profile)

    st.markdown("</div>", unsafe_allow_html=True)


def _edu_index(edu: str) -> int:
    mapping = {"": 0, "专科": 1, "本科": 2, "硕士": 3, "博士": 4}
    return mapping.get(edu, 0)


def _all_skill_options() -> list:
    try:
        from data.loader import load_skills
        return load_skills().get("skills", [])
    except Exception:
        return []
