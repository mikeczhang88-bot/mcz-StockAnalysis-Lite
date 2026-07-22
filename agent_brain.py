import os
import streamlit as st
import yfinance as yf
from typing import TypedDict, Annotated, Sequence
import operator
from langchain_core.messages import BaseMessage, SystemMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI  # 👈 1. 使用官方原生 SDK
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool

# ... [前面的 SYSTEM_PROMPT 和 fetch_stock_technical_indicators 保持不变] ...

# ==========================================
# 3. 初始化 LLM（标准原生 API 写法）
# ==========================================
def build_llm():
    gemini_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not gemini_key:
        raise ValueError("❌ 未找到 GEMINI_API_KEY，请在 Streamlit Secrets 里添加 GEMINI_API_KEY")
    
    # 使用 Google 官方标准包和官方通用模型标识符
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",  # 👈 2. 付费账户下使用 gemini-2.0-flash 稳定无阻
        google_api_key=gemini_key,
        temperature=0.2,
        streaming=True
    )
    return llm

# ==========================================
# 1. 系统提示词配置 (中文 + 清晰 Markdown)
# ==========================================
SYSTEM_PROMPT = """你是一位顶级的华尔街量化策略师和 AI 金融分析师。

【极重要规则】
1. 如果你需要股票技术指标，只能调用 **1 次** `fetch_stock_technical_indicators` 工具。
2. 获取到数据后，必须立即根据数据生成完整报告，**绝对禁止**再次调用任何工具！

请用专业、严谨、详实的中文输出一份机构级股票分析报告。报告必须包含以下 5 个核心章节，并使用清晰的标准 Markdown 格式排版（不要使用复杂公式或 LaTeX 格式）：

## 1. 核心要点与执行摘要 (Executive Summary)
- 核心投资逻辑、高阶市场前景及战术定位。

## 2. 技术面深度解析 (Technical Analysis)
- 结合最新现价、20日均线 (MA20)、14日相对强弱指标 (RSI) 进行趋势分析、均值回归分析以及关键支撑/阻力位。

## 3. 基本面与行业动态 (Fundamental & Sector Dynamics)
- 分析行业催化剂（如 AI 浪潮、供需平衡、利润率走势等）。

## 4. 投资逻辑与多空博弈 (Investment Thesis: Bull vs. Bear Case)
- 明确看多（Bull Case）与看空（Bear Case）的核心催化剂与风险点。

## 5. 结论与战术操作建议 (Actionable Recommendation)
- 给出现在明确的操作建议（如：分批建仓 / 逢低吸纳 / 持有 / 止盈离场），并给出具体的参考区间与止损位。

请保持排版清晰，重点词汇加粗，语言专业透彻。
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
# 3. 初始化 LLM（切换为 OpenAI 兼容 Endpoint 调 Gemini） - 替换
# ==========================================
# ==========================================
# 3. 初始化 LLM（标准原生 API 写法）
# ==========================================
def build_llm():
    gemini_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not gemini_key:
        raise ValueError("❌ 未找到 GEMINI_API_KEY，请在 Streamlit Secrets 里添加 GEMINI_API_KEY")
    
    # 使用 Google 官方标准包和官方通用模型标识符
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",  # 👈 2. 付费账户下使用 gemini-2.0-flash 稳定无阻
        google_api_key=gemini_key,
        temperature=0.2,
        streaming=True
    )
    return llm

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
        if not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)
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
