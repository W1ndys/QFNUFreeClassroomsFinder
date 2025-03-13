#!/bin/bash

echo "======================================"
echo " 曲阜师范大学教室课表查询系统 - 网页版"
echo " By W1ndys"
echo " https://github.com/W1ndys"
echo "======================================"
echo ""

# PID文件路径
PID_FILE=".web_app.pid"

# 清理旧日志文件，只保留最近的10个
clean_old_logs() {
    if [ -d "logs" ]; then
        cd logs
        # 保留最新的10个日志文件
        ls -t web_app_*.log | tail -n +11 | xargs -I {} rm -f {}
        cd ..
    fi
}

# 检查是否有旧进程在运行
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo "发现旧进程(PID: $OLD_PID)正在运行，正在终止..."
        kill $OLD_PID
        sleep 2
    fi
    rm -f "$PID_FILE"
fi

# 清理旧日志
echo "正在清理旧日志文件..."
clean_old_logs

# 检查venv目录是否存在
if [ ! -d "venv" ]; then
    echo "虚拟环境不存在，请先运行 create_venv_linux.sh 创建虚拟环境"
    exit 1
fi

# 激活虚拟环境
echo "正在激活虚拟环境..."
source venv/bin/activate

# 检查是否成功激活
if [ $? -ne 0 ]; then
    echo "激活虚拟环境失败，请检查venv目录是否正确"
    exit 1
fi

echo "虚拟环境已激活"
echo ""

# 运行网页应用
echo "正在启动网页服务..."
nohup python3 run_web.py > /dev/null 2>&1 &
APP_PID=$!

# 保存PID到文件
echo $APP_PID > "$PID_FILE"
echo "程序已启动，PID: $APP_PID"
echo "日志文件将保存在 logs 目录中"
echo "使用以下命令可以查看日志："
echo "tail -f logs/web_app_*.log"
echo ""
echo "要停止服务，请运行："
echo "kill \$(cat $PID_FILE)"

# 退出虚拟环境
deactivate

exit 0 