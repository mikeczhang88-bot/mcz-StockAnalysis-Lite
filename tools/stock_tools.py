# tools/stock_tools.py
import os
import requests
import pandas as pd
import streamlit as st
from langchain_core.tools import tool

@tool
def fetch_stock_technical_indicators(ticker: str) -> str:
    """
    使用 Alpha Vantage 获取美股最新价格、MA20 和 14日 RSI。
    Gets stock price, MA20, and 14-day RSI via Alpha Vantage.
    """
    try:
        api_key = st.secrets.get("ALPHA_VANTAGE_API_KEY") or os.environ.get("ALPHA_VANTAGE_API_KEY")
        if not api_key:
            return "❌ 系统未检测到 ALPHA_VANTAGE_API_KEY，请在 Secrets 中配置。"

        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker.upper()}&outputsize=compact&apikey={api_key}"
        response = requests.get(url, timeout=10)
        data = response.json()

        if "Time Series (Daily)" not in data:
            if "Note" in data:
                return "❌ 触发 Alpha Vantage 免费频率限制（每分钟 5 次），请稍等一分钟再试。"
            return f"❌ 未能获取到 {ticker} 的历史数据，请检查代码或股票代码是否正确。"

        daily_data = data["Time Series (Daily)"]
        df = pd.DataFrame.from_dict(daily_data, orient='index')
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        
        df['Close'] = df['4. close'].astype(float)

        if df.empty or len(df) < 20: 
            return f"❌ {ticker} 的历史数据不足，无法计算指标。"

        latest_close = float(df['Close'].iloc[-1])
        df['MA20'] = df['Close'].rolling(window=20).mean()
        latest_ma20 = float(df['MA20'].iloc[-1])
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-9)
        df['RSI'] = 100 - (100 / (1 + rs))
        latest_rsi = float(df['RSI'].iloc[-1])
        
        return (f"📊【{ticker.upper()} 技术面 / Technicals】\n"
                f"- 现价/Price: ${latest_close:.2f}\n"
                f"- MA20: ${latest_ma20:.2f} ({'线上/Above' if latest_close > latest_ma20 else '线下/Below'})\n"
                f"- RSI: {latest_rsi:.2f}")
    except Exception as e:
        return f"❌ 基础指标计算失败: {str(e)}"
