# 健康系统 - 飞书消息处理指南

## 🎯 工作原理

当前 OpenClaw 已经能响应飞书消息，AI 助手可以直接调用健康系统 API。

## 📋 消息处理逻辑

### 1. 图片消息

```
飞书图片 → OpenClaw → AI 助手 → 调用 /api/food/image → 返回营养数据
```

**AI 处理逻辑：**
1. 检测到图片
2. 下载图片到本地
3. 调用 `POST http://localhost:8081/api/food/image`
4. 返回识别结果

### 2. 文本消息

```
飞书文本 → OpenClaw → AI 助手 → 关键词匹配 → 调用相应 API
```

**关键词匹配：**
- "体重 XX" → `POST /api/weight`
- "吃了 XX" → `POST /api/food`
- "汇总" → `GET /api/summary`
- "帮助" → 返回使用说明

## 🚀 当前状态

| 功能 | 状态 |
|------|------|
| HTTP 服务 | ✅ 运行中 (8081) |
| 图片识别 API | ✅ `/api/food/image` |
| Web 界面 | ✅ `/shou` |
| 飞书消息响应 | ✅ 已启用 |
| AI 调用 API | ✅ 可实现 |

## 💡 实现方式

**不需要 hook！不需要额外配置！**

AI 助手在收到消息时，直接调用健康系统 API 即可。

示例代码（AI 助手内部逻辑）：
```python
if message.has_image:
    # 下载图片
    image_path = download_image(message.image_url)
    # 调用健康系统
    result = requests.post(
        "http://localhost:8081/api/food/image",
        files={"image": open(image_path, "rb")}
    )
    # 返回结果
    return result.json()
```

## 📊 完整流程

```
用户发送图片到飞书群
    ↓
OpenClaw Gateway 接收
    ↓
AI 助手处理（当前会话）
    ↓
调用健康系统 API
    ↓
图片存本地：~/.health-system/uploads/
数据存数据库：SQLite
    ↓
返回识别结果到飞书群
    ↓
Web 界面展示：http://localhost:8081/shou
```

## ✅ 完成！

所有功能已就绪，立即可用！
