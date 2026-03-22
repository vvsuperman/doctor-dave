#!/usr/bin/env python3
"""
健康管理系统 - MCP 服务
提供 AI 工具调用接口，支持自然语言交互

用法：
    python3 mcp_server.py
"""

import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional

# 数据库路径
DB_PATH = Path.home() / ".health-system" / "data" / "health.db"

# 食物数据库
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


def get_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def recognize_food(food_name: str) -> dict:
    """识别食物营养信息"""
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
    
    return {
        "name": food_name,
        "calories": 0,
        "protein": 0,
        "fat": 0,
        "carbs": 0,
        "note": "未在数据库中找到"
    }


def get_summary(user_id: int = 1) -> dict:
    """获取今日汇总"""
    conn = get_connection()
    c = conn.cursor()
    
    today = datetime.now().strftime("%Y-%m-%d")
    
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
    
    c.execute("""
        SELECT weight_kg FROM weight_records 
        WHERE user_id = ? AND date(recorded_at) = ?
        ORDER BY recorded_at DESC LIMIT 1
    """, (user_id, today))
    weight_row = c.fetchone()
    
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


def add_food(food_name: str, calories: Optional[float] = None, 
             protein: Optional[float] = 0, fat: Optional[float] = 0, 
             carbs: Optional[float] = 0, meal_type: Optional[str] = None,
             user_id: int = 1) -> dict:
    """添加食物记录"""
    # 如果没有提供热量，自动识别
    if calories is None or calories == 0:
        nutrition = recognize_food(food_name)
        calories = nutrition["calories"]
        protein = nutrition["protein"]
        fat = nutrition["fat"]
        carbs = nutrition["carbs"]
    
    conn = get_connection()
    c = conn.cursor()
    
    c.execute("""
        INSERT INTO food_records (user_id, food_name, calories, protein, fat, carbs, meal_type)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, food_name, calories, protein, fat, carbs, meal_type))
    
    conn.commit()
    record_id = c.lastrowid
    conn.close()
    
    return {
        "id": record_id,
        "food_name": food_name,
        "calories": calories,
        "message": f"✅ 已记录：{food_name} ({calories} kcal)"
    }


def add_weight(weight_kg: float, body_fat_pct: Optional[float] = None,
               note: Optional[str] = None, user_id: int = 1) -> dict:
    """添加体重记录"""
    conn = get_connection()
    c = conn.cursor()
    
    # 获取上次体重
    c.execute("""
        SELECT weight_kg FROM weight_records 
        WHERE user_id = ? ORDER BY recorded_at DESC LIMIT 1
    """, (user_id,))
    prev = c.fetchone()
    
    c.execute("""
        INSERT INTO weight_records (user_id, weight_kg, body_fat_pct, note)
        VALUES (?, ?, ?, ?)
    """, (user_id, weight_kg, body_fat_pct, note))
    
    conn.commit()
    record_id = c.lastrowid
    
    change = None
    if prev:
        change = round(weight_kg - prev["weight_kg"], 1)
    
    conn.close()
    
    change_str = ""
    if change is not None:
        change_str = f" ({'+' if change > 0 else ''}{change} kg)"
    
    return {
        "id": record_id,
        "weight_kg": weight_kg,
        "change": change,
        "message": f"⚖️ 体重：{weight_kg} kg{change_str}"
    }


def get_food_records(days: int = 7, user_id: int = 1) -> dict:
    """获取食物记录"""
    conn = get_connection()
    c = conn.cursor()
    
    c.execute("""
        SELECT * FROM food_records 
        WHERE user_id = ? 
        ORDER BY recorded_at DESC 
        LIMIT ?
    """, (user_id, days * 10))
    
    records = [dict(row) for row in c.fetchall()]
    conn.close()
    
    return {"records": records, "count": len(records)}


def get_weight_records(days: int = 30, user_id: int = 1) -> dict:
    """获取体重记录"""
    conn = get_connection()
    c = conn.cursor()
    
    c.execute("""
        SELECT * FROM weight_records 
        WHERE user_id = ? 
        ORDER BY recorded_at DESC 
        LIMIT ?
    """, (user_id, days))
    
    records = [dict(row) for row in c.fetchall()]
    conn.close()
    
    return {"records": records, "count": len(records)}


# ==================== MCP 工具定义 ====================

TOOLS = [
    {
        "name": "health_add_food",
        "description": "记录食物摄入，自动计算热量和营养成分。如果不提供热量，会从内置数据库自动匹配。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "food_name": {
                    "type": "string",
                    "description": "食物名称，例如：苹果、米饭、鸡胸肉"
                },
                "calories": {
                    "type": "number",
                    "description": "热量（千卡），可选，不提供则自动估算"
                },
                "protein": {
                    "type": "number",
                    "description": "蛋白质（克），可选"
                },
                "fat": {
                    "type": "number",
                    "description": "脂肪（克），可选"
                },
                "carbs": {
                    "type": "number",
                    "description": "碳水化合物（克），可选"
                },
                "meal_type": {
                    "type": "string",
                    "description": "餐次",
                    "enum": ["breakfast", "lunch", "dinner", "snack"]
                }
            },
            "required": ["food_name"]
        }
    },
    {
        "name": "health_add_weight",
        "description": "记录体重数据，自动计算与上次体重的变化。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "weight_kg": {
                    "type": "number",
                    "description": "体重（公斤）"
                },
                "body_fat_pct": {
                    "type": "number",
                    "description": "体脂率（百分比），可选"
                },
                "note": {
                    "type": "string",
                    "description": "备注，例如：晨起空腹、饭后"
                }
            },
            "required": ["weight_kg"]
        }
    },
    {
        "name": "health_get_summary",
        "description": "获取今日健康汇总，包括热量摄入、营养成分、体重等数据。",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False
        }
    },
    {
        "name": "health_get_food_records",
        "description": "获取历史食物记录列表。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "获取最近多少天的记录",
                    "default": 7
                }
            }
        }
    },
    {
        "name": "health_get_weight_records",
        "description": "获取历史体重记录列表。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "获取最近多少天的记录",
                    "default": 30
                }
            }
        }
    },
]


def handle_tool_call(tool_name: str, arguments: dict) -> dict:
    """处理工具调用"""
    try:
        if tool_name == "health_add_food":
            return add_food(**arguments)
        
        elif tool_name == "health_add_weight":
            return add_weight(**arguments)
        
        elif tool_name == "health_get_summary":
            return get_summary()
        
        elif tool_name == "health_get_food_records":
            return get_food_records(**arguments)
        
        elif tool_name == "health_get_weight_records":
            return get_weight_records(**arguments)
        
        else:
            return {"error": f"未知工具：{tool_name}"}
    
    except Exception as e:
        return {"error": str(e)}


# ==================== 主程序 ====================

if __name__ == "__main__":
    # 简单模式：从 stdin 读取 JSON-RPC 请求
    print("🔧 健康管理系统 MCP 服务", file=sys.stderr)
    print(f"📊 数据库：{DB_PATH}", file=sys.stderr)
    print("等待请求...\n", file=sys.stderr)
    
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            
            # JSON-RPC 2.0 处理
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")
            
            if method == "initialize":
                # 初始化响应
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "serverInfo": {
                            "name": "health-system",
                            "version": "3.0.0"
                        },
                        "capabilities": {
                            "tools": {}
                        }
                    }
                }
            
            elif method == "tools/list":
                # 返回工具列表
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": TOOLS
                    }
                }
            
            elif method == "tools/call":
                # 调用工具
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                result = handle_tool_call(tool_name, arguments)
                
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, ensure_ascii=False, indent=2)
                            }
                        ]
                    }
                }
            
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"未知方法：{method}"
                    }
                }
            
            # 输出响应
            print(json.dumps(response, ensure_ascii=False))
            sys.stdout.flush()
        
        except json.JSONDecodeError as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": f"JSON 解析错误：{str(e)}"
                }
            }
            print(json.dumps(error_response))
            sys.stdout.flush()
        
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": f"内部错误：{str(e)}"
                }
            }
            print(json.dumps(error_response))
            sys.stdout.flush()
