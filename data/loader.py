"""数据加载模块 - 加载岗位和技能数据"""
import json
import os
from typing import Optional

# 获取当前文件所在目录的上级目录（项目根目录）
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_CURRENT_DIR)

_DATA_DIR = os.path.join(_PROJECT_ROOT, "data")
_JOBS_PATH = os.path.join(_DATA_DIR, "jobs.json")
_SKILLS_PATH = os.path.join(_DATA_DIR, "skills.json")

# 缓存数据，避免重复读取文件
_jobs_cache = None
_skills_cache = None


def load_jobs():
    """加载所有岗位数据"""
    global _jobs_cache
    if _jobs_cache is None:
        with open(_JOBS_PATH, "r", encoding="utf-8") as f:
            _jobs_cache = json.load(f)
    return _jobs_cache


def load_skills():
    """加载技能标签数据"""
    global _skills_cache
    if _skills_cache is None:
        with open(_SKILLS_PATH, "r", encoding="utf-8") as f:
            _skills_cache = json.load(f)
    return _skills_cache


def get_job_by_id(job_id: str) -> Optional[dict]:
    """根据 ID 查找岗位"""
    jobs = load_jobs()
    for job in jobs:
        if job["id"] == job_id:
            return job
    return None


def _normalize_text(value):
    """将字段值统一转为小写字符串用于搜索"""
    if isinstance(value, str):
        return value.lower()
    if isinstance(value, list):
        return " ".join(str(item).lower() for item in value)
    return str(value).lower()


def search_jobs(keyword: str):
    """按关键词搜索岗位（匹配标题、公司、描述、要求）"""
    jobs = load_jobs()
    keyword_lower = keyword.lower()
    results = []
    for job in jobs:
        if (keyword_lower in _normalize_text(job["title"])
                or keyword_lower in _normalize_text(job["company"])
                or keyword_lower in _normalize_text(job.get("description", ""))
                or keyword_lower in _normalize_text(job.get("requirements", []))):
            results.append(job)
    return results
