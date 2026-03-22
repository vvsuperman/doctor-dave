#!/bin/bash
# 健康管理系统 v3.0 - 安装脚本

set -e

HEALTH_DIR="$HOME/.health-system"
SERVICE_NAME="health-system"
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🚀 安装健康管理系统 v3.0..."
echo ""

# 1. 创建目录
echo "📁 创建目录..."
mkdir -p $HEALTH_DIR/{data,logs,backup}

# 2. 复制文件
echo "📦 复制文件..."
cp -r $PROJECT_DIR/server/* $HEALTH_DIR/
cp -r $PROJECT_DIR/web $HEALTH_DIR/

# 3. 创建默认配置
echo "⚙️ 创建配置..."
cat > $HEALTH_DIR/config.json << EOF
{
  "feishu": {
    "enabled": true,
    "webhook_url": "",
    "group_id": ""
  },
  "server": {
    "host": "0.0.0.0",
    "port": 8765
  }
}
EOF

# 4. 安装 Python 依赖
echo "📦 安装依赖..."
pip3 install --user fastapi uvicorn pydantic requests -q

# 5. 初始化数据库
echo "🗄️ 初始化数据库..."
cd $HEALTH_DIR
python3 -c "from database import init_db; init_db()"

# 6. 创建 systemd 服务
echo "🔧 配置服务..."
cat > /tmp/health-system.service << EOF
[Unit]
Description=Health Management System v3.0
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$HEALTH_DIR
ExecStart=$(which python3) main.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

sudo mv /tmp/health-system.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME

# 7. 显示配置向导
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 安装完成！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📝 配置飞书 Webhook（可选）:"
echo "   编辑：$HEALTH_DIR/config.json"
echo "   添加 webhook_url 和 group_id"
echo ""
echo "🚀 启动服务:"
echo "   sudo systemctl start $SERVICE_NAME"
echo ""
echo "📊 访问地址:"
echo "   Web 界面：http://$(hostname -I 2>/dev/null | awk '{print $1}' || echo 'localhost'):8765/web"
echo "   API 文档：http://$(hostname -I 2>/dev/null | awk '{print $1}' || echo 'localhost'):8765/docs"
echo ""
echo "📖 管理命令:"
echo "   sudo systemctl status $SERVICE_NAME   # 查看状态"
echo "   sudo systemctl restart $SERVICE_NAME  # 重启"
echo "   sudo journalctl -u $SERVICE_NAME -f   # 查看日志"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
