#!/usr/bin/env python3
"""
健康系统 - OpenClaw Skill
自动处理飞书群消息（文本 + 图片）
"""

import os
import sys
import json
import requests
from pathlib import Path

# 健康系统 API
HEALTH_API_BASE = "http://localhost:8081"

def handle_message(message_text: str, image_url: str = None, sender_id: str = None):
    """
    处理飞书消息
    
    Args:
        message_text: 消息文本
        image_url: 图片 URL（如果有）
        sender_id: 发送者 ID
    
    Returns:
        str: 回复消息
    """
    
    print(f"📨 收到消息：{message_text[:100]}")
    if image_url:
        print(f"📸 包含图片：{image_url}")
    
    # 1. 如果有图片，下载并调用识别 API
    if image_url:
        try:
            # 下载图片
            import tempfile
            import requests
            
            temp_dir = Path.home() / ".health-system" / "tmp"
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            image_resp = requests.get(image_url, timeout=30)
            if image_resp.status_code == 200:
                # 保存图片
                import time
                filename = f"{int(time.time())}_{sender_id}.jpg"
                image_path = temp_dir / filename
                
                with open(image_path, "wb") as f:
                    f.write(image_resp.content)
                
                print(f"✅ 图片已保存：{image_path}")
                
                # 调用健康系统识别 API
                with open(image_path, "rb") as f:
                    files = {"image": f}
                    api_resp = requests.post(
                        f"{HEALTH_API_BASE}/api/food/image",
                        files=files,
                        timeout=60
                    )
                
                if api_resp.status_code == 200:
                    result = api_resp.json()
                    print(f"✅ 识别成功：{result.get('food_name')} - {result.get('calories')} kcal")
                    
                    # 返回识别结果
                    return (
                        f"✅ 食物识别完成\n"
                        f"🍽️ {result.get('food_name', '未知')}\n"
                        f"🔥 {result.get('calories', 0)} kcal\n"
                        f"💪 蛋白质：{result.get('protein', 0)}g\n"
                        f"🥑 脂肪：{result.get('fat', 0)}g\n"
                        f"🍞 碳水：{result.get('carbs', 0)}g\n"
                        f"\n"
                        f"📊 详情查看：http://localhost:8081/shou"
                    )
                else:
                    print(f"❌ API 调用失败：{api_resp.text}")
                    return f"❌ 识别失败：{api_resp.text}"
            
            # 清理临时文件
            try:
                image_path.unlink()
            except:
                pass
        
        except Exception as e:
            print(f"❌ 图片处理异常：{e}")
            return f"❌ 图片识别失败：{str(e)}"
    
    # 2. 纯文本消息处理
    if message_text:
        text = message_text.lower()
        
        # 体重记录
        if "体重" in text or "weight" in text:
            import re
            numbers = re.findall(r'\d+\.?\d*', message_text)
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
                    return f"⚖️ 体重：{weight} kg{change_str}"
        
        # 食物记录（文本）
        elif "吃" in text or "饭" in text:
            food_name = message_text.replace("吃", "").replace("了", "").replace("饭", "").strip()
            if food_name:
                resp = requests.post(
                    f"{HEALTH_API_BASE}/api/food",
                    json={"food_name": food_name},
                    timeout=10
                )
                if resp.status_code == 200:
                    result = resp.json()
                    return f"✅ 已记录：{result.get('food_name')} ({result.get('calories', 0)} kcal)"
        
        # 查询汇总
        elif "汇总" in text or "总结" in text or "summary" in text:
            resp = requests.get(f"{HEALTH_API_BASE}/api/summary", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return (
                    f"📊 今日汇总 ({data.get('date', '')})\n"
                    f"\n"
                    f"🔥 热量：{data.get('calories', 0)}/{data.get('calorie_target', 2000)} kcal\n"
                    f"剩余：{data.get('calorie_remaining', 0)} kcal\n"
                    f"\n"
                    f"💪 蛋白质：{data.get('protein', 0)}g\n"
                    f"🥑 脂肪：{data.get('fat', 0)}g\n"
                    f"🍞 碳水：{data.get('carbs', 0)}g\n"
                    f"\n"
                    f"🍽️ 餐数：{data.get('meal_count', 0)}"
                )
        
        # 帮助
        elif "帮助" in text or "help" in text or "?" in text:
            return (
                "🤖 健康管理系统 - 使用指南\n"
                f"\n"
                f"📸 记录食物：直接发送食物照片\n"
                f"🍽️ 文本记录：发送'吃了 XXX'\n"
                f"⚖️ 记录体重：发送'体重 XX kg'\n"
                f"📊 查看汇总：发送'汇总'\n"
                f"\n"
                f"🌐 Web 界面：http://localhost:8081/shou"
            )
    
    return None  # 未识别的消息


# OpenClaw Skill 入口
async def handle_inbound_message(message):
    """
    OpenClaw 消息处理入口
    
    Args:
        message: OpenClaw 消息对象
    
    Returns:
        str: 回复消息
    """
    try:
        # 提取消息内容
        text = message.get("text", "")
        image_url = message.get("image_url") or message.get("media_url")
        sender_id = message.get("sender_id") or message.get("user_id")
        channel = message.get("channel", "feishu")
        
        print(f"\n{'='*50}")
        print(f"📨 OpenClaw 收到消息")
        print(f"渠道：{channel}")
        print(f"发送者：{sender_id}")
        print(f"文本：{text[:100]}")
        print(f"图片：{image_url}")
        print(f"{'='*50}\n")
        
        # 处理消息
        response = handle_message(text, image_url, sender_id)
        
        if response:
            print(f"💬 回复：{response[:200]}")
            return response
        
        return None
    
    except Exception as e:
        print(f"❌ 消息处理异常：{e}")
        return f"❌ 处理失败：{str(e)}"


# 测试
if __name__ == "__main__":
    # 测试文本消息
    print("测试文本消息处理...")
    result = handle_message("吃了苹果")
    print(f"结果：{result}\n")
    
    # 测试体重
    print("测试体重记录...")
    result = handle_message("体重 65.5")
    print(f"结果：{result}\n")
    
    # 测试汇总
    print("测试查询汇总...")
    result = handle_message("汇总")
    print(f"结果：{result[:200]}\n")
