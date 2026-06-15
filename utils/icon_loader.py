import streamlit as st
from pathlib import Path
from textwrap import dedent


def load_svg(path, size=24):
    """
    读取本地 SVG 图标，并统一设置宽高。
    """
    svg_path = Path(path)

    if not svg_path.exists():
        return ""

    svg = svg_path.read_text(encoding="utf-8")

    # 去掉可能存在的 XML 声明
    svg = svg.replace('<?xml version="1.0" encoding="UTF-8"?>', "")

    # 给 svg 设置统一尺寸
    svg = svg.replace(
        "<svg",
        f'<svg width="{size}" height="{size}"',
        1
    )

    return svg


def icon_title(icon_path, title, subtitle=None, size=26):
    """
    渲染一个带 SVG 图标的标题。
    """
    svg = load_svg(icon_path, size=size)

    subtitle_html = ""
    if subtitle:
        subtitle_html = f'<p class="section-subtitle">{subtitle}</p>'

    html = f"""
<div class="section-title">
    <div class="section-icon">
        {svg}
    </div>
    <div class="section-text">
        <h3>{title}</h3>
        {subtitle_html}
    </div>
</div>
"""

    st.markdown(
        dedent(html),
        unsafe_allow_html=True
    )