"""测试岗位匹配引擎"""
import pytest
from services.matcher import (
    match_jobs,
    calculate_skill_match,
    calculate_education_match,
    calculate_overall_score,
    MatchResult,
)
from data.loader import load_jobs


def test_match_jobs_returns_list():
    """验证 match_jobs 返回列表"""
    profile = {
        "education": "本科",
        "school": "北京邮电大学",
        "major": "计算机科学与技术",
        "skills": ["Python", "Java", "SQL"],
        "target_position": "后端开发",
    }
    results = match_jobs(profile)
    assert isinstance(results, list)


def test_match_jobs_sorted_by_score():
    """验证匹配结果按分数降序排列"""
    profile = {
        "education": "本科",
        "school": "北京邮电大学",
        "major": "计算机科学与技术",
        "skills": ["Python", "Java", "SQL"],
        "target_position": "后端开发",
    }
    results = match_jobs(profile)
    for i in range(len(results) - 1):
        assert results[i].score >= results[i + 1].score


def test_match_jobs_returns_top_n():
    """验证指定返回数量"""
    profile = {
        "education": "本科",
        "school": "北京邮电大学",
        "major": "计算机科学与技术",
        "skills": ["Python"],
        "target_position": "后端开发",
    }
    results = match_jobs(profile, top_n=3)
    assert len(results) <= 3


def test_match_result_has_required_fields():
    """验证匹配结果包含必要字段"""
    profile = {
        "education": "本科",
        "school": "北京邮电大学",
        "major": "计算机科学与技术",
        "skills": ["Python", "Java"],
        "target_position": "后端开发",
    }
    results = match_jobs(profile, top_n=1)
    if results:
        r = results[0]
        assert isinstance(r, MatchResult)
        assert r.job is not None
        assert isinstance(r.score, (int, float))
        assert 0 <= r.score <= 100
        assert isinstance(r.skill_match, dict)
        assert isinstance(r.education_match, dict)


def test_calculate_skill_match_full():
    """验证技能完全匹配"""
    job_skills = ["Python", "Java", "SQL"]
    user_skills = ["Python", "Java", "SQL"]
    result = calculate_skill_match(user_skills, job_skills)
    assert result["matched_skills"] == ["Python", "Java", "SQL"]
    assert result["missing_skills"] == []
    assert result["match_rate"] == 1.0


def test_calculate_skill_match_partial():
    """验证技能部分匹配"""
    job_skills = ["Python", "Java", "SQL", "Docker", "Redis"]
    user_skills = ["Python", "SQL"]
    result = calculate_skill_match(user_skills, job_skills)
    assert "Python" in result["matched_skills"]
    assert "SQL" in result["matched_skills"]
    assert "Java" in result["missing_skills"]
    assert "Docker" in result["missing_skills"]
    assert 0 < result["match_rate"] < 1.0


def test_calculate_skill_match_none():
    """验证技能完全不匹配"""
    job_skills = ["Python", "Java", "SQL"]
    user_skills = ["平面设计", "Photoshop"]
    result = calculate_skill_match(user_skills, job_skills)
    assert result["matched_skills"] == []
    assert len(result["missing_skills"]) == 3
    assert result["match_rate"] == 0.0


def test_calculate_education_match_exact():
    """验证学历完全匹配"""
    result = calculate_education_match("本科", "本科")
    assert result["match"] is True
    assert result["match_level"] == "exact"


def test_calculate_education_match_higher():
    """验证用户学历高于要求"""
    result = calculate_education_match("硕士", "本科")
    assert result["match"] is True
    assert result["match_level"] == "higher"


def test_calculate_education_match_lower():
    """验证用户学历低于要求"""
    result = calculate_education_match("专科", "本科")
    assert result["match"] is False
    assert result["match_level"] == "lower"


def test_calculate_overall_score():
    """验证综合评分计算"""
    skill_match = {"match_rate": 0.8, "matched_skills": ["Python"], "missing_skills": ["Java"]}
    education_match = {"match": True, "match_level": "exact"}
    score = calculate_overall_score(skill_match, education_match)
    assert isinstance(score, (int, float))
    assert 0 <= score <= 100


def test_match_jobs_no_target_returns_all():
    """验证未指定目标岗位时返回所有岗位的匹配"""
    profile = {
        "education": "本科",
        "school": "北京邮电大学",
        "major": "计算机科学与技术",
        "skills": ["Python"],
        "target_position": "",
    }
    results = match_jobs(profile, top_n=5)
    assert len(results) > 0


def test_education_level_order():
    """验证学历等级排序"""
    from services.matcher import _EDUCATION_LEVELS
    assert _EDUCATION_LEVELS["博士"] > _EDUCATION_LEVELS["硕士"] > _EDUCATION_LEVELS["本科"] > _EDUCATION_LEVELS["专科"]
