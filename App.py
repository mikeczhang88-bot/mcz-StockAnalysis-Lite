import streamlit as st
from agent_brain import run_agent

# -------------------------------------------------------------------
# 1. 页面基本配置
# -------------------------------------------------------------------
st.set_page_config(page_title="MCZ Stock Analysis", layout="wide")

# -------------------------------------------------------------------
# 2. i18n 多语言字典
# -------------------------------------------------------------------
I18N = {
    "zh": {
        "title": "📈 MCZ StockAnalysis",
        "subtitle": "AI 金融智能助手 | 股票分析与深度对话",
        "lang_btn": "🌐 语言",
        "help_btn": "❓ 帮助",
        "help_title": "💡 使用指南",
        "help_content": """
1. **查股价/简讯**：输入 `JNJ股价` 或 `NJ现在价格是多少`，直接获取最新现价与技术指标简讯。
2. **生成完整报告**：直接输入股票代码（如 `AAPL`、`TSLA`）或 `分析 TSLA`，系统将自动生成 5 段式机构级深度分析报告。
3. **多轮追问**：生成报告后，可直接在下方输入框继续提问（例如：“为什么建议在 MA20 止损？”），AI 会结合上下文进行解答。
        """,
        "logout_btn": "🚪 退出",
        "logout_msg": "👋 您已成功退出系统，请刷新页面重新进入。",
        "relogin_btn": "🔄 重新启动",
        "input_placeholder": "输入股票代码生成报告（如 AAPL），或直接输入问题...",
        "welcome_tips": "💡 **快速开始**：直接在底部输入框发送 **`AAPL`** 或 **`TSLA`** 生成分析报告，生成后可继续自由追问！",
        "spinner_msg": "🤖 正在思考与分析中，请稍候...",
        "error_msg": "❌ 分析过程发生错误："
    },
    "en": {
        "title": "📈 MCZ StockAnalysis",
        "subtitle": "AI Financial Copilot | Analysis & Chat",
        "lang_btn": "🌐 Lang",
        "help_btn": "❓ Help",
        "help_title": "💡 User Guide",
        "help_content": """
1. **Quick Price**: Type e.g., `AAPL price` for a quick current quote and core indicators.
2. **Full Report**: Type a ticker symbol (e.g., `AAPL`, `TSLA`) to generate an institutional 5-section research report.
3. **Follow-up Chat**: Ask follow-up questions anytime after the report is generated (e.g., "Why set stop loss at MA20?").
        """,
        "logout_btn": "🚪 Exit",
        "logout_msg": "👋 You have successfully exited. Refresh to restart.",
        "relogin_btn": "🔄 Restart",
        "input_placeholder": "Type ticker for report (e.g., AAPL) or ask any question...",
        "welcome_tips": "💡 **Quick Start**: Type **`AAPL`** or **`TSLA`** below to generate research report. You can ask follow-up questions anytime!",
        "spinner_msg": "🤖 Thinking & Analyzing...",
        "error_msg": "❌ An error occurred:"
    }
}

# -------------------------------------------------------------------
# 3. Session State 管理
# -------------------------------------------------------------------
if "logged_out" not in st.session_state:
    st.session_state["logged_out"] = False
if "lang_code" not in st.session_state:
    st.session_state["lang_code"] = "zh"
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

lang_code = st.session_state["lang_code"]
t = I18N[lang_code]

if st.session_state["logged_out"]:
    st.info(t["logout_msg"])
    if st.button(t["relogin_btn"], type="primary"):
        st.session_state["logged_out"] = False
        st.session_state["chat_history"] = []
        st.rerun()
    st.stop()

# -------------------------------------------------------------------
# 4. 顶部控制栏 (标题、语言选择、帮助、退出)
# -------------------------------------------------------------------
# 调整列比例：标题占 6，语言、帮助、退出各占 1.5
col_title, col_lang, col_help, col_logout = st.columns([6, 1.8, 1.8, 1.8], vertical_alignment="bottom")

with col_title:
    st.title(t["title"])
    st.caption(t["subtitle"])

with col_lang:
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

with col_help:
    # 帮助按钮气泡框
    with st.popover(t["help_btn"], use_container_width=True):
        st.markdown(f"### {t['help_title']}")
        st.markdown(t["help_content"])

with col_logout:
    if st.button(t["logout_btn"], use_container_width=True):
        st.session_state["logged_out"] = True
        st.rerun()

st.divider()

# -------------------------------------------------------------------
# 5. 空白引导与聊天逻辑
# -------------------------------------------------------------------
if not st.session_state["chat_history"]:
    st.info(t["welcome_tips"])

for message in st.session_state["chat_history"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_input := st.chat_input(t["input_placeholder"]):
    st.chat_message("user").markdown(user_input)
    
    with st.chat_message("assistant"):
        with st.spinner(t["spinner_msg"]):
            try:
                response, is_new_report = run_agent(
                    user_input=user_input,
                    history_messages=st.session_state["chat_history"],
                    lang=lang_code
                )
                
                if is_new_report:
                    st.session_state["chat_history"] = [
                        {"role": "user", "content": f"分析股票 {user_input.strip()}"},
                        {"role": "assistant", "content": response}
                    ]
                else:
                    st.session_state["chat_history"].append({"role": "user", "content": user_input})
                    st.session_state["chat_history"].append({"role": "assistant", "content": response})
                
                st.rerun()
            except Exception as e:
                st.error(f"{t['error_msg']} {e}")
