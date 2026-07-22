import streamlit as st
from agent_brain import run_agent

# -------------------------------------------------------------------
# 1. 页面基本配置
# -------------------------------------------------------------------
st.set_page_config(
    page_title="MCZ Stock Analysis",
    layout="wide",
    initial_sidebar_state="collapsed"  # 默认折叠侧边栏，避免移动端遮挡
)

# -------------------------------------------------------------------
# 2. i18n 多语言配置字典
# -------------------------------------------------------------------
I18N = {
    "zh": {
        "title": "📈 MCZ StockAnalysis-Lite",
        "subtitle": "AI 智能股票分析系统",
        "about_title": "💡 系统简介",
        "about_desc": "基于 LangGraph 与 Gemini 驱动，结合实时技术指标（MA20、RSI14），一键生成机构级股票多维度分析报告。",
        "lang_label": "界面语言 / Language",
        "input_label": "请输入股票代码：",
        "input_placeholder": "例如：AAPL, TSLA",
        "analyze_btn": "开始分析",
        "logout_btn": "🚪 退出系统",
        "logout_msg": "👋 您已成功退出系统，请关闭页面或刷新重新进入。",
        "relogin_btn": "🔄 重新启动系统",
        "warning_empty": "⚠️ 请输入有效的股票代码！",
        "spinner_msg": "🤖 正在获取数据并生成报告，请稍候...",
        "error_msg": "❌ 分析过程发生错误："
    },
    "en": {
        "title": "📈 MCZ StockAnalysis-Lite",
        "subtitle": "AI Stock Analysis System",
        "about_title": "💡 About",
        "about_desc": "Powered by LangGraph & Gemini. Combines real-time technicals (MA20, RSI14) to generate institutional reports.",
        "lang_label": "Language / 语言",
        "input_label": "Enter Stock Ticker:",
        "input_placeholder": "e.g. AAPL, TSLA",
        "analyze_btn": "Analyze",
        "logout_btn": "🚪 Exit System",
        "logout_msg": "👋 You have successfully exited. Close page or refresh to restart.",
        "relogin_btn": "🔄 Restart System",
        "warning_empty": "⚠️ Please enter a stock ticker!",
        "spinner_msg": "🤖 Fetching data & generating report...",
        "error_msg": "❌ An error occurred during analysis:"
    }
}

# -------------------------------------------------------------------
# 3. 退出状态检查
# -------------------------------------------------------------------
if "logged_out" not in st.session_state:
    st.session_state["logged_out"] = False

if st.session_state["logged_out"]:
    lang_code = st.session_state.get("lang_code", "zh")
    t = I18N[lang_code]
    st.info(t["logout_msg"])
    if st.button(t["relogin_btn"], type="primary"):
        st.session_state["logged_out"] = False
        st.rerun()
    st.stop()

# -------------------------------------------------------------------
# 4. 侧边栏（纯原生控件，无 CSS，极简不挡屏）
# -------------------------------------------------------------------
with st.sidebar:
    lang_choice = st.radio(
        label="Language / 语言",
        options=["中文", "English"],
        index=0
    )
    lang_code = "zh" if lang_choice == "中文" else "en"
    st.session_state["lang_code"] = lang_code
    t = I18N[lang_code]

    st.divider()

    st.write(f"**{t['about_title']}**")
    st.caption(t["about_desc"])

    st.divider()

    if st.button(t["logout_btn"], use_container_width=True):
        st.session_state["logged_out"] = True
        st.rerun()

# -------------------------------------------------------------------
# 5. 主界面渲染
# -------------------------------------------------------------------
st.title(t["title"])
st.caption(t["subtitle"])

symbol = st.text_input(
    label=t["input_label"], 
    value="", 
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
