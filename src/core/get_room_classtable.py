import requests
from bs4 import BeautifulSoup
from src.utils.session_manager import get_session
import logging


def get_room_classtable(xnxqh, room_name, week, day=None, jc1=None, jc2=None):
    """
    获取指定教室的课表信息

    参数:
        xnxqh (str): 学年学期，格式如 "2024-2025-2"
        room_name (str): 教室名称前缀，如 "格物楼B"将匹配所有以"格物楼B"开头的教室
        week (int): 周次，如 3
        day (int, optional): 星期几，1-7，如果不指定则返回整周课表
        jc1 (str, optional): 开始节次，默认为空
        jc2 (str, optional): 结束节次，默认为空

    返回:
        dict: 课表信息，包含匹配前缀的所有教室数据
    """
    try:
        session = get_session()

        # 先访问全校性教室课表查询页面
        classroom_page_url = "http://zhjw.qfnu.edu.cn/jsxsd/kbcx/kbxx_classroom"
        classroom_response = session.get(classroom_page_url)
        logging.info(
            f"全校性教室课表查询页面响应状态码: {classroom_response.status_code}"
        )
        # 添加响应文本日志，便于调试
        logging.debug(
            f"全校性教室课表查询页面响应状态码: {classroom_response.status_code}"
        )

        # 如果访问课表查询页面失败，记录错误
        if classroom_response.status_code != 200:
            logging.error(f"访问课表查询页面失败: {classroom_response.status_code}")
            return {"error": "访问课表查询页面失败"}

        # 预加载框架，这是查询前的必要步骤
        kbjcmsid = "94786EE0ABE2D3B2E0531E64A8C09931"  # 课表基础模式ID
        init_url = f"http://zhjw.qfnu.edu.cn/jsxsd/kbxx/initJc?xnxq={xnxqh}&kbjcmsid={kbjcmsid}"
        init_response = session.get(init_url)
        logging.info(f"预加载框架响应状态码: {init_response.status_code}")
        # 添加响应文本日志，便于调试
        logging.debug(f"预加载框架响应状态码: {init_response.status_code}")

        # 如果预加载失败，记录错误
        if init_response.status_code != 200:
            logging.error(f"预加载框架失败: {init_response.status_code}")
            return {"error": "预加载框架失败"}

        # 查询课表
        url = "http://zhjw.qfnu.edu.cn/jsxsd/kbcx/kbxx_classroom_ifr"

        # 构建请求参数
        data = {
            "xnxqh": xnxqh,
            "kbjcmsid": kbjcmsid,  # 使用相同的课表基础模式ID
            "skyx": "",
            "xqid": "",
            "jzwid": "",
            "skjsid": "",
            "skjs": room_name,
            "zc1": str(week),
            "zc2": str(week),
            "skxq1": str(day) if day else "",
            "skxq2": str(day) if day else "",
            "jc1": jc1,
            "jc2": jc2,
        }

        # 发送POST请求
        response = session.post(url, data=data)
        response.raise_for_status()

        # 添加响应文本日志，便于调试
        logging.debug(f"课表查询响应状态码: {response.status_code}")

        # 解析返回的HTML
        soup = BeautifulSoup(response.text, "html.parser")

        # 提取课表信息 - 修改为适应新的HTML结构
        table = soup.find("table", id="kbtable")
        if not table:
            logging.error("未找到课表数据")
            return {"error": "未找到课表数据"}
        # 解析表格数据
        result = parse_classtable_new(table, day, room_name)

        return {
            "status": "success",
            "room": room_name,
            "week": week,
            "day": day,
            "data": result,
        }

    except requests.RequestException as e:
        logging.error(f"获取教室课表失败: {str(e)}")
        return {"error": f"请求失败: {str(e)}"}
    except Exception as e:
        logging.error(f"处理教室课表数据时出错: {str(e)}")
        return {"error": f"处理数据失败: {str(e)}"}


def parse_classtable_new(table, specific_day=None, room_name=None):
    """
    解析课表HTML表格 - 适应新的HTML结构

    参数:
        table: BeautifulSoup表格对象
        specific_day: 指定的星期几，如果提供则只返回该天的课表
        room_name: 教室名称前缀，如果提供则返回所有匹配前缀的教室课表

    返回:
        list: 解析后的课表数据，按教室组织
    """
    rooms_data = []

    # 记录日志，帮助调试
    logging.debug(f"开始解析课表，specific_day={specific_day}, room_name={room_name}")

    try:
        # 获取表头信息
        headers_row = table.find("thead").find_all("tr")[1]  # 第二行包含节次信息
        periods = []

        # 跳过第一列（教室\节次）
        for td in headers_row.find_all("td")[1:]:
            periods.append(td.text.strip())

        logging.debug(f"解析到的节次: {periods}")

        # 获取每个教室的数据
        rows = table.find_all("tr")[2:]  # 跳过表头两行
        logging.debug(f"找到 {len(rows)} 行教室数据")

        for row in rows:
            cells = row.find_all("td")
            if not cells or len(cells) <= 1:
                continue

            # 获取教室名
            current_room_name = cells[0].text.strip()
            logging.debug(f"处理教室: {current_room_name}")

            # 如果指定了教室名前缀，且当前教室名不是以该前缀开头，则跳过
            if room_name and not current_room_name.startswith(room_name):
                logging.debug(f"教室 {current_room_name} 不匹配前缀 {room_name}，跳过")
                continue

            room_schedule = {}
            has_classes = False  # 标记该教室是否有课

            # 处理每一天的数据
            for day_num in range(1, 8):  # 1-7对应周一到周日
                # 如果指定了特定的天，且不是当前处理的天，则跳过
                if specific_day and int(specific_day) != day_num:
                    continue

                day_schedule = {}

                # 计算当天的起始列索引 - 每天只有一列
                col_idx = day_num  # 索引从1开始，第1列是教室名，第2-8列是周一到周日

                if col_idx < len(cells):
                    cell = cells[col_idx]
                    period = periods[col_idx - 1]  # 获取对应的时间段

                    # 获取课程内容
                    course_divs = cell.find_all("div", class_="kbcontent1")

                    if course_divs:
                        has_day_classes = False
                        for course_div in course_divs:
                            course_text = course_div.text.strip()
                            if course_text and course_text != "&nbsp;":
                                class_data = parse_class_info_new(course_text)
                                if class_data:
                                    if period not in day_schedule:
                                        day_schedule[period] = []
                                    day_schedule[period].append(class_data)
                                    has_classes = True
                                    has_day_classes = True

                        # 只有当这一天有课时，才添加到结果中
                        if has_day_classes:
                            if str(day_num) not in room_schedule:
                                room_schedule[str(day_num)] = {}
                            room_schedule[str(day_num)].update(day_schedule)

            # 只有当教室有课时，才添加到结果中
            if has_classes:
                rooms_data.append(
                    {"name": current_room_name, "schedule": room_schedule}
                )
                logging.debug(f"教室 {current_room_name} 有课，添加到结果")
            else:
                logging.debug(f"教室 {current_room_name} 没有课，不添加到结果")

    except Exception as e:
        logging.error(f"解析课表时出错: {str(e)}")

    return rooms_data


def parse_class_info_new(info_text):
    """
    解析课程信息文本 - 适应新的格式

    参数:
        info_text: 课程信息文本

    返回:
        dict: 解析后的课程信息
    """
    if not info_text or info_text.strip() == "" or info_text.strip() == "&nbsp;":
        return None

    lines = [line.strip() for line in info_text.split("\n") if line.strip()]
    if not lines:
        return None

    class_info = {}

    # 第一行通常是课程名称和教师
    if len(lines) > 0:
        first_line = lines[0]
        if "(" in first_line and ")" in first_line:
            # 尝试分离课程名称和教师
            parts = first_line.split("(")[0].strip().split()
            if len(parts) > 1:
                class_info["course_name"] = "".join(parts[:-1])
                class_info["teacher"] = parts[-1]
            else:
                class_info["course_name"] = first_line
        else:
            class_info["course_name"] = first_line

    # 解析周次信息
    for line in lines:
        if "(" in line and ")" in line and "周" in line:
            weeks_part = line.split("(")[1].split(")")[0]
            class_info["weeks"] = weeks_part
            break

    # 解析班级信息
    for i, line in enumerate(lines):
        if i > 0 and not ("(" in line and ")" in line and "周" in line):
            if "楼" not in line:  # 不是教室信息
                class_info["class"] = line
                break

    # 解析教室信息
    for line in lines:
        if "楼" in line:
            class_info["room"] = line
            break

    return class_info


def convert_day_to_number(day_name):
    """
    将星期名称转换为数字

    参数:
        day_name: 星期名称，如"星期一"

    返回:
        int: 对应的数字，1-7
    """
    day_map = {
        "星期一": 1,
        "星期二": 2,
        "星期三": 3,
        "星期四": 4,
        "星期五": 5,
        "星期六": 6,
        "星期日": 7,
        "星期天": 7,
    }
    return day_map.get(day_name, 0)
