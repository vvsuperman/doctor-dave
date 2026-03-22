# 🏗️ 健康管理系统 v3.0 - 架构说明

## 📊 混合架构设计

健康管理系统 v3.0 采用 **HTTP + MCP 混合架构**，同时支持：
- 🌐 **HTTP 服务** - Web 界面和 API（给人用）
- 🤖 **MCP 服务** - AI 工具调用（给 AI 用）
- 📱 **飞书集成** - 群聊消息（团队用）

```
┌─────────────────────────────────────────────────────────┐
│                   健康管理系统 v3.0                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌───────────────┐         ┌───────────────┐           │
│  │  HTTP 服务     │         │  MCP 服务      │           │
│  │  (FastAPI)    │         │  (JSON-RPC)   │           │
│  │               │         │               │           │
│  │  - Web 界面    │         │  - AI 工具     │           │
│  │  - REST API   │         │  - 自然语言    │           │
│  │  - Webhook    │         │  - 智能对话    │           │
│  │  - 定时任务   │         │               │           │
│  └───────┬───────┘         └───────┬───────┘           │
│          │                         │                    │
│          │  ┌─────────────────┐   │                    │
│          └──│  业务逻辑层      │───┘                    │
│             │  (共享代码)      │                        │
│             └────────┬────────┘                        │
│                      │                                  │
│             ┌────────▼────────┐                        │
│             │  SQLite 数据库   │                        │
│             │  (本地存储)     │                        │
│             └─────────────────┘                        │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 三种使用方式

### 1️⃣ Web 界面（HTTP 服务）

**适合：** 详细查看数据、图表分析、手动记录

```
用户 → 浏览器 → http://localhost:8765/web → FastAPI → SQLite
```

**特点：**
- ✅ 精美的可视化界面
- ✅ 实时数据更新
- ✅ 图表展示
- ✅ 适合深度使用

---

### 2️⃣ AI 对话（MCP 服务）

**适合：** 自然语言交互、模糊指令、智能建议

```
用户 → AI 助手 → MCP 工具 → SQLite
      "吃了苹果"   health_add_food
```

**特点：**
- ✅ 自然语言理解
- ✅ 模糊指令处理
- ✅ 智能追问
- ✅ 个性化建议

**示例对话：**
```
用户：今天吃得怎么样？
AI：📊 今日汇总：
     - 热量：856/2000 kcal（剩余 1144 kcal）
     - 蛋白质：32g（偏低）
     - 脂肪：28g
     - 碳水：120g
     
     建议：晚餐可以补充一些蛋白质！

用户：中午吃了个苹果
AI：✅ 已记录：苹果 (52 kcal)
    今日总摄入：908/2000 kcal
```

---

### 3️⃣ 飞书群聊（HTTP Webhook）

**适合：** 团队监督、快速记录、定时提醒

```
用户 → 飞书 → Webhook → FastAPI → SQLite
                /webhook/feishu
```

**特点：**
- ✅ 无需打开 App
- ✅ 团队互相监督
- ✅ 定时提醒
- ✅ 社交激励

**指令：**
```
吃了苹果      → 记录食物
体重 65.5     → 记录体重
汇总          → 查看数据
帮助          → 使用指南
```

---

## 📁 项目结构

```
health-system-v3/
├── server/                  # HTTP 服务（FastAPI）
│   ├── main.py             # 主服务入口
│   ├── database.py         # 数据库模块
│   └── ...
│
├── mcp/                     # MCP 服务
│   ├── mcp_server.py       # MCP 服务器
│   └── test_mcp.py         # 测试脚本
│
├── web/                     # Web 前端
│   └── index.html          # 单页应用
│
├── data/                    # 数据目录
│   └── health.db           # SQLite 数据库
│
├── install.sh              # 安装脚本
├── README.md               # 使用说明
├── SKILL.md                # clawhub 发布配置
└── ARCHITECTURE.md         # 本文档
```

---

## 🔧 服务管理

### HTTP 服务

```bash
# 启动
cd ~/.health-system
python3 main.py

# 或 systemd 管理
sudo systemctl start health-system
sudo systemctl status health-system
```

**访问：**
- Web: http://localhost:8765/web
- API: http://localhost:8765/docs
- Webhook: http://localhost:8765/webhook/feishu

---

### MCP 服务

```bash
# 测试
cd /path/to/health-system-v3/mcp
echo '{"method":"tools/list"}' | python3 mcp_server.py

# 集成到 AI 助手
# 在 AI 配置中添加 MCP 服务端点
```

**MCP 端点：**
- stdin/stdout JSON-RPC
- 或通过 HTTP 包装器

---

## 📊 数据流对比

### HTTP 服务数据流

```
用户输入 "体重 65.5"
    ↓
飞书/浏览器
    ↓
HTTP POST /webhook/feishu 或 /api/weight
    ↓
FastAPI 路由处理
    ↓
关键词匹配/参数解析
    ↓
数据库操作
    ↓
返回 JSON 响应
```

---

### MCP 服务数据流

```
用户说 "体重 65.5"
    ↓
AI 助手理解语义
    ↓
选择工具 health_add_weight
    ↓
MCP JSON-RPC 调用
    ↓
数据库操作
    ↓
返回结果给 AI
    ↓
AI 组织自然语言回复
```

---

## 🎯 使用建议

| 场景 | 推荐方式 | 原因 |
|------|---------|------|
| 快速记录 | 飞书群聊 | 最方便，无需切换 App |
| 查看详细信息 | Web 界面 | 可视化好，数据全面 |
| 自然对话 | AI (MCP) | 理解语义，可追问 |
| 团队监督 | 飞书群聊 | 公开透明，互相激励 |
| 数据分析 | Web 界面 | 图表展示 |
| 模糊指令 | AI (MCP) | AI 理解能力强 |
| 定时提醒 | HTTP 服务 | 内置定时任务 |

---

## 🚀 部署方式

### 单机部署（推荐）

```bash
# 运行安装脚本
./install.sh

# 启动 HTTP 服务
sudo systemctl start health-system

# MCP 服务（可选，如果需要 AI 集成）
# 在 AI 配置中指向 mcp_server.py
```

### Docker 部署（未来）

```bash
docker run -d \
  -p 8765:8765 \
  -v ~/.health-system:/data \
  health-system:latest
```

---

## 📈 扩展方向

### 短期
- [ ] MCP HTTP 包装器（通过 HTTP 调用 MCP）
- [ ] 更多食物数据
- [ ] 体重趋势图表

### 中期
- [ ] 微信集成
- [ ] Telegram 集成
- [ ] 饮食建议 AI

### 长期
- [ ] 多用户支持
- [ ] 数据同步
- [ ] 移动端 App

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**健康生活，从记录开始！💪**
