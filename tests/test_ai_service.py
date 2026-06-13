"""测试 AI 服务模块"""
import sys
import types
from pathlib import Path

import pytest
from services.ai_service import (
    _DEFAULT_BASE_URL,
    _DEFAULT_MODEL,
    _DISABLE_STREAMLIT_SECRETS_ENV,
    _get_ai_config,
    _get_dotenv_value,
    _get_env_value,
    _parse_dotenv_line,
    _sanitize_error_text,
    build_matching_prompt,
    build_analysis_prompt,
    build_optimization_prompt,
    parse_ai_response,
)


AI_ENV_NAMES = (
    "ZHIPUAI_API_KEY",
    "ZHIPU_API_KEY",
    "ZHIPUAI_KEY",
    "GLM_API_KEY",
    "DASHSCOPE_API_KEY",
    "BAILIAN_API_KEY",
    "BIGMODEL_API_KEY",
    "ZHIPUAI_BASE_URL",
    "GLM_BASE_URL",
    "DASHSCOPE_BASE_URL",
    "BAILIAN_BASE_URL",
    "BIGMODEL_BASE_URL",
    "ZHIPUAI_MODEL",
    "GLM_MODEL",
    "DASHSCOPE_MODEL",
    "BAILIAN_MODEL",
    "BIGMODEL_MODEL",
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "OPENAI_MODEL",
    "DEEPSEEK_API_KEY",
    "DEEPSEEK_MODEL",
)


def clear_ai_env(monkeypatch):
    """隔离测试，避免读到开发机或 CI 中的真实 API 配置。"""
    for name in AI_ENV_NAMES:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr("services.ai_service._DOTENV_PATH", Path("__missing_test.env"))
    monkeypatch.setenv(_DISABLE_STREAMLIT_SECRETS_ENV, "1")


def test_build_matching_prompt_contains_student_info():
    """验证匹配 prompt 包含学生信息"""
    profile = {
        "name": "张三",
        "education": "本科",
        "school": "北京邮电大学",
        "major": "计算机科学与技术",
        "skills": ["Python", "Java"],
        "target_position": "后端开发",
    }
    jobs = [
        {"title": "Java后端开发", "company": "字节跳动", "requirements": ["Java", "Spring Boot"]}
    ]
    prompt = build_matching_prompt(profile, jobs)
    assert "张三" in prompt
    assert "本科" in prompt
    assert "后端开发" in prompt
    assert "Java后端开发" in prompt


def test_build_matching_prompt_has_hr_tone():
    """验证 prompt 包含 HR 口吻指令"""
    profile = {"skills": ["Python"], "target_position": "开发"}
    jobs = [{"title": "开发", "company": "A公司", "requirements": ["Python"]}]
    prompt = build_matching_prompt(profile, jobs)
    assert "HR" in prompt or "hr" in prompt.lower()
    assert "表格" in prompt or "表" in prompt


def test_build_analysis_prompt():
    """验证简历分析 prompt"""
    profile = {
        "name": "李四",
        "education": "硕士",
        "school": "北京大学",
        "major": "软件工程",
        "skills": ["Python", "Django", "SQL"],
        "experience": "在字节跳动实习6个月，参与后端开发",
        "target_position": "后端开发",
    }
    job = {"title": "后端开发工程师", "company": "腾讯", "requirements": ["Python", "Django", "Redis"]}
    prompt = build_analysis_prompt(profile, job)
    assert "李四" in prompt
    assert "硕士" in prompt
    assert "北京大学" in prompt
    assert "腾讯" in prompt


def test_build_optimization_prompt():
    """验证简历优化 prompt"""
    profile = {
        "name": "王五",
        "education": "本科",
        "school": "华中科技大学",
        "major": "计算机科学",
        "skills": ["Java", "MySQL"],
        "experience": "做过一个电商网站项目",
        "target_position": "Java开发",
    }
    job = {"title": "Java开发工程师", "company": "阿里巴巴", "requirements": ["Java", "Spring Boot", "Redis", "Kafka"]}
    prompt = build_optimization_prompt(profile, job)
    assert "王五" in prompt
    assert "优化" in prompt or "建议" in prompt


def test_parse_ai_response_returns_string():
    """验证解析 AI 响应返回字符串"""
    response = "根据您的背景，我推荐以下岗位：\n| 岗位 | 公司 | 匹配度 |"
    result = parse_ai_response(response)
    assert isinstance(result, str)
    assert len(result) > 0


def test_parse_ai_response_handles_empty():
    """验证处理空响应"""
    result = parse_ai_response("")
    assert isinstance(result, str)
    assert "暂无" in result or len(result) > 0


def test_build_matching_prompt_no_target():
    """验证未指定目标岗位时的 prompt"""
    profile = {
        "education": "本科",
        "school": "浙江大学",
        "major": "数学",
        "skills": ["Python", "数据分析", "Excel"],
        "target_position": "",
    }
    jobs = [{"title": "数据分析师", "company": "B公司", "requirements": ["Python", "数据分析"]}]
    prompt = build_matching_prompt(profile, jobs)
    assert "推荐" in prompt


def test_default_model_is_qwen_omni_plus():
    """验证默认模型切到百炼全模态模型。"""
    assert _DEFAULT_MODEL == "qwen3.5-omni-plus-2026-03-15"
    assert _DEFAULT_BASE_URL == "https://dashscope.aliyuncs.com/compatible-mode/v1"


def test_get_env_value_uses_first_configured_name(monkeypatch):
    """验证新环境变量优先于兼容旧环境变量。"""
    monkeypatch.setenv("DEEPSEEK_MODEL", "deepseek-chat")
    monkeypatch.setenv("GLM_MODEL", "qwen3.5-omni-plus-2026-03-15")
    value = _get_env_value("GLM_MODEL", "DEEPSEEK_MODEL", default="fallback")
    assert value == "qwen3.5-omni-plus-2026-03-15"


def test_glm_config_does_not_reuse_deepseek_key(monkeypatch):
    """验证 GLM 默认配置不会误读旧 DeepSeek Key。"""
    clear_ai_env(monkeypatch)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-deepseek-placeholder")

    config = _get_ai_config()
    assert config["api_key"] == ""
    assert config["base_url"] == "https://dashscope.aliyuncs.com/compatible-mode/v1"
    assert config["model"] == "qwen3.5-omni-plus-2026-03-15"


def test_disabled_streamlit_secrets_are_ignored(monkeypatch):
    """验证测试隔离开关会阻止读取本机 Streamlit secrets。"""
    clear_ai_env(monkeypatch)
    fake_streamlit = types.SimpleNamespace(secrets={"ai": {"api_key": "secret-key"}})
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)

    config = _get_ai_config()
    assert config["api_key"] == ""


def test_glm_config_reads_streamlit_ai_secrets(monkeypatch):
    """验证可从 Streamlit secrets 的 [ai] 分组读取 GLM 配置。"""
    clear_ai_env(monkeypatch)
    monkeypatch.delenv(_DISABLE_STREAMLIT_SECRETS_ENV, raising=False)

    fake_streamlit = types.SimpleNamespace(
        secrets={
            "ai": {
                "api_key": "zhipu-test-key",
                "base_url": "https://example.test/v4",
                "model": "qwen3.5-omni-plus-2026-03-15",
            }
        }
    )
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)

    config = _get_ai_config()
    assert config == {
        "api_key": "zhipu-test-key",
        "base_url": "https://example.test/v4",
        "model": "qwen3.5-omni-plus-2026-03-15",
    }


def test_env_config_overrides_streamlit_secrets(monkeypatch):
    """验证环境变量优先于 Streamlit secrets。"""
    clear_ai_env(monkeypatch)
    monkeypatch.setenv("GLM_API_KEY", "env-key")
    fake_streamlit = types.SimpleNamespace(secrets={"ai": {"api_key": "secret-key"}})
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)

    config = _get_ai_config()
    assert config["api_key"] == "env-key"


def test_parse_dotenv_line_supports_quotes_and_export():
    """验证 .env 行解析支持常见写法。"""
    assert _parse_dotenv_line("export ZHIPUAI_API_KEY='abc123'") == ("ZHIPUAI_API_KEY", "abc123")
    assert _parse_dotenv_line('GLM_MODEL="qwen3.5-omni-plus-2026-03-15"') == ("GLM_MODEL", "qwen3.5-omni-plus-2026-03-15")
    assert _parse_dotenv_line("\ufeffZHIPUAI_API_KEY=abc123") == ("ZHIPUAI_API_KEY", "abc123")
    assert _parse_dotenv_line("# comment") is None


def test_dotenv_config_overrides_env_config(monkeypatch, tmp_path):
    """验证本地 .env 优先于系统环境变量。"""
    clear_ai_env(monkeypatch)
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text(
        "ZHIPUAI_API_KEY=dotenv-key\n"
        "ZHIPUAI_MODEL=qwen3.5-omni-plus-2026-03-15\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("services.ai_service._DOTENV_PATH", dotenv_path)
    monkeypatch.setenv("ZHIPUAI_API_KEY", "env-key")

    assert _get_dotenv_value("ZHIPUAI_API_KEY") == "dotenv-key"
    config = _get_ai_config()
    assert config["api_key"] == "dotenv-key"


def test_sanitize_error_text_masks_secret_like_tokens():
    """验证错误信息不会把疑似 API key 原样显示给用户。"""
    raw = "invalid key 6339cfc2dc4845fa9111bac6ea678637.O0qrHyqkO0fghNMj"
    sanitized = _sanitize_error_text(raw)
    assert "6339cfc2" not in sanitized
    assert "***masked***" in sanitized
