# 🧠 心理健康AI助手

基于 **Vue 3 + FastAPI** 的全栈心理健康服务平台，提供 AI 心理咨询、情绪日记记录、心理健康知识库 以及 管理后台数据分析 等功能。集成 **DeepSeek 大语言模型**，实现流式对话与情绪智能分析，为高校、企业或个人提供便捷的心理健康支持工具。

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
| AI 集成 | DeepSeek API (流式) |
| 文件上传 | aiofiles + 本地存储 |
| 跨域 | CORS 中间件 |
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
│   │   ├── services/           # 业务逻辑层
│   │   └── utils/              # AI 客户端、文件上传
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
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token 过期时间（分钟） | `30` |

> ⚠️ `.env` 文件已加入 `.gitignore`，请勿提交到仓库！

---

## 🧪 测试账户（演示用）

- **普通用户**：`allen / 123456`（请自行注册）
- **管理员**：`admin / admin123`（需在数据库中手动将 `user_type` 设为 `2`）

---

## 🎯 项目亮点

- **全栈实战**：从数据库设计到前端交互，独立完成完整闭环。
- **AI 集成**：对接 DeepSeek 大模型，实现流式对话和情绪分析，提升用户体验。
- **数据驱动**：ECharts 可视化看板，帮助管理者掌握平台运营状况。
- **安全设计**：JWT 认证、密码加密、SQLAlchemy 防注入。
- **工程化**：模块化分层、异步 ORM、统一异常处理、响应拦截器。
- **响应式主题**：支持亮/暗色模式切换，提升使用舒适度。
