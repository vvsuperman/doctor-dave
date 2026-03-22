#!/usr/bin/env python3
"""
健康系统 - 飞书消息自动处理
作为 OpenClaw 的外部脚本运行，监听并处理消息
"""

import sys
import json
import requests
from pathlib import Path

HEALTH_API_BASE = "http://localhost:8081"

def process_message(text: str, image_url: str = None):
    """处理消息并返回回复"""
    
    # 1. 图片消息 - 调用识别 API
    if image_url:
        try:
            # 下载图片
            temp_dir = Path.home() / ".health-system" / "tmp"
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            import time
            resp = requests.get(image_url, timeout=30)
            if resp.status_code == 200:
                filename = f"{int(time.time())}_feishu.jpg"
                image_path = temp_dir / filename
                
                with open(image_path, "wb") as f:
                    f.write(resp.content)
                
                # 调用识别 API
                with open(image_path, "rb") as f:
                    api_resp = requests.post(
                        f"{HEALTH_API_BASE}/api/food/image",
                        files={"image": f},
                        timeout=60
                    )
                
                if api_resp.status_code == 200:
                    result = api_resp.json()
                    
                    # 清理临时文件
                    try:
                        image_path.unlink()
                    except:
                        pass
                    
                    return {
                        "reply": (
                            f"✅ 食物识别完成\n"
                            f"🍽️ {result.get('food_name', '未知')}\n"
                            f"🔥 {result.get('calories', 0)} kcal\n"
                            f"💪 蛋白质：{result.get('protein', 0)}g\n"
                            f"🥑 脂肪：{result.get('fat', 0)}g\n"
                            f"🍞 碳水：{result.get('carbs', 0)}g"
                        ),
                        "success": True
                    }
            
            return {"reply": "❌ 图片下载失败", "success": False}
        
        except Exception as e:
            return {"reply": f"❌ 识别失败：{str(e)}", "success": False}
    
    # 2. 文本消息处理
    if text:
        text_lower = text.lower()
        
        # 体重
        if "体重" in text_lower or "weight" in text_lower:
            import re
            numbers = re.findall(r'\d+\.?\d*', text)
            if numbers:
                weight = float(numbers[0])
                resp = requests.post(
                    f"{HEALTH_API_BASE}/api/weight",
                    json={"weight_kg": weight},
                    timeout=10
                )
                if resp.status_code == 200:
                    result = resp.json()
                    change_str = ""
                    if result.get("change"):
                        change = result["change"]
                        change_str = f" ({'+' if change > 0 else ''}{change}kg)"
                    return {"reply": f"⚖️ 体重：{weight} kg{change_str}", "success": True}
        
        # 食物（文本）
        elif "吃" in text_lower or "饭" in text_lower:
            food_name = text.replace("吃", "").replace("了", "").replace("饭", "").strip()
            if food_name:
                resp = requests.post(
                    f"{HEALTH_API_BASE}/api/food",
                    json={"food_name": food_name},
                    timeout=10
                )
                if resp.status_code == 200:
                    result = resp.json()
                    return {"reply": f"✅ 已记录：{result.get('food_name')} ({result.get('calories', 0)} kcal)", "success": True}
        
        # 汇总
        elif "汇总" in text_lower or "总结" in text_lower:
            resp = requests.get(f"{HEALTH_API_BASE}/api/summary", timeout=10)
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
                    ),
                    "success": True
                }
        
        # 帮助
        elif "帮助" in text_lower or "help" in text_lower:
            return {
                "reply": (
                    "🤖 健康管理系统\n"
                    f"\n"
                    f"📸 发送食物照片 → 自动识别\n"
                    f"🍽️ 发送'吃了 XXX' → 文本记录\n"
                    f"⚖️ 发送'体重 XX' → 记录体重\n"
                    f"📊 发送'汇总' → 查看今日数据\n"
                    f"\n"
                    f"🌐 Web: http://localhost:8081/shou"
                ),
                "success": True
            }
    
    return {"reply": None, "success": False}


if __name__ == "__main__":
    # 从 stdin 读取消息（JSON 格式）
    for line in sys.stdin:
        try:
            message = json.loads(line.strip())
            text = message.get("text", "")
            image_url = message.get("image_url")
            
            result = process_message(text, image_url)
            
            # 输出回复（JSON 格式）
            print(json.dumps(result, ensure_ascii=False))
            sys.stdout.flush()
        
        except json.JSONDecodeError as e:
            print(json.dumps({"error": str(e), "success": False}))
            sys.stdout.flush()
