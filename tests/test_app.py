"""测试主应用的数据处理和会话管理"""
import pytest
from app import (
    init_session_state,
    reset_session,
    format_profile_for_display,
    get_default_skills,
)


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
    assert "matched_jobs" not in state


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
