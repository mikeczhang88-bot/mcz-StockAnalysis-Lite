import streamlit as st
from agent_brain import run_agent

# -------------------------------------------------------------------
# 1. 页面基本配置
# -------------------------------------------------------------------
st.set_page_config(
    page_title="MCZ Stock Analysis",
    layout="wide"
)

# -------------------------------------------------------------------
# 2. i18n 多语言配置字典
# -------------------------------------------------------------------
I18N = {
    "zh": {
        "title": "📈 MCZ StockAnalysis-Lite",
        "subtitle": "AI 智能股票分析系统",
        "lang_btn": "🌐 语言",
        "input_label": "请输入股票代码：",
        "input_placeholder": "例如：AAPL, TSLA",
        "analyze_btn": "开始分析",
        "logout_btn": "🚪 退出",
        "logout_msg": "👋 您已成功退出系统，请刷新页面重新进入。",
        "relogin_btn": "🔄 重新启动",
        "warning_empty": "⚠️ 请输入有效的股票代码！",
        "spinner_msg": "🤖 正在获取数据并生成报告，请稍候...",
        "error_msg": "❌ 分析过程发生错误："
    },
    "en": {
        "title": "📈 MCZ StockAnalysis-Lite",
        "subtitle": "AI Stock Analysis System",
        "lang_btn": "🌐 Lang",
        "input_label": "Enter Stock Ticker:",
        "input_placeholder": "e.g. AAPL, TSLA",
        "analyze_btn": "Analyze",
        "logout_btn": "🚪 Exit",
        "logout_msg": "👋 You have successfully exited. Refresh to restart.",
        "relogin_btn": "🔄 Restart",
        "warning_empty": "⚠️ Please enter a stock ticker!",
        "spinner_msg": "🤖 Fetching data & generating report...",
        "error_msg": "❌ An error occurred during analysis:"
    }
}

# -------------------------------------------------------------------
# 3. Session State 初始化与退出状态检查
# -------------------------------------------------------------------
if "logged_out" not in st.session_state:
    st.session_state["logged_out"] = False

if "lang_code" not in st.session_state:
    st.session_state["lang_code"] = "zh"

lang_code = st.session_state["lang_code"]
t = I18N[lang_code]

if st.session_state["logged_out"]:
    st.info(t["logout_msg"])
    if st.button(t["relogin_btn"], type="primary"):
        st.session_state["logged_out"] = False
        st.rerun()
    st.stop()

# -------------------------------------------------------------------
# 4. 顶部标题栏与控制按键对齐
# -------------------------------------------------------------------
# 使用 vertical_alignment="bottom" 确保按钮向下对齐，与副标题同高
col_title, col_lang, col_logout = st.columns([7, 2, 2], vertical_alignment="bottom")

with col_title:
    st.title(t["title"])
    st.caption(t["subtitle"])

with col_lang:
    # 使用 popover 让语言选择按键和退出按键具有完全一致的按钮规格大小
    with st.popover(t["lang_btn"], use_container_width=True):
        selected_lang = st.radio(
            "选择语言 / Select Language",
            options=["中文", "English"],
            index=0 if lang_code == "zh" else 1
        )
        new_lang_code = "zh" if selected_lang == "中文" else "en"
        if new_lang_code != lang_code:
            st.session_state["lang_code"] = new_lang_code
            st.rerun()

with col_logout:
    if st.button(t["logout_btn"], use_container_width=True):
        st.session_state["logged_out"] = True
        st.rerun()

st.divider()

# -------------------------------------------------------------------
# 5. 主界面渲染（输入与分析）
# -------------------------------------------------------------------
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
