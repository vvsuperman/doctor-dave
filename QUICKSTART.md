# 🚀 健康管理系统 v3.0 - 快速开始

## ✅ 架构说明

**使用 OpenClaw + MCP，无需单独配置飞书 webhook！**

```
飞书群聊 → OpenClaw Gateway → MCP 服务 → 健康系统
                    (已配置渠道)  (AI 工具调用)
```

---

## 📊 三种使用方式

### 1️⃣ Web 界面（推荐用于查看详情）

**访问：** http://localhost:8765/web

**功能：**
- 📊 今日热量汇总
- 🍽️ 添加食物记录
- ⚖️ 记录体重
- 📝 历史记录
- ⚙️ 个人设置

---

### 2️⃣ AI 对话（MCP 工具）

**在 AI 会话中自然对话：**

```
你：中午吃了个苹果
AI：✅ 已记录：苹果 (52 kcal)

你：今天吃得怎么样？
AI：📊 今日汇总：
     - 热量：52/2000 kcal
     - 剩余：1948 kcal

你：体重 65.5
AI：⚖️ 体重：65.5 kg
```

**MCP 工具：**
- `health_add_food` - 记录食物
- `health_add_weight` - 记录体重
- `health_get_summary` - 获取汇总

---

### 3️⃣ 飞书群聊（通过 OpenClaw）

**无需配置！** OpenClaw 已集成飞书渠道。

**使用方式：** 在群中发送消息，AI 通过 MCP 自动处理。

---

## 🔧 服务管理

### HTTP 服务（Web + API）

```bash
# 启动
cd ~/.health-system
python3 main.py

# 或 systemd
sudo systemctl start health-system

# 访问
http://localhost:8765/web
```

### MCP 服务（AI 对话）

```bash
# 测试
cd /path/to/health-system-v3/mcp
echo '{"method":"tools/list"}' | python3 mcp_server.py

# 集成到 OpenClaw
# 在 openclaw.json 中配置 MCP 服务器
```

---

## 📁 项目位置

```
/home/admin/.openclaw/workspace/skills/health-system-v3/
├── server/main.py      # HTTP 服务
├── mcp/mcp_server.py   # MCP 服务
├── web/index.html      # Web 前端
└── install.sh          # 安装脚本
```

---

## 💡 配置说明

**不需要配置飞书 webhook！**

飞书消息通过 OpenClaw Gateway 自动路由到 MCP 服务。

OpenClaw 已配置：
- ✅ 飞书渠道（appId/appSecret）
- ✅ 群聊权限
- ✅ 消息路由

---

## 🎯 下一步

1. **访问 Web 界面** - http://localhost:8765/web
2. **配置 OpenClaw MCP** - 在 openclaw.json 中添加 MCP 服务
3. **开始使用** - 飞书群聊或 Web 界面记录数据

---

**健康生活，从记录开始！💪**
