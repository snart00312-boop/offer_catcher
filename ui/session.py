"""Session state helpers shared by the Streamlit pages."""

from __future__ import annotations


DEFAULTS = {
    "page": "form",
    "profile": {},
    "profile_source": "manual",
    "profile_revision": 0,
    "resume_raw_text": None,
    "resume_file_name": None,
    "resume_document_id": None,
    "resume_selected_id": None,
    "resume_selected_name": None,
    "resume_selected_size": 0,
    "resume_selected_bytes": None,
    "resume_uploader_version": 0,
    "resume_status": "idle",
    "resume_error": None,
    "parsed_profile": None,
    "resume_parse_count": 0,
    "chat_history": [],
    "matched_jobs": [],
    "selected_job_id": None,
    "show_all_jobs": False,
    "manual_form_open": False,
    "analysis_cache": {},
    "processing": False,
    "processing_kind": None,
}


def init_session_state(state) -> None:
    """Initialize missing keys without replacing existing user state."""
    for key, value in DEFAULTS.items():
        if key not in state:
            if isinstance(value, (dict, list)):
                state[key] = value.copy()
            else:
                state[key] = value


def reset_session(state) -> None:
    """Reset the current flow while keeping the state object usable."""
    for key in list(state.keys()):
        del state[key]
    init_session_state(state)


def clear_resume_state(state) -> None:
    """Forget the current resume, selected file and review widget values."""
    for key, value in {
        "resume_raw_text": None,
        "resume_file_name": None,
        "resume_document_id": None,
        "resume_selected_id": None,
        "resume_selected_name": None,
        "resume_selected_size": 0,
        "resume_selected_bytes": None,
        "resume_uploader_version": int(state.get("resume_uploader_version", 0)) + 1,
        "resume_status": "idle",
        "resume_error": None,
        "parsed_profile": None,
    }.items():
        state[key] = value


def mark_profile_changed(state) -> None:
    """Invalidate AI output after the user changes the matching profile."""
    state["profile_revision"] = int(state.get("profile_revision", 0)) + 1
    state["analysis_cache"] = {}
    state["chat_history"] = []


def select_first_job(state) -> None:
    """Select the first deterministic result when the profile is confirmed."""
    results = state.get("matched_jobs") or []
    state["selected_job_id"] = results[0].job.get("id") if results else None


def selected_job_result(state):
    """Resolve the selected MatchResult, falling back to the top result."""
    results = state.get("matched_jobs") or []
    selected_id = state.get("selected_job_id")
    if selected_id:
        for result in results:
            if result.job.get("id") == selected_id:
                return result
    return results[0] if results else None
