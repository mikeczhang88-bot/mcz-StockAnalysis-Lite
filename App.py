import streamlit as st
from agent_brain import evolve_stock_agent

# 1. 页面基本配置
st.set_page_config(
    page_title="AI 量化股票分析 Agent",
    page_icon="📈",
    layout="wide"
)

# 2. 页面大标题与说明
st.title("📈 AI 机构级美股量化分析 Agent")
st.markdown("输入美股代码（如 COST, NVDA, AAPL），自动调用实时数据并生成深度多维研报。")

# 3. 侧边栏设置与说明
with st.sidebar:
    st.header("⚙️ 控制面板")
    st.info("💡 **系统状态**：已接入 Gemini API 与 LangGraph 智能智能体网络。")
    st.markdown("---")
    st.markdown("### 📌 快捷测试代码")
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    
    # 快捷输入按钮
    selected_symbol = None
    if col_btn1.button("COST"):
        selected_symbol = "COST"
    if col_btn2.button("NVDA"):
        selected_symbol = "NVDA"
    if col_btn3.button("AAPL"):
        selected_symbol = "AAPL"

# 4. 初始化 Session State 保持聊天历史
if "messages" not in st.session_state:
    st.session_state.messages = []

# 5. 渲染历史对话记录
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 6. 处理用户输入（支持键盘输入或点击侧边栏按钮）
user_input = st.chat_input("输入美股代码或分析指令，例如：分析 COST 的技术面与基本面")

# 如果点击了侧边栏快捷按钮，覆盖 user_input
if selected_symbol:
    user_input = f"请对 {selected_symbol} 进行全面的技术面与基本面量化分析"

# 7. 主分析逻辑
if user_input:
    # 显示用户消息
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 渲染 AI 实时打字机回答
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""

        # 构建发送给 LangGraph Agent 的输入格式
        inputs = {"messages": [("user", user_input)]}

        try:
            # 运行 LangGraph 流式响应
            for event in evolve_stock_agent.stream(inputs, stream_mode="updates"):
                for node_name, value in event.items():
                    if "messages" in value:
                        last_msg = value["messages"][-1]
                        
                        # 过滤掉工具调用消息，只处理模型返回的最终分析文本
                        if hasattr(last_msg, "content") and last_msg.content and not getattr(last_msg, "tool_calls", None):
                            content = last_msg.content
                            
                            # 提取文本内容：兼容字符串格式与 block 列表格式
                            if isinstance(content, str):
                                full_response += content
                            elif isinstance(content, list):
                                for block in content:
                                    if isinstance(block, dict) and block.get("type") == "text":
                                        full_response += block.get("text", "")
                            
                            # 实时刷新页面（带打字光标效果）
                            response_placeholder.markdown(full_response + "▌")

            # 最终渲染干净的 Markdown 研报（去掉光标）
            response_placeholder.markdown(full_response)
            
            # 保存 AI 回复到历史会话
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            error_msg = f"❌ 分析过程中出现错误: {str(e)}"
            response_placeholder.error(error_msg)
