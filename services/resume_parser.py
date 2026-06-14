"""简历解析服务 — 文件提取 + AI 解析 + 校验"""

import io
import json
import re
from typing import Optional


class ResumeParseError(Exception):
    """简历解析异常，message 可直接展示给用户。"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


_EXPECTED_FIELDS = ["name", "education", "school", "major", "grad_year", "skills", "experience"]

_EDUCATION_MAP = {
    "专科": "专科", "大专": "专科",
    "本科": "本科", "学士": "本科", "大学本科": "本科",
    "硕士": "硕士", "硕士研究生": "硕士", "研究生": "硕士", "mba": "硕士",
    "博士": "博士", "博士研究生": "博士",
}

_FALLBACK_PATTERNS = [
    (r"(?:姓名|名字)[：:]\s*(.+)", "name"),
    (r"(?:学历|最高学历|学位)[：:]\s*(.+)", "education"),
    (r"(?:学校|毕业院校|院校)[：:]\s*(.+)", "school"),
    (r"(?:专业|所学专业)[：:]\s*(.+)", "major"),
    (r"(?:毕业年份|毕业时间|毕业日期)[：:]\s*(\d{4})", "grad_year"),
    (r"(?:技能|技术栈|擅长|掌握)[：:]\s*(.+)", "_skills_line"),
    (r"(?:实习|项目|工作)[经历]*[：:]\s*(.+)", "experience"),
]


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """从 PDF 字节中提取文本，失败抛 ResumeParseError。"""
    try:
        import fitz
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        if doc.page_count > 3:
            doc.close()
            raise ResumeParseError("简历页数超过 3 页，请上传 3 页以内的简历文件。")
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text("text"))
        doc.close()
        full_text = "\n".join(text_parts).strip()
        if len(full_text) > 15000:
            doc.close()
            raise ResumeParseError("简历文本过长（超过 15000 字符），请确认上传的是简历文件。")
        if not full_text:
            raise ResumeParseError("PDF 中未提取到文本内容，请确保简历不是扫描件或纯图片。")
        return full_text
    except ResumeParseError:
        raise
    except Exception as e:
        raise ResumeParseError(f"PDF 文件解析失败：{str(e)}，请检查文件是否损坏。")


def extract_text_from_docx(file_bytes: bytes) -> str:
    """从 DOCX 字节中提取文本，失败抛 ResumeParseError。"""
    try:
        from docx import Document
        doc = Document(io.BytesIO(file_bytes))
        text_parts = []
        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text.strip())
        full_text = "\n".join(text_parts).strip()
        if not full_text:
            raise ResumeParseError("DOCX 中未提取到文本内容，请检查文件。")
        if len(full_text) > 15000:
            raise ResumeParseError("简历文本过长（超过 15000 字符），请确认上传的是简历文件。")
        return full_text
    except ResumeParseError:
        raise
    except Exception as e:
        raise ResumeParseError(f"DOCX 文件解析失败：{str(e)}，请检查文件是否损坏。")


def _empty_result() -> dict:
    return {f: None for f in _EXPECTED_FIELDS} | {"skills": []}


def _normalize_result(raw: dict) -> dict:
    result = {}
    for field in _EXPECTED_FIELDS:
        result[field] = raw.get(field)
    if result.get("skills") is None:
        result["skills"] = []
    if isinstance(result["skills"], str):
        result["skills"] = [s.strip() for s in re.split(r"[，,、\s]+", result["skills"]) if s.strip()]
    return result


def _parse_ai_response(response_text: str) -> dict:
    """解析 AI 返回的简历结构化文本，优先 JSON，失败 fallback 正则。"""
    if not response_text or not response_text.strip():
        return _empty_result()

    text = response_text.strip()

    # 尝试 1：提取 ```json ... ``` 中的 JSON
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if json_match:
        try:
            return _normalize_result(json.loads(json_match.group(1)))
        except (json.JSONDecodeError, TypeError):
            pass

    # 尝试 2：直接解析整个响应为 JSON
    try:
        return _normalize_result(json.loads(text))
    except (json.JSONDecodeError, TypeError):
        pass

    # 尝试 3：正则 fallback
    result = _empty_result()
    skills_found = []
    for pattern, field in _FALLBACK_PATTERNS:
        match = re.search(pattern, text)
        if match:
            value = match.group(1).strip()
            if field == "_skills_line":
                skills_found = [s.strip() for s in re.split(r"[，,、\s]+", value) if s.strip()]
            elif field in result:
                result[field] = value

    if skills_found:
        result["skills"] = skills_found

    if all(result.get(f) in (None, [], "") for f in _EXPECTED_FIELDS):
        return _empty_result()

    return result


def validate_and_fill(parsed: dict) -> tuple[dict, list[str]]:
    """校验 AI 返回的 Profile dict，返回 (清理后的 dict, 缺失字段列表)。"""
    cleaned = {}
    missing = []

    cleaned["name"] = parsed.get("name") if parsed.get("name") else "同学"

    raw_edu = (parsed.get("education") or "").strip()
    cleaned["education"] = _EDUCATION_MAP.get(raw_edu.lower(), "")
    if not cleaned["education"]:
        for key, val in _EDUCATION_MAP.items():
            if key in raw_edu:
                cleaned["education"] = val
                break
    if not cleaned["education"]:
        missing.append("education")

    cleaned["school"] = parsed.get("school") or ""
    if not cleaned["school"]:
        missing.append("school")

    cleaned["major"] = parsed.get("major") or ""
    if not cleaned["major"]:
        missing.append("major")

    cleaned["grad_year"] = parsed.get("grad_year") or ""
    if not cleaned["grad_year"]:
        missing.append("grad_year")
    else:
        cleaned["grad_year"] = str(cleaned["grad_year"])

    skills = parsed.get("skills") or []
    seen = set()
    unique_skills = []
    for s in skills:
        s_clean = s.strip()
        if s_clean and s_clean.lower() not in seen:
            seen.add(s_clean.lower())
            unique_skills.append(s_clean)
    cleaned["skills"] = unique_skills
    if not unique_skills:
        missing.append("skills")

    cleaned["experience"] = parsed.get("experience") or ""
    if not cleaned["experience"]:
        cleaned["experience"] = "暂无实习经历"

    cleaned["target_position"] = ""
    cleaned["city"] = ""

    return cleaned, missing


def build_resume_parsing_prompt(raw_text: str) -> str:
    """构建简历解析的 AI prompt。"""
    text_snippet = raw_text[:4000] if len(raw_text) > 4000 else raw_text
    return f"""你是一位专业的简历解析助手。请从以下简历文本中提取关键信息，并严格按 JSON 格式返回。

【简历文本】
{text_snippet}

【输出要求】
返回一个 JSON 对象，包含以下字段。无法确定的字段设为 null：

```json
{{
  "name": "姓名（字符串或 null）",
  "education": "学历（值必须是：专科、本科、硕士、博士 之一，或 null）",
  "school": "学校全称（字符串或 null）",
  "major": "专业名称（字符串或 null）",
  "grad_year": "毕业年份（4位数字字符串，如 '2025'，或 null）",
  "skills": ["技能列表"，如 ["Python", "Java", "React"]，无技能时返回空数组 []],
  "experience": "实习/项目经历的简要描述（字符串或 null）"
}}
```

只返回 JSON，不要包含任何解释文字。"""


def parse_resume(file_bytes: bytes, filename: str, ai_service=None) -> dict:
    """完整的简历解析流程：文件提取 → AI 解析 → 校验。"""
    name_lower = filename.lower()

    if name_lower.endswith(".pdf"):
        raw_text = extract_text_from_pdf(file_bytes)
    elif name_lower.endswith(".docx"):
        raw_text = extract_text_from_docx(file_bytes)
    elif name_lower.endswith(".doc"):
        raise ResumeParseError("暂不支持 .doc 格式，请用 Word 另存为 .docx 后重新上传。")
    else:
        raise ResumeParseError(f"不支持的文件格式：{filename.split('.')[-1]}，请上传 PDF 或 DOCX 文件。")

    if ai_service is not None:
        from services.ai_service import call_ai_chat
        try:
            prompt = build_resume_parsing_prompt(raw_text)
            messages = [
                {"role": "system", "content": "你是一位专业的简历解析助手，只输出 JSON。"},
                {"role": "user", "content": prompt},
            ]
            ai_response = call_ai_chat(messages, temperature=0.1)
            parsed = _parse_ai_response(ai_response)
        except Exception as e:
            raise ResumeParseError(f"AI 解析失败：{str(e)}，请重试或手动填写信息。")
    else:
        parsed = _parse_ai_response(raw_text)

    cleaned, missing = validate_and_fill(parsed)
    cleaned["_raw_text"] = raw_text
    cleaned["_missing_fields"] = missing

    return cleaned
