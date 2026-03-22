#!/usr/bin/env python3
"""
食物图片识别服务
使用 OpenClaw 集成的 Qwen-VL 视觉模型识别食物并计算营养
"""

import subprocess
import json
import tempfile
import base64
from pathlib import Path

# 食物营养数据库
FOOD_DATABASE = {
    "米饭": {"calories": 130, "protein": 2.7, "fat": 0.3, "carbs": 28},
    "鸡蛋": {"calories": 144, "protein": 13, "fat": 10, "carbs": 1.1},
    "面包": {"calories": 265, "protein": 9, "fat": 3.5, "carbs": 49},
    "牛奶": {"calories": 54, "protein": 3.2, "fat": 3.3, "carbs": 5},
    "苹果": {"calories": 52, "protein": 0.3, "fat": 0.2, "carbs": 14},
    "香蕉": {"calories": 89, "protein": 1.1, "fat": 0.3, "carbs": 23},
    "鸡胸肉": {"calories": 165, "protein": 31, "fat": 3.6, "carbs": 0},
    "牛肉": {"calories": 250, "protein": 26, "fat": 15, "carbs": 0},
    "蔬菜": {"calories": 25, "protein": 2, "fat": 0.3, "carbs": 5},
    "粥": {"calories": 46, "protein": 1.1, "fat": 0.3, "carbs": 10},
    "包子": {"calories": 230, "protein": 8, "fat": 5, "carbs": 40},
    "饺子": {"calories": 200, "protein": 10, "fat": 8, "carbs": 25},
    "面条": {"calories": 110, "protein": 3.5, "fat": 0.5, "carbs": 23},
    "咖啡": {"calories": 2, "protein": 0.3, "fat": 0, "carbs": 0},
}


def recognize_food_from_image(image_path: str) -> dict:
    """
    使用 Qwen-VL 视觉模型识别食物图片
    
    Args:
        image_path: 图片文件路径
    
    Returns:
        dict: {"food_name": str, "calories": float, "protein": float, "fat": float, "carbs": float}
    """
    
    # 将图片转换为 base64
    with open(image_path, "rb") as f:
        image_base64 = base64.b64encode(f.read()).decode("utf-8")
    
    # 构建提示词
    prompt = """请识别这张图片中的食物，并估算营养成分。
返回严格的 JSON 格式，不要有其他文字：
{
    "food_name": "食物名称（中文）",
    "calories": 数字（千卡）,
    "protein": 数字（克）,
    "fat": 数字（克）,
    "carbs": 数字（克）,
    "confidence": "识别置信度（high/medium/low）"
}

如果图片中不是食物或无法识别，返回：
{"error": "无法识别", "message": "原因"}
"""
    
    # 调用 OpenClaw image 工具
    try:
        # 方法 1：使用 openclaw image 命令
        cmd = [
            "openclaw", "image",
            "--image", image_path,
            "--prompt", prompt
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            # 解析返回的 JSON
            output = result.stdout.strip()
            print(f"🔍 视觉模型识别结果：{output[:200]}")
            
            # 尝试提取 JSON
            if "{" in output and "}" in output:
                start = output.index("{")
                end = output.rindex("}") + 1
                json_str = output[start:end]
                
                try:
                    nutrition = json.loads(json_str)
                    print(f"✅ 识别成功：{nutrition.get('food_name', '未知')}")
                    return nutrition
                except json.JSONDecodeError as e:
                    print(f"⚠️ JSON 解析失败：{e}")
        
        # 如果视觉模型失败，回退到数据库匹配
        print("⚠️ 视觉模型识别失败，回退到数据库匹配")
        return {"food_name": "未知食物", "calories": 0, "protein": 0, "fat": 0, "carbs": 0, "note": "视觉识别失败"}
    
    except subprocess.TimeoutExpired:
        print("❌ 视觉模型调用超时")
        return {"food_name": "未知食物", "calories": 0, "protein": 0, "fat": 0, "carbs": 0, "note": "识别超时"}
    
    except Exception as e:
        print(f"❌ 识别异常：{e}")
        return {"food_name": "未知食物", "calories": 0, "protein": 0, "fat": 0, "carbs": 0, "note": str(e)}


def match_food_in_database(food_name: str) -> dict:
    """
    在内置数据库中匹配食物营养
    
    Args:
        food_name: 食物名称
    
    Returns:
        dict: 营养信息
    """
    food_name_lower = food_name.lower()
    
    for name, nutrition in FOOD_DATABASE.items():
        if name in food_name_lower or food_name_lower in name:
            return {
                "name": name,
                "calories": nutrition["calories"],
                "protein": nutrition["protein"],
                "fat": nutrition["fat"],
                "carbs": nutrition["carbs"],
            }
    
    # 未找到匹配
    return {
        "name": food_name,
        "calories": 0,
        "protein": 0,
        "fat": 0,
        "carbs": 0,
        "note": "未在数据库中找到"
    }


if __name__ == "__main__":
    # 测试
    import sys
    
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        result = recognize_food_from_image(image_path)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("用法：python3 food_recognizer.py <图片路径>")
