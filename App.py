# App.py
import streamlit as st
from agent_brain import run_agent

# 1. 必须是第一个调用的 st. 命令！
st.set_page_config(page_title="MCZ Stock Analysis", layout="wide")

# 2. 缩小侧边栏宽度的 CSS 样式
st.markdown(
    """
    <style>
        section[data-testid="stSidebar"] {
            width: 250px !important;
        }
    </style>
    """,
    unsafe_allow_code=True
)

# -------------------------------------------------------------------
# 3. i18n 字典
# -------------------------------------------------------------------
I18N = {
    "zh": {
        "title": "📈 MCZ StockAnalysis-Lite",
        "about_title": "💡 系统简介",
        "about_desc": "本系统基于 LangGraph 与 Gemini 驱动，结合实时技术指标（MA20、RSI14），一键生成机构级股票多维度分析报告。",
        "lang_label": "语言 / Language",
        "input_label": "请输入股票代码：",
        "input_placeholder": "例如：AAPL",
        "analyze_btn": "开始分析",
        "warning_empty": "⚠️ 请输入有效的股票代码！",
        "spinner_msg": "🤖 正在获取数据并生成报告，请稍候...",
        "error_msg": "❌ 分析过程发生错误："
    },
    "en": {
        "title": "📈 MCZ StockAnalysis-Lite",
        "about_title": "💡 About",
        "about_desc": "Powered by LangGraph & Gemini. Combines real-time technicals (MA20, RSI14) to generate institutional-grade stock analysis reports.",
        "lang_label": "Language / 语言",
        "input_label": "Enter Stock Ticker:",
        "input_placeholder": "e.g. AAPL",
        "analyze_btn": "Analyze",
        "warning_empty": "⚠️ Please enter a stock ticker!",
        "spinner_msg": "🤖 Fetching data & generating report...",
        "error_msg": "❌ An error occurred during analysis:"
    }
}

# -------------------------------------------------------------------
# 4. 侧边栏渲染
# -------------------------------------------------------------------
with st.sidebar:
    lang_choice = st.radio(
        label="Language / 语言",
        options=["中文", "English"],
        index=0
    )
    lang_code = "zh" if lang_choice == "中文" else "en"
    t = I18N[lang_code]

    st.divider()

    st.markdown(f"**{t['about_title']}**")
    st.caption(t['about_desc'])

# -------------------------------------------------------------------
# 5. 主界面
# -------------------------------------------------------------------
st.title(t["title"])

symbol = st.text_input(label=t["input_label"], value="AAPL", placeholder=t["input_placeholder"])

if st.button(t["analyze_btn"], type="primary"):
    if not symbol.strip():
        st.warning(t["warning_empty"])
    else:
        with st.spinner(t["spinner_msg"]):
            try:
                response = run_agent(symbol=symbol.strip(), lang=lang_code)
                st.markdown(response)
            except Exception as e:
                st.error(f"{t['error_msg']} {e}")
