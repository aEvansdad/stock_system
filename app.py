# app.py
import streamlit as st
from ui.dashboard import render_dashboard

# 设置页面基本配置
st.set_page_config(
    page_title="Stock Intelligence",
    page_icon="📈",
    layout="wide"
)

if __name__ == "__main__":
    render_dashboard()