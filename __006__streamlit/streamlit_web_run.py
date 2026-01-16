import os

from common.path_utils import get_file_path

file_path = get_file_path("__006__streamlit/streamlit_web.py")
os.system(
    f"streamlit run {file_path}")
