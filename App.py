import streamlit as st
from agent_brain import run_agent # 假设您的运行入口函数为 run_agent

# -------------------------------------------------------------------
# 1. 语言配置字典 (UI 文本)
# -------------------------------------------------------------------
I18N = {
    "zh": {
        "title": "📈 MCZ StockAnalysis-Lite (AI 智能股票分析系统)",
        "sidebar_lang": "语言 / Language",
        "input_label": "请输入要分析的股票代码（如 AAPL, TSLA）：",
        "analyze_btn": "开始分析",
        "running_msg": "Agent 正在分析中，请稍候...",
        "error_msg": "分析过程出现错误："
    },
    "en": {
        "title": "📈 MCZ StockAnalysis-Lite (AI Stock Analysis System)",
        "sidebar_lang": "Language / 语言",
        "input_label": "Enter Stock Ticker (e.g., AAPL, TSLA):",
        "analyze_btn": "Analyze",
        "running_msg": "Agent is analyzing, please wait...",
        "error_msg": "An error occurred during analysis:"
    }
}

st.set_page_config(page_title="Stock Analysis Lite", layout="wide")

# -------------------------------------------------------------------
# 2. 侧边栏：语言选择器
# -------------------------------------------------------------------
with st.sidebar:
    lang_choice = st.radio(
        "Language / 语言",
        options=["中文", "English"],
        index=0
    )
    # 映射语言代码
    lang_code = "zh" if lang_choice == "中文" else "en"
    t = I18N[lang_code]

# -------------------------------------------------------------------
# 3. 主界面 UI 渲染
# -------------------------------------------------------------------
st.title(t["title"])

symbol = st.text_input(t["input_label"], value="AAPL")

if st.button(t["analyze_btn"]):
    if not symbol:
        st.warning("Please enter a stock ticker / 请输入股票代码")
    else:
        with st.spinner(t["running_msg"]):
            try:
                # 将用户选择的语言代码 (lang_code) 传递给 agent_brain
                # 提示：如果是流式输出，请根据您的实际 agent 调用逻辑处理
                response = run_agent(symbol=symbol, lang=lang_code)
                st.markdown(response)
            except Exception as e:
                st.error(f"{t['error_msg']} {e}")
