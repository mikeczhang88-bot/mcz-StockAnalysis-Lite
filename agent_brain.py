import os
import streamlit as st
import yfinance as yf
from typing import TypedDict, Annotated, Sequence
import operator
from langchain_core.messages import BaseMessage, SystemMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool

import re
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

def is_stock_ticker(text: str) -> bool:
    """简单正则判断：是否为纯股票代码（如 AAPL, TSLA, 600519）或简单的“分析 AAPL”指令"""
    text = text.strip().upper()
    # 匹配 1-6 位的英文字符，或类似于 "分析 AAPL" / "ANALYZE AAPL"
    clean_text = re.sub(r'^(分析|ANALYZE|CHECK|LOOK UP)\s*', '', text, flags=re.IGNORECASE)
    return bool(re.match(r'^[A-Z0-9\.\-]{1,6}$', clean_text)), clean_text
    
# ==========================================
# 1. 系统提示词配置 (中文 + 清晰 Markdown)
# ==========================================
# agent_brain.py 中的提示词更新

SYSTEM_PROMPT_ZH = """你是一位顶级的华尔街量化策略师和 AI 金融分析师。

【极重要规则】
1. 如果你需要股票技术指标，只能调用 **1 次** `fetch_stock_technical_indicators` 工具。
2. 获取到数据后，必须立即根据数据生成完整报告，**绝对禁止**再次调用任何工具！

【排版与文本格式严格要求】
1. **禁止使用任何 LaTeX 或数学公式语法（严禁使用 $ 符号或 \\[ \\] 包裹数字）**，所有数字、区间和指标直接写纯文本即可（例如：写 218.50 - 224.80，不要写成数学公式）。
2. **绝对禁止使用 `#`（一级标题）**！不要生成形如 "# Institutional Equity Research..." 的文档大标题。
3. **绝对禁止输出开场白/客套话**以及分隔线（`---`），必须直接从 `## 1. 核心要点与执行摘要` 开始输出。
4. 严格且仅包含以下 5 个二级标题 `##`：

## 1. 核心要点与执行摘要 (Executive Summary)
## 2. 技术面深度解析 (Technical Analysis)
## 3. 基本面与行业动态 (Fundamental & Sector Dynamics)
## 4. 投资逻辑与多空博弈 (Investment Thesis: Bull vs. Bear Case)
## 5. 结论与战术操作建议 (Actionable Recommendation)

请保持排版清晰，重点词汇加粗，语言专业透彻。
"""

SYSTEM_PROMPT_EN = """You are a top Wall Street Quantitative Strategist and AI Financial Analyst.

[CRITICAL RULES]
1. If you need stock technical indicators, you can ONLY call `fetch_stock_technical_indicators` tool ONCE.
2. After fetching data, immediately generate the full report based on the data. NEVER call any tool again!

[STRICT FORMATTING REQUIREMENTS]
1. **DO NOT use any LaTeX or MathJax formulas (STRICTLY PROHIBITED to use $ or \\[ \\] around numbers)**. Write all numbers and price ranges as plain text (e.g., write 218.50 - 224.80).
2. **DO NOT use `#` (H1 Header)**. Never generate document titles like "# Institutional Equity Research...".
3. **DO NOT output conversational intros or horizontal rules (`---`)**. Start directly with `## 1. Executive Summary`.
4. Strictly use the following 5 H2 (`##`) sections:

## 1. Executive Summary
## 2. Technical Analysis
## 3. Fundamental & Sector Dynamics
## 4. Investment Thesis: Bull vs. Bear Case
## 5. Actionable Recommendation

Keep the layout clean, bold key terms, and maintain a professional tone.
"""

# ==========================================
# 2. 内置基础股票工具
# ==========================================
@tool
def fetch_stock_technical_indicators(symbol: str) -> str:
    """获取美股的最新价格、MA20和RSI14指标。"""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="60d")
        if df.empty:
            return f"未能获取到股票 {symbol} 的数据，请检查代码是否正确。"
        
        close_prices = df['Close']
        current_price = close_prices.iloc[-1]
        ma20 = close_prices.rolling(window=20).mean().iloc[-1]
        
        delta = close_prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi14 = 100 - (100 / (1 + rs)).iloc[-1]
        
        return f"""
股票代码: {symbol.upper()}
最新现价: ${current_price:.2f}
20日移动平均线 (MA20): ${ma20:.2f}
14日相对强弱指标 (RSI): {rsi14:.2f}
"""
    except Exception as e:
        return f"获取指标失败: {str(e)}"

# ==========================================
# 3. 初始化 LLM（标准原生 API 写法 + v1beta 路径指定）
# ==========================================
def build_llm():
    gemini_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not gemini_key:
        raise ValueError("❌ 未找到 GEMINI_API_KEY，请在 Streamlit Secrets 里添加 GEMINI_API_KEY")
    
    # 使用官方推荐的通用最新模型别名
    llm = ChatGoogleGenerativeAI(
        model="gemini-flash-latest",
        google_api_key=gemini_key,
        temperature=0.2,
        streaming=True
    )
    return llm

# ==========================================
# 4. LangGraph 构建
# ==========================================
# ==========================================
# 4. LangGraph 构建
# ==========================================
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]

def create_agent_graph():
    llm = build_llm()
    tools = [fetch_stock_technical_indicators]
    llm_with_tools = llm.bind_tools(tools)

    def agent_node(state: AgentState):
        messages = state["messages"]
        # 直接调用模型，SystemMessage 会由 run_agent 初始化时放入 messages 开头
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def should_continue(state: AgentState):
        messages = state["messages"]
        last_message = messages[-1]
        tool_already_called = any(isinstance(m, ToolMessage) for m in messages)
        if last_message.tool_calls and not tool_already_called:
            return "tools"
        return END

    workflow = StateGraph(AgentState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(tools))
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges("agent", should_continue, ["tools", END])
    workflow.add_edge("tools", "agent")

    return workflow.compile()

evolve_stock_agent = create_agent_graph()

# ==========================================
# 5. 供前端 App.py 调用的主函数
# ==========================================
# agent_brain.py 文件最底部的 run_agent 函数
# agent_brain.py 核心修改部分
def run_agent(user_input: str, history_messages: list = None, lang: str = "zh") -> tuple[str, bool]:
    """
    统一入口：自动识别是生成新报告还是追问
    :return: (回复内容, 是否是新报告)
    """
    sys_prompt = SYSTEM_PROMPT_EN if lang == "en" else SYSTEM_PROMPT_ZH
    is_ticker, symbol = is_stock_ticker(user_input)

    # 1. 如果输入的是股票代码 -> 触发生成全新报告
    if is_ticker:
        messages = [
            SystemMessage(content=sys_prompt),
            HumanMessage(content=f"Please analyze stock {symbol}" if lang == "en" else f"请分析股票 {symbol}")
        ]
        final_state = evolve_stock_agent.invoke({"messages": messages})
        return extract_text(final_state["messages"][-1].content), True

    # 2. 如果是普通提问/追问 -> 带上历史上下文回答
    messages = [SystemMessage(content=sys_prompt)]
    if history_messages:
        for msg in history_messages:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
    
    messages.append(HumanMessage(content=user_input))
    final_state = evolve_stock_agent.invoke({"messages": messages})
    return extract_text(final_state["messages"][-1].content), False

def extract_text(raw_content) -> str:
    """清洗返回内容"""
    if isinstance(raw_content, list):
        return "\n".join([item["text"] for item in raw_content if isinstance(item, dict) and "text" in item])
    return str(raw_content)
