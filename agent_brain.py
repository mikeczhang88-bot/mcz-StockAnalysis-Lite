import os
import re
import operator
import streamlit as st
import yfinance as yf
from typing import TypedDict, Annotated, Sequence

from langchain_core.messages import BaseMessage, SystemMessage, ToolMessage, HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool

# ==========================================
# 1. 系统提示词配置 (中文 + 清晰 Markdown)
# ==========================================
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
# 3. 初始化 LLM
# ==========================================
def build_llm():
    gemini_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not gemini_key:
        raise ValueError("❌ 未找到 GEMINI_API_KEY，请在 Streamlit Secrets 里添加 GEMINI_API_KEY")
    
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
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]

def create_agent_graph():
    llm = build_llm()
    tools = [fetch_stock_technical_indicators]
    llm_with_tools = llm.bind_tools(tools)

    def agent_node(state: AgentState):
        messages = state["messages"]
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
# 5. 辅助与主运行逻辑
# ==========================================
def extract_text(raw_content) -> str:
    """清洗与提取 LLM 输出文本"""
    if isinstance(raw_content, list):
        return "\n".join([item["text"] for item in raw_content if isinstance(item, dict) and "text" in item])
    return str(raw_content)

def classify_user_intent(text: str) -> tuple[str, str]:
    """
    智能识别用户意图：
    1. 'quick_price': 查询股价/指标简讯
    2. 'full_report': 生成完整深度报告
    3. 'chat': 普通追问或知识咨询
    """
    text_clean = text.strip()
    text_upper = text_clean.upper()

    # 1. 查股价/价格判断 (包含 股价/价格/现价/多少钱/price/quote 等关键词)
    price_keywords = r'(股价|价格|现价|多少钱|PRICE|QUOTE)'
    if re.search(price_keywords, text_upper):
        # 提取 1-5 位连续英文字母（无需单词边界，如 JNJ现在 -> JNJ）
        match = re.search(r'[A-Z]{1,5}', text_upper)
        symbol = match.group(0) if match else text_clean
        return 'quick_price', symbol

    # 2. 生成完整报告判断 (纯代码或 "分析 JNJ")
    ticker_match = re.sub(r'^(分析|ANALYZE|CHECK|LOOK UP|报告|RESEARCH)\s*', '', text_upper, flags=re.IGNORECASE)
    if re.match(r'^[A-Z0-9\.\-]{1,6}$', ticker_match):
        return 'full_report', ticker_match

    # 3. 其他所有情况归为普通对话
    return 'chat', text_clean


def run_agent(user_input: str, history_messages: list = None, lang: str = "zh") -> tuple[str, bool]:
    sys_prompt = SYSTEM_PROMPT_EN if lang == "en" else SYSTEM_PROMPT_ZH
    intent, payload = classify_user_intent(user_input)

    # -------------------------------------------------------------
    # 场景 1：简短查询股价 -> 极简回答，严禁报告
    # -------------------------------------------------------------
    if intent == 'quick_price':
        prompt_price = (
            f"The user wants a quick price & indicator query for stock '{payload}'. "
            f"1. Call `fetch_stock_technical_indicators('{payload}')` once.\n"
            f"2. Answer directly in 2-3 short sentences with the latest price, MA20, RSI, and a very brief 1-sentence comment.\n"
            f"3. DO NOT output headers or full analysis reports!"
        ) if lang == "en" else (
            f"用户正在快速查询股票 '{payload}' 的当前股价与指标。\n"
            f"1. 请调用 1 次 `fetch_stock_technical_indicators('{payload}')` 工具。\n"
            f"2. 用 2-3 句话直接回答最新现价、MA20、RSI14，并附带一句极简点评。\n"
            f"3. 绝对不要输出 Markdown 标题，绝对不要输出 5 段式大报告！"
        )
        
        # 使用独立的轻量级 Prompt，彻底脱离大报告约束
        messages = [
            SystemMessage(content="你是一位高效的 AI 金融助手。只回答核心数据与简短结论，简洁明了。"),
            HumanMessage(content=prompt_price)
        ]
        final_state = evolve_stock_agent.invoke({"messages": messages})
        return extract_text(final_state["messages"][-1].content), False

    # -------------------------------------------------------------
    # 场景 2：纯股票代码/分析指令 -> 生成 5 段式完整深度报告
    # -------------------------------------------------------------
    elif intent == 'full_report':
        messages = [
            SystemMessage(content=sys_prompt),
            HumanMessage(content=f"Please analyze stock {payload}" if lang == "en" else f"请分析股票 {payload}")
        ]
        final_state = evolve_stock_agent.invoke({"messages": messages})
        return extract_text(final_state["messages"][-1].content), True

    # -------------------------------------------------------------
    # 场景 3：普通追问与多轮对话 -> 灵活回答，不套用大报告格式
    # -------------------------------------------------------------
    else:
        chat_sys_prompt = "你是专业、亲切的 AI 金融助手。根据用户的提问和上下文进行解答，回答精炼专业。"
        messages = [SystemMessage(content=chat_sys_prompt)]
        
        if history_messages:
            for msg in history_messages:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
                    
        messages.append(HumanMessage(content=user_input))
        final_state = evolve_stock_agent.invoke({"messages": messages})
        return extract_text(final_state["messages"][-1].content), False
