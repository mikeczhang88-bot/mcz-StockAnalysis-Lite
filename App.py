import streamlit as st
from agent_brain import run_agent

# -------------------------------------------------------------------
# 1. 界面所有静态文本的国际化字典 (i18n)
# -------------------------------------------------------------------
I18N = {
    "zh": {
        "page_title": "MCZ 股票分析系统",
        "title": "📈 MCZ StockAnalysis-Lite (AI 智能股票分析系统)",
        "sidebar_header": "设置",
        "lang_label": "界面与输出语言 / Language",
        "input_label": "请输入要分析的股票代码（例如 AAPL, TSLA）：",
        "input_placeholder": "例如：AAPL",
        "analyze_btn": "开始智能分析",
        "warning_empty": "⚠️ 请先输入股票代码！",
        "spinner_msg": "🤖 AI Agent 正在实时拉取数据并生成分析报告，请稍候...",
        "error_msg": "❌ 分析过程中发生错误："
    },
    "en": {
        "page_title": "MCZ Stock Analysis System",
        "title": "📈 MCZ StockAnalysis-Lite (AI Stock Analysis System)",
        "sidebar_header": "Settings",
        "lang_label": "Language / 语言",
        "input_label": "Enter Stock Ticker to Analyze (e.g., AAPL, TSLA):",
        "input_placeholder": "e.g. AAPL",
        "analyze_btn": "Start Analysis",
        "warning_empty": "⚠️ Please enter a valid stock ticker!",
        "spinner_msg": "🤖 AI Agent is fetching data and generating the report, please wait...",
        "error_msg": "❌ An error occurred during analysis:"
    }
}

# -------------------------------------------------------------------
# 2. 侧边栏：语言切换选择器（默认中文 index=0）
# -------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Settings")
    lang_choice = st.radio(
        label="Language / 语言",
        options=["中文", "English"],
        index=0  # 0 对应第一个选项“中文”，实现默认中文
    )
    # 将选择映射为语言代码 "zh" 或 "en"
    lang_code = "zh" if lang_choice == "中文" else "en"
    t = I18N[lang_code]

# 动态设置页面 Title
st.set_page_config(page_title=t["page_title"], layout="wide")

# -------------------------------------------------------------------
# 3. 主界面渲染（根据选择的语言动态显示）
# -------------------------------------------------------------------
st.title(t["title"])

# 输入框
symbol = st.text_input(
    label=t["input_label"], 
    value="AAPL", 
    placeholder=t["input_placeholder"]
)

# 点击按钮触发分析
if st.button(t["analyze_btn"], type="primary"):
    if not symbol.strip():
        st.warning(t["warning_empty"])
    else:
        with st.spinner(t["spinner_msg"]):
            try:
                # 关键：将 lang_code ("zh" 或 "en") 传给后台 Agent
                response = run_agent(symbol=symbol.strip(), lang=lang_code)
                st.markdown(response)
            except Exception as e:
                st.error(f"{t['error_msg']} {e}")
