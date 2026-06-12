"""测试数据加载模块"""
import json
import os
import pytest
from data.loader import load_jobs, load_skills, get_job_by_id, search_jobs


# 获取测试数据路径
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(TEST_DIR), "data")


def test_load_jobs_returns_list():
    """验证 load_jobs 返回列表"""
    jobs = load_jobs()
    assert isinstance(jobs, list)


def test_load_jobs_count():
    """验证岗位数量约为 50 条"""
    jobs = load_jobs()
    assert len(jobs) >= 45, f"期望至少 45 个岗位，实际 {len(jobs)}"


def test_load_jobs_has_required_fields():
    """验证每个岗位包含必填字段"""
    jobs = load_jobs()
    required_fields = ["id", "title", "company", "industry", "location",
                       "salary_range", "education_required", "description",
                       "requirements", "job_type"]
    for job in jobs:
        for field in required_fields:
            assert field in job, f"岗位 {job.get('id', 'unknown')} 缺少字段 {field}"


def test_load_skills_returns_dict():
    """验证 load_skills 返回字典"""
    skills = load_skills()
    assert isinstance(skills, dict)


def test_load_skills_has_skills_list():
    """验证技能数据包含 skills 列表"""
    skills = load_skills()
    assert "skills" in skills
    assert isinstance(skills["skills"], list)
    assert len(skills["skills"]) > 0


def test_load_skills_has_categories():
    """验证技能数据包含 categories 分类"""
    skills = load_skills()
    assert "categories" in skills
    assert isinstance(skills["categories"], dict)


def test_get_job_by_id_exists():
    """验证通过 ID 查找岗位"""
    job = get_job_by_id("job_001")
    assert job is not None
    assert job["id"] == "job_001"


def test_get_job_by_id_not_exists():
    """验证查找不存在的 ID 返回 None"""
    job = get_job_by_id("nonexistent")
    assert job is None


def test_search_jobs_by_title():
    """验证按岗位名称搜索"""
    results = search_jobs("前端")
    assert len(results) > 0
    for job in results:
        assert "前端" in job["title"] or "前端" in str(job.get("description", ""))


def test_search_jobs_by_company():
    """验证按公司名称搜索"""
    results = search_jobs("字节跳动")
    assert len(results) > 0
    for job in results:
        assert "字节跳动" in job["company"] or "字节跳动" in str(job.get("description", ""))


def test_search_jobs_no_results():
    """验证搜索无结果返回空列表"""
    results = search_jobs("不可能存在的岗位名称xyz")
    assert isinstance(results, list)
    assert len(results) == 0
