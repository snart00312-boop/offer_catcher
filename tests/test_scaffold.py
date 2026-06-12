"""测试项目脚手架结构"""
import os


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_project_directory_exists():
    """验证项目根目录存在"""
    assert os.path.isdir(PROJECT_ROOT)


def test_data_directory_exists():
    """验证 data 目录存在"""
    assert os.path.isdir(os.path.join(PROJECT_ROOT, "data"))


def test_services_directory_exists():
    """验证 services 目录存在"""
    assert os.path.isdir(os.path.join(PROJECT_ROOT, "services"))


def test_tests_directory_exists():
    """验证 tests 目录存在"""
    assert os.path.isdir(os.path.join(PROJECT_ROOT, "tests"))


def test_streamlit_config_directory_exists():
    """验证 .streamlit 目录存在"""
    assert os.path.isdir(os.path.join(PROJECT_ROOT, ".streamlit"))
