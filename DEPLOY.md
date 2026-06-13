# Offer Catcher Deployment Guide

This guide is for a developer or operator who needs to run Offer Catcher locally, configure the AI provider, run tests, or deploy it to Streamlit Cloud.

## What This App Needs

Offer Catcher is a Python Streamlit app. It can run without an AI key: the deterministic matching engine still returns ranked job recommendations. An AI key enables HR-style explanations, follow-up chat, resume fit analysis, and optimization suggestions.

Required runtime:

- Python 3.10 or newer
- Streamlit
- OpenAI-compatible Python SDK
- pytest for verification

## Local Setup

From the project directory, create and activate a virtual environment, then install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Start the app:

```powershell
streamlit run app.py
```

The first screen is the student profile form. After submission, the result page shows deterministic ranked recommendations first, then AI-assisted discussion if an AI key is configured.

## AI Configuration

For local development, copy `.env.example` to `.env` and fill in your provider settings. Do not commit `.env`.

Preferred DashScope/Bailian-compatible variables:

```dotenv
DASHSCOPE_API_KEY=your-bailian-api-key
DASHSCOPE_MODEL=qwen3.5-omni-plus-2026-03-15
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

OpenAI-compatible fallback variables are supported only when no DashScope/Bailian key is configured:

```dotenv
OPENAI_API_KEY=your-openai-compatible-key
OPENAI_MODEL=your-model-name
OPENAI_BASE_URL=https://api.example.com/v1
```

Streamlit Cloud deployments should store these values in app secrets rather than in files. Supported secret layouts include top-level variables and grouped sections such as `[ai]`, `[dashscope]`, `[bailian]`, or `[openai]`.

## Testing

Run the full suite before shipping changes:

```powershell
python -m pytest -q
```

The tests explicitly disable reading local Streamlit secrets so that developer machines and CI do not leak real AI configuration into unit tests. If a test needs to exercise Streamlit secrets, it must unset the test guard and inject fake secrets.

## Deployment Checklist

Before deploying:

- Confirm `.env` and Streamlit secrets files are not committed.
- Run `python -m pytest -q`.
- Start the app locally and submit a sample student profile.
- Confirm the ranked recommendation table appears even without an AI key.
- Confirm AI chat returns a friendly unavailable message when no key is configured.
- Confirm AI chat works when a valid key is configured.

## Operational Notes

The matching engine is deterministic and should be treated as the source of truth for ranking, scores, matched skills, gaps, education fit, major fit, target role fit, and city fit. The AI layer should explain and extend those results, not replace them.

If a key is ever printed in logs, test output, or chat output, rotate it immediately. Error messages are masked, but real credentials should still be treated as sensitive.

