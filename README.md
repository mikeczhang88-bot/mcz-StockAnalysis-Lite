MCZ StockAnalysis-Lite (AI 智能股票分析系统)
README.md 
________________________________________
📈 MCZ StockAnalysis-Lite (AI 智能股票分析系统)
基于 LangGraph、LangChain 与 Streamlit 构建的轻量级 AI 量化与股票分析 Agent。系统能够自动获取美股实时行情及技术指标（MA20、RSI14），结合大语言模型生成机构级的多维股票分析报告。
________________________________________
核心功能
•	多维度量化分析：涵盖核心摘要、技术面分析、基本面与行业动态、多空博弈及战术建议。
•	Agent 自动化工具调用：基于 LangGraph 构建的图结构 Agent，可根据提示词自动调用量化工具提取价格与技术指标。
•	实时流式输出：集成 Streamlit 界面，支持分析报告的流式 Markdown 实时渲染。
•	极速部署：针对 Streamlit Community Cloud 进行优化，支持开箱即用。
________________________________________
项目结构
Plaintext
├── App.py               # Streamlit 主程序与前端 UI 界面
├── agent_brain.py       # LangGraph 核心逻辑、系统提示词与 LLM 配置
├── requirements.txt     # Python 项目依赖配置文件
└── README.md            # 项目说明文档
________________________________________
环境要求与依赖
•	Python 版本：3.10+
•	核心依赖库（参见 requirements.txt）：
o	streamlit
o	yfinance
o	langchain
o	langchain-google-genai
o	langgraph
________________________________________
快速配置与运行
1. 本地运行
1.	克隆仓库：
Bash
git clone https://github.com/mikeczhang88-bot/mcz-StockAnalysis-Lite.git
cd mcz-StockAnalysis-Lite
2.	安装依赖：
Bash
pip install -r requirements.txt
3.	设置 API Key：
在项目根目录下创建 .env 文件或设置环境变量：
Code snippet
GEMINI_API_KEY="你的_Google_Gemini_API_Key"
4.	启动 Streamlit：
Bash
streamlit run App.py
________________________________________
2. Streamlit Cloud 云端部署
1.	将仓库 Fork 或 Push 至你的 GitHub 账号。
2.	登录 Streamlit Community Cloud 并导入项目。
3.	在 App Settings -> Secrets 中添加 API Key：
Ini, TOML
GEMINI_API_KEY = "你的_Google_Gemini_API_Key"
4.	点击 Deploy 即可一键完成部署。
________________________________________
💡 Gemini API 最佳实践配置说明
为了保证大模型调用的稳定性和兼容性，本项目在不同类型的 API 账户下推荐使用以下配置：
1. 付费账户 (Tier 1 Prepay) —— 推荐
•	API Key：请使用绑定了付费账户的项目 Key（如 Default Gemini Project）。
•	模型别名：gemini-flash-latest
•	特点：无并发/频率限制，支持最新 Flash 模型，绝不报 404/429 错。
Python
# agent_brain.py 中 build_llm() 标准写法
llm = ChatGoogleGenerativeAI(
    model="gemini-flash-latest",
    google_api_key=gemini_key,
    temperature=0.2,
    streaming=True
)
2. 免费账户 (Free Tier)
•	API Key：使用免费项目的 Key。
•	模型别名：gemini-1.5-flash
•	特点：适合低频测试。由于 LangGraph 会触发多次思考，请勿高频连续点击（每次请求之间建议间隔 1 分钟，以防触发 429 限流）。
________________________________________
常见问题与排错 (Troubleshooting)
•	错误 429 RESOURCE_EXHAUSTED：
o	原因：使用了免费额度的 Key 且请求超限。
o	排查：检查 Streamlit Secrets 中的 GEMINI_API_KEY 是否误填为了 Free Tier 项目的 Key。建议切换为付费 Tier 1 项目的 Key。
•	错误 404 NOT_FOUND：
o	原因：使用了硬编码的具体版本号（如废弃的模型别名）或走错了 Endpoint 路由。
o	排查：确保在 agent_brain.py 中使用 langchain-google-genai 原生 SDK，并将模型名设为通用别名 gemini-flash-latest。
