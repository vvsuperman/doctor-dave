#!/usr/bin/env python3
"""
健康管理系统 v3.0 - 主服务
FastAPI + SQLite + 飞书集成
"""

from fastapi import FastAPI, Request, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import shutil
from typing import Optional, List
from datetime import datetime, timedelta
import sqlite3
import json
import re
import requests
import threading
import time
from pathlib import Path

from database import init_db, get_connection, DB_PATH
from food_recognizer import recognize_food_from_image, match_food_in_database

# ==================== 初始化 ====================

app = FastAPI(title="Health System API", version="3.0", description="智能健康管理系统")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置
CONFIG_FILE = Path.home() / ".health-system" / "config.json"
DEFAULT_CONFIG = {
    "server": {
        "host": "0.0.0.0",
        "port": 8081  # Web 端口
    },
    "notes": "飞书消息通过 OpenClaw Gateway 路由，无需配置 webhook"
}

def load_config():
    """加载配置"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return DEFAULT_CONFIG

def save_config(config):
    """保存配置"""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

config = load_config()

# ==================== 飞书配置（已移除，使用 OpenClaw 渠道）====================
# 注意：飞书消息通过 OpenClaw Gateway 路由，不需要单独配置 webhook
# OpenClaw 已配置飞书渠道，消息自动转发到 MCP 服务

# ==================== 数据模型 ====================

class FoodRecord(BaseModel):
    food_name: str
    calories: Optional[float] = 0
    protein: Optional[float] = 0
    fat: Optional[float] = 0
    carbs: Optional[float] = 0
    serving_size: Optional[str] = "100g"
    meal_type: Optional[str] = None

class WeightRecord(BaseModel):
    weight_kg: float
    body_fat_pct: Optional[float] = None
    note: Optional[str] = None

class UserSettings(BaseModel):
    name: Optional[str] = None
    height_cm: Optional[float] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    current_weight_kg: Optional[float] = None
    target_weight_kg: Optional[float] = None
    goal_type: Optional[str] = "维持"  # '减重' | '增肌' | '维持'
    activity_level: Optional[str] = "中等"
    calorie_target: Optional[int] = 2000

class UserProfile(BaseModel):
    name: Optional[str] = None
    height_cm: Optional[float] = None
    age: Optional[int] = None
    current_weight_kg: Optional[float] = None
    target_weight_kg: Optional[float] = None
    goal_type: Optional[str] = "维持"

# ==================== 数据库工具 ====================

def get_summary_from_db(user_id: int = 1):
    """获取今日汇总"""
    conn = get_connection()
    c = conn.cursor()
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 今日食物
    c.execute("""
        SELECT SUM(calories) as total_cal, 
               SUM(protein) as total_protein,
               SUM(fat) as total_fat,
               SUM(carbs) as total_carbs,
               COUNT(*) as meal_count
        FROM food_records 
        WHERE user_id = ? AND date(recorded_at) = ?
    """, (user_id, today))
    food_stats = c.fetchone()
    
    # 今日体重
    c.execute("""
        SELECT weight_kg FROM weight_records 
        WHERE user_id = ? AND date(recorded_at) = ?
        ORDER BY recorded_at DESC LIMIT 1
    """, (user_id, today))
    weight_row = c.fetchone()
    
    # 用户设置
    c.execute("SELECT calorie_target FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    calorie_target = user["calorie_target"] if user else 2000
    
    conn.close()
    
    return {
        "date": today,
        "calories": food_stats["total_cal"] or 0,
        "calorie_target": calorie_target,
        "calorie_remaining": calorie_target - (food_stats["total_cal"] or 0),
        "protein": food_stats["total_protein"] or 0,
        "fat": food_stats["total_fat"] or 0,
        "carbs": food_stats["total_carbs"] or 0,
        "meal_count": food_stats["meal_count"] or 0,
        "latest_weight": weight_row["weight_kg"] if weight_row else None,
    }

# ==================== 食物数据库 ====================

FOOD_DATABASE = {
    "米饭": {"calories": 130, "protein": 2.7, "fat": 0.3, "carbs": 28},
    "面条": {"calories": 110, "protein": 3.5, "fat": 0.5, "carbs": 23},
    "馒头": {"calories": 223, "protein": 7, "fat": 1.1, "carbs": 47},
    "鸡蛋": {"calories": 144, "protein": 13, "fat": 10, "carbs": 1.1},
    "牛奶": {"calories": 54, "protein": 3.2, "fat": 3.3, "carbs": 5},
    "面包": {"calories": 265, "protein": 9, "fat": 3.5, "carbs": 49},
    "苹果": {"calories": 52, "protein": 0.3, "fat": 0.2, "carbs": 14},
    "香蕉": {"calories": 89, "protein": 1.1, "fat": 0.3, "carbs": 23},
    "鸡胸肉": {"calories": 165, "protein": 31, "fat": 3.6, "carbs": 0},
    "牛肉": {"calories": 250, "protein": 26, "fat": 15, "carbs": 0},
    "鱼": {"calories": 206, "protein": 22, "fat": 12, "carbs": 0},
    "蔬菜": {"calories": 25, "protein": 2, "fat": 0.3, "carbs": 5},
    "土豆": {"calories": 77, "protein": 2, "fat": 0.1, "carbs": 17},
    "豆腐": {"calories": 76, "protein": 8, "fat": 4.8, "carbs": 1.9},
    "粥": {"calories": 46, "protein": 1.1, "fat": 0.3, "carbs": 10},
    "包子": {"calories": 230, "protein": 8, "fat": 5, "carbs": 40},
    "饺子": {"calories": 200, "protein": 10, "fat": 8, "carbs": 25},
    "火锅": {"calories": 150, "protein": 10, "fat": 10, "carbs": 5},
    "沙拉": {"calories": 80, "protein": 3, "fat": 5, "carbs": 8},
    "咖啡": {"calories": 2, "protein": 0.3, "fat": 0, "carbs": 0},
}

def recognize_food(food_name: str) -> dict:
    """识别食物营养信息"""
    food_name_lower = food_name.lower()
    
    # 模糊匹配
    for name, nutrition in FOOD_DATABASE.items():
        if name in food_name_lower or food_name_lower in name:
            return {
                "name": name,
                "calories": nutrition["calories"],
                "protein": nutrition["protein"],
                "fat": nutrition["fat"],
                "carbs": nutrition["carbs"],
            }
    
    # 未找到
    return {
        "name": food_name,
        "calories": 0,
        "protein": 0,
        "fat": 0,
        "carbs": 0,
        "note": "未在数据库中找到"
    }


@app.get("/")
async def root():
    """返回首页"""
    return {"message": "Health System API v3.0", "docs": "/docs", "web": "/web"}

@app.get("/shou", response_class=HTMLResponse)
async def web_interface():
    """返回 Web 前端"""
    import os
    # 获取项目根目录（server 的父目录）
    base_dir = Path(__file__).resolve().parent.parent
    web_path = base_dir / "web" / "index.html"
    
    if web_path.exists():
        with open(web_path, encoding='utf-8') as f:
            return f.read()
    
    return HTMLResponse("<h1>Web 前端未找到 - " + str(web_path) + "</h1>", status_code=404)

@app.get("/api/summary")
async def api_get_summary(user_id: int = 1):
    """获取今日汇总"""
    return get_summary_from_db(user_id)

@app.post("/api/food")
async def api_add_food(record: FoodRecord, user_id: int = 1):
    """添加食物记录"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO food_records (user_id, food_name, calories, protein, fat, carbs, serving_size, meal_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, record.food_name, record.calories, record.protein, 
          record.fat, record.carbs, record.serving_size, record.meal_type))
    conn.commit()
    record_id = c.lastrowid
    conn.close()
    
    return {"id": record_id, "message": f"已记录：{record.food_name}"}

@app.post("/api/weight")
async def api_add_weight(record: WeightRecord, user_id: int = 1):
    """添加体重记录"""
    conn = get_connection()
    c = conn.cursor()
    
    c.execute("SELECT weight_kg FROM weight_records WHERE user_id = ? ORDER BY recorded_at DESC LIMIT 1", (user_id,))
    prev = c.fetchone()
    
    c.execute("INSERT INTO weight_records (user_id, weight_kg, body_fat_pct, note) VALUES (?, ?, ?, ?)", 
              (user_id, record.weight_kg, record.body_fat_pct, record.note))
    conn.commit()
    record_id = c.lastrowid
    
    change = None
    if prev:
        change = round(record.weight_kg - prev["weight_kg"], 1)
    
    conn.close()
    
    return {"id": record_id, "weight_kg": record.weight_kg, "change": change}

@app.get("/api/food")
async def api_get_food_records(user_id: int = 1, days: int = 7, limit: int = 50):
    """获取食物记录"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT * FROM food_records WHERE user_id = ? ORDER BY recorded_at DESC LIMIT ?
    """, (user_id, limit))
    records = [dict(row) for row in c.fetchall()]
    conn.close()
    return {"records": records}

@app.get("/api/weight")
async def api_get_weight_records(user_id: int = 1, days: int = 30):
    """获取体重记录"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT * FROM weight_records WHERE user_id = ? ORDER BY recorded_at DESC LIMIT ?
    """, (user_id, days))
    records = [dict(row) for row in c.fetchall()]
    conn.close()
    return {"records": records}

@app.put("/api/settings")
async def api_update_settings(settings: UserSettings, user_id: int = 1):
    """更新用户设置"""
    conn = get_connection()
    c = conn.cursor()
    
    c.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if not c.fetchone():
        c.execute("""
            INSERT INTO users (id, name, height_cm, gender, age, current_weight_kg, target_weight_kg, goal_type, activity_level, calorie_target)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, settings.name, settings.height_cm, settings.gender, settings.age,
              settings.current_weight_kg, settings.target_weight_kg, settings.goal_type,
              settings.activity_level, settings.calorie_target))
    else:
        c.execute("""
            UPDATE users SET name=?, height_cm=?, gender=?, age=?, current_weight_kg=?,
                   target_weight_kg=?, goal_type=?, activity_level=?, calorie_target=?,
                   updated_at=CURRENT_TIMESTAMP WHERE id=?
        """, (settings.name, settings.height_cm, settings.gender, settings.age,
              settings.current_weight_kg, settings.target_weight_kg, settings.goal_type,
              settings.activity_level, settings.calorie_target, user_id))
    
    conn.commit()
    conn.close()
    return {"message": "设置已更新"}

@app.put("/api/profile")
async def api_update_profile(profile: UserProfile, user_id: int = 1):
    """更新用户档案（姓名、身高、体重、目标等）"""
    conn = get_connection()
    c = conn.cursor()
    
    # 检查用户是否存在
    c.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    exists = c.fetchone()
    
    if not exists:
        # 创建新用户
        c.execute("""
            INSERT INTO users (id, name, height_cm, age, current_weight_kg, target_weight_kg, goal_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, profile.name, profile.height_cm, profile.age,
              profile.current_weight_kg, profile.target_weight_kg, profile.goal_type))
    else:
        # 更新现有用户
        c.execute("""
            UPDATE users SET 
                name = COALESCE(?, name),
                height_cm = COALESCE(?, height_cm),
                age = COALESCE(?, age),
                current_weight_kg = COALESCE(?, current_weight_kg),
                target_weight_kg = COALESCE(?, target_weight_kg),
                goal_type = COALESCE(?, goal_type),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (profile.name, profile.height_cm, profile.age,
              profile.current_weight_kg, profile.target_weight_kg, profile.goal_type, user_id))
    
    conn.commit()
    conn.close()
    return {"message": "用户档案已更新"}

@app.get("/api/profile")
async def api_get_profile(user_id: int = 1):
    """获取用户档案"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT name, height_cm, age, current_weight_kg, target_weight_kg, goal_type,
               calorie_target, activity_level
        FROM users WHERE id = ?
    """, (user_id,))
    user = c.fetchone()
    conn.close()
    
    if user:
        return dict(user)
    return {}

@app.post("/api/profile/name")
async def api_set_name(name: str, user_id: int = 1):
    """设置姓名"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET name = ? WHERE id = ?", (name, user_id))
    conn.commit()
    conn.close()
    return {"message": f"姓名已设置为：{name}"}

@app.post("/api/profile/height")
async def api_set_height(height_cm: float, user_id: int = 1):
    """设置身高 (cm)"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET height_cm = ? WHERE id = ?", (height_cm, user_id))
    conn.commit()
    conn.close()
    return {"message": f"身高已设置为：{height_cm} cm"}

@app.post("/api/profile/weight")
async def api_set_weight(weight_kg: float, user_id: int = 1):
    """设置当前体重 (kg)"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET current_weight_kg = ? WHERE id = ?", (weight_kg, user_id))
    conn.commit()
    conn.close()
    return {"message": f"体重已设置为：{weight_kg} kg"}

@app.post("/api/profile/target")
async def api_set_target(target_weight_kg: float, user_id: int = 1):
    """设置目标体重 (kg)"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET target_weight_kg = ? WHERE id = ?", (target_weight_kg, user_id))
    conn.commit()
    conn.close()
    return {"message": f"目标体重已设置为：{target_weight_kg} kg"}

@app.post("/api/profile/goal")
async def api_set_goal(goal_type: str, user_id: int = 1):
    """设置目标类型（减重/增肌/维持）"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET goal_type = ? WHERE id = ?", (goal_type, user_id))
    conn.commit()
    conn.close()
    return {"message": f"目标已设置为：{goal_type}"}

@app.get("/api/settings")
async def api_get_settings(user_id: int = 1):
    """获取用户设置"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    
    if user:
        return dict(user)
    return {}


# ==================== 每日总结与建议 ====================

def generate_daily_summary(user_id: int = 1) -> dict:
    """生成每日总结和建议"""
    conn = get_connection()
    c = conn.cursor()
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 今日食物统计
    c.execute("""
        SELECT SUM(calories) as total_cal, 
               SUM(protein) as total_protein,
               SUM(fat) as total_fat,
               SUM(carbs) as total_carbs,
               COUNT(*) as meal_count
        FROM food_records 
        WHERE user_id = ? AND date(recorded_at) = ?
    """, (user_id, today))
    food_stats = c.fetchone()
    
    # 用户信息
    c.execute("""
        SELECT name, calorie_target, goal_type, current_weight_kg, target_weight_kg
        FROM users WHERE id = ?
    """, (user_id,))
    user = c.fetchone()
    
    conn.close()
    
    total_calories = food_stats["total_cal"] or 0
    calorie_target = user["calorie_target"] if user else 2000
    goal_type = user["goal_type"] if user else "维持"
    
    # 计算热量差
    calorie_diff = total_calories - calorie_target
    
    # 生成建议
    suggestions = []
    
    # 热量建议
    if calorie_diff > 0:
        suggestions.append(f"⚠️ 今天热量超标 {calorie_diff:.0f} kcal，明天注意控制哦～")
    elif calorie_diff < -200:
        suggestions.append(f"💪 热量缺口 {abs(calorie_diff):.0f} kcal，继续保持！")
    else:
        suggestions.append("✅ 今天热量控制得很好！")
    
    # 营养素建议
    total_protein = food_stats["total_protein"] or 0
    total_fat = food_stats["total_fat"] or 0
    total_carbs = food_stats["total_carbs"] or 0
    
    if total_protein < 50:
        suggestions.append("💪 蛋白质摄入偏低，明天可以多吃点鸡胸肉、鱼、蛋！")
    elif total_protein > 150:
        suggestions.append("🥩 蛋白质摄入充足，很棒！")
    
    if total_fat > 80:
        suggestions.append("🥑 脂肪摄入偏高，明天清淡一点～")
    
    if total_carbs > 300:
        suggestions.append("🍞 碳水摄入偏高，可以适当减少主食～")
    
    if total_protein >= 50 and total_fat <= 80 and total_carbs <= 300:
        suggestions.append("🌟 营养均衡，完美！")
    
    # 根据目标类型给建议
    if goal_type == "减重":
        if calorie_diff < 0:
            suggestions.append("🎯 减重目标进行中，继续加油！")
        else:
            suggestions.append("⚠️ 减重需要热量缺口，明天要控制饮食哦～")
    elif goal_type == "增肌":
        suggestions.append("💪 增肌期间保证蛋白质摄入，配合力量训练！")
    
    return {
        "date": today,
        "user_name": user["name"] if user else "亲",
        "total_calories": total_calories,
        "calorie_target": calorie_target,
        "calorie_diff": calorie_diff,
        "protein": total_protein,
        "fat": total_fat,
        "carbs": total_carbs,
        "meal_count": food_stats["meal_count"] or 0,
        "goal_type": goal_type,
        "suggestions": suggestions,
    }


# ==================== 定时提醒 ====================

def reminder_scheduler():
    """定时提醒调度器"""
    print("⏰ 定时提醒服务已启动")
    
    last_check = None
    last_daily_summary_date = None
    
    while True:
        try:
            now = datetime.now()
            current_time = now.strftime("%H:%M")
            today = now.strftime("%Y-%m-%d")
            
            # 每分钟检查一次
            if last_check != current_time:
                last_check = current_time
                
                conn = get_connection()
                c = conn.cursor()
                
                # 查询需要发送的提醒
                c.execute("""
                    SELECT * FROM reminders 
                    WHERE time = ? AND enabled = 1
                """, (current_time,))
                
                reminders = c.fetchall()
                
                for reminder in reminders:
                    # 检查今天是否已发送
                    c.execute("SELECT last_sent FROM reminders WHERE id = ?", (reminder["id"],))
                    row = c.fetchone()
                    
                    if row["last_sent"] != today:
                        message = reminder["message"]
                        
                        # 20:00 的提醒前添加每日总结
                        if reminder["reminder_type"] == "scold":
                            summary = generate_daily_summary()
                            
                            # 生成总结消息
                            summary_msg = (
                                f"📊 **每日总结** ({summary['date']})\n"
                                f"\n"
                                f"👤 {summary['user_name']}，今天辛苦了！\n"
                                f"\n"
                                f"🔥 今日总热量：{summary['total_calories']:.0f} / {summary['calorie_target']} kcal\n"
                            )
                            
                            if summary['calorie_diff'] > 0:
                                summary_msg += f"⚠️ 热量超标：+{summary['calorie_diff']:.0f} kcal\n"
                            else:
                                summary_msg += f"✅ 热量缺口：{abs(summary['calorie_diff']):.0f} kcal\n"
                            
                            summary_msg += (
                                f"\n"
                                f"💪 蛋白质：{summary['protein']:.0f}g\n"
                                f"🥑 脂肪：{summary['fat']:.0f}g\n"
                                f"🍞 碳水：{summary['carbs']:.0f}g\n"
                                f"🍽️ 餐数：{summary['meal_count']} 餐\n"
                                f"\n"
                                f"💡 **营养建议：**\n"
                            )
                            
                            for suggestion in summary['suggestions']:
                                summary_msg += f"{suggestion}\n"
                            
                            summary_msg += (
                                f"\n"
                                f"---\n"
                                f"\n"
                                f"{message}"
                            )
                            
                            message = summary_msg
                            
                            # 标记总结已发送
                            last_daily_summary_date = today
                        
                        print(f"📤 定时提醒：{message[:100]}...")
                        print(f"   💡 提醒消息通过 MCP 服务由 OpenClaw 发送到飞书")
                        
                        # 更新最后发送时间
                        c.execute("UPDATE reminders SET last_sent = ? WHERE id = ?", (today, reminder["id"]))
                        conn.commit()
                
                conn.close()
            
            time.sleep(30)  # 30 秒检查一次
        
        except Exception as e:
            print(f"❌ 提醒服务异常：{e}")
            time.sleep(60)

# ==================== 启动 ====================

if __name__ == "__main__":
    import uvicorn
    
    # 初始化数据库
    init_db()
    
    # 启动定时提醒线程
    threading.Thread(target=reminder_scheduler, daemon=True).start()
    
    # 启动 Web 服务
    host = config.get("server", {}).get("host", "0.0.0.0")
    port = config.get("server", {}).get("port", 8765)
    
    print(f"\n🚀 健康管理系统 v3.0 启动中...")
    print(f"📊 Web 界面：http://localhost:{port}/shou")
    print(f"📖 API 文档：http://localhost:{port}/docs")
    print(f"🤖 MCP 服务：mcp/mcp_server.py")
    print(f"\n💡 飞书消息通过 OpenClaw Gateway 路由到 MCP 服务")
    print(f"\n按 Ctrl+C 停止服务\n")
    
    uvicorn.run(app, host=host, port=port)

@app.post("/api/food/image")
async def api_add_food_from_image(
    image: UploadFile = File(..., description="食物图片"),
    meal_type: str = None,
    user_id: int = 1
):
    """从图片识别食物并记录"""
    try:
        # 1. 保存图片到 uploads 目录
        upload_dir = Path.home() / ".health-system" / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        import time
        timestamp = int(time.time())
        file_ext = Path(image.filename).suffix or ".jpg"
        filename = f"{timestamp}_{user_id}{file_ext}"
        file_path = upload_dir / filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        
        # 生成访问 URL
        image_url = f"/uploads/{filename}"
        
        print(f"📸 收到图片：{file_path}")
        
        # 2. 使用视觉模型识别食物
        nutrition = recognize_food_from_image(str(file_path))
        
        # 3. 如果视觉识别失败，尝试从文件名匹配
        if nutrition.get("calories", 0) == 0:
            print("⚠️ 视觉识别失败，使用文件名匹配")
            food_name = image.filename.split(".")[0]
            nutrition = match_food_in_database(food_name)
        
        # 4. 记录到数据库（包含图片 URL）
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO food_records (user_id, food_name, calories, protein, fat, carbs, meal_type, image_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, nutrition.get("food_name", "未知"), 
              nutrition.get("calories", 0), nutrition.get("protein", 0),
              nutrition.get("fat", 0), nutrition.get("carbs", 0),
              meal_type, image_url))
        
        conn.commit()
        record_id = c.lastrowid
        conn.close()
        
        return {
            "id": record_id,
            "food_name": nutrition.get("food_name", "未知"),
            "calories": nutrition.get("calories", 0),
            "protein": nutrition.get("protein", 0),
            "fat": nutrition.get("fat", 0),
            "carbs": nutrition.get("carbs", 0),
            "image_url": image_url,
            "confidence": nutrition.get("confidence", "unknown"),
            "message": f"✅ 已识别并记录：{nutrition.get('food_name', '未知')} ({nutrition.get('calories', 0)} kcal)"
        }
    
    except Exception as e:
        print(f"❌ 图片识别异常：{e}")
        raise HTTPException(status_code=500, detail=str(e))

# 挂载 uploads 目录
from fastapi.staticfiles import StaticFiles
app.mount("/uploads", StaticFiles(directory=str(Path.home() / ".health-system" / "uploads")), name="uploads")
