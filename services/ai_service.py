"""AI provider adapter and prompt builders for Offer Catcher.

The deterministic matcher remains the source of truth for ranking. This module
only asks the configured model to explain that ranking or help the user act on
it. Provider errors are sanitized before they reach the UI.
"""

from __future__ import annotations

import os
import re
import time
from collections.abc import Generator, Iterable
from pathlib import Path

import httpx
from openai import OpenAI


_DEFAULT_API_KEY = ""
_DEFAULT_BASE_URL = "https://llm-xzld0nked9gxsskh.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"
_DEFAULT_MODEL = "qwen3.8-27b"
_DOTENV_PATH = Path(__file__).resolve().parent.parent / ".env"
_AI_SECRET_SECTIONS = ("ai", "bailian", "dashscope", "glm", "zhipuai")
_OPENAI_SECRET_SECTIONS = ("openai",)
_DISABLE_STREAMLIT_SECRETS_ENV = "OFFER_CATCHER_DISABLE_STREAMLIT_SECRETS"
_SECRET_LIKE_PATTERN = re.compile(r"(?<![A-Za-z0-9_-])[A-Za-z0-9][A-Za-z0-9._-]{19,}(?![A-Za-z0-9_-])")


class AIServiceError(RuntimeError):
    """A provider failure that is safe for callers to handle."""

    def __init__(self, message: str, code: str = "provider_error"):
        self.message = message
        self.code = code
        super().__init__(message)


def _normalize_config_value(value) -> str:
    return "" if value is None else str(value).strip()


def _sanitize_error_text(error_text: str) -> str:
    return _SECRET_LIKE_PATTERN.sub("***masked***", str(error_text))


def _get_env_value(*names: str, default: str) -> str:
    for name in names:
        value = _normalize_config_value(os.environ.get(name))
        if value:
            return value
    return default


def _parse_dotenv_line(line: str) -> tuple[str, str] | None:
    line = line.strip().lstrip("\ufeff")
    if not line or line.startswith("#") or "=" not in line:
        return None
    key, value = line.split("=", 1)
    key = key.strip()
    if key.startswith("export "):
        key = key[7:].strip()
    if not key:
        return None
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        value = value[1:-1]
    return key, value


def _load_dotenv_values() -> dict[str, str]:
    try:
        if not _DOTENV_PATH.is_file():
            return {}
        values: dict[str, str] = {}
        for line in _DOTENV_PATH.read_text(encoding="utf-8-sig").splitlines():
            parsed = _parse_dotenv_line(line)
            if parsed:
                values[parsed[0]] = parsed[1]
        return values
    except OSError:
        return {}


def _get_dotenv_value(*names: str) -> str:
    values = _load_dotenv_values()
    for name in names:
        value = _normalize_config_value(values.get(name))
        if value:
            return value
    return ""


def _get_streamlit_secret_value(names: tuple[str, ...], sections: tuple[str, ...]) -> str:
    if os.environ.get(_DISABLE_STREAMLIT_SECRETS_ENV) == "1":
        return ""
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
            if not hasattr(section, "get"):
                continue
            for name in names:
                value = _normalize_config_value(section.get(name))
                if value:
                    return value
    except Exception:
        return ""
    return ""


def _get_config_value(*names: str, secret_sections: tuple[str, ...], default: str) -> str:
    value = _get_dotenv_value(*names)
    if value:
        return value
    env_names = tuple(name for name in names if name.upper() == name)
    if env_names:
        value = _get_env_value(*env_names, default="")
        if value:
            return value
    return _get_streamlit_secret_value(names, secret_sections) or default


def _get_ai_config() -> dict:
    api_key = _get_config_value(
        "DASHSCOPE_API_KEY", "BAILIAN_API_KEY", "ZHIPUAI_API_KEY", "ZHIPU_API_KEY",
        "ZHIPUAI_KEY", "GLM_API_KEY", "BIGMODEL_API_KEY", "api_key",
        secret_sections=_AI_SECRET_SECTIONS, default=_DEFAULT_API_KEY,
    )
    base_url = _get_config_value(
        "DASHSCOPE_BASE_URL", "BAILIAN_BASE_URL", "ZHIPUAI_BASE_URL", "GLM_BASE_URL",
        "BIGMODEL_BASE_URL", "base_url", secret_sections=_AI_SECRET_SECTIONS,
        default=_DEFAULT_BASE_URL,
    )
    model = _get_config_value(
        "DASHSCOPE_MODEL", "BAILIAN_MODEL", "ZHIPUAI_MODEL", "GLM_MODEL",
        "BIGMODEL_MODEL", "model", secret_sections=_AI_SECRET_SECTIONS,
        default=_DEFAULT_MODEL,
    )
    openai_base_url = _get_config_value(
        "OPENAI_BASE_URL", "base_url", secret_sections=_OPENAI_SECRET_SECTIONS, default="",
    )
    if not api_key and openai_base_url:
        api_key = _get_config_value(
            "OPENAI_API_KEY", "api_key", secret_sections=_OPENAI_SECRET_SECTIONS, default="",
        )
        base_url = openai_base_url
        model = _get_config_value(
            "OPENAI_MODEL", "model", secret_sections=_OPENAI_SECRET_SECTIONS, default=model,
        )
    return {"api_key": api_key, "base_url": base_url, "model": model}


def _get_client():
    config = _get_ai_config()
    # Some DashScope-compatible endpoints publish an unreachable AAAA record.
    # Binding the transport to an IPv4 address keeps the OpenAI-compatible
    # client reliable on hosts where IPv6 routing is unavailable.
    http_client = httpx.Client(
        transport=httpx.HTTPTransport(local_address="0.0.0.0"),
        timeout=35.0,
        follow_redirects=True,
    )
    return OpenAI(
        api_key=config["api_key"],
        base_url=config["base_url"],
        timeout=35.0,
        http_client=http_client,
    )


def _profile_lines(student_profile: dict) -> str:
    profile = student_profile if isinstance(student_profile, dict) else {}
    raw_skills = profile.get("skills", []) or []
    skills = [raw_skills] if isinstance(raw_skills, str) else list(raw_skills)
    return "\n".join(
        [
            f"- 姓名: {profile.get('name') or '未填写'}",
            f"- 学历: {profile.get('education') or '未填写'}",
            f"- 学校: {profile.get('school') or '未填写'}",
            f"- 专业: {profile.get('major') or '未填写'}",
            f"- 技能: {', '.join(str(s) for s in skills) or '未填写'}",
            f"- 经历: {profile.get('experience') or '未填写'}",
            f"- 目标岗位: {profile.get('target_position') or '未明确'}",
            f"- 目标城市: {profile.get('city') or '未指定'}",
        ]
    )


def _job_snapshot(item: object, index: int) -> dict:
    """Convert a dict or MatchResult to a prompt-safe snapshot."""
    if hasattr(item, "job"):
        job = getattr(item, "job", {}) or {}
        snapshot = {
            "index": index,
            "score": getattr(item, "score", None),
            "level": getattr(item, "recommendation_level", ""),
            "reasons": list(getattr(item, "reasons", []) or []),
            "matched_skills": list((getattr(item, "skill_match", {}) or {}).get("matched_skills", []) or []),
            "missing_skills": list((getattr(item, "skill_match", {}) or {}).get("missing_skills", []) or []),
        }
    else:
        job = item if isinstance(item, dict) else {}
        snapshot = {"index": index, "score": job.get("score"), "level": job.get("recommendation_level", ""), "reasons": job.get("reasons", []), "matched_skills": job.get("matched_skills", []), "missing_skills": job.get("missing_skills", [])}
    snapshot["title"] = job.get("title", "未命名岗位")
    snapshot["company"] = job.get("company", "未标注")
    snapshot["location"] = job.get("location", "未标注")
    snapshot["salary"] = job.get("salary_range", "面议")
    snapshot["education"] = job.get("education_required", "不限")
    snapshot["requirements"] = job.get("requirements", [])
    snapshot["preferred_skills"] = job.get("preferred_skills", [])
    snapshot["description"] = job.get("description", "无")
    return snapshot


def _job_text(items: Iterable[object], limit: int = 10) -> str:
    lines: list[str] = []
    for index, item in enumerate(list(items or [])[:limit], 1):
        snapshot = _job_snapshot(item, index)
        score = f"规则匹配分 {snapshot['score']:.1f}" if isinstance(snapshot["score"], (int, float)) else "规则分未提供"
        reasons = "；".join(str(reason) for reason in snapshot["reasons"][:3]) or "暂无"
        lines.append(
            f"{index}. {snapshot['title']}｜{snapshot['company']}｜{snapshot['location']}｜{snapshot['salary']}｜{score}｜{snapshot['level'] or '未分级'}\n"
            f"   要求: {', '.join(map(str, snapshot['requirements'])) or '不限'}\n"
            f"   命中: {', '.join(map(str, snapshot['matched_skills'])) or '暂无'}；缺口: {', '.join(map(str, snapshot['missing_skills'])) or '暂无'}\n"
            f"   程序判断: {reasons}"
        )
    return "\n".join(lines) or "暂无岗位"


def build_matching_prompt(student_profile: dict, matched_jobs: list) -> str:
    return f"""你是一位资深 HR 职业顾问，请用专业、温暖但客观的口吻解释程序已经计算好的岗位排序。

【学生信息】
{_profile_lines(student_profile)}

【程序匹配结果】
{_job_text(matched_jobs)}

规则匹配分、顺序和岗位名称以程序结果为准，不要重新编造分数或交换排序。请按以下格式输出：
### 匹配推荐结果
用简洁表格复述前 5 个岗位及其规则匹配分，然后给出 2-3 条基于命中技能和关键缺口的行动建议。"""


def build_analysis_prompt(student_profile: dict, job: dict, match_result: object | None = None) -> str:
    snapshot = _job_snapshot(match_result if match_result is not None else job, 1)
    return f"""你是一位资深 HR 招聘专家，请分析候选人与一个岗位的匹配情况。

【候选人信息】
{_profile_lines(student_profile)}

【岗位信息】
- 岗位: {snapshot['title']}
- 公司: {snapshot['company']}
- 地点: {snapshot['location']}
- 规则匹配分: {snapshot['score'] if snapshot['score'] is not None else '未提供'}（仅作参考，不是录用概率）
- 程序匹配理由: {'；'.join(map(str, snapshot['reasons'])) or '暂无'}
- 程序命中的技能: {', '.join(map(str, snapshot['matched_skills'])) or '暂无'}
- 程序识别的缺口: {', '.join(map(str, snapshot['missing_skills'])) or '暂无'}
- 硬性要求: {', '.join(map(str, snapshot['requirements'])) or '不限'}
- 岗位描述: {snapshot['description']}

请按“匹配亮点 / 风险与缺口 / 面试准备”三个部分输出，尊重程序给出的事实，不自行改变分数。"""


def build_optimization_prompt(student_profile: dict, job: dict, match_result: object | None = None) -> str:
    snapshot = _job_snapshot(match_result if match_result is not None else job, 1)
    return f"""你是一位资深 HR 简历优化专家，帮助候选人针对指定岗位改写表达。

【候选人信息】
{_profile_lines(student_profile)}

【目标岗位】
- 岗位: {snapshot['title']}｜{snapshot['company']}
- 技能要求: {', '.join(map(str, snapshot['requirements'])) or '不限'}
- 当前技能缺口: {', '.join(map(str, snapshot['missing_skills'])) or '暂无'}
- 岗位描述: {snapshot['description']}

请用表格给出教育背景、技能、项目/实习经历、自我评价的修改建议，并给出 3 条可直接执行的要点。不得虚构候选人的经历。"""


def build_chat_prompt(student_profile: dict, job_context: dict | None, user_message: str, chat_history: list[dict] | None = None) -> str:
    context = job_context or {}
    matched_jobs = context.get("matched_jobs", [])
    selected = context.get("selected_match")
    history = chat_history or []
    history_text = "\n".join(f"{item.get('role', 'user')}: {item.get('content', '')}" for item in history[-6:])
    return f"""你是一位资深 HR 职业顾问，只基于给定候选人和岗位事实回答问题。

【候选人】
{_profile_lines(student_profile)}

【当前选中岗位】
{_job_text([selected] if selected else [], limit=1)}

【可见岗位清单】
{_job_text(matched_jobs, limit=10)}

【最近对话】
{history_text or '暂无'}

【本次问题】
{user_message}

如果信息不足，请明确说需要补充什么；不要虚构岗位、薪资、录用结果或候选人经历。"""


def parse_ai_response(response: str) -> str:
    if not response or not str(response).strip():
        return "暂无 AI 响应，请稍后重试。"
    return str(response).strip()


def call_ai_chat(messages: list, temperature: float = 0.7, *, raise_errors: bool = False) -> str:
    config = _get_ai_config()
    if not config["api_key"]:
        message = "（AI 服务暂时不可用：未配置 API Key。请在本地 .env、环境变量或 Streamlit secrets 中设置 DASHSCOPE_API_KEY / BAILIAN_API_KEY 后重启应用。）"
        if raise_errors:
            raise AIServiceError(message, "missing_api_key")
        return message
    try:
        response = _get_client().chat.completions.create(
            model=config["model"], messages=messages, temperature=temperature, stream=False,
        )
        content = getattr(getattr(response, "choices", [None])[0], "message", None)
        content = getattr(content, "content", "") if content is not None else ""
        if not content:
            raise AIServiceError("AI 返回了空内容。", "empty_response")
        return parse_ai_response(content)
    except AIServiceError:
        if raise_errors:
            raise
        return "（AI 服务暂时不可用：返回内容为空，请稍后重试。）"
    except Exception as exc:
        error_text = _sanitize_error_text(str(exc))
        lower_error = error_text.lower()
        if "401" in lower_error or "unauthorized" in lower_error or "api key" in lower_error:
            message = f"（AI 服务认证失败：API Key 不可用或没有 {config['model']} 权限。请检查配置。原始错误: {error_text}）"
            code = "authentication"
        elif "free quota exhausted" in lower_error or "quota exhausted" in lower_error or "use free tier only" in lower_error:
            message = f"（AI 服务额度不足：{config['model']} 的免费额度已用完。请在百炼控制台充值或关闭“仅使用免费额度”后重试。）"
            code = "quota_exhausted"
        elif "timeout" in lower_error or "timed out" in lower_error:
            message = "（AI 服务请求超时，请稍后重试。）"
            code = "timeout"
        elif "429" in lower_error or "rate limit" in lower_error:
            message = "（AI 服务当前请求较多，请稍后重试。）"
            code = "rate_limit"
        else:
            message = f"（AI 服务暂时不可用，错误信息: {error_text}。请稍后重试。）"
            code = "provider_error"
        if raise_errors:
            raise AIServiceError(message, code) from exc
        return message


def _build_messages(student_profile: dict, job_context: dict | None, query_type: str, user_message: str, chat_history: list[dict] | None) -> list[dict]:
    system_prompt = "你是一位资深 HR 职业顾问，回答结构化、客观、可执行，不补造事实。"
    context = job_context or {}
    if query_type == "matching":
        user_prompt = build_matching_prompt(student_profile, context.get("matched_jobs", []))
    elif query_type == "analysis":
        user_prompt = build_analysis_prompt(student_profile, context.get("job", {}), context.get("selected_match"))
    elif query_type == "optimization":
        user_prompt = build_optimization_prompt(student_profile, context.get("job", {}), context.get("selected_match"))
    else:
        user_prompt = build_chat_prompt(student_profile, context, user_message, chat_history)
    return [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]


def chat_with_ai(student_profile: dict, job_context: dict | None = None, query_type: str = "matching", user_message: str = "", chat_history: list[dict] | None = None) -> str:
    return call_ai_chat(_build_messages(student_profile, job_context, query_type, user_message, chat_history))


def _call_ai_chat_stream(messages: list, temperature: float = 0.7) -> Generator[str, None, None]:
    config = _get_ai_config()
    if not config["api_key"]:
        yield "（AI 服务暂时不可用：未配置 API Key。请在配置后重试。）"
        return
    try:
        stream = _get_client().chat.completions.create(
            model=config["model"], messages=messages, temperature=temperature, stream=True,
        )
        emitted = False
        for chunk in stream:
            choices = getattr(chunk, "choices", [])
            delta = getattr(choices[0], "delta", None) if choices else None
            content = getattr(delta, "content", None) if delta is not None else None
            if content:
                emitted = True
                yield content
        if not emitted:
            yield "（AI 未返回内容，请稍后重试。）"
    except Exception as exc:
        error_text = _sanitize_error_text(str(exc))
        lower_error = error_text.lower()
        if "401" in lower_error or "unauthorized" in lower_error or "api key" in lower_error:
            yield "（AI 服务认证失败，请检查 API Key 配置后重试。）"
        elif "free quota exhausted" in lower_error or "quota exhausted" in lower_error or "use free tier only" in lower_error:
            yield f"（AI 服务额度不足：{config['model']} 的免费额度已用完。请在百炼控制台充值或关闭“仅使用免费额度”后重试。）"
        elif "timeout" in lower_error or "timed out" in lower_error:
            yield "（AI 服务请求超时，请稍后重试。）"
        else:
            yield f"（AI 服务暂时不可用，错误信息: {error_text}。请稍后重试。）"


def chat_with_ai_stream(
    student_profile: dict,
    job_context: dict | None = None,
    query_type: str = "matching",
    user_message: str = "",
    chat_history: list[dict] | None = None,
) -> Generator[str, None, None]:
    """Return a streaming explanation with bounded conversation context."""
    yield from _call_ai_chat_stream(_build_messages(student_profile, job_context, query_type, user_message, chat_history))


def call_ai_chat_with_retry(messages: list, temperature: float = 0.7, max_retries: int = 2) -> str:
    """Retry only the explicit, non-streaming request and return a safe message."""
    last_error: AIServiceError | None = None
    for attempt in range(max(0, max_retries) + 1):
        try:
            return call_ai_chat(messages, temperature, raise_errors=True)
        except AIServiceError as exc:
            last_error = exc
            if attempt < max_retries and exc.code in {"timeout", "rate_limit", "provider_error"}:
                time.sleep(1.0 * (attempt + 1))
                continue
            break
    if last_error is None:
        return "（AI 服务调用失败，请稍后重试。）"
    return f"（AI 服务调用失败，已重试 {max_retries} 次。{last_error.message}）"
