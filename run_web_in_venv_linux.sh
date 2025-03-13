#!/bin/bash

echo "======================================"
echo " 曲阜师范大学教室课表查询系统 - 网页版"
echo " By W1ndys"
echo " https://github.com/W1ndys"
echo "======================================"
echo ""

# PID文件路径
PID_FILE=".web_app.pid"

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
python3 run_web.py &
APP_PID=$!

# 保存PID到文件
echo $APP_PID > "$PID_FILE"
echo "程序已启动，PID: $APP_PID"

# 等待程序运行
wait $APP_PID

# 如果程序异常退出
if [ $? -ne 0 ]; then
    echo ""
    echo "程序异常退出，错误代码: $?"
    read -p "按回车键继续..."
fi

# 清理PID文件
rm -f "$PID_FILE"

# 退出虚拟环境
deactivate 