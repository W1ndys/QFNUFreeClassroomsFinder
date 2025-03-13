import os
import logging
import colorlog
from src.web.app import app
from datetime import datetime


def setup_logger():
    """
    配置日志系统
    """
    # 确保logs目录存在
    if not os.path.exists("logs"):
        os.makedirs("logs")

    # 创建logger
    logger = colorlog.getLogger()
    logger.setLevel(logging.DEBUG)

    # 清除可能存在的处理器
    if logger.handlers:
        logger.handlers.clear()

    # 配置控制台处理器 - 使用ColoredFormatter
    console_handler = colorlog.StreamHandler()
    console_handler.setLevel(logging.INFO)  # 设置控制台处理器的日志级别
    console_formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(levelname)s: %(message)s%(reset)s",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
    )
    console_handler.setFormatter(console_formatter)

    # 配置文件处理器
    log_filename = f"logs/web_app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    file_handler = logging.FileHandler(log_filename, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)

    # 添加处理器到logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    # 记录日志文件位置
    logger.info(f"日志文件保存在: {os.path.abspath(log_filename)}")

    return logger


def print_welcome():
    """
    打印欢迎信息
    """
    logger = logging.getLogger()
    logger.info(f"\n{'*' * 10} 曲阜师范大学教室课表查询系统 - 网页版 {'*' * 10}\n")
    logger.info("By W1ndys")
    logger.info("https://github.com/W1ndys")
    logger.info("\n")
    logger.info("网页服务已启动，请在浏览器中访问以下地址：")
    logger.info("http://127.0.0.1:5000")
    logger.info("\n")
    logger.info("按 Ctrl+C 停止服务")
    logger.info("\n")


if __name__ == "__main__":
    # 设置日志
    logger = setup_logger()

    # 打印欢迎信息
    print_welcome()

    try:
        # 启动Flask应用
        app.run(debug=False, host="0.0.0.0", port=5000)
    except KeyboardInterrupt:
        logger.info("服务已停止")
    except Exception as e:
        logger.error(f"服务发生错误: {str(e)}")
        raise
