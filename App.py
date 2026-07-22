import streamlit as st
from agent_brain import run_agent

# -------------------------------------------------------------------
# 1. 页面基本配置 (必须作为第一个 Streamlit 命令执行)
# -------------------------------------------------------------------
st.set_page_config(
    page_title="MCZ Stock Analysis",
    layout="wide",
    initial_sidebar_state="expanded" # 保持侧边栏默认展开
)

# -------------------------------------------------------------------
# 2. i18n 语言配置字典
# -------------------------------------------------------------------
I18N = {
    "zh": {
        "title": "📈 MCZ StockAnalysis-Lite",
        "subtitle": "AI 智能股票分析系统",
        "about_title": "💡 系统简介",
        "about_desc": "本系统基于 LangGraph 与 Gemini 驱动，结合实时技术指标（MA20、RSI14），一键生成机构级股票多维度分析报告。",
        "lang_label": "语言 / Language",
        "input_label": "请输入股票代码：",
        "input_placeholder": "例如：AAPL, TSLA",
        "analyze_btn": "开始分析",
        "warning_empty": "⚠️ 请输入有效的股票代码！",
        "spinner_msg": "🤖 正在获取数据并生成报告，请稍候...",
        "error_msg": "❌ 分析过程发生错误："
    },
    "en": {
        "title": "📈 MCZ StockAnalysis-Lite",
        "subtitle": "AI Stock Analysis System",
        "about_title": "💡 About",
        "about_desc": "Powered by LangGraph & Gemini. Combines real-time technicals (MA20, RSI14) to generate institutional-grade stock analysis reports.",
        "lang_label": "Language / 语言",
        "input_label": "Enter Stock Ticker:",
        "input_placeholder": "e.g. AAPL, TSLA",
        "analyze_btn": "Analyze",
        "warning_empty": "⚠️ Please enter a stock ticker!",
        "spinner_msg": "🤖 Fetching data & generating report...",
        "error_msg": "❌ An error occurred during analysis:"
    }
}

# -------------------------------------------------------------------
# 3. 侧边栏渲染 (简洁化布局，避免占用过多空间)
# -------------------------------------------------------------------
with st.sidebar:
    # 单选框选择语言
    lang_choice = st.radio(
        label="Language / 语言",
        options=["中文", "English"],
        index=0
    )
    lang_code = "zh" if lang_choice == "中文" else "en"
    t = I18N[lang_code]

    st.divider()

    # 系统简介
    st.markdown(f"**{t['about_title']}**")
    st.caption(t['about_desc'])

# -------------------------------------------------------------------
# 4. 主界面渲染
# -------------------------------------------------------------------
st.title(t["title"])
st.caption(t["subtitle"])

symbol = st.text_input(
    label=t["input_label"], 
    value="AAPL", 
    placeholder=t["input_placeholder"]
)

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
