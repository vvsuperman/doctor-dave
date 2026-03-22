# Doctor Dave - 健康管理系统

> 🏥 你的私人健康饮食管理助手  
> 💪 让健康饮食变得更有趣！

[![GitHub](https://img.shields.io/github/license/vvsuperman/doctor-dave)](https://github.com/vvsuperman/doctor-dave)
[![Version](https://img.shields.io/badge/version-3.1-blue)](https://github.com/vvsuperman/doctor-dave)
[![Python](https://img.shields.io/badge/python-3.6+-green)](https://www.python.org/)

---

## 📖 目录

- [功能介绍](#-功能介绍)
- [快速开始](#-快速开始)
- [使用指南](#-使用指南)
- [系统架构](#-系统架构)
- [配置说明](#-配置说明)
- [常见问题](#-常见问题)
- [开发指南](#-开发指南)
- [更新日志](#-更新日志)

---

## ✨ 功能介绍

### 🎯 核心功能

| 功能 | 描述 | 状态 |
|------|------|------|
| **拍照识食物** | AI 自动识别食物营养成分 | ✅ |
| **饮食记录** | 文本/图片方式记录每日饮食 | ✅ |
| **体重追踪** | 记录体重变化趋势 | ✅ |
| **营养分析** | 热量/蛋白质/脂肪/碳水统计 | ✅ |
| **毒舌模式** | 不健康食物会被"怼" | ✅ |
| **定时提醒** | 一日三餐 + 体重记录提醒 | ✅ |
| **每日总结** | 20:00 推送营养报告 + 建议 | ✅ |
| **个人档案** | 身高/体重/目标管理 | ✅ |
| **Web 看板** | 可视化数据展示 | ✅ |

### 🎭 特色功能

#### 1. 智能餐次判断
根据时间自动判断餐次：
- 🌅 **早餐**：00:00 - 11:00
- ☀️ **午餐**：11:00 - 16:00
- 🌆 **晚餐**：16:00 - 23:59

#### 2. 毒舌/鼓励模式
- 🔴 **不健康食物**（热量>500kcal 或 脂肪>30g）→ 毒舌提醒
- 🟢 **健康食物**（水果、蔬菜等）→ 鼓励表扬
- ⚪ **普通食物** → 正常记录

#### 3. 每日营养报告
每天 20:00 自动推送：
- 今日总热量摄入
- 热量缺口/超标分析
- 三大营养素评估
- 个性化健康建议

---

## 🚀 快速开始

### 前置要求

- Python 3.6+
- OpenClaw 环境
- 飞书账号
- systemd（Linux）

### 安装步骤

#### 1. 克隆项目
```bash
git clone https://github.com/vvsuperman/doctor-dave.git
cd doctor-dave
```

#### 2. 安装依赖
```bash
pip3 install fastapi uvicorn requests apscheduler
```

#### 3. 初始化数据库
```bash
cd server
python3 database.py
```

#### 4. 安装系统服务
```bash
sudo cp health-system-v3.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable health-system
sudo systemctl start health-system
```

#### 5. 验证运行
```bash
curl http://localhost:8081/api/summary
```

访问 Web 界面：http://localhost:8081/shou

---

## 📝 使用指南

### 💬 飞书群命令

#### 饮食记录
```
# 发送食物照片 → 自动识别
[图片]

# 文本记录
吃了苹果
吃了炸鸡

# 查看今日汇总
汇总
今天吃了什么
```

#### 体重管理
```
# 记录体重
体重 75.5
weight 75.5

# 设置档案体重
档案体重 70
```

#### 个人信息
```
# 设置基本信息
姓名 张三
身高 175
档案体重 70

# 设置目标
目标 65          # 目标体重 65kg
目标 减重        # 目标类型：减重/增肌/维持

# 查看档案
档案
我的信息
```

#### 帮助
```
帮助
help
```

### 🌐 Web 界面

**访问地址：** http://localhost:8081/shou

**功能：**
- ✅ 今日热量摄入概览
- ✅ 三大营养素统计
- ✅ 历史饮食记录（按日期分组）
- ✅ 食物图片展示
- ❌ ~~拍照上传~~（仅通过飞书录入）

---

## 🔧 系统架构

### 技术栈

| 层级 | 技术 |
|------|------|
| **前端** | HTML5 + CSS3 + Vanilla JS |
| **后端** | FastAPI (Python 3.6+) |
| **数据库** | SQLite |
| **消息处理** | OpenClaw Hook |
| **定时任务** | APScheduler |
| **系统服务** | systemd |

### 架构图

```
┌─────────────────┐
│   飞书群聊      │
│  (用户交互)     │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  OpenClaw       │
│  Gateway        │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ health_hook.py  │
│ (消息处理器)    │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ FastAPI Server  │
│ (端口 8081)     │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ SQLite Database │
│ (数据存储)      │
└─────────────────┘
```

---

## ⚙️ 配置说明

### 服务配置

编辑 `/etc/systemd/system/health-system.service`:

```ini
[Unit]
Description=Doctor Dave - Health Management System
After=network.target

[Service]
Type=simple
User=admin
WorkingDirectory=/path/to/health-system-v3/server
ExecStart=/usr/bin/python3 /path/to/health-system-v3/server/main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### 提醒时间配置

编辑 `server/database.py` 中的默认提醒：

```python
default_reminders = [
    ('breakfast', '07:00', '☀️ 早上好！该吃早餐啦～'),
    ('lunch', '11:30', '🍚 午餐时间到！'),
    ('dinner', '17:00', '🌆 晚餐时间！'),
    ('scold', '20:00', '⚠️ 每日总结 + 毒舌提醒'),
    ('weight', '21:00', '⚖️ 该记录体重啦！'),
]
```

### 毒舌语录配置

编辑 `health_hook.py` 中的 `SNARKY_COMMENTS`:

```python
SNARKY_COMMENTS = [
    "🐷 你个死胖子，想变肥猪么？",
    "⚠️ 这热量，你是打算原地起飞？",
    # ... 添加更多
]
```

---

## ❓ 常见问题

### Q1: 服务启动失败？
```bash
# 查看日志
sudo journalctl -u health-system -f

# 检查端口占用
sudo lsof -i :8081

# 重启服务
sudo systemctl restart health-system
```

### Q2: 飞书消息不响应？
- 检查 OpenClaw Gateway 是否运行
- 确认 health_hook.py 配置正确
- 查看飞书渠道配置

### Q3: 数据库文件在哪？
```
~/.health-system/data/health.db
```

### Q4: 如何备份数据？
```bash
# 备份数据库
cp ~/.health-system/data/health.db ~/backup/health_$(date +%Y%m%d).db

# 备份配置
cp -r ~/.health-system/config.json ~/backup/
```

### Q5: 如何重置数据？
```bash
# 停止服务
sudo systemctl stop health-system

# 删除数据库
rm ~/.health-system/data/health.db

# 重新初始化
cd server
python3 database.py

# 重启服务
sudo systemctl start health-system
```

---

## 🛠️ 开发指南

### 项目结构

```
doctor-dave/
├── server/
│   ├── main.py              # FastAPI 后端
│   ├── database.py          # 数据库管理
│   └── food_recognizer.py   # 食物识别
├── health_hook.py           # OpenClaw Hook 处理器
├── web/
│   └── index.html           # Web 前端
├── health-system-v3.service # systemd 服务配置
├── README.md                # 本文档
└── .gitignore              # Git 忽略文件
```

### 添加新功能

#### 1. 添加 API 端点
编辑 `server/main.py`:

```python
@app.get("/api/new-feature")
async def new_feature(user_id: int = 1):
    # 实现逻辑
    return {"data": "..."}
```

#### 2. 添加数据库字段
编辑 `server/database.py`:

```python
c.execute("ALTER TABLE users ADD COLUMN new_field TEXT")
```

#### 3. 更新 Hook 处理器
编辑 `health_hook.py`:

```python
def process_text(text: str) -> dict:
    if "新命令" in text:
        # 处理逻辑
        return {"reply": "响应"}
```

### 代码规范

- 使用 Python 类型注解
- 遵循 PEP 8 风格指南
- 函数添加文档字符串
- 关键逻辑添加注释

---

## 📊 数据库表结构

### users 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| name | TEXT | 姓名 |
| height_cm | REAL | 身高 (cm) |
| current_weight_kg | REAL | 当前体重 (kg) |
| target_weight_kg | REAL | 目标体重 (kg) |
| goal_type | TEXT | 目标类型（减重/增肌/维持） |
| calorie_target | INTEGER | 每日热量目标 |
| created_at | TIMESTAMP | 创建时间 |

### food_records 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| user_id | INTEGER | 用户 ID |
| food_name | TEXT | 食物名称 |
| calories | REAL | 热量 (kcal) |
| protein | REAL | 蛋白质 (g) |
| fat | REAL | 脂肪 (g) |
| carbs | REAL | 碳水 (g) |
| meal_type | TEXT | 餐次（早餐/午餐/晚餐） |
| image_path | TEXT | 图片路径 |
| recorded_at | TIMESTAMP | 记录时间 |

### weight_records 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| user_id | INTEGER | 用户 ID |
| weight_kg | REAL | 体重 (kg) |
| recorded_at | TIMESTAMP | 记录时间 |

---

## ⚠️ 使用须知

### 隐私保护
- 📍 所有数据存储在本地（`~/.health-system/`）
- 🔒 不会上传到任何云端服务器
- 👤 多用户数据隔离（通过 user_id）

### 健康建议
- 💡 系统提供的建议仅供参考
- 🩺 如有健康问题请咨询专业医生
- 🎯 减重目标应合理（建议每周 0.5-1kg）

### 数据准确性
- 📸 AI 识别结果可能存在误差
- 📊 建议定期校准体重记录
- 🍽️ 外出就餐热量估算可能不准确

### 系统维护
- 💾 定期备份数据库
- 🔄 及时更新系统版本
- 📝 查看更新日志了解新特性

### 使用限制
- 🌐 需要稳定的网络连接（飞书消息）
- ⏰ 定时提醒依赖系统时间准确性
- 📱 目前仅支持飞书平台

---

## 📝 更新日志

### v3.1 - 2026-03-22
- ✨ 命名系统为 "Doctor Dave"
- ✨ 添加个人档案管理（姓名/身高/体重/目标）
- ✨ 添加每日营养总结（20:00 推送）
- ✨ 添加个性化健康建议
- 🎭 优化毒舌模式语录库
- 🗑️ 移除 Web 端拍照上传功能
- 🔧 修复数据库字段缺失问题
- 📝 完善 README 文档

### v3.0 - 2026-03-21
- ✨ FastAPI 后端重构
- ✨ SQLite 数据库支持
- ✨ Web 管理界面
- ✨ 飞书群集成
- ✨ 毒舌/鼓励模式
- ✨ 定时提醒服务
- ✨ systemd 开机自启

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📮 联系方式

- **GitHub Issues**: [提交问题](https://github.com/vvsuperman/doctor-dave/issues)
- **项目地址**: https://github.com/vvsuperman/doctor-dave

---

## 🙏 致谢

感谢以下开源项目：

- [OpenClaw](https://github.com/openclaw/openclaw) - AI 助手框架
- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架
- [APScheduler](https://apscheduler.readthedocs.io/) - 定时任务

---

<div align="center">

**🏥 Doctor Dave - 你的健康，我来守护！**

Made with ❤️ by Doctor Dave Team

</div>
