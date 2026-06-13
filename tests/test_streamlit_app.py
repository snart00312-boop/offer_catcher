"""Streamlit 页面级烟测。"""
from streamlit.testing.v1 import AppTest

from services.matcher import match_jobs


def test_form_page_renders_without_exceptions():
    """验证首页表单能在 Streamlit 测试环境中渲染。"""
    app = AppTest.from_file("app.py", default_timeout=10)
    app.run()

    assert not app.exception
    assert len(app.selectbox) >= 3
    assert len(app.text_input) >= 4
    assert len(app.button) >= 1


def test_chat_page_renders_deterministic_recommendations_without_ai_call():
    """验证结果页能在无 AI 调用时展示确定性推荐表。"""
    profile = {
        "name": "测试同学",
        "education": "本科",
        "school": "北京邮电大学",
        "major": "计算机科学与技术",
        "grad_year": "2026",
        "city": "北京",
        "skills": ["Java", "MySQL", "Redis", "数据结构与算法"],
        "experience": "后端项目经验",
        "target_position": "后端开发",
    }
    app = AppTest.from_file("app.py", default_timeout=10)
    app.session_state["page"] = "chat"
    app.session_state["profile"] = profile
    app.session_state["matched_jobs"] = match_jobs(profile, top_n=10)
    app.session_state["chat_history"] = [{"role": "assistant", "content": "测试消息"}]

    app.run()

    assert not app.exception
    assert len(app.dataframe) == 1
    rendered_markdown = "\n".join(item.value for item in app.markdown)
    assert "综合匹配度" in rendered_markdown
    assert "关键判断" in rendered_markdown

