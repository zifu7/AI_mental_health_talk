# 🧠 心理健康 AI 助手「小暖」

基于 **Vue 3 + FastAPI** 的全栈心理健康服务平台，提供 AI 心理咨询、情绪日记、心理健康知识库与管理后台数据分析。集成 **DeepSeek 大语言模型**：对话侧是自研的 function calling Agent，知识库侧是带**评测闭环**的 RAG 混合检索。

📐 **[设计决策文档](设计决策.md)** —— 9 条关键技术选型的"为什么"、各自代价与实测证据
📊 **[检索评测报告](backend/eval/results/report_v3_tokenizer.md)** —— 52 条人工标注查询、6 类查询、8 种策略横向对比、阈值扫描

---

## 🤖 AI 部分怎么做的

### 对话 Agent（`app/services/agent.py`）

基于 DeepSeek function calling 自研，未依赖 LangChain——因为有两处需要精确控制：**用户身份与数据库会话等服务端参数经 `partial` 预绑定注入，不进入模型的参数 schema**；**工具异常转字符串回传模型**由模型自行决定重试或如实告知，而不是直接 500。

- 最多 3 轮工具循环，防止模型死循环烧 token
- 流式模式下 tool_calls 按 `index` 拼装分片，实现"工具执行状态"与"正文逐字输出"共存
- 隐私取舍：日记工具只返回聚合统计（平均分、高频情绪），不返回日记原文

### RAG 混合检索（`app/services/retrieval.py`）

向量 + BM25 双路召回，RRF 融合（k=60，权重 2:1），再做**文章级去重**——同一篇文章最多保留最靠前的一段，把 top-k 名额让给更多样的文章。

- 中文分词手写 bigram，不引入 jieba，原理完全透明
- 索引时注入标题前缀、展示前剥离（索引文本 ≠ 展示文本），让标题同时进入语义与词面两条通道
- **阈值拒答**：融合榜单 top1 余弦 < 0.55 时返回空列表，由上层如实告知"知识库没有查到"，避免硬凑一篇最像的文章诱发幻觉

### 评测闭环（`backend/eval/`）

策略迭代要能回答"改好了还是改坏了"，所以建了一套 golden set：**52 条人工标注查询，分 6 类**（关键词 / 改写 / 口语化 / 多意图 / 术语 / 库外），按文章级统计 Hit@k、Recall@k、MRR。

对照实验纪律：语料、切块、查询向量全固定，**一次只变一个变量**；每次改动留独立版本报告（v1_no_title → v2_title → v3_tokenizer）可前后对比。

| 指标（v3 生产策略 hybrid_cut_dedup） | 值 |
|---|---|
| Hit@3 / Recall@5 / MRR@10 | 0.808 / 0.837 / 0.739 |
| 单次检索耗时 | ~22ms |
| 阈值 0.55 下：正常问题放行率 / 库外误召率 | 0.93 / 0.12 |

复现评测（需先配置 `EMBEDDING_API_KEY`）：

```bash
cd backend
venv/Scripts/python -m eval.run_eval v4_你的标签
```

---

## ✨ 核心功能

### 👤 用户端

- **AI 心理咨询（流式对话）**  
  基于 DeepSeek 模型实现实时流式对话，提供温暖、专业的心理支持。

- **情绪日记**  
  记录每日情绪状态、触发因素、睡眠压力等，并自动生成 AI 情绪分析报告。

- **心理健康知识库**  
  浏览、搜索心理学科普文章，支持标签分类、阅读量统计。

- **用户注册/登录**  
  支持 JWT 身份认证，区分普通用户与管理员。

### 🛠️ 管理后台

- **数据仪表盘**  
  可视化展示用户活跃度、情绪趋势、咨询会话统计，使用 ECharts 实现。

- **知识文章管理**  
  富文本编辑器（WangEditor）支持文章增删改查、发布/下线、封面上传。

- **咨询记录管理**  
  查看所有用户的会话详情、消息记录，支持按时间/用户筛选。

- **情绪日志管理**  
  查看用户提交的情绪日记，包含 AI 分析结果（情绪评分、风险等级、改善建议）。

---

## 🚀 技术栈

| 领域 | 技术 |
|------|------|
| 前端框架 | Vue 3 + Vite |
| UI 组件库 | Element Plus |
| 状态管理 | Pinia |
| 路由 | Vue Router |
| HTTP 请求 | Axios |
| 富文本编辑器 | WangEditor |
| 数据可视化 | ECharts |
| Markdown 渲染 | 自定义组件 |
| 后端框架 | FastAPI (Python 3.10+) |
| 数据库 | MySQL + SQLAlchemy (异步) |
| 认证 | JWT + bcrypt |
| 大模型 | DeepSeek API（流式 + function calling） |
| Embedding | 硅基流动 BAAI/bge-m3（OpenAI 兼容接口） |
| 检索 | 向量余弦 + 手写 BM25 + RRF 融合 |
| 流式传输 | SSE（`@microsoft/fetch-event-source`） |
| 文件上传 | aiofiles + 本地存储 |
| 跨域 | CORS 中间件 |
| 部署 | Docker Compose + Nginx |
## 📦 项目结构

```
vite-project/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── api/                # 路由接口（v1）
│   │   │   ├── auth.py         # 注册/登录
│   │   │   ├── chat.py         # 心理咨询（流式）
│   │   │   ├── diary.py        # 情绪日记
│   │   │   ├── knowledge.py    # 文章管理
│   │   │   └── analytics.py    # 数据统计
│   │   ├── core/               # 配置、数据库、安全
│   │   ├── models/             # SQLAlchemy 模型
│   │   ├── schemas/            # Pydantic 校验模型
│   │   ├── services/
│   │   │   ├── agent.py        # ★ function calling 对话 Agent
│   │   │   ├── rag.py          # ★ 文本切分 / Embedding / 建索引
│   │   │   ├── retrieval.py    # ★ 向量 + BM25 + RRF 混合检索
│   │   │   └── ...             # 各业务模块 Service
│   │   └── utils/              # AI 客户端、文件上传
│   ├── eval/                   # ★ 检索评测：golden set + 指标 + 版本报告
│   │   ├── golden.py           #   52 条标注查询（6 类）
│   │   ├── run_eval.py         #   8 种策略横向对比
│   │   └── results/            #   各版本报告与原始数据
│   ├── requirements.txt        # Python 依赖
│   └── .env.example            # 环境变量模板
│
└── frontend/                   # Vue 3 前端
    ├── src/
    │   ├── api/                # 接口封装
    │   ├── components/         # 可复用组件
    │   ├── views/              # 页面视图
    │   ├── stores/             # Pinia 状态管理
    │   ├── router/             # 路由配置
    │   ├── utils/              # 工具函数（axios 拦截器）
    │   └── config/             # 全局配置
    ├── public/                 # 静态资源
    ├── index.html
    └── package.json
```
## 🔧 快速开始

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd vite-project
```

### 2. 后端配置

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

创建 `.env` 文件（参考 `.env.example`）：

```env
DATABASE_URL=mysql+pymysql://用户名:密码@localhost/数据库名
SECRET_KEY=你的JWT密钥
DEEPSEEK_API_KEY=你的DeepSeek密钥
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
# Embedding（RAG 检索用）：DeepSeek 官方无 embedding 接口，用硅基流动的 BGE 系列
EMBEDDING_API_KEY=你的硅基流动密钥
EMBEDDING_BASE_URL=https://api.siliconflow.cn/v1
EMBEDDING_MODEL=BAAI/bge-m3
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

启动后端服务：

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 前端配置

```bash
cd frontend
npm install
```

修改 `vite.config.js` 中的代理目标（若后端地址不同）：

```js
proxy: {
  "/api": {
    target: "http://localhost:8000",   // 改成你的后端地址
    changeOrigin: true,
  },
}
```

启动前端开发服务器：

```bash
npm run dev
```

访问 `http://localhost:5173` 即可体验。

### 4. 数据库初始化

> 后端启动时会自动创建表（通过 `Base.metadata.create_all`），确保数据库已存在。

---

## 📌 环境变量说明

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `DATABASE_URL` | MySQL 连接串 | `mysql+pymysql://root:123456@localhost/ai_psychology` |
| `SECRET_KEY` | JWT 签名密钥 | 随机字符串 |
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | `sk-xxx` |
| `DEEPSEEK_BASE_URL` | DeepSeek 接口地址 | `https://api.deepseek.com/v1` |
| `EMBEDDING_API_KEY` | 向量模型密钥（硅基流动） | `sk-xxx` |
| `EMBEDDING_BASE_URL` | Embedding 接口地址 | `https://api.siliconflow.cn/v1` |
| `EMBEDDING_MODEL` | Embedding 模型名 | `BAAI/bge-m3` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token 过期时间（分钟） | `30` |

> ⚠️ `.env` 文件已加入 `.gitignore`，请勿提交到仓库！

---

## 🧪 测试账户（演示用）

- **普通用户**：`allen / 123456`（请自行注册）
- **管理员**：`admin / admin123`（需在数据库中手动将 `user_type` 设为 `2`）

---

## 🎯 项目亮点

- **AI 不是调个接口**：Agent 自行拼装 function calling 协议、处理流式分片；RAG 自行实现 BM25 与 RRF，不套框架——因为有两处需要精确控制（见上方「AI 部分怎么做的」）。
- **检索有据可依**：52 条标注评测集 + 8 种策略横向对比 + 版本化报告，每个结论都能溯源到具体数字，每个"改进"都单独验证过。
- **敢说不**：检索不到就拒答，不硬凑最像的文章喂给模型——把及格线交给确定性的分数判断，而不是指望模型自觉。
- **全栈闭环**：从数据库设计到前端交互，独立完成开发与上线部署（Docker Compose + Nginx）。
- **安全设计**：JWT 认证、密码加密、SQLAlchemy 防注入、会话归属校验。
- **响应式主题**：支持亮/暗色模式切换，提升使用舒适度。
