import streamlit as st
from agent_brain import run_agent

# 1. 页面基本配置
st.set_page_config(page_title="MCZ Stock Analysis", layout="wide")

# 2. 多语言字典
I18N = {
    "zh": {
        "title": "📈 MCZ StockAnalysis",
        "subtitle": "AI 金融智能助手 | 股票分析与深度对话",
        "lang_btn": "🌐 语言",
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
        "logout_btn": "🚪 Exit",
        "logout_msg": "👋 You have successfully exited. Refresh to restart.",
        "relogin_btn": "🔄 Restart",
        "input_placeholder": "Type ticker for report (e.g., AAPL) or ask any question...",
        "welcome_tips": "💡 **Quick Start**: Type **`AAPL`** or **`TSLA`** below to generate research report. You can ask follow-up questions anytime!",
        "spinner_msg": "🤖 Thinking & Analyzing...",
        "error_msg": "❌ An error occurred:"
    }
}

# 3. Session State 管理
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

# 4. 顶部控制栏
col_title, col_lang, col_logout = st.columns([7, 2, 2], vertical_alignment="bottom")

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

with col_logout:
    if st.button(t["logout_btn"], use_container_width=True):
        st.session_state["logged_out"] = True
        st.rerun()

st.divider()

# 5. 空白状态下的引导提示
if not st.session_state["chat_history"]:
    st.info(t["welcome_tips"])

# 6. 渲染聊天历史
for message in st.session_state["chat_history"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 7. 统一聊天/代码输入框
if user_input := st.chat_input(t["input_placeholder"]):
    # 显示用户输入
    st.chat_message("user").markdown(user_input)
    
    with st.chat_message("assistant"):
        with st.spinner(t["spinner_msg"]):
            try:
                # 调用 Agent
                response, is_new_report = run_agent(
                    user_input=user_input,
                    history_messages=st.session_state["chat_history"],
                    lang=lang_code
                )
                
                # 如果是全新的股票代码报告，清空旧历史，开始新话题
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
