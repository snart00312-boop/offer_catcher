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

The first screen is the resume-first start page. Choose a PDF/DOCX and click “解析这份简历”, then review the extracted fields before matching. Manual entry remains available in the collapsed “手动填写资料” section. The workspace shows deterministic ranked recommendations first; AI analysis, chat, and regenerated explanations stream into the page on demand. If the AI provider is unavailable, the parser uses an explicitly labelled local fallback for common Chinese and English resume layouts; users still confirm every field before matching.

## AI Configuration

For local development, copy `.env.example` to `.env` and fill in your provider settings. Do not commit `.env`.

Preferred DashScope/Bailian-compatible variables:

```dotenv
DASHSCOPE_API_KEY=your-bailian-api-key
DASHSCOPE_MODEL=qwen3.8-27b
DASHSCOPE_BASE_URL=https://llm-xzld0nked9gxsskh.cn-beijing.maas.aliyuncs.com/compatible-mode/v1
```

OpenAI-compatible fallback variables are supported only when no DashScope/Bailian key is configured:

```dotenv
OPENAI_API_KEY=your-openai-compatible-key
OPENAI_MODEL=your-model-name
OPENAI_BASE_URL=https://api.example.com/v1
```

Streamlit Cloud deployments should store these values in app secrets rather than in files. Supported secret layouts include top-level variables and grouped sections such as `[ai]`, `[dashscope]`, `[bailian]`, or `[openai]`.

The default configuration is the `qwen3.8-27b` compatible endpoint supplied for
this demo. The client reuses its HTTP connection, keeps the network timeout at
20 seconds, and sends only the five highest-ranked roles in explanation/chat
context so the first response arrives sooner. Full job details remain local in
the workspace and do not require an AI request.

## GitHub / Streamlit Community Cloud Redeploy

This working copy is connected to `https://github.com/snart00312-boop/offer_catcher.git`.
The Streamlit entrypoint is `app.py`, the default branch is `main`, and Python
dependencies are declared in `requirements.txt`.

Before pushing, run the local checks and confirm that `.env` and
`.streamlit/secrets.toml` are absent from the commit:

```powershell
python -m pytest -q
git status --short
git add app.py services ui data requirements.txt .streamlit/config.toml DEPLOY.md .env.example docs tests
git commit -m "upgrade offer catcher resume flow"
git push origin main
```

The `git add` list is intentionally explicit so local secrets and smoke-test
logs are not staged. If your branch is different, push that branch and select
it in Community Cloud.

For an existing Community Cloud app, a push to the configured repository,
branch, and entrypoint starts a new deployment. Changes to `requirements.txt`
trigger dependency installation; inspect the deployment logs if the app does
not become healthy. For a new app, open `share.streamlit.io`, choose **Create
app**, then select this repository, `main`, and `app.py`.

In the app's **Advanced settings → Secrets** field, paste the following TOML
with the real key supplied through your secret manager; never commit this block
to GitHub:

```toml
[dashscope]
api_key = "粘贴你的 DashScope API Key"
model = "qwen3.8-27b"
base_url = "https://llm-xzld0nked9gxsskh.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"
```

After saving secrets, redeploy or reboot the app, then verify upload → AI parse
→ review → confirm → workspace. The first AI request should be made with a
small synthetic or anonymous resume during deployment verification.

Official references: [Deploy your app on Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy), [Secrets management](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management), and [Manage your app](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app).

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
- Confirm uploading the same file twice does not invoke parsing twice unless “重新解析” is clicked.
- Confirm a second job can be selected and the analysis buttons refer to that selected job.
- Confirm a text PDF and a DOCX containing a table reach the review screen; a scanned PDF explains why manual entry is needed.
- Verify the same uploaded file is not parsed again during ordinary Streamlit reruns; use “重新解析” for an intentional retry.

## Operational Notes

The matching engine is deterministic and should be treated as the source of truth for ranking, scores, matched skills, gaps, education fit, major fit, target role fit, and city fit. The AI layer should explain and extend those results, not replace them.

If a key is ever printed in logs, test output, or chat output, rotate it immediately. Error messages are masked, but real credentials should still be treated as sensitive.
