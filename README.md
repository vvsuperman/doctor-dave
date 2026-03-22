# Doctor Dave - 健康管理系统

> 🏥 你的私人健康饮食管理助手

---

## 📋 系统概述

**Doctor Dave** 是一个智能健康管理系统，通过飞书群聊交互，自动记录饮食、追踪体重、提供营养建议。

---

## 🎯 核心功能

### 1. 📸 拍照识食物
- 在飞书群发送食物照片
- AI 自动识别食物营养成分
- 支持毒舌/鼓励模式

### 2. 📊 数据汇总
- Web 界面实时查看
- 热量、蛋白质、脂肪、碳水统计
- 按日期分组展示

### 3. ⏰ 定时提醒
- 早餐 (07:00)、午餐 (11:30)、晚餐 (17:00)
- 夜宵提醒 (20:00)
- 体重记录 (21:00)

### 4. 🎭 毒舌模式
- 高热量食物 → 毒舌提醒
- 健康食物 → 鼓励表扬
- 让健康饮食更有趣

---

## 🌐 访问方式

### Web 界面
**地址：** http://localhost:8081/shou

**功能：**
- ✅ 查看今日汇总
- ✅ 查看历史饮食记录
- ❌ ~~拍照上传~~（已移除，仅通过飞书录入）

### API 文档
**地址：** http://localhost:8081/docs

---

## 💬 飞书群使用

### 记录食物
- **发送食物照片** → 自动识别
- **说"吃了 XXX"** → 文本记录

### 记录体重
- **说"体重 XX"** → 记录体重

### 查看汇总
- **说"汇总"** → 今日数据

---

## 🔧 技术架构

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

## 📁 项目结构

```
~/.openclaw/workspace/skills/health-system-v3/
├── server/
│   ├── main.py          # FastAPI 后端
│   ├── database.py      # 数据库管理
│   └── food_recognizer.py # 食物识别
├── health_hook.py       # OpenClaw Hook 处理器
├── web/
│   └── index.html       # Web 前端
├── health-system-v3.service # systemd 服务
└── README.md            # 本文档
```

---

## 🚀 服务管理

```bash
# 查看状态
sudo systemctl status health-system

# 重启服务
sudo systemctl restart health-system

# 查看日志
sudo journalctl -u health-system -f
```

---

## 🎭 毒舌模式

### 触发条件
- 热量 > 500 kcal
- 脂肪 > 30g
- 关键词匹配（炸鸡、火锅、奶茶等）

### 示例
```
用户：[发送炸鸡图片]
AI: ✅ 食物识别完成
    🍽️ 炸鸡 (晚餐)
    🔥 550 kcal

    🐷 你个死胖子，想变肥猪么？
```

---

## ⏰ 餐次判断

| 餐次 | 时间范围 |
|------|---------|
| **早餐** | 00:00 - 11:00 |
| **午餐** | 11:00 - 16:00 |
| **晚餐** | 16:00 - 23:59 |

---

## 📊 数据库表结构

### food_records
- id, user_id, food_name
- calories, protein, fat, carbs
- meal_type (早餐/午餐/晚餐)
- image_path, recorded_at

### weight_records
- id, user_id, weight_kg
- body_fat_pct, note
- recorded_at

---

## 🛠️ 开发说明

### 添加新食物
编辑 `server/main.py` 中的 `FOOD_DATABASE`

### 添加毒舌语录
编辑 `health_hook.py` 中的 `SNARKY_COMMENTS`

### 修改提醒时间
编辑 `server/database.py` 中的默认提醒

---

## 📝 更新日志

### v3.1 - 2026-03-22
- ✅ 命名系统为 "Doctor Dave"
- ✅ 移除 Web 端拍照上传功能（仅保留查看）
- ✅ 添加毒舌提醒模式
- ✅ 添加餐次自动判断
- ✅ 开机自启动配置

### v3.0 - 2026-03-21
- ✅ FastAPI 后端
- ✅ SQLite 数据库
- ✅ Web 管理界面
- ✅ 飞书集成

---

## 💡 别名约定

当用户提到以下名称时，均指代本系统：
- `doctor`
- `dave`
- `doctor dave`
- `doctor-dave`

---

**项目地址：** `~/.openclaw/workspace/skills/health-system-v3/`  
**Web 界面：** http://localhost:8081/shou  
**API 文档：** http://localhost:8081/docs

---

🏥 **Doctor Dave - 你的健康，我来守护！**
