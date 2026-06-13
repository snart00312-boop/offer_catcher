"""岗位匹配引擎 - 基于学生背景与岗位要求计算可解释匹配度。"""
from dataclasses import dataclass, field
import re
from typing import List, Optional

from data.loader import load_jobs


# 学历等级映射
_EDUCATION_LEVELS = {
    "专科": 1,
    "本科": 2,
    "硕士": 3,
    "博士": 4,
}

# 匹配维度权重。总和保持为 1，便于解释给用户。
_SKILL_WEIGHT = 0.45
_EDUCATION_WEIGHT = 0.15
_MAJOR_WEIGHT = 0.20
_TARGET_WEIGHT = 0.15
_CITY_WEIGHT = 0.05

_UNKNOWN_TARGETS = {"", "我不确定", "不确定", "帮我推荐", "🤷 我不确定，帮我推荐"}
_UNLIMITED_CITIES = {"", "不限", "不限制", "全国", "未指定"}

_SKILL_ALIASES = {
    "html/css": ["html", "css", "html/css"],
    "vue.js": ["vue", "vue.js"],
    "node.js": ["node", "node.js"],
    "spring boot": ["spring", "spring boot"],
    "mysql": ["mysql", "sql"],
    "postgresql": ["postgresql", "sql"],
    "tableau": ["tableau", "数据可视化"],
    "power bi": ["power bi", "数据可视化"],
    "figma": ["figma", "产品设计工具"],
    "axure": ["axure", "产品设计工具", "原型"],
    "office 办公软件": ["office", "excel", "ppt"],
    "数据结构与算法": ["数据结构", "算法"],
    "自然语言处理": ["自然语言处理", "nlp"],
    "计算机视觉": ["计算机视觉", "cv"],
    "机器学习": ["机器学习", "ml"],
    "深度学习": ["深度学习", "dl"],
}


@dataclass
class MatchResult:
    """单个岗位的匹配结果"""
    job: dict
    score: float
    skill_match: dict = field(default_factory=dict)
    education_match: dict = field(default_factory=dict)
    major_match: dict = field(default_factory=dict)
    target_match: dict = field(default_factory=dict)
    city_match: dict = field(default_factory=dict)
    recommendation_level: str = ""
    reasons: list[str] = field(default_factory=list)


def _normalize_text(value: str) -> str:
    """用于匹配的轻量文本归一化。"""
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _contains_term(text: str, term: str) -> bool:
    """匹配中英文技能词，避免 Java 误命中 JavaScript。"""
    text = _normalize_text(text)
    term = _normalize_text(term)
    if not term:
        return False
    if re.fullmatch(r"[a-z0-9.+# -]+", term):
        pattern = rf"(?<![a-z0-9+#.]){re.escape(term)}(?![a-z0-9+#.])"
        return re.search(pattern, text) is not None
    return term in text


def _skill_terms(skill: str) -> set[str]:
    """展开技能同义词，提升岗位要求短语匹配率。"""
    normalized = _normalize_text(skill)
    terms = {normalized}
    terms.update(_SKILL_ALIASES.get(normalized, []))
    return {term for term in terms if term}


def _extract_education_level(value: str) -> int:
    """从“本科及以上”等自然语言要求中提取最低学历等级。"""
    text = str(value or "")
    for label in ("博士", "硕士", "本科", "专科"):
        if label in text:
            return _EDUCATION_LEVELS[label]
    if "不限" in text or "无要求" in text:
        return 0
    return _EDUCATION_LEVELS.get(text, 0)


def calculate_skill_match(user_skills: List[str], job_skills: List[str]) -> dict:
    """计算技能匹配度"""
    expanded_user_skills = {
        term
        for skill in user_skills
        for term in _skill_terms(skill)
    }

    matched = []
    missing = []
    evidence = {}
    for js in job_skills:
        requirement = js.strip()
        matched_terms = sorted(term for term in expanded_user_skills if _contains_term(requirement, term))
        if matched_terms:
            matched.append(requirement)
            evidence[requirement] = matched_terms
        else:
            missing.append(requirement)

    requirement_count = len([s for s in job_skills if str(s).strip()])
    match_rate = len(matched) / requirement_count if requirement_count else 0
    return {
        "matched_skills": matched,
        "missing_skills": missing,
        "match_rate": round(match_rate, 2),
        "evidence": evidence,
    }


def calculate_education_match(user_education: str, required_education: str) -> dict:
    """计算学历匹配度"""
    user_level = _extract_education_level(user_education)
    required_level = _extract_education_level(required_education)

    if required_level == 0:
        return {
            "match": True,
            "match_level": "not_required",
            "user_level": user_level,
            "required_level": required_level,
        }

    if user_level >= required_level:
        if user_level == required_level:
            match_level = "exact"
        else:
            match_level = "higher"
    else:
        match_level = "lower"

    return {
        "match": user_level >= required_level,
        "match_level": match_level,
        "user_level": user_level,
        "required_level": required_level,
    }


def calculate_major_match(
    user_major: str,
    job_description: str,
    job_requirements: list,
    target_majors: Optional[list] = None,
) -> dict:
    """计算专业相关度"""
    user_major_lower = _normalize_text(user_major)
    target_majors = target_majors or []

    for target_major in target_majors:
        target_major_lower = _normalize_text(target_major)
        if target_major_lower and (
            target_major_lower in user_major_lower or user_major_lower in target_major_lower
        ):
            return {
                "is_relevant": True,
                "matched_keywords": [target_major],
                "source": "target_majors",
            }

    # 检查岗位描述和要求中是否包含专业相关关键词
    relevant_keywords = [
        user_major_lower,
        *user_major_lower.split(),
    ]

    text_to_check = _normalize_text(job_description + " " + " ".join(job_requirements))

    matched_keywords = [kw for kw in relevant_keywords if kw and kw in text_to_check]
    is_relevant = len(matched_keywords) > 0

    return {
        "is_relevant": is_relevant,
        "matched_keywords": matched_keywords,
        "source": "description" if is_relevant else "none",
    }


def calculate_target_match(target_position: str, job: dict) -> dict:
    """计算目标岗位方向匹配度。"""
    target = _normalize_text(target_position)
    if target in _UNKNOWN_TARGETS:
        return {"match_rate": 0.75, "match_level": "open", "matched_keywords": []}

    title = _normalize_text(job.get("title", ""))
    description = _normalize_text(job.get("description", ""))
    keyword_parts = [part for part in re.split(r"[ /,，、]+", target) if part]
    matched_keywords = [kw for kw in keyword_parts if kw in title or kw in description]

    if target and target in title:
        return {"match_rate": 1.0, "match_level": "title", "matched_keywords": [target]}
    if matched_keywords:
        return {"match_rate": 0.82, "match_level": "related", "matched_keywords": matched_keywords}
    return {"match_rate": 0.35, "match_level": "different", "matched_keywords": []}


def calculate_city_match(preferred_city: str, job: dict) -> dict:
    """计算目标城市匹配度。"""
    city = _normalize_text(preferred_city)
    location = _normalize_text(job.get("location", ""))
    if city in _UNLIMITED_CITIES:
        return {"match_rate": 1.0, "match_level": "open"}
    if city and city in location:
        return {"match_rate": 1.0, "match_level": "exact"}
    return {"match_rate": 0.35, "match_level": "different"}


def calculate_overall_score(
    skill_match: dict,
    education_match: dict,
    major_match: Optional[dict] = None,
    target_match: Optional[dict] = None,
    city_match: Optional[dict] = None,
) -> float:
    """计算综合评分（0-100）"""
    skill_score = skill_match["match_rate"] * 100 * _SKILL_WEIGHT

    if education_match["match"]:
        edu_base = 1.0
    else:
        edu_base = 0.2
    edu_score = edu_base * 100 * _EDUCATION_WEIGHT

    if major_match:
        major_score = (100 if major_match["is_relevant"] else 35) * _MAJOR_WEIGHT
    else:
        major_score = 50 * _MAJOR_WEIGHT  # 没有专业信息时给中间分

    target_rate = target_match.get("match_rate", 0.75) if target_match else 0.75
    city_rate = city_match.get("match_rate", 1.0) if city_match else 1.0
    target_score = target_rate * 100 * _TARGET_WEIGHT
    city_score = city_rate * 100 * _CITY_WEIGHT

    total = skill_score + edu_score + major_score + target_score + city_score
    return round(total, 1)


def _recommendation_level(score: float) -> str:
    if score >= 80:
        return "强匹配"
    if score >= 65:
        return "稳妥匹配"
    if score >= 50:
        return "潜力匹配"
    return "谨慎尝试"


def _build_reasons(
    skill_match: dict,
    education_match: dict,
    major_match: dict,
    target_match: dict,
    city_match: dict,
) -> list[str]:
    """生成给 UI 和 AI 共用的可解释推荐理由。"""
    reasons = []
    if skill_match["matched_skills"]:
        reasons.append(f"命中 {len(skill_match['matched_skills'])} 条岗位技能要求")
    if education_match["match"]:
        reasons.append("学历满足岗位门槛")
    else:
        reasons.append("学历低于岗位门槛，建议谨慎投递")
    if major_match["is_relevant"]:
        reasons.append("专业背景与岗位方向相关")
    if target_match["match_level"] in ("title", "related"):
        reasons.append("目标岗位方向与岗位标题或描述一致")
    if city_match["match_level"] == "exact":
        reasons.append("工作城市符合偏好")
    return reasons[:4]


def match_jobs(student_profile: dict, top_n: int = 10) -> List[MatchResult]:
    """根据学生画像匹配岗位，返回按匹配度降序排列的结果"""
    skills = student_profile.get("skills", [])
    education = student_profile.get("education", "")
    major = student_profile.get("major", "")
    target = student_profile.get("target_position", "")
    city = student_profile.get("city", "")
    candidates = load_jobs()

    results = []
    for job in candidates:
        job_skills = job.get("requirements", [])
        required_edu = job.get("education_required", "本科")

        skill_match = calculate_skill_match(skills, job_skills)
        education_match = calculate_education_match(education, required_edu)
        major_match = calculate_major_match(
            major,
            job.get("description", ""),
            job_skills,
            job.get("target_majors", []),
        )
        target_match = calculate_target_match(target, job)
        city_match = calculate_city_match(city, job)

        score = calculate_overall_score(
            skill_match,
            education_match,
            major_match,
            target_match,
            city_match,
        )

        results.append(MatchResult(
            job=job,
            score=score,
            skill_match=skill_match,
            education_match=education_match,
            major_match=major_match,
            target_match=target_match,
            city_match=city_match,
            recommendation_level=_recommendation_level(score),
            reasons=_build_reasons(
                skill_match,
                education_match,
                major_match,
                target_match,
                city_match,
            ),
        ))

    # 按分数降序排列
    results.sort(key=lambda r: r.score, reverse=True)
    return results[:top_n]
