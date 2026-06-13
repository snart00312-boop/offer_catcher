"""把领域结果转换为 UI 友好的展示数据。"""


def build_match_table_rows(matched_jobs: list, limit: int = 5) -> list[dict]:
    """把匹配结果转换为 Streamlit 表格可展示的数据。"""
    rows = []
    for index, result in enumerate(matched_jobs[:limit], 1):
        job = result.job
        matched_skills = result.skill_match.get("matched_skills", [])
        missing_skills = result.skill_match.get("missing_skills", [])
        rows.append({
            "排名": index,
            "岗位": job.get("title", "未命名岗位"),
            "公司": job.get("company", "未标注"),
            "城市": job.get("location", "未标注"),
            "薪资": job.get("salary_range", "面议"),
            "匹配度": f"{result.score:.1f}",
            "推荐档": result.recommendation_level,
            "命中技能": "、".join(matched_skills[:2]) or "待补充",
            "关键缺口": "、".join(missing_skills[:2]) or "暂无明显缺口",
        })
    return rows


def build_top_match_insights(match_result) -> dict:
    """提取首选岗位的核心解释，用于页面和测试。"""
    job = match_result.job
    return {
        "title": job.get("title", "未命名岗位"),
        "company": job.get("company", "未标注"),
        "score": f"{match_result.score:.1f}",
        "level": match_result.recommendation_level,
        "reasons": match_result.reasons,
        "matched_skills": match_result.skill_match.get("matched_skills", []),
        "missing_skills": match_result.skill_match.get("missing_skills", []),
        "education_status": match_result.education_match.get("match_level", "unknown"),
        "major_relevant": match_result.major_match.get("is_relevant", False),
        "city_status": match_result.city_match.get("match_level", "open"),
    }

