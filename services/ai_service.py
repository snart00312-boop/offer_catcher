"""AI 服务模块 - 构建 Prompt 并调用大模型 API"""
import os
import re
from pathlib import Path

from openai import OpenAI


# 默认 API 配置（可通过环境变量覆盖）
_DEFAULT_API_KEY = ""
_DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
_DEFAULT_MODEL = "qwen3.5-omni-plus-2026-03-15"
_DOTENV_PATH = Path(__file__).resolve().parent.parent / ".env"
_AI_SECRET_SECTIONS = ("ai", "bailian", "dashscope", "glm", "zhipuai")
_OPENAI_SECRET_SECTIONS = ("openai",)
_SECRET_LIKE_PATTERN = re.compile(r"(?<![A-Za-z0-9_-])[A-Za-z0-9][A-Za-z0-9._-]{19,}(?![A-Za-z0-9_-])")


def _normalize_config_value(value) -> str:
    """把环境变量、.env 或 Streamlit secrets 中的配置值规整为字符串。"""
    if value is None:
        return ""
    return str(value).strip()


def _sanitize_error_text(error_text: str) -> str:
    """避免把 API key 或长 token 原样暴露到页面。"""
    return _SECRET_LIKE_PATTERN.sub("***masked***", str(error_text))


def _get_env_value(*names: str, default: str) -> str:
    """按优先级读取环境变量，兼容旧配置名。"""
    for name in names:
        value = _normalize_config_value(os.environ.get(name))
        if value:
            return value
    return default


def _parse_dotenv_line(line: str) -> tuple[str, str] | None:
    """解析单行 .env 配置。"""
    line = line.strip().lstrip("\ufeff")
    if not line or line.startswith("#") or "=" not in line:
        return None

    key, value = line.split("=", 1)
    key = key.strip()
    if key.startswith("export "):
        key = key[len("export "):].strip()
    if not key:
        return None

    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        value = value[1:-1]
    return key, value


def _load_dotenv_values() -> dict[str, str]:
    """读取项目根目录下的单个 .env 文件。"""
    try:
        if not _DOTENV_PATH.is_file():
            return {}

        values = {}
        for line in _DOTENV_PATH.read_text(encoding="utf-8-sig").splitlines():
            parsed = _parse_dotenv_line(line)
            if parsed:
                key, value = parsed
                values[key] = value
        return values
    except OSError:
        return {}


def _get_dotenv_value(*names: str) -> str:
    """按优先级读取本地 .env 配置。"""
    values = _load_dotenv_values()
    for name in names:
        value = _normalize_config_value(values.get(name))
        if value:
            return value
    return ""


def _get_streamlit_secret_value(names: tuple[str, ...], sections: tuple[str, ...]) -> str:
    """读取 Streamlit secrets，兼容顶层变量和分组变量。"""
    try:
        import streamlit as st

        secrets = st.secrets
    except Exception:
        return ""

    try:
        for name in names:
            value = _normalize_config_value(secrets.get(name))
            if value:
                return value

        for section_name in sections:
            section = secrets.get(section_name, {})
            for name in names:
                value = _normalize_config_value(section.get(name))
                if value:
                    return value
    except Exception:
        return ""

    return ""


def _get_config_value(*names: str, secret_sections: tuple[str, ...], default: str) -> str:
    """先读本地 .env，再读环境变量，最后读 Streamlit secrets。"""
    value = _get_dotenv_value(*names)
    if value:
        return value

    env_names = tuple(name for name in names if name.upper() == name)
    value = _get_env_value(*env_names, default="") if env_names else ""
    if value:
        return value

    value = _get_streamlit_secret_value(names, secret_sections)
    return value or default


def _get_ai_config() -> dict:
    """读取 OpenAI-compatible AI 配置，.env 优先于系统环境变量。"""
    api_key = _get_config_value(
        "DASHSCOPE_API_KEY",
        "BAILIAN_API_KEY",
        "ZHIPUAI_API_KEY",
        "ZHIPU_API_KEY",
        "ZHIPUAI_KEY",
        "GLM_API_KEY",
        "BIGMODEL_API_KEY",
        "api_key",
        secret_sections=_AI_SECRET_SECTIONS,
        default=_DEFAULT_API_KEY,
    )
    base_url = _get_config_value(
        "DASHSCOPE_BASE_URL",
        "BAILIAN_BASE_URL",
        "ZHIPUAI_BASE_URL",
        "GLM_BASE_URL",
        "BIGMODEL_BASE_URL",
        "base_url",
        secret_sections=_AI_SECRET_SECTIONS,
        default=_DEFAULT_BASE_URL,
    )
    model = _get_config_value(
        "DASHSCOPE_MODEL",
        "BAILIAN_MODEL",
        "ZHIPUAI_MODEL",
        "GLM_MODEL",
        "BIGMODEL_MODEL",
        "model",
        secret_sections=_AI_SECRET_SECTIONS,
        default=_DEFAULT_MODEL,
    )

    openai_base_url = _get_config_value(
        "OPENAI_BASE_URL",
        "base_url",
        secret_sections=_OPENAI_SECRET_SECTIONS,
        default="",
    )
    if not api_key and openai_base_url:
        api_key = _get_config_value(
            "OPENAI_API_KEY",
            "api_key",
            secret_sections=_OPENAI_SECRET_SECTIONS,
            default="",
        )
        base_url = openai_base_url
        model = _get_config_value(
            "OPENAI_MODEL",
            "model",
            secret_sections=_OPENAI_SECRET_SECTIONS,
            default=model,
        )

    return {"api_key": api_key, "base_url": base_url, "model": model}


def _get_client():
    """获取 OpenAI 客户端实例"""
    config = _get_ai_config()
    return OpenAI(api_key=config["api_key"], base_url=config["base_url"])


def build_matching_prompt(student_profile: dict, matched_jobs: list) -> str:
    """构建岗位匹配推荐的 prompt"""
    name = student_profile.get("name", "同学")
    education = student_profile.get("education", "未填写")
    school = student_profile.get("school", "未填写")
    major = student_profile.get("major", "未填写")
    skills = ", ".join(student_profile.get("skills", [])) or "未填写"
    experience = student_profile.get("experience", "未填写")
    target = student_profile.get("target_position", "未明确")
    city = student_profile.get("city", "未指定")

    jobs_text = ""
    for i, job in enumerate(matched_jobs[:10], 1):
        reqs = ", ".join(job.get("requirements", []))
        jobs_text += f"{i}. {job['title']} - {job['company']}\n"
        jobs_text += f"   地点: {job.get('location', '未标注')} | 薪资: {job.get('salary_range', '面议')}\n"
        jobs_text += f"   学历要求: {job.get('education_required', '不限')}\n"
        jobs_text += f"   技能要求: {reqs}\n\n"

    prompt = f"""你是一位资深的 HR 职业顾问，正在为一位大学生提供岗位匹配推荐服务。请以专业、温暖但不失客观的 HR 口吻给出建议。

【学生信息】
- 姓名: {name}
- 学历: {education}
- 学校: {school}
- 专业: {major}
- 技能: {skills}
- 经历: {experience}
- 目标岗位: {target}
- 目标城市: {city}

【待推荐岗位】
{jobs_text}

请按以下格式输出：

### 匹配推荐结果

| 推荐岗位 | 公司 | 地点 | 匹配度 | 推荐理由 |
| ...... | ...... | ...... | ...... | ...... |

（表格中按匹配度从高到低排列）

然后给出 2-3 条整体的职业建议，语气保持 HR 专业风格。
"""
    return prompt


def build_analysis_prompt(student_profile: dict, job: dict) -> str:
    """构建简历匹配度分析的 prompt"""
    name = student_profile.get("name", "同学")
    education = student_profile.get("education", "未填写")
    school = student_profile.get("school", "未填写")
    major = student_profile.get("major", "未填写")
    skills = ", ".join(student_profile.get("skills", [])) or "未填写"
    experience = student_profile.get("experience", "未填写")

    reqs = ", ".join(job.get("requirements", []))
    preferred = ", ".join(job.get("preferred_skills", [])) or "无"

    prompt = f"""你是一位资深的 HR 招聘专家，正在对候选人的背景与目标岗位进行匹配度分析。请以专业 HR 的口吻输出。

【候选人信息】
- 姓名: {name}
- 学历: {education}
- 学校: {school}
- 专业: {major}
- 技能: {skills}
- 经历: {experience}

【目标岗位】
- 岗位: {job['title']}
- 公司: {job['company']}
- 岗位描述: {job.get('description', '无')}
- 硬性要求: {reqs}
- 加分项: {preferred}

请按以下格式输出：

### 简历匹配度分析

| 维度 | 要求 | 你的情况 | 匹配状态 | 建议 |
| ...... | ...... | ...... | ...... | ...... |

维度包括：学历、专业、技能匹配、经验匹配等。

然后给出 2-3 条具体的提升建议，保持 HR 专业风格。
"""
    return prompt


def build_optimization_prompt(student_profile: dict, job: dict) -> str:
    """构建简历优化建议的 prompt"""
    name = student_profile.get("name", "同学")
    skills = ", ".join(student_profile.get("skills", [])) or "未填写"
    experience = student_profile.get("experience", "未填写")
    major = student_profile.get("major", "未填写")

    reqs = ", ".join(job.get("requirements", []))

    prompt = f"""你是一位资深的 HR 简历优化专家，正在帮助一位学生针对特定岗位优化简历。请以专业 HR 口吻输出。

【候选人信息】
- 姓名: {name}
- 专业: {major}
- 技能: {skills}
- 经历: {experience}

【目标岗位】
- 岗位: {job['title']}
- 公司: {job['company']}
- 技能要求: {reqs}
- 岗位描述: {job.get('description', '无')}

请按以下格式输出：

### 简历优化建议

| 简历模块 | 当前状态 | 优化建议 | 优先级 |
| ...... | ...... | ...... | ...... |

模块包括：教育背景、技能清单、项目/实习经历、自我评价等。

然后给出 3 条最重要的修改要点，保持 HR 专业风格。
"""
    return prompt


def parse_ai_response(response: str) -> str:
    """解析 AI 响应，确保返回有效文本"""
    if not response or not response.strip():
        return "暂无 AI 响应，请稍后重试。"
    return response.strip()


def call_ai_chat(messages: list, temperature: float = 0.7) -> str:
    """调用大模型 API 进行对话"""
    try:
        config = _get_ai_config()
        if not config["api_key"]:
            return "（AI 服务暂时不可用：未配置 API Key。请在本地 .env、环境变量或 Streamlit secrets 中设置 DASHSCOPE_API_KEY / BAILIAN_API_KEY 后重启应用。）"

        client = _get_client()
        response = client.chat.completions.create(
            model=config["model"],
            messages=messages,
            temperature=temperature,
            stream=False,
        )
        return response.choices[0].message.content
    except Exception as e:
        error_text = _sanitize_error_text(str(e))
        lower_error = error_text.lower()
        if "401" in lower_error or "unauthorized" in lower_error or "api key" in lower_error:
            return f"（AI 服务认证失败：当前 API Key 不可用或没有 {config['model']} 权限。请检查 key 是否来自阿里云百炼平台、base_url 是否为 {config['base_url']}、模型是否已开通。原始错误: {error_text}）"
        return f"（AI 服务暂时不可用，错误信息: {error_text}。请检查 DASHSCOPE_API_KEY / BAILIAN_API_KEY 配置。）"


def chat_with_ai(student_profile: dict, job_context: dict = None,
                 query_type: str = "matching", user_message: str = "") -> str:
    """
    统一 AI 对话入口

    query_type:
        - "matching": 岗位匹配推荐
        - "analysis": 简历匹配度分析
        - "optimization": 简历优化建议
        - "chat": 自由对话
    """
    system_prompt = "你是一位资深 HR 职业顾问，始终保持专业、客观的风格。回答结构化清晰，适当使用表格展示信息。"

    if query_type == "matching":
        matched_jobs = job_context.get("matched_jobs", []) if job_context else []
        user_prompt = build_matching_prompt(student_profile, matched_jobs)
    elif query_type == "analysis":
        job = job_context.get("job", {}) if job_context else {}
        user_prompt = build_analysis_prompt(student_profile, job)
    elif query_type == "optimization":
        job = job_context.get("job", {}) if job_context else {}
        user_prompt = build_optimization_prompt(student_profile, job)
    else:
        user_prompt = user_message

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    return call_ai_chat(messages)
