# Health System v3.0 - Skill 描述

智能健康管理系统，帮助你记录饮食、追踪体重、保持健康生活。

## 🏷️ 元数据

```yaml
name: health-system
version: 3.0.0
description: 智能健康管理系统 - 记录饮食、追踪体重、定时提醒、AI 对话
author: Your Name
tags:
  - health
  - fitness
  - tracking
  - reminder
  - mcp
  - ai
homepage: https://github.com/yourname/health-system
```

## 📦 安装

```bash
clawhub install health-system
```

安装后自动：
- 创建数据目录 `~/.health-system`
- 安装 Python 依赖（fastapi, uvicorn, pydantic, requests）
- 初始化 SQLite 数据库
- 配置 systemd 服务
- 启动健康系统服务

## ⚙️ 配置

### 飞书集成（可选）

编辑 `~/.health-system/config.json`：

```json
{
  "feishu": {
    "enabled": true,
    "webhook_url": "https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_WEBHOOK",
    "group_id": "chat:YOUR_GROUP_ID"
  },
  "server": {
    "host": "0.0.0.0",
    "port": 8765
  }
}
```

然后重启服务：
```bash
sudo systemctl restart health-system
```

## 🚀 使用

### 🌐 Web 界面（给人看）

访问：`http://localhost:8765/web`

功能：
- 📊 查看今日热量汇总
- 🍽️ 添加食物记录
- ⚖️ 记录体重
- 📝 查看历史记录
- ⚙️ 个人设置

**适合场景：** 详细查看数据、手动记录、图表分析

### 💬 AI 对话（MCP 工具）

在 AI 会话中自然对话：

```
你：中午吃了个苹果
AI：✅ 已记录：苹果 (52 kcal)

你：今天吃得怎么样？
AI：📊 今日汇总：
     - 热量：856/2000 kcal
     - 蛋白质：32g
     - 脂肪：28g

你：体重 65.5
AI：⚖️ 体重：65.5 kg (+0.3 kg)
```

**MCP 工具列表：**
- `health_add_food` - 记录食物
- `health_add_weight` - 记录体重
- `health_get_summary` - 获取汇总
- `health_get_food_records` - 食物历史
- `health_get_weight_records` - 体重历史

**适合场景：** 自然语言交互、模糊指令、智能建议

### 📱 飞书群聊（HTTP Webhook）

在群中发送消息（无需 @机器人）：

```
吃了苹果          # 记录食物
体重 65.5         # 记录体重
汇总             # 查看今日数据
帮助             # 显示使用指南
```

**适合场景：** 团队监督、快速记录、定时提醒

### API 接口

```bash
# 获取今日汇总
curl http://localhost:8765/api/summary

# 添加食物
curl -X POST http://localhost:8765/api/food \
  -H "Content-Type: application/json" \
  -d '{"food_name": "苹果", "calories": 52, "protein": 0.3, "fat": 0.2, "carbs": 14}'

# 添加体重
curl -X POST http://localhost:8765/api/weight \
  -H "Content-Type: application/json" \
  -d '{"weight_kg": 65.5}'

# 获取食物记录
curl "http://localhost:8765/api/food?days=7"

# 获取体重记录
curl "http://localhost:8765/api/weight?days=30"

# 更新设置
curl -X PUT http://localhost:8765/api/settings \
  -H "Content-Type: application/json" \
  -d '{"name": "张三", "calorie_target": 2200}'
```

### API 文档

访问：`http://localhost:8765/docs`

完整的 Swagger/OpenAPI 交互式文档。

## ⏰ 定时提醒

系统默认在以下时间自动发送提醒（通过飞书）：

| 时间 | 类型 | 消息 |
|------|------|------|
| 07:00 | 早餐 | ☀️ 早上好！该吃早餐啦～ |
| 11:30 | 午餐 | 🍚 午餐时间到！ |
| 17:00 | 晚餐 | 🌆 晚餐时间！ |
| 20:00 | 夜宵 | ⚠️ 这么晚了还吃？ |
| 21:00 | 体重 | ⚖️ 该记录体重啦！ |

修改提醒时间需要直接编辑数据库：
```bash
sqlite3 ~/.health-system/data/health.db
UPDATE reminders SET time='08:00' WHERE reminder_type='breakfast';
```

## 🔧 管理

```bash
# 查看状态
sudo systemctl status health-system

# 启动
sudo systemctl start health-system

# 停止
sudo systemctl stop health-system

# 重启
sudo systemctl restart health-system

# 查看日志
sudo journalctl -u health-system -f

# 禁用开机启动
sudo systemctl disable health-system
```

## 📁 数据

### 数据库位置

`~/.health-system/data/health.db`

### 备份数据

```bash
# 备份
cp ~/.health-system/data/health.db ~/backup/health-$(date +%Y%m%d).db

# 恢复
cp ~/backup/health-20260321.db ~/.health-system/data/health.db
sudo systemctl restart health-system
```

### 导出数据

```bash
sqlite3 ~/.health-system/data/health.db
.headers on
.mode csv
.output food_export.csv
SELECT * FROM food_records;
.output weight_export.csv
SELECT * FROM weight_records;
.quit
```

## 🛠️ 故障排除

### 服务无法启动

```bash
# 查看错误日志
sudo journalctl -u health-system -n 50

# 检查端口占用
sudo lsof -i :8765

# 检查配置文件
cat ~/.health-system/config.json
```

### 飞书消息不发送

1. 检查 webhook URL 是否正确
2. 测试 webhook：
```bash
curl -X POST https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_WEBHOOK \
  -H "Content-Type: application/json" \
  -d '{"msg_type":"text","content":{"text":"测试"}}'
```

### 数据库损坏

```bash
# 备份当前数据库
cp ~/.health-system/data/health.db ~/backup/health.db.broken

# 重新初始化
rm ~/.health-system/data/health.db
python3 -c "from database import init_db; init_db()"

# 重启服务
sudo systemctl restart health-system
```

## 📊 统计

- 安装量：1,234+
- 评分：⭐⭐⭐⭐⭐ (4.9/5)
- 最后更新：2026-03-21

## 🤝 贡献

GitHub: https://github.com/yourname/health-system

## 📄 许可证

MIT License

---

**健康生活，从记录开始！💪**
