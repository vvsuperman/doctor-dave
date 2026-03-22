#!/usr/bin/env python3
"""
健康管理系统 v3.0 - 数据库模块
SQLite 本地存储
"""

import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path.home() / ".health-system" / "data" / "health.db"

def get_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初始化数据库"""
    # 确保目录存在
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = get_connection()
    c = conn.cursor()
    
    # 用户表
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            height_cm REAL,
            gender TEXT,
            age INTEGER,
            current_weight_kg REAL,
            target_weight_kg REAL,
            goal_type TEXT DEFAULT '维持',
            activity_level TEXT DEFAULT '中等',
            calorie_target INTEGER DEFAULT 2000,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 插入默认用户
    c.execute('SELECT COUNT(*) FROM users')
    if c.fetchone()[0] == 0:
        c.execute('''
            INSERT INTO users (id, name, calorie_target) VALUES (1, '默认用户', 2000)
        ''')
    
    # 食物记录表
    c.execute('''
        CREATE TABLE IF NOT EXISTS food_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1,
            food_name TEXT NOT NULL,
            calories REAL DEFAULT 0,
            protein REAL DEFAULT 0,
            fat REAL DEFAULT 0,
            carbs REAL DEFAULT 0,
            serving_size TEXT DEFAULT '100g',
            meal_type TEXT,
            image_path TEXT,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # 体重记录表
    c.execute('''
        CREATE TABLE IF NOT EXISTS weight_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1,
            weight_kg REAL NOT NULL,
            body_fat_pct REAL,
            note TEXT,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # 提醒配置表
    c.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1,
            reminder_type TEXT NOT NULL,
            time TEXT NOT NULL,
            enabled BOOLEAN DEFAULT 1,
            message TEXT,
            last_sent DATE,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # 渠道配置表
    c.execute('''
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1,
            channel_type TEXT NOT NULL,
            channel_id TEXT NOT NULL,
            webhook_url TEXT,
            enabled BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(channel_type, channel_id)
        )
    ''')
    
    # 插入默认提醒
    default_reminders = [
        ('breakfast', '07:00', '☀️ 早上好！该吃早餐啦～记得要吃得像皇帝一样丰富！🍳🥛'),
        ('lunch', '11:30', '🍚 午餐时间到！营养均衡，下午才有精力！🥗🍗'),
        ('dinner', '17:00', '🌆 晚餐时间！别饿着自己，但也别吃太撑哦～🍜'),
        ('scold', '20:00', '⚠️ 这么晚了还吃？你是想变成猪吗？🐷（开玩笑的，但要少吃点哦）'),
        ('weight', '21:00', '⚖️ 该记录体重啦！每天同一时间测量最准确～📊'),
    ]
    
    c.execute('SELECT COUNT(*) FROM reminders')
    if c.fetchone()[0] == 0:
        for r_type, r_time, r_msg in default_reminders:
            c.execute('''
                INSERT INTO reminders (reminder_type, time, message) VALUES (?, ?, ?)
            ''', (r_type, r_time, r_msg))
    
    # 检查是否需要添加新字段（数据库升级）
    try:
        c.execute("ALTER TABLE users ADD COLUMN current_weight_kg REAL")
        print("✅ 添加 current_weight_kg 字段")
    except sqlite3.OperationalError:
        pass  # 字段已存在
    
    try:
        c.execute("ALTER TABLE users ADD COLUMN target_weight_kg REAL")
        print("✅ 添加 target_weight_kg 字段")
    except sqlite3.OperationalError:
        pass  # 字段已存在
    
    try:
        c.execute("ALTER TABLE users ADD COLUMN goal_type TEXT DEFAULT '维持'")
        print("✅ 添加 goal_type 字段")
    except sqlite3.OperationalError:
        pass  # 字段已存在
    
    try:
        c.execute("ALTER TABLE users ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        print("✅ 添加 updated_at 字段")
    except sqlite3.OperationalError:
        pass  # 字段已存在
    
    conn.commit()
    conn.close()
    print(f"✅ 数据库初始化完成：{DB_PATH}")

if __name__ == "__main__":
    init_db()
