"""测试岗位匹配引擎"""
import pytest
from services.matcher import (
    match_jobs,
    calculate_skill_match,
    calculate_education_match,
    calculate_major_match,
    calculate_target_match,
    calculate_city_match,
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
        assert isinstance(r.target_match, dict)
        assert isinstance(r.city_match, dict)
        assert isinstance(r.recommendation_level, str)
        assert isinstance(r.reasons, list)


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


def test_calculate_skill_match_handles_requirement_phrases():
    """验证用户技能可命中岗位要求中的自然语言短语。"""
    job_skills = ["熟悉 Java 或 Go 语言", "熟悉 MySQL 和 Redis", "了解消息队列"]
    user_skills = ["Java", "MySQL", "Redis"]
    result = calculate_skill_match(user_skills, job_skills)
    assert "熟悉 Java 或 Go 语言" in result["matched_skills"]
    assert "熟悉 MySQL 和 Redis" in result["matched_skills"]
    assert result["match_rate"] == 0.67


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


def test_calculate_education_match_understands_and_above_requirement():
    """验证“本科及以上/硕士及以上”能被识别为最低学历门槛。"""
    assert calculate_education_match("本科", "本科及以上")["match"] is True
    assert calculate_education_match("硕士", "本科及以上")["match_level"] == "higher"
    assert calculate_education_match("本科", "硕士及以上")["match"] is False


def test_calculate_major_match_uses_target_majors():
    """验证岗位结构化专业字段参与评分。"""
    result = calculate_major_match(
        "软件工程",
        "负责后端系统开发",
        ["熟悉 Java"],
        ["计算机科学与技术", "软件工程"],
    )
    assert result["is_relevant"] is True
    assert result["source"] == "target_majors"


def test_target_and_city_match_are_explainable():
    """验证目标岗位和城市偏好会形成解释字段。"""
    job = {"title": "后端开发工程师（校招）", "description": "参与交易系统研发", "location": "北京"}
    assert calculate_target_match("后端开发", job)["match_level"] == "title"
    assert calculate_city_match("北京", job)["match_level"] == "exact"


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


def test_match_jobs_prefers_relevant_backend_jobs():
    """验证典型后端画像能把后端岗位排到前列。"""
    profile = {
        "education": "本科",
        "school": "北京邮电大学",
        "major": "计算机科学与技术",
        "skills": ["Java", "MySQL", "Redis", "数据结构与算法"],
        "target_position": "后端开发",
        "city": "北京",
    }
    results = match_jobs(profile, top_n=5)
    assert results
    assert any("后端" in r.job["title"] for r in results[:3])
    assert results[0].reasons
    assert 0 <= results[0].score <= 100


@pytest.mark.parametrize(
    ("profile", "expected_keyword"),
    [
        (
            {
                "education": "本科",
                "school": "浙江大学",
                "major": "数学",
                "skills": ["Python", "SQL", "Excel", "Tableau"],
                "target_position": "数据分析师",
                "city": "上海",
            },
            "数据",
        ),
        (
            {
                "education": "本科",
                "school": "中国美术学院",
                "major": "交互设计",
                "skills": ["Figma", "Sketch", "UI 设计", "用户研究"],
                "target_position": "UI/UX 设计师",
                "city": "上海",
            },
            "设计",
        ),
        (
            {
                "education": "本科",
                "school": "复旦大学",
                "major": "市场营销",
                "skills": ["内容运营", "活动策划", "数据分析", "Excel"],
                "target_position": "运营",
                "city": "上海",
            },
            "运营",
        ),
    ],
)
def test_match_jobs_prefers_relevant_role_families(profile, expected_keyword):
    """验证非技术画像也能稳定命中对应岗位族。"""
    results = match_jobs(profile, top_n=5)
    assert results
    assert any(expected_keyword in r.job["title"] for r in results[:3])


def test_education_level_order():
    """验证学历等级排序"""
    from services.matcher import _EDUCATION_LEVELS
    assert _EDUCATION_LEVELS["博士"] > _EDUCATION_LEVELS["硕士"] > _EDUCATION_LEVELS["本科"] > _EDUCATION_LEVELS["专科"]
