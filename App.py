import streamlit as st
from agent_brain import run_agent

# -------------------------------------------------------------------
# 1. 页面配置
# -------------------------------------------------------------------
st.set_page_config(page_title="MCZ Stock Analysis", layout="wide")

# -------------------------------------------------------------------
# 2. i18n 多语言字典
# -------------------------------------------------------------------
I18N = {
    "zh": {
        "title": "📈 MCZ StockAnalysis-Lite",
        "subtitle": "AI 智能股票分析系统 (支持深度追问)",
        "lang_btn": "🌐 语言",
        "input_label": "请输入股票代码：",
        "input_placeholder": "例如：AAPL, TSLA",
        "analyze_btn": "生成报告",
        "chat_placeholder": "对报告有疑问？请输入您的追问（例如：为什么建议在 MA20 止损？）：",
        "logout_btn": "🚪 退出",
        "logout_msg": "👋 您已成功退出系统，请刷新页面重新进入。",
        "relogin_btn": "🔄 重新启动",
        "warning_empty": "⚠️ 请输入有效的股票代码！",
        "spinner_msg": "🤖 正在分析中，请稍候...",
        "error_msg": "❌ 分析过程发生错误："
    },
    "en": {
        "title": "📈 MCZ StockAnalysis-Lite",
        "subtitle": "AI Stock Analysis System (with Follow-up Q&A)",
        "lang_btn": "🌐 Lang",
        "input_label": "Enter Stock Ticker:",
        "input_placeholder": "e.g. AAPL, TSLA",
        "analyze_btn": "Generate Report",
        "chat_placeholder": "Any questions on the report? Type your follow-up here...",
        "logout_btn": "🚪 Exit",
        "logout_msg": "👋 You have successfully exited. Refresh to restart.",
        "relogin_btn": "🔄 Restart",
        "warning_empty": "⚠️ Please enter a stock ticker!",
        "spinner_msg": "🤖 Analyzing, please wait...",
        "error_msg": "❌ An error occurred during analysis:"
    }
}

# -------------------------------------------------------------------
# 3. Session State 初始化（保存对话历史）
# -------------------------------------------------------------------
if "logged_out" not in st.session_state:
    st.session_state["logged_out"] = False

if "lang_code" not in st.session_state:
    st.session_state["lang_code"] = "zh"

# chat_history 用于存储整个多轮对话记录
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
# 4. 顶部控制栏
# -------------------------------------------------------------------
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

# -------------------------------------------------------------------
# 5. 股票代码输入与生成首次报告
# -------------------------------------------------------------------
col_input, col_btn = st.columns([4, 1], vertical_alignment="bottom")

with col_input:
    symbol = st.text_input(
        label=t["input_label"], 
        value="", 
        placeholder=t["input_placeholder"]
    )

with col_btn:
    if st.button(t["analyze_btn"], type="primary", use_container_width=True):
        if not symbol.strip():
            st.warning(t["warning_empty"])
        else:
            # 清空旧的对话，开启针对新股票的分析
            st.session_state["chat_history"] = []
            
            with st.spinner(t["spinner_msg"]):
                try:
                    # 首次调用 Agent 生成报告
                    report = run_agent(symbol=symbol.strip(), lang=lang_code)
                    
                    # 写入历史记录
                    user_first_msg = f"分析股票 {symbol.strip()}" if lang_code == "zh" else f"Analyze stock {symbol.strip()}"
                    st.session_state["chat_history"].append({"role": "user", "content": user_first_msg})
                    st.session_state["chat_history"].append({"role": "assistant", "content": report})
                    st.rerun()
                except Exception as e:
                    st.error(f"{t['error_msg']} {e}")

# -------------------------------------------------------------------
# 6. 对话历史渲染与追问交互区
# -------------------------------------------------------------------
# 渲染所有历史对话（包含初始生成的报告和后续的追问）
for message in st.session_state["chat_history"]:
    # 忽略最一开始自动触发的系统级 user 消息，只展示分析报告和后续追问
    if message["content"].startswith("分析股票 ") or message["content"].startswith("Analyze stock "):
        continue
        
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 只有当已经生成过报告后，才开放底部追问输入框
if st.session_state["chat_history"]:
    if user_prompt := st.chat_input(t["chat_placeholder"]):
        # 1. 显示并保存用户的追问
        st.chat_message("user").markdown(user_prompt)
        st.session_state["chat_history"].append({"role": "user", "content": user_prompt})

        # 2. 调用 Agent 结合上下文回答追问
        with st.chat_message("assistant"):
            with st.spinner(t["spinner_msg"]):
                try:
                    # 传入完整的 chat_history 历史记录
                    response = run_agent(
                        history_messages=st.session_state["chat_history"], 
                        lang=lang_code
                    )
                    st.markdown(response)
                    # 保存 Agent 回答
                    st.session_state["chat_history"].append({"role": "assistant", "content": response})
                except Exception as e:
                    st.error(f"{t['error_msg']} {e}")
