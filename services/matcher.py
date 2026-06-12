"""岗位匹配引擎 - 基于学生背景与岗位要求计算匹配度"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from data.loader import load_jobs, search_jobs


# 学历等级映射
_EDUCATION_LEVELS = {
    "专科": 1,
    "本科": 2,
    "硕士": 3,
    "博士": 4,
}

# 技能匹配权重
_SKILL_WEIGHT = 0.6
_EDUCATION_WEIGHT = 0.2
_MAJOR_WEIGHT = 0.2


@dataclass
class MatchResult:
    """单个岗位的匹配结果"""
    job: dict
    score: float
    skill_match: dict = field(default_factory=dict)
    education_match: dict = field(default_factory=dict)
    major_match: dict = field(default_factory=dict)


def calculate_skill_match(user_skills: List[str], job_skills: List[str]) -> dict:
    """计算技能匹配度"""
    user_skills_lower = {s.strip().lower() for s in user_skills if s.strip()}
    job_skills_lower = {s.strip().lower() for s in job_skills if s.strip()}

    matched = []
    missing = []
    for js in job_skills:
        if js.strip().lower() in user_skills_lower:
            matched.append(js.strip())
        else:
            missing.append(js.strip())

    match_rate = len(matched) / len(job_skills_lower) if job_skills_lower else 0
    return {
        "matched_skills": matched,
        "missing_skills": missing,
        "match_rate": round(match_rate, 2),
    }


def calculate_education_match(user_education: str, required_education: str) -> dict:
    """计算学历匹配度"""
    user_level = _EDUCATION_LEVELS.get(user_education, 0)
    required_level = _EDUCATION_LEVELS.get(required_education, 0)

    if user_level >= required_level:
        if user_level == required_level:
            return {"match": True, "match_level": "exact"}
        else:
            return {"match": True, "match_level": "higher"}
    else:
        return {"match": False, "match_level": "lower"}


def calculate_major_match(user_major: str, job_description: str, job_requirements: list) -> dict:
    """计算专业相关度"""
    user_major_lower = user_major.strip().lower() if user_major else ""

    # 检查岗位描述和要求中是否包含专业相关关键词
    relevant_keywords = [
        user_major_lower,
        *user_major_lower.split(),
    ]

    text_to_check = (job_description + " " + " ".join(job_requirements)).lower()

    matched_keywords = [kw for kw in relevant_keywords if kw and kw in text_to_check]
    is_relevant = len(matched_keywords) > 0

    return {
        "is_relevant": is_relevant,
        "matched_keywords": matched_keywords,
    }


def calculate_overall_score(
    skill_match: dict,
    education_match: dict,
    major_match: Optional[dict] = None,
) -> float:
    """计算综合评分（0-100）"""
    skill_score = skill_match["match_rate"] * 100 * _SKILL_WEIGHT

    if education_match["match"]:
        edu_score = 100 * _EDUCATION_WEIGHT
    else:
        edu_score = 0 * _EDUCATION_WEIGHT

    if major_match:
        major_score = (100 if major_match["is_relevant"] else 30) * _MAJOR_WEIGHT
    else:
        major_score = 50 * _MAJOR_WEIGHT  # 没有专业信息时给中间分

    total = skill_score + edu_score + major_score
    return round(total, 1)


def match_jobs(student_profile: dict, top_n: int = 10) -> List[MatchResult]:
    """根据学生画像匹配岗位，返回按匹配度降序排列的结果"""
    skills = student_profile.get("skills", [])
    education = student_profile.get("education", "")
    major = student_profile.get("major", "")
    target = student_profile.get("target_position", "")

    # 获取候选岗位列表
    if target and target not in ("", "我不确定", "不确定"):
        # 如果指定了目标岗位，优先搜索相关岗位
        candidates = search_jobs(target)
        if not candidates:
            # 搜索不到则返回所有岗位
            candidates = load_jobs()
    else:
        candidates = load_jobs()

    results = []
    for job in candidates:
        job_skills = job.get("requirements", [])
        required_edu = job.get("education_required", "本科")

        skill_match = calculate_skill_match(skills, job_skills)
        education_match = calculate_education_match(education, required_edu)
        major_match = calculate_major_match(major, job.get("description", ""), job_skills)

        score = calculate_overall_score(skill_match, education_match, major_match)

        results.append(MatchResult(
            job=job,
            score=score,
            skill_match=skill_match,
            education_match=education_match,
            major_match=major_match,
        ))

    # 按分数降序排列
    results.sort(key=lambda r: r.score, reverse=True)
    return results[:top_n]
