#!/usr/bin/env python3
"""
健康系统 - OpenClaw Hook 处理器
自动处理飞书消息（文本 + 图片）
"""

import sys
import json
import requests
import tempfile
from pathlib import Path
from datetime import datetime

HEALTH_API = "http://localhost:8081"

# ==================== 毒舌提醒配置 ====================

# 高热量食物关键词（触发毒舌）
UNHEALTHY_FOODS = [
    "炸鸡", "汉堡", "薯条", "火锅", "烧烤", "烤肉", "奶茶", 
    "蛋糕", "奶油", "油条", "肥肉", "披萨", "可乐", "雪碧",
    "辣条", "泡面", "方便面", "鸡排", "鸡腿", "五花肉",
    "培根", "香肠", "热狗", "甜甜圈", "冰淇淋", "雪糕"
]

# 毒舌语录库
SNARKY_COMMENTS = [
    "🐷 你个死胖子，想变肥猪么？",
    "⚠️ 这热量，你是打算原地起飞？",
    "💀 吃完这顿，减肥计划又要明天开始了？",
    "🤔 你是跟自己有仇吗？",
    "🎯 精准踩雷，专挑高热量的吃！",
    "📈 体重秤已经准备好迎接新高峰了！",
    "🔥 这热量，够你跑 10 公里了！",
    "💪 健身房的教练看到都要哭了！",
    "🍔 你是汉堡成精了吗？",
    "🥓 脂肪在向你招手，你看见了没？",
    "⚡ 一口下去，三天的运动白费！",
    "🎪 你是马戏团的猪吗？这么能吃！",
    "💣 热量炸弹已引爆，请做好准备！",
    "🚨 警告！检测到严重超标行为！",
    "😱 你这是要把自己吃成球吗？",
]

# 健康食物关键词（触发鼓励）
HEALTHY_FOODS = [
    "苹果", "香蕉", "橙子", "蔬菜", "水果", "沙拉", "鸡胸肉",
    "鱼肉", "虾", "牛奶", "酸奶", "燕麦", "全麦", "鸡蛋",
    "豆腐", "豆浆", "青菜", "西兰花", "番茄", "黄瓜"
]

# 鼓励语录库
ENCOURAGING_COMMENTS = [
    "👍 不错哦，继续保持！",
    "💪 健康饮食，你做得很好！",
    "🌟 这才是正确的选择！",
    "🎯 自律的人最美丽！",
    "🥗 吃得健康，活得漂亮！",
    "✨ 今天的你也很棒！",
    "🏆 给你点赞，继续加油！",
    "🌈 健康饮食，从我做起！",
    "💚 你的身体会感谢你的！",
    "🎊 优秀！这才是健康的选择！",
]

def get_snarky_comment() -> str:
    """随机返回一条毒舌评论"""
    import random
    return random.choice(SNARKY_COMMENTS)

def get_encouraging_comment() -> str:
    """随机返回一条鼓励评论"""
    import random
    return random.choice(ENCOURAGING_COMMENTS)

def is_unhealthy_food(food_name: str, calories: float, fat: float) -> bool:
    """
    判断食物是否不健康
    条件：
    1. 包含不健康关键词
    2. 热量 > 500 kcal
    3. 脂肪 > 30g
    """
    food_name_lower = food_name.lower()
    
    # 检查关键词
    for unhealthy in UNHEALTHY_FOODS:
        if unhealthy in food_name_lower:
            return True
    
    # 检查数值
    if calories > 500 or fat > 30:
        return True
    
    return False

def is_healthy_food(food_name: str) -> bool:
    """判断食物是否健康"""
    food_name_lower = food_name.lower()
    
    for healthy in HEALTHY_FOODS:
        if healthy in food_name_lower:
            return True
    
    return False

def get_meal_type(hour: int) -> str:
    """
    根据时间判断餐次
    - 早餐：11:00 前
    - 午餐：11:00-16:00
    - 晚餐：16:00 之后
    """
    if hour < 11:
        return "早餐"
    elif hour < 16:
        return "午餐"
    else:
        return "晚餐"

def download_image(image_url: str) -> str:
    """下载图片到临时文件"""
    temp_dir = Path.home() / ".health-system" / "tmp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    import time
    resp = requests.get(image_url, timeout=30)
    if resp.status_code == 200:
        filename = f"{int(time.time())}_feishu.jpg"
        image_path = temp_dir / filename
        
        with open(image_path, "wb") as f:
            f.write(resp.content)
        
        return str(image_path)
    return None

def recognize_food(image_path: str) -> dict:
    """调用健康系统 API 识别食物"""
    # 获取当前时间，判断餐次
    now = datetime.now()
    meal_type = get_meal_type(now.hour)
    
    with open(image_path, "rb") as f:
        resp = requests.post(
            f"{HEALTH_API}/api/food/image",
            files={"image": f},
            data={"meal_type": meal_type},
            timeout=60
        )
    
    if resp.status_code == 200:
        result = resp.json()
        result["meal_type"] = meal_type  # 返回餐次信息
        return result
    return {"error": resp.text}

def process_text(text: str) -> dict:
    """处理文本消息"""
    text_lower = text.lower()
    
    # ==================== 个人信息录入 ====================
    
    # 设置姓名
    if "姓名" in text_lower or "名字" in text_lower:
        import re
        match = re.search(r'姓名 [是叫]？(.+)', text)
        if match:
            name = match.group(1).strip()
            resp = requests.post(
                f"{HEALTH_API}/api/profile/name",
                params={"name": name},
                timeout=10
            )
            if resp.status_code == 200:
                return {"reply": f"✅ 姓名已设置为：{name}"}
    
    # 设置身高
    if "身高" in text_lower:
        import re
        numbers = re.findall(r'\d+\.?\d*', text)
        if numbers:
            height = float(numbers[0])
            resp = requests.post(
                f"{HEALTH_API}/api/profile/height",
                params={"height_cm": height},
                timeout=10
            )
            if resp.status_code == 200:
                return {"reply": f"✅ 身高已设置为：{height} cm"}
    
    # 设置体重（档案）
    if "档案体重" in text_lower or "设置体重" in text_lower:
        import re
        numbers = re.findall(r'\d+\.?\d*', text)
        if numbers:
            weight = float(numbers[0])
            resp = requests.post(
                f"{HEALTH_API}/api/profile/weight",
                params={"weight_kg": weight},
                timeout=10
            )
            if resp.status_code == 200:
                return {"reply": f"✅ 档案体重已设置为：{weight} kg"}
    
    # 设置目标体重
    if "目标" in text_lower or "减到" in text_lower:
        import re
        numbers = re.findall(r'\d+\.?\d*', text)
        if numbers:
            target = float(numbers[0])
            resp = requests.post(
                f"{HEALTH_API}/api/profile/target",
                params={"target_weight_kg": target},
                timeout=10
            )
            if resp.status_code == 200:
                return {"reply": f"✅ 目标体重已设置为：{target} kg"}
    
    # 设置目标类型
    if "目标" in text_lower and ("减重" in text_lower or "增肌" in text_lower or "维持" in text_lower):
        goal = "减重" if "减重" in text_lower else "增肌" if "增肌" in text_lower else "维持"
        resp = requests.post(
            f"{HEALTH_API}/api/profile/goal",
            params={"goal_type": goal},
            timeout=10
        )
        if resp.status_code == 200:
            return {"reply": f"✅ 目标已设置为：{goal}"}
    
    # 查看档案
    if "档案" in text_lower or "我的信息" in text_lower:
        resp = requests.get(f"{HEALTH_API}/api/profile", timeout=10)
        if resp.status_code == 200:
            profile = resp.json()
            if profile:
                reply = (
                    f"📋 个人档案\n"
                    f"\n"
                    f"👤 姓名：{profile.get('name', '未设置')}\n"
                    f"📏 身高：{profile.get('height_cm', 0):.0f} cm\n"
                    f"⚖️ 体重：{profile.get('current_weight_kg', 0):.1f} kg\n"
                    f"🎯 目标：{profile.get('target_weight_kg', 0):.1f} kg\n"
                    f"💪 目标类型：{profile.get('goal_type', '维持')}\n"
                    f"🔥 每日热量目标：{profile.get('calorie_target', 2000)} kcal"
                )
                return {"reply": reply}
    
    # ==================== 原有功能 ====================
    
    # 体重记录
    if "体重" in text_lower or "weight" in text_lower:
        import re
        numbers = re.findall(r'\d+\.?\d*', text)
        if numbers:
            weight = float(numbers[0])
            resp = requests.post(
                f"{HEALTH_API}/api/weight",
                json={"weight_kg": weight},
                timeout=10
            )
            if resp.status_code == 200:
                result = resp.json()
                change_str = ""
                if result.get("change"):
                    change = result["change"]
                    change_str = f" ({'+' if change > 0 else ''}{change}kg)"
                return {"reply": f"⚖️ 体重：{weight} kg{change_str}"}
    
    # 食物（文本）
    elif "吃" in text_lower or "饭" in text_lower:
        food_name = text.replace("吃", "").replace("了", "").replace("饭", "").strip()
        if food_name:
            # 判断餐次
            meal_type = get_meal_type(datetime.now().hour)
            resp = requests.post(
                f"{HEALTH_API}/api/food",
                json={"food_name": food_name, "meal_type": meal_type},
                timeout=10
            )
            if resp.status_code == 200:
                result = resp.json()
                calories = result.get('calories', 0)
                fat = result.get('fat', 0)
                
                # 判断是否健康，添加毒舌或鼓励
                comment = ""
                if is_unhealthy_food(food_name, calories, fat):
                    comment = f"\n{get_snarky_comment()}"
                elif is_healthy_food(food_name):
                    comment = f"\n{get_encouraging_comment()}"
                
                return {"reply": f"✅ 已记录：{result.get('food_name')} ({calories} kcal) - {meal_type}{comment}"}
    
    # 汇总
    elif "汇总" in text_lower or "总结" in text_lower:
        resp = requests.get(f"{HEALTH_API}/api/summary", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "reply": (
                    f"📊 今日汇总 ({data.get('date', '')})\n"
                    f"\n"
                    f"🔥 热量：{data.get('calories', 0)}/{data.get('calorie_target', 2000)} kcal\n"
                    f"剩余：{data.get('calorie_remaining', 0)} kcal\n"
                    f"💪 蛋白质：{data.get('protein', 0)}g\n"
                    f"🥑 脂肪：{data.get('fat', 0)}g\n"
                    f"🍞 碳水：{data.get('carbs', 0)}g\n"
                    f"🍽️ 餐数：{data.get('meal_count', 0)}"
                )
            }
    
    # 帮助
    elif "帮助" in text_lower or "help" in text_lower:
        return {
            "reply": (
                "🤖 Doctor Dave 健康管理系统\n"
                f"\n"
                f"📸 **记录饮食**\n"
                f"  发送食物照片 → 自动识别\n"
                f"  说'吃了 XXX' → 文本记录\n"
                f"\n"
                f"⚖️ **记录体重**\n"
                f"  说'体重 XX' → 记录体重\n"
                f"\n"
                f"📋 **个人信息**\n"
                f"  说'姓名 XXX' → 设置姓名\n"
                f"  说'身高 XXX' → 设置身高 (cm)\n"
                f"  说'档案体重 XXX' → 设置体重 (kg)\n"
                f"  说'目标 XXX' → 设置目标体重 (kg)\n"
                f"  说'目标 减重/增肌/维持' → 设置目标类型\n"
                f"  说'档案' → 查看个人信息\n"
                f"\n"
                f"📊 **查看数据**\n"
                f"  说'汇总' → 今日数据\n"
                f"\n"
                f"⏰ **定时提醒**\n"
                f"  07:00 早餐 | 11:30 午餐 | 17:00 晚餐\n"
                f"  20:00 每日总结 + 毒舌提醒\n"
                f"  21:00 体重记录\n"
                f"\n"
                f"🌐 Web: http://localhost:8081/shou"
            )
        }
    
    return {"reply": None}

def handle_message(message: dict) -> dict:
    """
    处理消息入口
    
    Args:
        message: OpenClaw 消息对象
        {
            "text": "消息文本",
            "image_url": "图片 URL",
            "sender_id": "发送者 ID",
            "chat_id": "群聊 ID",
            "channel": "feishu"
        }
    
    Returns:
        {"reply": "回复消息"} 或 None
    """
    try:
        text = message.get("text", "")
        image_url = message.get("image_url") or message.get("media_url")
        
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"📨 健康系统收到消息", file=sys.stderr)
        print(f"渠道：{message.get('channel', 'unknown')}", file=sys.stderr)
        print(f"群聊：{message.get('chat_id', 'unknown')}", file=sys.stderr)
        print(f"文本：{text[:100]}", file=sys.stderr)
        print(f"图片：{image_url}", file=sys.stderr)
        print(f"{'='*60}\n", file=sys.stderr)
        
        # 1. 图片消息 - 识别食物
        if image_url:
            print(f"📸 处理图片消息...", file=sys.stderr)
            image_path = download_image(image_url)
            
            if image_path:
                result = recognize_food(image_path)
                
                # 清理临时文件
                try:
                    Path(image_path).unlink()
                except:
                    pass
                
                if "error" not in result:
                    meal_type = result.get('meal_type', get_meal_type(datetime.now().hour))
                    food_name = result.get('food_name', '未知')
                    calories = result.get('calories', 0)
                    protein = result.get('protein', 0)
                    fat = result.get('fat', 0)
                    carbs = result.get('carbs', 0)
                    
                    # 判断是否健康，添加毒舌或鼓励
                    comment = ""
                    if is_unhealthy_food(food_name, calories, fat):
                        comment = f"\n\n{get_snarky_comment()}"
                    elif is_healthy_food(food_name):
                        comment = f"\n\n{get_encouraging_comment()}"
                    
                    reply = (
                        f"✅ 食物识别完成\n"
                        f"🍽️ {food_name} ({meal_type})\n"
                        f"🔥 {calories} kcal\n"
                        f"💪 蛋白质：{protein}g\n"
                        f"🥑 脂肪：{fat}g\n"
                        f"🍞 碳水：{carbs}g\n"
                        f"{comment}"
                        f"\n\n📊 详情：http://localhost:8081/shou"
                    )
                    print(f"💬 回复：{reply[:200]}", file=sys.stderr)
                    return {"reply": reply}
                else:
                    return {"reply": f"❌ 识别失败：{result['error']}"}
        
        # 2. 文本消息处理
        if text:
            print(f"📝 处理文本消息...", file=sys.stderr)
            result = process_text(text)
            if result.get("reply"):
                print(f"💬 回复：{result['reply'][:200]}", file=sys.stderr)
                return result
        
        return {"reply": None}
    
    except Exception as e:
        print(f"❌ 处理异常：{e}", file=sys.stderr)
        return {"reply": f"❌ 处理失败：{str(e)}"}


# OpenClaw Hook 入口
if __name__ == "__main__":
    # 从 stdin 读取消息（每行一个 JSON）
    for line in sys.stdin:
        try:
            message = json.loads(line.strip())
            result = handle_message(message)
            
            # 输出结果到 stdout
            print(json.dumps(result, ensure_ascii=False))
            sys.stdout.flush()
        
        except json.JSONDecodeError as e:
            print(json.dumps({"error": str(e)}))
            sys.stdout.flush()
