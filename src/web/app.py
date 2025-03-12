import os
import json
import base64
from io import BytesIO
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from PIL import Image
import logging
import datetime
import time

from src.utils.session_manager import get_session, reset_session
from src.utils.captcha_ocr import get_ocr_res
from src.core.get_room_classtable import get_room_classtable

# 创建Flask应用
app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "templates"),
    static_folder=os.path.join(os.path.dirname(__file__), "static"),
)
CORS(app)  # 启用CORS
app.secret_key = os.urandom(24)  # 设置密钥用于session

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 验证码URL
CAPTCHA_URL = "http://zhjw.qfnu.edu.cn/jsxsd/verifycode.servlet"
# 登录URL
LOGIN_URL = "http://zhjw.qfnu.edu.cn/jsxsd/xk/LoginToXkLdap"


@app.route("/")
def index():
    """首页路由"""
    return render_template("index.html")


@app.route("/get_captcha", methods=["GET"])
def get_captcha():
    """获取验证码图片"""
    try:
        # 获取会话
        req_session = get_session()

        # 请求验证码
        response = req_session.get(CAPTCHA_URL)

        if response.status_code != 200:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"请求验证码失败，状态码: {response.status_code}",
                    }
                ),
                500,
            )

        # 将验证码图片转为base64编码
        image = Image.open(BytesIO(response.content))
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        # 如果请求中包含auto_ocr参数且为true，则自动识别验证码
        auto_ocr = request.args.get("auto_ocr", "false").lower() == "true"
        ocr_result = None
        if auto_ocr:
            ocr_result = get_ocr_res(image)

        return jsonify(
            {
                "status": "success",
                "captcha_image": f"data:image/png;base64,{img_str}",
                "ocr_result": ocr_result,
            }
        )

    except Exception as e:
        logger.error(f"获取验证码出错: {str(e)}")
        return jsonify({"status": "error", "message": f"获取验证码出错: {str(e)}"}), 500


@app.route("/login", methods=["POST"])
def login():
    """处理登录请求"""
    try:
        data = request.json
        username = data.get("username")
        password = data.get("password")
        captcha = data.get("captcha")

        if not all([username, password, captcha]):
            return (
                jsonify({"status": "error", "message": "用户名、密码和验证码不能为空"}),
                400,
            )

        # 生成登录所需的encoded字符串
        account_b64 = base64.b64encode(username.encode()).decode()
        password_b64 = base64.b64encode(password.encode()).decode()
        encoded = f"{account_b64}%%%{password_b64}"

        # 获取会话
        req_session = get_session()

        # 发送登录请求
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36",
            "Origin": "http://zhjw.qfnu.edu.cn",
            "Referer": "http://zhjw.qfnu.edu.cn/",
        }

        login_data = {
            "userAccount": "",
            "userPassword": "",
            "RANDOMCODE": captcha,
            "encoded": encoded,
        }

        response = req_session.post(
            LOGIN_URL, headers=headers, data=login_data, timeout=10
        )

        if response.status_code != 200:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"登录请求失败，状态码: {response.status_code}",
                    }
                ),
                500,
            )

        # 检查登录结果
        if "验证码错误" in response.text:
            return jsonify({"status": "error", "message": "验证码错误"}), 400

        if "密码错误" in response.text or "账号或密码错误" in response.text:
            return jsonify({"status": "error", "message": "用户名或密码错误"}), 400

        # 检查是否成功登录
        main_page = req_session.get(
            "http://zhjw.qfnu.edu.cn/jsxsd/framework/xsMain.jsp"
        )
        if main_page.status_code != 200:
            return (
                jsonify({"status": "error", "message": "登录失败，无法访问主页"}),
                500,
            )

        # 登录成功，在session中标记已登录
        session["logged_in"] = True

        return jsonify({"status": "success", "message": "登录成功"})

    except Exception as e:
        logger.error(f"登录出错: {str(e)}")
        return jsonify({"status": "error", "message": f"登录出错: {str(e)}"}), 500


@app.route("/logout", methods=["POST"])
def logout():
    """处理登出请求"""
    try:
        # 重置会话
        reset_session()

        # 清除Flask session
        session.clear()

        return jsonify({"status": "success", "message": "已成功登出"})

    except Exception as e:
        logger.error(f"登出出错: {str(e)}")
        return jsonify({"status": "error", "message": f"登出出错: {str(e)}"}), 500


@app.route("/query_classtable", methods=["POST"])
def query_classtable():
    """查询教室课表"""
    try:
        # 检查是否已登录
        if not session.get("logged_in"):
            return jsonify({"status": "error", "message": "未登录，请先登录"}), 401

        data = request.json
        xnxqh = data.get("xnxqh")  # 学年学期
        room_name = data.get("room_name")  # 教室名称
        week = data.get("week")  # 周次
        day = data.get("day")  # 星期几

        if not all([xnxqh, room_name, week]):
            return (
                jsonify(
                    {"status": "error", "message": "学年学期、教室名称和周次不能为空"}
                ),
                400,
            )

        # 转换为整数
        try:
            week = int(week)
            if day:
                day = int(day)
        except ValueError:
            return (
                jsonify({"status": "error", "message": "周次和星期几必须是数字"}),
                400,
            )

        # 查询课表
        result = get_room_classtable(xnxqh, room_name, week, day)

        return jsonify(result)

    except Exception as e:
        logger.error(f"查询课表出错: {str(e)}")
        return jsonify({"status": "error", "message": f"查询课表出错: {str(e)}"}), 500


@app.route("/get_current_term", methods=["GET"])
def get_current_term():
    """获取当前学期信息"""
    # 这里可以根据当前日期计算当前学期，或者从教务系统获取
    # 简单示例：根据当前月份判断学期
    now = datetime.datetime.now()
    year = now.year
    month = now.month

    # 简单判断学期
    if 2 <= month <= 7:  # 2-7月为第二学期
        term = f"{year-1}-{year}-2"
    else:  # 8-1月为第一学期
        if month >= 8:
            term = f"{year}-{year+1}-1"
        else:
            term = f"{year-1}-{year}-1"

    return jsonify({"status": "success", "current_term": term})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
