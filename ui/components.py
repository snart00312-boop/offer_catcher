"""Reusable Streamlit components for the Offer Catcher workbench."""

from __future__ import annotations

import html

import streamlit as st

from data.loader import load_skills
from services.profile_service import EDUCATION_OPTIONS, build_profile, resume_coverage
from ui.presenters import build_match_table_rows, build_top_match_insights


TARGET_OPTIONS = (
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
)


EXAMPLE_PROFILE = build_profile(
    name="示例候选人",
    education="本科",
    school="北京邮电大学",
    major="计算机科学与技术",
    grad_year="2025",
    city="北京",
    skills=("Python", "SQL", "Git", "Docker"),
    experience="参与校园数据平台项目，负责后端接口、数据处理和自动化测试，完成从需求拆分到上线验证。",
    target_position="后端开发",
)


def _esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def render_brand_header(subtitle: bool = True):
    """Render the compact OC brand lockup."""
    compact = " compact" if not subtitle else ""
    subtitle_html = (
        '<p class="subtitle">把简历变成清晰的岗位选择，再用 HR 视角准备下一步。</p>'
        if subtitle
        else ""
    )
    pills = (
        '<div class="header-pills"><span>规则匹配</span><span>简历核对</span><span>HR 解读</span></div>'
        if subtitle
        else ""
    )
    st.html(
        f"""<header class="app-header{compact}">
            <div class="brand-lockup">
                <div class="brand-mark" aria-hidden="true">OC</div>
                <div class="brand-copy">
                    <p class="eyebrow">OFFER CATCHER / CAREER STUDIO</p>
                    <h1>Offer捕手</h1>
                    {subtitle_html}
                </div>
            </div>
            {pills}
        </header>"""
    )


def render_stepper(active: str = "start"):
    steps = (("start", "01", "开始"), ("review", "02", "核对资料"), ("workspace", "03", "岗位工作台"))
    current_index = {name: index for index, (name, _, _) in enumerate(steps)}.get(active, 0)
    parts = []
    for index, (name, number, label) in enumerate(steps):
        state = "is-active" if index == current_index else ("is-done" if index < current_index else "")
        parts.append(f'<div class="step-item {state}"><span>{number}</span><strong>{label}</strong></div>')
        if index < len(steps) - 1:
            parts.append(f'<div class="step-line {"is-done" if index < current_index else ""}"></div>')
    st.html(f'<nav class="stepper" aria-label="流程进度">{"".join(parts)}</nav>')


def render_start_intro():
    st.markdown(
        """
        <section class="hero-copy oc-reveal">
            <div class="hero-kicker">YOUR NEXT MOVE</div>
            <h2>从你的经历，找到下一份机会。</h2>
            <p>上传简历，先确认事实，再看岗位。所有匹配分来自可解释的规则，AI 负责把下一步说清楚。</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_upload_card(has_file: bool = False):
    st.markdown(
        """
        <div class="upload-card oc-reveal">
            <div class="upload-mark" aria-hidden="true">↥</div>
            <div>
                <h3>从简历开始</h3>
                <p>支持文字版 PDF / DOCX，单文件不超过 10MB。解析文本会发送给已配置的 AI 服务。</p>
            </div>
            <div class="upload-meta"><span>PDF</span><span>DOCX</span><span>≤ 3 页 PDF</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _field_label(label: str, field: str, missing: set[str] | None = None, required: bool = False) -> str:
    """Make missing extraction fields visible in text as well as styling."""
    suffix = " *" if required else ""
    if missing and field in missing:
        suffix += " · 待补充"
    return f"{label}{suffix}"


def _render_profile_fields(
    initial: dict | None = None,
    *,
    key_prefix: str,
    missing: set[str] | None = None,
    single_column: bool = False,
) -> dict:
    """Render the shared profile fields inside an already-open form."""
    initial = initial or {}
    missing = missing or set()
    skills_options = list(dict.fromkeys(list(load_skills().get("skills", [])) + list(initial.get("skills", []) or [])))
    initial_skills = [skill for skill in initial.get("skills", []) if skill in skills_options]
    custom_existing = [skill for skill in initial.get("skills", []) if skill not in skills_options]
    target_value = str(initial.get("target_position", "") or "")
    target_index = TARGET_OPTIONS.index(target_value) if target_value in TARGET_OPTIONS else 0
    initial_grad = str(initial.get("grad_year", "") or "")
    grad_options = ("",) + tuple(str(year) for year in range(1980, 2051))
    grad_index = grad_options.index(initial_grad) if initial_grad in grad_options else 0

    st.markdown('<div class="section-label">教育背景</div>', unsafe_allow_html=True)

    def render_education_fields():
        name = st.text_input(_field_label("姓名（选填）", "name", missing), value=initial.get("name", "") or "", placeholder="可匿名", key=f"{key_prefix}_name")
        education = st.selectbox(_field_label("学历", "education", missing, required=True), options=EDUCATION_OPTIONS, index=_edu_index(initial.get("education", "")), key=f"{key_prefix}_education")
        school = st.text_input(_field_label("学校", "school", missing, required=True), value=initial.get("school", "") or "", placeholder="如：北京大学", key=f"{key_prefix}_school")
        major = st.text_input(_field_label("专业", "major", missing, required=True), value=initial.get("major", "") or "", placeholder="如：计算机科学与技术", key=f"{key_prefix}_major")
        grad_year = st.selectbox(_field_label("毕业年份", "grad_year", missing, required=True), options=grad_options, index=grad_index, key=f"{key_prefix}_grad_year")
        city = st.text_input(_field_label("目标城市（选填）", "city", missing), value=initial.get("city", "") or "", placeholder="如：北京、上海", key=f"{key_prefix}_city")
        return name, education, school, major, grad_year, city

    if single_column:
        name, education, school, major, grad_year, city = render_education_fields()
    else:
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input(_field_label("姓名（选填）", "name", missing), value=initial.get("name", "") or "", placeholder="可匿名", key=f"{key_prefix}_name")
            education = st.selectbox(_field_label("学历", "education", missing, required=True), options=EDUCATION_OPTIONS, index=_edu_index(initial.get("education", "")), key=f"{key_prefix}_education")
            school = st.text_input(_field_label("学校", "school", missing, required=True), value=initial.get("school", "") or "", placeholder="如：北京大学", key=f"{key_prefix}_school")
        with col2:
            major = st.text_input(_field_label("专业", "major", missing, required=True), value=initial.get("major", "") or "", placeholder="如：计算机科学与技术", key=f"{key_prefix}_major")
            grad_year = st.selectbox(_field_label("毕业年份", "grad_year", missing, required=True), options=grad_options, index=grad_index, key=f"{key_prefix}_grad_year")
            city = st.text_input(_field_label("目标城市（选填）", "city", missing), value=initial.get("city", "") or "", placeholder="如：北京、上海", key=f"{key_prefix}_city")

    st.markdown('<div class="section-label">技能与经历</div>', unsafe_allow_html=True)
    selected_skills = st.multiselect(_field_label("技能标签", "skills", missing, required=True), options=skills_options, default=initial_skills, placeholder="选择你的技能…", key=f"{key_prefix}_skills")
    custom_skill = st.text_input("其他技能（选填，用逗号分隔）", value=", ".join(custom_existing), placeholder="如：Figma, Scrum", key=f"{key_prefix}_custom_skill")
    experience = st.text_area(_field_label("实习 / 项目经历（选填）", "experience", missing), value=initial.get("experience", "") or "", placeholder="用 1–3 句话描述你做过什么、产生了什么结果。", height=110, key=f"{key_prefix}_experience")

    st.markdown('<div class="section-label">求职偏好</div>', unsafe_allow_html=True)
    target_position = st.selectbox(_field_label("目标岗位方向（选填）", "target_position", missing), options=TARGET_OPTIONS, index=target_index, key=f"{key_prefix}_target")
    custom_target = ""
    if target_position not in ("", "🤷 我不确定，帮我推荐") or (target_value and target_value not in TARGET_OPTIONS):
        custom_target = st.text_input("自定义岗位名称（选填）", value="" if target_position == target_value else target_value, placeholder="如：增长产品经理", key=f"{key_prefix}_custom_target")

    final_target = custom_target.strip() if custom_target.strip() else ("" if target_position == "🤷 我不确定，帮我推荐" else target_position)
    return build_profile(
        name=name,
        education=education,
        school=school,
        major=major,
        grad_year=grad_year,
        skills=selected_skills,
        custom_skill=custom_skill,
        experience=experience,
        target_position=final_target,
        city=city,
    )


def render_manual_profile_form(initial: dict | None = None, key_prefix: str = "manual") -> tuple[dict, bool]:
    """Render the shared manual profile form and return (profile, submitted)."""
    with st.form(f"{key_prefix}_profile_form", border=False):
        profile = _render_profile_fields(initial, key_prefix=key_prefix)
        submitted = st.form_submit_button("确认资料并匹配岗位", type="primary", width="stretch")
    return profile, submitted


def render_profile_summary(profile: dict, source: str = "manual"):
    name = profile.get("name") or "同学"
    source_label = {"resume": "简历识别", "example": "演示数据"}.get(source, "手动填写")
    skills = profile.get("skills", []) or []
    skills_html = "".join(f'<span class="skill-chip">{_esc(skill)}</span>' for skill in skills[:8])
    if len(skills) > 8:
        skills_html += f'<span class="summary-chip">+{len(skills) - 8} 项</span>'
    st.markdown(
        f"""<section class="profile-summary oc-reveal">
            <div class="summary-head"><div><span class="eyebrow">{_esc(source_label)}</span><h2>{_esc(name)}的求职画像</h2></div><span class="status-pill">资料已确认</span></div>
            <div class="summary-grid">
                <div><span>学历 / 学校</span><strong>{_esc(profile.get('education') or '待补充')} · {_esc(profile.get('school') or '待补充')}</strong></div>
                <div><span>专业 / 毕业</span><strong>{_esc(profile.get('major') or '待补充')} · {_esc(profile.get('grad_year') or '待补充')}</strong></div>
                <div><span>目标方向</span><strong>{_esc(profile.get('target_position') or '开放探索')}</strong></div>
                <div><span>目标城市</span><strong>{_esc(profile.get('city') or '不限')}</strong></div>
            </div>
            <div class="summary-skills">{skills_html or '<span class="muted">尚未填写技能</span>'}</div>
        </section>""",
        unsafe_allow_html=True,
    )


def render_match_overview(matched_jobs: list, selected_result=None):
    """Render the stable deterministic overview and compatibility table."""
    if not matched_jobs:
        st.info("暂无匹配结果，请编辑资料后重新匹配。")
        return
    selected_result = selected_result or matched_jobs[0]
    top = build_top_match_insights(selected_result)
    reasons = "".join(f"<li>{_esc(reason)}</li>" for reason in top["reasons"])
    matched_skill_text = "、".join(top["matched_skills"][:3]) or "待补充"
    missing_skill_text = "、".join(top["missing_skills"][:3]) or "暂无明显缺口"
    st.markdown(
        f"""<section class="match-board oc-reveal">
            <div class="top-match-panel"><div class="card-kicker">当前选中岗位</div><h3>{_esc(top['title'])}</h3><p class="match-note">{_esc(top['company'])} · {_esc(top['level'])} · 规则匹配参考分</p><div class="score-line"><span class="score-value">{_esc(top['score'])}</span><span class="score-label">综合匹配度 / 100</span></div><ul class="reason-list">{reasons or '<li>暂无可展示的理由</li>'}</ul></div>
            <div class="signal-panel"><div class="card-kicker">关键判断</div><h3>为什么是它</h3><div class="signal-stack"><div class="signal-row"><span>命中技能</span><strong>{_esc(matched_skill_text)}</strong></div><div class="signal-row"><span>关键缺口</span><strong>{_esc(missing_skill_text)}</strong></div><div class="signal-row"><span>学历状态</span><strong>{_esc(top['education_status'])}</strong></div><div class="signal-row"><span>城市偏好</span><strong>{_esc(top['city_status'])}</strong></div></div></div>
        </section>""",
        unsafe_allow_html=True,
    )
    with st.expander("查看完整岗位排序", expanded=False):
        st.dataframe(build_match_table_rows(matched_jobs, limit=min(10, len(matched_jobs))), hide_index=True, width="stretch")


def render_job_card(result, index: int, selected: bool = False):
    job = result.job
    selected_class = " selected" if selected else ""
    matched = result.skill_match.get("matched_skills", [])
    reason = result.reasons[0] if result.reasons else "根据你的资料计算"
    st.markdown(
        f"""<div class="job-card{selected_class}"><div class="job-card-top"><span class="rank-badge">{index:02d}</span><span class="score-badge">{result.score:.1f}</span></div><h3>{_esc(job.get('title', '未命名岗位'))}</h3><p class="job-company">{_esc(job.get('company', '未标注'))}</p><div class="job-meta"><span>{_esc(job.get('location', '未标注'))}</span><span>{_esc(job.get('salary_range', '面议'))}</span></div><p class="job-reason">{_esc(reason)}</p><div class="job-tags">{''.join(f'<span>{_esc(skill)}</span>' for skill in matched[:3])}</div></div>""",
        unsafe_allow_html=True,
    )


def render_job_detail(result):
    job = result.job
    matched = result.skill_match.get("matched_skills", [])
    missing = result.skill_match.get("missing_skills", [])
    reasons = result.reasons or ["规则匹配结果已生成"]
    st.markdown(
        f"""<section class="job-detail"><div class="card-kicker">岗位详情 · 内置岗位库</div><h2>{_esc(job.get('title', '未命名岗位'))}</h2><p class="detail-company">{_esc(job.get('company', '未标注'))} · {_esc(job.get('location', '未标注'))} · {_esc(job.get('salary_range', '面议'))}</p><div class="detail-score"><strong>{result.score:.1f}</strong><span>规则匹配参考分<br><small>{_esc(result.recommendation_level)}</small></span></div><div class="detail-columns"><div><h4>匹配依据</h4><ul>{''.join(f'<li>{_esc(reason)}</li>' for reason in reasons)}</ul></div><div><h4>技能信号</h4><p><b>已覆盖：</b>{_esc('、'.join(matched) or '暂无')}</p><p><b>待补充：</b>{_esc('、'.join(missing) or '暂无明显缺口')}</p><p><b>学历要求：</b>{_esc(job.get('education_required', '不限'))}</p></div></div><div class="detail-description"><h4>岗位描述</h4><p>{_esc(job.get('description', '暂无岗位描述'))}</p></div></section>""",
        unsafe_allow_html=True,
    )


def render_action_buttons(on_analysis, on_optimization, on_refresh):
    st.markdown('<section class="action-heading"><div><div class="card-kicker">AI ON DEMAND</div><h2>把判断变成下一步</h2><p>选择一个动作，AI 会基于当前选中岗位与规则结果继续分析。</p></div></section>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("生成匹配分析", width="stretch", key="action_analysis"):
            on_analysis()
    with col2:
        if st.button("给出简历建议", width="stretch", key="action_optimization"):
            on_optimization()
    with col3:
        if st.button("重新生成解读", width="stretch", key="action_refresh"):
            on_refresh()


def render_ai_history(chat_history: list[dict]):
    for message in chat_history:
        with st.chat_message(message.get("role", "assistant")):
            st.markdown(message.get("content", ""))


def render_resume_review_panel(raw_text: str, parsed_profile: dict, on_confirm, document_id: str = "resume"):
    """Render editable extraction review with a document-scoped widget namespace."""
    raw_text = str(raw_text or "")
    recognized, total, coverage = resume_coverage(parsed_profile)
    missing = set(parsed_profile.get("_missing_fields", []))
    warnings = parsed_profile.get("_warnings", []) or []
    key_prefix = f"review_{document_id[:12]}"
    st.markdown(f'<div class="review-shell oc-reveal"><div class="review-header"><div><div class="card-kicker">DOCUMENT REVIEW</div><h2>核对识别结果</h2><p>已识别 {recognized}/{total} 项 · 这是完整度，不代表准确率。</p></div><span class="coverage-number">{coverage}%</span></div><div class="coverage-bar"><div class="coverage-fill" style="width:{coverage}%;"></div></div></div>', unsafe_allow_html=True)
    for warning in warnings:
        st.warning(warning)
    if missing:
        labels = {
            "name": "姓名",
            "education": "学历",
            "school": "学校",
            "major": "专业",
            "grad_year": "毕业年份",
            "skills": "技能",
            "experience": "实习 / 项目经历",
        }
        missing_labels = "、".join(labels[field] for field in labels if field in missing)
        st.warning(f"待补充字段：{missing_labels}。请在右侧逐项核对；带 * 的字段补全后才能匹配岗位。")
    with st.form(f"{key_prefix}_form", border=False):
        left, right = st.columns([0.9, 1.25])
        with left:
            st.markdown('<div class="source-panel"><div class="card-kicker">SOURCE TEXT</div><p class="source-caption">仅展示本次解析的文本，文件不会写入项目目录。</p></div>', unsafe_allow_html=True)
            with st.expander("展开原始简历文本", expanded=False):
                st.text(raw_text[:12000])
        with right:
            profile = _render_profile_fields(parsed_profile, key_prefix=key_prefix, missing=missing, single_column=True)
            submitted = st.form_submit_button("确认资料并匹配岗位", type="primary", width="stretch")
    if submitted:
        on_confirm(profile)


def _edu_index(education: str) -> int:
    try:
        return list(EDUCATION_OPTIONS).index(education)
    except ValueError:
        return 0
