"""Offer捕手 — a focused Streamlit career matching studio."""

from __future__ import annotations

import hashlib
import html

import streamlit as st

from services.ai_service import call_ai_chat, chat_with_ai_stream
from services.matcher import match_jobs
from services.profile_service import build_profile, validate_profile
from services.resume_parser import ResumeParseError, parse_resume
from ui.components import (
    render_action_buttons,
    render_ai_history,
    render_brand_header,
    EXAMPLE_PROFILE,
    render_job_card,
    render_job_detail,
    render_manual_profile_form,
    render_match_overview,
    render_profile_summary,
    render_resume_review_panel,
    render_start_intro,
    render_stepper,
    render_upload_card,
)
from ui.session import (
    clear_resume_state,
    init_session_state as _init_session_state,
    mark_profile_changed,
    reset_session as _reset_session,
    select_first_job,
    selected_job_result,
)
from ui.styles import load_css


st.set_page_config(
    page_title="Offer捕手 · Career Studio",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def init_session_state(state):
    """Backward-compatible wrapper used by tests and the app entry point."""
    _init_session_state(state)


def reset_session(state):
    """Backward-compatible full flow reset."""
    _reset_session(state)


def get_default_skills() -> list:
    from data.loader import load_skills

    return load_skills().get("skills", [])


def format_profile_for_display(profile: dict) -> str:
    """Keep a compact HTML summary for compatibility with existing callers."""
    def esc(value) -> str:
        return html.escape(str(value or ""), quote=True)

    parts: list[str] = []
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
        parts.append("".join(f'<span class="skill-chip">{esc(skill)}</span>' for skill in profile["skills"]))
    if profile.get("experience"):
        experience = str(profile["experience"])
        parts.append(f'<span class="summary-chip">经历 · {esc(experience[:60] + ("..." if len(experience) > 60 else ""))}</span>')
    if profile.get("target_position"):
        parts.append(f'<span class="summary-chip summary-name">目标 · <strong>{esc(profile["target_position"])}</strong></span>')
    if profile.get("city"):
        parts.append(f'<span class="summary-chip">城市 · {esc(profile["city"])}</span>')
    return "".join(parts) if parts else "暂无信息"


def _file_id(file_bytes: bytes, filename: str) -> str:
    return hashlib.sha256(file_bytes).hexdigest()[:24] + ":" + str(filename or "").lower()


def _save_profile_and_match(profile: dict, source: str) -> bool:
    errors = validate_profile(profile)
    if errors:
        for error in errors:
            st.error(f"{error}")
        return False
    if source in {"manual", "example"}:
        # A manual submission is an intentional choice of source; do not leave
        # a previously selected resume looking like an unfinished parse.
        clear_resume_state(st.session_state)
    st.session_state["profile"] = profile
    st.session_state["profile_source"] = source
    mark_profile_changed(st.session_state)
    with st.spinner("正在计算可解释的岗位匹配…"):
        st.session_state["matched_jobs"] = match_jobs(profile, top_n=10)
    select_first_job(st.session_state)
    st.session_state["page"] = "workspace"
    st.session_state["manual_form_open"] = False
    st.session_state["resume_status"] = "confirmed" if source == "resume" else "idle"
    return True


def handle_manual_submit(
    education,
    school,
    major,
    grad_year,
    city,
    selected_skills,
    custom_skill,
    experience,
    target_position,
    custom_target,
    name,
):
    """Validate and submit the shared manual form."""
    final_target = custom_target.strip() if custom_target and custom_target.strip() else ("" if target_position == "🤷 我不确定，帮我推荐" else target_position)
    profile = build_profile(
        name=name,
        education=education,
        school=school,
        major=major,
        grad_year=grad_year,
        city=city,
        skills=selected_skills,
        custom_skill=custom_skill,
        experience=experience,
        target_position=final_target,
    )
    return _save_profile_and_match(profile, "manual")


def handle_resume_confirm(profile: dict):
    """Validate the edited extraction and enter the deterministic workspace."""
    if not _save_profile_and_match(profile, "resume"):
        return False
    # Keep the confirmed draft in session state until the user starts a new
    # document. Streamlit may still serialize the review widgets during the
    # rerun triggered by the confirmation; clearing it here can leave stale
    # widget state in testing and browser sessions.
    st.session_state["resume_status"] = "confirmed"
    st.rerun()
    return True


def _append_ai_stream(reply_generator, *, label: str = ""):
    content = st.write_stream(reply_generator)
    if content:
        st.session_state["chat_history"].append({"role": "assistant", "content": content, "label": label})
    return content


def _ai_context(profile: dict, matched_jobs: list, selected=None) -> dict:
    return {
        "matched_jobs": matched_jobs,
        "selected_match": selected,
        "job": selected.job if selected is not None else {},
    }


def handle_first_matching(profile: dict, matched_jobs: list):
    """Compatibility entry point; matching explanations are now on demand."""
    selected = selected_job_result(st.session_state) or (matched_jobs[0] if matched_jobs else None)
    return _append_ai_stream(
        chat_with_ai_stream(profile, job_context=_ai_context(profile, matched_jobs, selected), query_type="matching"),
        label="岗位匹配解读",
    )


def handle_analysis(profile: dict, matched_jobs: list):
    if st.session_state.get("processing"):
        return
    selected = selected_job_result(st.session_state) or (matched_jobs[0] if matched_jobs else None)
    if selected is None:
        st.warning("暂无匹配的岗位数据")
        return
    st.session_state["processing"] = True
    st.session_state["processing_kind"] = "analysis"
    try:
        _append_ai_stream(
            chat_with_ai_stream(profile, job_context=_ai_context(profile, matched_jobs, selected), query_type="analysis", chat_history=st.session_state.get("chat_history", [])),
            label=f"{selected.job.get('title', '岗位')} · 匹配分析",
        )
    finally:
        st.session_state["processing"] = False
        st.session_state["processing_kind"] = None


def handle_optimization(profile: dict, matched_jobs: list):
    if st.session_state.get("processing"):
        return
    selected = selected_job_result(st.session_state) or (matched_jobs[0] if matched_jobs else None)
    if selected is None:
        st.warning("暂无匹配的岗位数据")
        return
    st.session_state["processing"] = True
    st.session_state["processing_kind"] = "optimization"
    try:
        _append_ai_stream(
            chat_with_ai_stream(profile, job_context=_ai_context(profile, matched_jobs, selected), query_type="optimization", chat_history=st.session_state.get("chat_history", [])),
            label=f"{selected.job.get('title', '岗位')} · 简历建议",
        )
    finally:
        st.session_state["processing"] = False
        st.session_state["processing_kind"] = None


def handle_chat_message(prompt: str, profile: dict, matched_jobs: list):
    if st.session_state.get("processing"):
        st.info("AI 正在回复中，请稍候…")
        return
    selected = selected_job_result(st.session_state)
    history = st.session_state.get("chat_history", [])
    st.session_state["chat_history"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state["processing"] = True
    st.session_state["processing_kind"] = "chat"
    try:
        with st.chat_message("assistant"):
            _append_ai_stream(
                chat_with_ai_stream(profile, job_context=_ai_context(profile, matched_jobs, selected), query_type="chat", user_message=prompt, chat_history=history),
                label="追问",
            )
    finally:
        st.session_state["processing"] = False
        st.session_state["processing_kind"] = None


def _render_resume_flow(*, show_uploader: bool = True) -> None:
    """Render upload selection, explicit parsing and review without duplicate calls."""
    if show_uploader:
        uploaded_file = st.file_uploader(
            "选择简历文件",
            type=["pdf", "docx"],
            label_visibility="collapsed",
            key=f"resume_uploader_{st.session_state.get('resume_uploader_version', 0)}",
        )
        if uploaded_file is not None:
            file_bytes = uploaded_file.getvalue()
            current_id = _file_id(file_bytes, uploaded_file.name)
            if current_id != st.session_state.get("resume_selected_id"):
                st.session_state["resume_selected_id"] = current_id
                st.session_state["resume_selected_name"] = uploaded_file.name
                st.session_state["resume_selected_size"] = uploaded_file.size
                st.session_state["resume_selected_bytes"] = file_bytes
                st.session_state["resume_document_id"] = current_id
                st.session_state["resume_status"] = "selected"
                st.session_state["resume_error"] = None
                st.session_state["parsed_profile"] = None
                st.session_state["resume_raw_text"] = None

    selected_name = st.session_state.get("resume_selected_name")
    status = st.session_state.get("resume_status", "idle")
    if selected_name:
        size_kb = max(1, round(st.session_state.get("resume_selected_size", 0) / 1024))
        suffix = html.escape(str(selected_name).rsplit(".", 1)[-1].upper())
        status_label = "已解析，等待核对" if status == "review" else ("解析失败" if status == "error" else ("已确认" if status == "confirmed" else "已选择，等待解析"))
        st.markdown(f'<div class="file-pill"><span class="file-icon">{suffix}</span><div><strong>{html.escape(selected_name)}</strong><small>{size_kb} KB · {status_label}</small></div></div>', unsafe_allow_html=True)

    if status == "selected" and st.session_state.get("resume_selected_bytes"):
        if st.button("解析这份简历", type="primary", width="stretch", key="parse_resume_button"):
            st.session_state["resume_status"] = "extracting"
            st.session_state["processing"] = True
            st.session_state["processing_kind"] = "resume"
            try:
                with st.spinner("正在读取文本并识别资料…"):
                    parsed = parse_resume(
                        st.session_state["resume_selected_bytes"],
                        st.session_state["resume_selected_name"],
                        ai_service=call_ai_chat,
                    )
                st.session_state["resume_raw_text"] = parsed.get("_raw_text", "")
                st.session_state["resume_file_name"] = st.session_state["resume_selected_name"]
                st.session_state["parsed_profile"] = parsed
                st.session_state["resume_status"] = "review"
                st.session_state["resume_error"] = None
                st.session_state["resume_parse_count"] = int(st.session_state.get("resume_parse_count", 0)) + 1
            except ResumeParseError as exc:
                st.session_state["resume_status"] = "error"
                st.session_state["resume_error"] = exc.message
            except Exception as exc:
                st.session_state["resume_status"] = "error"
                st.session_state["resume_error"] = f"文件读取失败：{exc}"
            finally:
                st.session_state["processing"] = False
                st.session_state["processing_kind"] = None
            status = st.session_state.get("resume_status", "idle")
            if status == "review":
                st.rerun()

    if status == "error" and st.session_state.get("resume_error"):
        st.error(st.session_state["resume_error"])
        st.caption("你可以重新解析这份文件，或展开下方手动填写资料。")
        if st.button("重新解析", key="retry_resume_button"):
            st.session_state["resume_status"] = "selected"
            st.session_state["resume_error"] = None
            st.rerun()

    if status == "review" and st.session_state.get("parsed_profile"):
        render_resume_review_panel(
            raw_text=st.session_state.get("resume_raw_text", ""),
            parsed_profile=st.session_state["parsed_profile"],
            on_confirm=handle_resume_confirm,
            document_id=st.session_state.get("resume_document_id", "resume"),
        )
        if st.button("换一份简历", key="replace_resume_button"):
            clear_resume_state(st.session_state)
            st.rerun()


def _render_start_actions() -> None:
    """Keep secondary entry points visible without expanding the long form."""
    st.markdown('<div class="entry-actions-label">或者从这里开始</div>', unsafe_allow_html=True)
    left, right = st.columns(2)
    with left:
        if st.button("手动填写资料", width="stretch", key="open_manual_button"):
            st.session_state["manual_form_open"] = True
            st.rerun()
    with right:
        if st.button("试用示例数据", width="stretch", key="example_profile_button"):
            if _save_profile_and_match(EXAMPLE_PROFILE, "example"):
                st.rerun()


def _render_start_page() -> None:
    st.markdown(load_css(), unsafe_allow_html=True)
    render_brand_header()
    render_stepper("start")
    render_start_intro()
    render_upload_card(bool(st.session_state.get("resume_selected_name")))
    st.markdown('<div class="privacy-note">简历只在当前会话中处理，不会写入项目目录。确认前请检查识别结果。</div>', unsafe_allow_html=True)
    _render_resume_flow()
    _render_start_actions()

    with st.expander("手动填写资料", expanded=bool(st.session_state.get("manual_form_open"))):
        st.caption("没有简历也可以直接开始。上传和手动入口使用同一套匹配规则。")
        profile, submitted = render_manual_profile_form(initial=st.session_state.get("profile") or {}, key_prefix="manual")
        if submitted and _save_profile_and_match(profile, "manual"):
            st.rerun()
    st.markdown('<div class="footer">Offer捕手 · Career Studio · 内置岗位库</div>', unsafe_allow_html=True)


def _render_review_page() -> None:
    """Render the document review as a focused second step."""
    st.markdown(load_css(), unsafe_allow_html=True)
    render_brand_header(subtitle=False)
    render_stepper("review")
    st.markdown('<section class="review-page-intro"><div class="card-kicker">STEP 02 · REVIEW</div><h2>确认这份简历，再开始匹配</h2><p>字段只在当前会话中编辑。补齐带 * 的项目后，岗位排序才会使用这份画像。</p></section>', unsafe_allow_html=True)
    _render_resume_flow(show_uploader=False)
    if st.button("返回开始页", key="back_to_start_button"):
        clear_resume_state(st.session_state)
        st.rerun()
    st.markdown('<div class="footer">Offer捕手 · 核对完成后进入岗位工作台</div>', unsafe_allow_html=True)


def render_form_page():
    if st.session_state.get("resume_status") == "review" and st.session_state.get("parsed_profile"):
        _render_review_page()
    else:
        _render_start_page()


def _regenerate_explanation():
    """Generate a fresh matching explanation for the currently selected job set."""
    st.session_state["chat_history"] = []
    st.session_state["analysis_cache"] = {}
    profile = st.session_state.get("profile", {})
    matched_jobs = st.session_state.get("matched_jobs", [])
    selected = selected_job_result(st.session_state)
    if selected is not None and matched_jobs:
        st.session_state["processing"] = True
        st.session_state["processing_kind"] = "matching"
        try:
            with st.spinner("正在重新生成岗位解读…"):
                with st.chat_message("assistant"):
                    _append_ai_stream(
                        chat_with_ai_stream(
                            profile,
                            job_context=_ai_context(profile, matched_jobs, selected),
                            query_type="matching",
                        ),
                        label="岗位匹配解读",
                    )
        finally:
            st.session_state["processing"] = False
            st.session_state["processing_kind"] = None
    st.rerun()


def _refresh():
    """Backward-compatible alias; it refreshes explanation, not job ranking."""
    _regenerate_explanation()


def render_chat_page():
    """Render the new job workspace; ``chat`` remains a compatibility alias."""
    st.markdown(load_css(), unsafe_allow_html=True)
    profile = st.session_state.get("profile", {})
    matched_jobs = st.session_state.get("matched_jobs", [])
    render_brand_header(subtitle=False)
    render_stepper("workspace")

    top_left, top_right = st.columns([5, 1])
    with top_left:
        render_profile_summary(profile, st.session_state.get("profile_source", "manual"))
    with top_right:
        if st.button("编辑资料", width="stretch", key="edit_profile_button"):
            st.session_state["page"] = "form"
            st.rerun()
        if st.button("重新开始", width="stretch", key="new_flow_button"):
            reset_session(st.session_state)
            st.rerun()

    if not matched_jobs:
        st.warning("暂无岗位结果，请编辑资料后重新匹配。")
        return

    selected = selected_job_result(st.session_state)
    list_col, detail_col = st.columns([0.9, 1.4], gap="large")
    with list_col:
        st.markdown('<div class="workspace-heading"><div class="card-kicker">CURATED ROLES</div><h2>适合你的岗位</h2><p>按规则匹配分排序，分数用于比较岗位，不代表录用概率。</p></div>', unsafe_allow_html=True)
        visible_limit = len(matched_jobs) if st.session_state.get("show_all_jobs") else min(5, len(matched_jobs))
        for index, result in enumerate(matched_jobs[:visible_limit], 1):
            job_id = result.job.get("id", f"job-{index}")
            render_job_card(result, index, selected is result)
            if st.button("查看岗位" if selected is not result else "已选中", key=f"select_job_{job_id}", width="stretch", disabled=selected is result):
                st.session_state["selected_job_id"] = job_id
                st.session_state["chat_history"] = []
                st.rerun()
        if len(matched_jobs) > 5 and not st.session_state.get("show_all_jobs"):
            if st.button(f"查看更多岗位（还有 {len(matched_jobs) - 5} 个）", key="show_more_jobs", width="stretch"):
                st.session_state["show_all_jobs"] = True
                st.rerun()
    with detail_col:
        if selected:
            render_job_detail(selected)
            render_match_overview(matched_jobs, selected_result=selected)
            render_action_buttons(
                on_analysis=lambda: handle_analysis(profile, matched_jobs),
                on_optimization=lambda: handle_optimization(profile, matched_jobs),
                on_refresh=_regenerate_explanation,
            )
            render_ai_history(st.session_state.get("chat_history", []))
            if not st.session_state.get("chat_history"):
                st.info("先选一个动作，或直接在下方问 AI。规则匹配结果已经可以使用。")
            if st.session_state.get("processing"):
                st.info("AI 正在处理中，请稍候…")
            prompt = st.chat_input("追问当前岗位，例如：面试最该准备什么？")
            if prompt:
                handle_chat_message(prompt, profile, matched_jobs)
    st.markdown('<div class="footer">Offer捕手 · 规则匹配负责排序，AI 负责解释</div>', unsafe_allow_html=True)


def main():
    init_session_state(st.session_state)
    if st.session_state.get("page") in ("workspace", "chat"):
        render_chat_page()
    else:
        render_form_page()


if __name__ == "__main__":
    main()
