import os
import json
import base64
from io import BytesIO
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from PIL import Image
import logging
from datetime import datetime
import time

from src.utils.session_manager import get_session, reset_session
from src.utils.captcha_ocr import get_ocr_res
from src.core.get_room_classtable import get_room_classtable

# 创建Flask应用
app = Flask(
    __name__,
    template_folder=os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "src/web/templates"
    ),
    static_folder=os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "src/web/static"
    ),
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

# 开学日期配置
SEMESTER_START_DATES = {
    "2023-2024-1": "2023-09-04",  # 2023-2024学年第一学期开学日期
    "2023-2024-2": "2024-02-26",  # 2023-2024学年第二学期开学日期
    "2024-2025-1": "2024-09-02",  # 2024-2025学年第一学期开学日期
    "2024-2025-2": "2025-02-17",  # 2024-2025学年第二学期开学日期
}


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
        username = data.get("username") if data else None
        password = data.get("password") if data else None
        captcha = data.get("captcha") if data else None

        if not all([username, password, captcha]):
            return (
                jsonify({"status": "error", "message": "用户名、密码和验证码不能为空"}),
                400,
            )

        # 生成登录所需的encoded字符串
        if username is not None and password is not None:
            account_b64 = base64.b64encode(username.encode()).decode()
            password_b64 = base64.b64encode(password.encode()).decode()
            encoded = f"{account_b64}%%%{password_b64}"
        else:
            return jsonify({"status": "error", "message": "用户名或密码不能为空"}), 400

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
        xnxqh = data.get("xnxqh") if data else None  # 学年学期
        room_name = data.get("room_name") if data else None  # 教室名称
        week = data.get("week") if data else None  # 周次
        day = data.get("day") if data else None  # 星期几
        jc1 = data.get("jc1") if data else None  # 开始节次，默认为空
        jc2 = data.get("jc2") if data else None  # 结束节次，默认为空

        if not all([xnxqh, room_name, week]):
            return (
                jsonify(
                    {"status": "error", "message": "学年学期、教室名称和周次不能为空"}
                ),
                400,
            )

        # 转换为整数
        try:
            week = int(week) if week is not None else None
            if day is not None:
                day = int(day)
        except ValueError:
            return (
                jsonify({"status": "error", "message": "周次和星期几必须是数字"}),
                400,
            )

        # 查询课表
        result = get_room_classtable(xnxqh, room_name, week, day, jc1, jc2)
        logger.info(f"查询课表结果: {result}")
        return jsonify(result)

    except Exception as e:
        logger.error(f"查询课表出错: {str(e)}")
        return jsonify({"status": "error", "message": f"查询课表出错: {str(e)}"}), 500


@app.route("/get_current_term", methods=["GET"])
def get_current_term():
    """获取当前学期"""
    try:
        now = datetime.now()
        year = now.year
        month = now.month

        if month >= 9:
            start_year = year
            end_year = year + 1
            term = 1
        elif month <= 1:
            start_year = year - 1
            end_year = year
            term = 1
        else:
            start_year = year - 1
            end_year = year
            term = 2

        current_term = f"{start_year}-{end_year}-{term}"
        return jsonify({"status": "success", "current_term": current_term})

    except Exception as e:
        logger.error(f"获取当前学期出错: {str(e)}")
        return jsonify({"status": "error", "message": str(e)})


@app.route("/get_current_week_day", methods=["GET"])
def get_current_week_day():
    """获取当前周次和星期"""
    try:
        term = request.args.get("term")
        if not term:
            return jsonify({"status": "error", "message": "缺少学期参数"})

        # 获取学期开始日期
        start_date = SEMESTER_START_DATES.get(term)
        if not start_date:
            return jsonify({"status": "error", "message": "未找到该学期的开始日期"})

        # 计算当前是第几周和星期几
        today = datetime.now().date()
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()

        # 计算相差的天数
        days_diff = (today - start_date_obj).days

        # 如果是2024-2025-2学期，并且当前日期早于开学日期，则模拟为第1周
        if term == "2024-2025-2" and days_diff < 0:
            current_week = 1
            # 使用当前星期几
            current_day = today.weekday() + 1  # weekday()返回0-6，对应周一到周日
        else:
            # 计算当前是第几周（从1开始）
            current_week = days_diff // 7 + 1

            # 如果超过20周，则限制为20周
            if current_week > 20:
                current_week = 20
            elif current_week < 1:
                current_week = 1

            # 计算当前是星期几（1-7，对应周一到周日）
            current_day = today.weekday() + 1  # weekday()返回0-6，对应周一到周日

        return jsonify(
            {
                "status": "success",
                "current_week": current_week,
                "current_day": current_day,
                "term": term,
            }
        )
    except Exception as e:
        logger.error(f"获取当前周次和星期出错: {str(e)}")
        return jsonify({"status": "error", "message": str(e)})


@app.route("/api/announcements", methods=["GET"])
def get_announcements():
    """获取广告/宣传内容"""
    try:
        # 这里可以从数据库或配置文件中获取最新的广告/宣传内容
        # 为了简单起见，这里直接返回一个示例内容

        # 检查是否有广告配置文件
        announcements_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "src/web/announcements.json",
        )

        if os.path.exists(announcements_file):
            try:
                with open(announcements_file, "r", encoding="utf-8") as f:
                    announcements_data = json.load(f)
            except Exception as e:
                logger.error(f"读取广告配置文件出错: {str(e)}")
                announcements_data = get_default_announcements()
        else:
            announcements_data = get_default_announcements()

        return jsonify({"status": "success", "data": announcements_data})

    except Exception as e:
        logger.error(f"获取广告/宣传内容出错: {str(e)}")
        return (
            jsonify({"status": "error", "message": f"获取广告/宣传内容出错: {str(e)}"}),
            500,
        )


@app.route("/api/classrooms", methods=["GET"])
def get_classrooms():
    """获取所有教室列表"""
    try:
        # 读取教室配置文件
        classrooms_file = os.path.join(os.path.dirname(__file__), "classrooms.json")

        if not os.path.exists(classrooms_file):
            return jsonify({"status": "error", "message": "教室配置文件不存在"}), 404

        try:
            with open(classrooms_file, "r", encoding="utf-8") as f:
                classrooms_data = json.load(f)
        except Exception as e:
            logger.error(f"读取教室配置文件出错: {str(e)}")
            return (
                jsonify(
                    {"status": "error", "message": f"读取教室配置文件出错: {str(e)}"}
                ),
                500,
            )

        # 获取查询参数
        building_prefix = request.args.get("building", "")

        # 如果指定了建筑物前缀，只返回该建筑物的教室
        if building_prefix:
            filtered_data = {}
            for building, rooms in classrooms_data.items():
                if building.startswith(building_prefix):
                    filtered_data[building] = rooms
            return jsonify({"status": "success", "data": filtered_data})

        return jsonify({"status": "success", "data": classrooms_data})

    except Exception as e:
        logger.error(f"获取教室列表出错: {str(e)}")
        return (
            jsonify({"status": "error", "message": f"获取教室列表出错: {str(e)}"}),
            500,
        )


@app.route("/api/free_classrooms", methods=["POST"])
def get_free_classrooms():
    """查询空闲教室"""
    try:
        # 检查是否已登录
        if not session.get("logged_in"):
            return jsonify({"status": "error", "message": "未登录，请先登录"}), 401

        data = request.json or {}
        building_prefix = data.get("building_prefix")  # 教学楼前缀
        week = data.get("week")  # 周次
        day = data.get("day")  # 星期几
        start_period = data.get("start_period")  # 开始节次
        end_period = data.get("end_period")  # 结束节次
        xnxqh = data.get("xnxqh")  # 学年学期

        if not all([building_prefix, week, day, start_period, end_period, xnxqh]):
            return (
                jsonify({"status": "error", "message": "请填写所有必要的查询条件"}),
                400,
            )

        # 1. 获取课表查询结果
        if not all(isinstance(x, str) for x in [week, day, start_period, end_period]):
            return (
                jsonify({"status": "error", "message": "周次、星期和节次必须是字符串"}),
                400,
            )

        try:
            week_num = int(str(week))
            day_num = int(str(day))
            start_num = int(str(start_period))
            end_num = int(str(end_period))
        except (ValueError, TypeError):
            return (
                jsonify(
                    {"status": "error", "message": "周次、星期和节次必须是有效的数字"}
                ),
                400,
            )

        result = get_room_classtable(
            xnxqh, building_prefix, week_num, day_num, str(start_num), str(end_num)
        )
        if result.get("status") != "success":
            return jsonify({"status": "error", "message": "查询课表失败"}), 500

        # 2. 从classrooms.json获取所有符合前缀的教室
        try:
            with open(
                os.path.join(os.path.dirname(__file__), "classrooms.json"),
                "r",
                encoding="utf-8",
            ) as f:
                all_classrooms = json.load(f)["classrooms"]
        except Exception as e:
            logger.error(f"读取教室列表失败: {str(e)}")
            return jsonify({"status": "error", "message": "读取教室列表失败"}), 500

        # 3. 根据前缀过滤教室
        matched_classrooms = [
            room for room in all_classrooms if room.startswith(building_prefix)
        ]
        if not matched_classrooms:
            return jsonify(
                {
                    "status": "success",
                    "data": {"free_classrooms": [], "message": "未找到符合条件的教室"},
                }
            )

        # 4. 根据课表结果过滤出有课的教室
        occupied_classrooms = set()
        if result.get("data"):
            for room_data in result["data"]:
                room_name = room_data.get("name")
                if room_name and str(day) in room_data.get("schedule", {}):
                    day_schedule = room_data["schedule"][str(day)]
                    # 检查指定时间段是否有课
                    has_class = False
                    for period in range(start_num, end_num + 1):
                        period_key = f"第{period}节"
                        if period_key in day_schedule and day_schedule[period_key]:
                            has_class = True
                            break
                    if has_class:
                        occupied_classrooms.add(room_name)

        # 5. 计算空闲教室
        free_classrooms = [
            room for room in matched_classrooms if room not in occupied_classrooms
        ]

        # 6. 返回结果
        return jsonify(
            {
                "status": "success",
                "data": {
                    "free_classrooms": free_classrooms,
                    "total_count": len(free_classrooms),
                    "message": f"找到 {len(free_classrooms)} 个空闲教室",
                },
            }
        )

    except Exception as e:
        logger.error(f"查询空闲教室出错: {str(e)}")
        return (
            jsonify({"status": "error", "message": f"查询空闲教室出错: {str(e)}"}),
            500,
        )


def get_default_announcements():
    """获取默认的广告/宣传内容"""
    return {
        "top": {
            "title": "公告",
            "content": {
                "welcome": {"description": "公告描述"},
                "contact": {"qq_group": "00000000"},
            },
        },
        "bottom": {
            "title": "推荐内容",
            "content": {
                "tools": [
                    {"name": "功能1", "url": "#", "icon": "fas fa-star"},
                    {
                        "name": "功能2",
                        "url": "#",
                        "icon": "fas fa-star",
                    },
                    {"name": "功能3", "url": "#", "icon": "fas fa-star"},
                ]
            },
        },
    }


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
