"""Student profile normalization and validation.

This module is deliberately independent from Streamlit so the upload flow and
the manual form can use exactly the same business rules.
"""

from __future__ import annotations

import re
from typing import Iterable


PROFILE_FIELDS = (
    "name",
    "education",
    "school",
    "major",
    "grad_year",
    "skills",
    "experience",
    "target_position",
    "city",
)

RESUME_FIELDS = ("name", "education", "school", "major", "grad_year", "skills", "experience")
REQUIRED_FIELDS = ("education", "school", "major", "grad_year", "skills")
EDUCATION_OPTIONS = ("", "专科", "本科", "硕士", "博士")


def normalize_skills(values: Iterable[object] | None, custom: str = "") -> list[str]:
    """Normalize skills, retaining user supplied values outside the catalog."""
    candidates: list[object] = list(values or [])
    if custom:
        candidates.extend(re.split(r"[,，、;；\n]+", custom))

    result: list[str] = []
    seen: set[str] = set()
    for value in candidates:
        if not isinstance(value, str):
            continue
        skill = value.strip()
        if not skill:
            continue
        marker = skill.casefold()
        if marker not in seen:
            seen.add(marker)
            result.append(skill)
    return result


def normalize_profile(profile: dict | None) -> dict:
    """Return a safe, matching-ready profile without parser metadata."""
    source = profile if isinstance(profile, dict) else {}
    cleaned = {field: source.get(field, "") for field in PROFILE_FIELDS}
    for field in ("name", "education", "school", "major", "grad_year", "experience", "target_position", "city"):
        value = cleaned[field]
        cleaned[field] = str(value).strip() if value is not None else ""
    cleaned["skills"] = normalize_skills(source.get("skills"))
    return cleaned


def validate_profile(profile: dict | None) -> list[str]:
    """Return user-facing validation messages for the shared profile rules."""
    candidate = normalize_profile(profile)
    errors: list[str] = []
    if candidate["education"] not in EDUCATION_OPTIONS[1:]:
        errors.append("请选择学历")
    if not candidate["school"]:
        errors.append("请填写学校")
    if not candidate["major"]:
        errors.append("请填写专业")
    if not re.fullmatch(r"(?:19|20|21)\d{2}", candidate["grad_year"]):
        errors.append("请填写有效的四位毕业年份")
    if not candidate["skills"]:
        errors.append("请至少选择或填写一个技能")
    return errors


def build_profile(
    *,
    name: str = "",
    education: str = "",
    school: str = "",
    major: str = "",
    grad_year: str = "",
    skills: Iterable[object] | None = None,
    custom_skill: str = "",
    experience: str = "",
    target_position: str = "",
    city: str = "",
) -> dict:
    """Build a normalized profile from form or review values."""
    return normalize_profile(
        {
            "name": name,
            "education": education,
            "school": school,
            "major": major,
            "grad_year": grad_year,
            "skills": normalize_skills(skills, custom_skill),
            "experience": experience,
            "target_position": target_position,
            "city": city,
        }
    )


def recognized_resume_fields(parsed: dict | None) -> list[str]:
    """Return fields genuinely recognized by the parser, excluding defaults."""
    source = parsed if isinstance(parsed, dict) else {}
    explicit = source.get("_recognized_fields")
    if isinstance(explicit, (list, tuple, set)):
        return [field for field in RESUME_FIELDS if field in explicit]

    recognized: list[str] = []
    for field in RESUME_FIELDS:
        value = source.get(field)
        if field == "skills":
            valid = isinstance(value, list) and any(isinstance(item, str) and item.strip() for item in value)
        else:
            valid = isinstance(value, str) and bool(value.strip())
        if valid:
            recognized.append(field)
    return recognized


def resume_coverage(parsed: dict | None) -> tuple[int, int, int]:
    """Return (recognized, total, percentage) for the seven resume fields."""
    total = len(RESUME_FIELDS)
    recognized = len(recognized_resume_fields(parsed))
    return recognized, total, round(recognized / total * 100) if total else 0

