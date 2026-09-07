"""测试主应用的数据处理和会话管理"""
from contextlib import nullcontext

import pytest
from app import (
    init_session_state,
    reset_session,
    format_profile_for_display,
    get_default_skills,
)
from services.matcher import MatchResult
from ui.presenters import build_match_table_rows, build_top_match_insights


def test_init_session_state_sets_defaults():
    """验证初始化设置默认值"""
    state = {}
    init_session_state(state)
    assert "page" in state
    assert state["page"] == "form"
    assert "profile" in state
    assert "chat_history" in state
    assert state["chat_history"] == []


def test_reset_session_clears_data():
    """验证重置会话清除数据但保留结构"""
    state = {
        "page": "chat",
        "profile": {"name": "张三", "education": "本科"},
        "chat_history": [{"role": "user", "content": "你好"}],
        "matched_jobs": [{"title": "测试岗位"}],
    }
    reset_session(state)
    assert state["page"] == "form"
    assert state["profile"] == {}
    assert state["chat_history"] == []
    assert state["matched_jobs"] == []
    assert state["processing"] is False


def test_format_profile_for_display():
    """验证格式化学生信息"""
    profile = {
        "name": "张三",
        "education": "本科",
        "school": "北京大学",
        "major": "计算机",
        "skills": ["Python", "Java"],
        "experience": "实习经历",
        "target_position": "后端开发",
        "city": "北京",
    }
    formatted = format_profile_for_display(profile)
    assert "张三" in formatted
    assert "本科" in formatted
    assert "北京大学" in formatted
    assert "Python" in formatted


def test_format_profile_for_display_missing_fields():
    """验证格式化时处理缺失字段"""
    profile = {"name": "李四", "education": "硕士"}
    formatted = format_profile_for_display(profile)
    assert "李四" in formatted
    assert "硕士" in formatted


def test_get_default_skills_returns_list():
    """验证获取默认技能列表"""
    skills = get_default_skills()
    assert isinstance(skills, list)
    assert len(skills) > 0
    assert "Python" in skills


def test_build_match_table_rows_formats_recommendations():
    """验证匹配结果可转换为表格行。"""
    result = MatchResult(
        job={
            "title": "后端开发工程师",
            "company": "测试公司",
            "location": "北京",
            "salary_range": "20K-30K",
        },
        score=82.4,
        skill_match={"matched_skills": ["熟悉 Java"], "missing_skills": ["了解消息队列"]},
        recommendation_level="强匹配",
    )

    rows = build_match_table_rows([result])
    assert rows[0]["岗位"] == "后端开发工程师"
    assert rows[0]["匹配度"] == "82.4"
    assert rows[0]["推荐档"] == "强匹配"
    assert rows[0]["关键缺口"] == "了解消息队列"


def test_build_top_match_insights_extracts_reasoning():
    """验证首选岗位洞察包含解释字段。"""
    result = MatchResult(
        job={"title": "数据分析师", "company": "测试公司"},
        score=74.0,
        skill_match={"matched_skills": ["SQL"], "missing_skills": ["Tableau"]},
        education_match={"match_level": "exact"},
        major_match={"is_relevant": True},
        city_match={"match_level": "open"},
        recommendation_level="稳妥匹配",
        reasons=["命中 1 条岗位技能要求", "学历满足岗位门槛"],
    )

    insights = build_top_match_insights(result)
    assert insights["title"] == "数据分析师"
    assert insights["score"] == "74.0"
    assert insights["major_relevant"] is True
    assert "学历满足岗位门槛" in insights["reasons"]


def test_regenerate_explanation_calls_ai_and_keeps_job_ranking(monkeypatch):
    """“重新生成解读”必须请求 AI，但不能重新计算或替换岗位排序。"""
    import app

    result = MatchResult(job={"id": "a", "title": "岗位 A"}, score=80)
    state = {
        "profile": {"name": "测试", "skills": ["Python"]},
        "matched_jobs": [result],
        "selected_job_id": "a",
        "chat_history": [{"role": "assistant", "content": "旧解读"}],
        "analysis_cache": {"old": "结果"},
        "processing": False,
        "processing_kind": None,
    }
    calls = []
    original_state = app.st.session_state
    original_rerun = app.st.rerun
    original_spinner = app.st.spinner
    original_stream = app.chat_with_ai_stream
    monkeypatch.setattr(app.st, "session_state", state)
    monkeypatch.setattr(app.st, "rerun", lambda: None)
    monkeypatch.setattr(app.st, "spinner", lambda *args, **kwargs: nullcontext())

    def fake_stream(*args, **kwargs):
        calls.append((args, kwargs))
        return iter(["新的", "解读"])

    monkeypatch.setattr(app, "chat_with_ai_stream", fake_stream)
    try:
        app._regenerate_explanation()
    finally:
        app.st.session_state = original_state
        app.st.rerun = original_rerun
        app.st.spinner = original_spinner
        app.chat_with_ai_stream = original_stream

    assert len(calls) == 1
    assert state["chat_history"] == [{"role": "assistant", "content": "新的解读", "label": "岗位匹配解读"}]
    assert state["matched_jobs"] == [result]
    assert state["analysis_cache"] == {}
