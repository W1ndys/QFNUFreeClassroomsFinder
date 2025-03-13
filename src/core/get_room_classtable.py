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

        # 如果访问课表查询页面失败，记录错误
        if classroom_response.status_code != 200:
            logging.error(f"访问课表查询页面失败: {classroom_response.status_code}")
            return {"error": "访问课表查询页面失败"}

        # 预加载框架，这是查询前的必要步骤
        kbjcmsid = "94786EE0ABE2D3B2E0531E64A8C09931"  # 课表基础模式ID
        init_url = f"http://zhjw.qfnu.edu.cn/jsxsd/kbxx/initJc?xnxq={xnxqh}&kbjcmsid={kbjcmsid}"
        init_response = session.get(init_url)
        logging.info(f"预加载框架响应状态码: {init_response.status_code}")

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
            "jc1": jc1 if jc1 else "",  # 确保传递节次参数
            "jc2": jc2 if jc2 else "",  # 确保传递节次参数
        }

        # 记录请求参数，便于调试
        logging.info(f"课表查询请求参数: {data}")

        # 发送POST请求
        response = session.post(url, data=data)
        response.raise_for_status()

        # 添加响应文本日志，便于调试
        logging.info(f"课表查询响应状态码: {response.status_code}")

        # 解析返回的HTML
        soup = BeautifulSoup(response.text, "html.parser")

        # 提取课表信息 - 修改为适应新的HTML结构
        table = soup.find("table", id="kbtable")
        if not table:
            logging.error("未找到课表数据")
            return {"error": "未找到课表数据"}

        # 解析表格数据
        result = parse_classtable_new(table, day, room_name, jc1, jc2)

        return {
            "status": "success",
            "room": room_name,
            "week": week,
            "day": day,
            "jc1": jc1,
            "jc2": jc2,
            "data": result,
        }

    except requests.RequestException as e:
        logging.error(f"获取教室课表失败: {str(e)}")
        return {"error": f"请求失败: {str(e)}"}
    except Exception as e:
        logging.error(f"处理教室课表数据时出错: {str(e)}")
        return {"error": f"处理数据失败: {str(e)}"}


def parse_classtable_new(table, specific_day=None, room_name=None, jc1=None, jc2=None):
    """
    解析课表HTML表格 - 新算法

    参数:
        table: BeautifulSoup表格对象
        specific_day: 指定的星期几，如果提供则只返回该天的课表
        room_name: 教室名称前缀，如果提供则返回所有匹配前缀的教室课表
        jc1: 开始节次，如果提供则只返回该节次及之后的课表
        jc2: 结束节次，如果提供则只返回该节次及之前的课表

    返回:
        list: 解析后的课表数据，按教室组织
    """
    rooms_data = []

    logging.info(
        f"开始解析课表，specific_day={specific_day}, room_name={room_name}, jc1={jc1}, jc2={jc2}"
    )

    try:
        # 获取表头信息 - 节次
        if not table.find("thead"):
            logging.error("表格结构异常，未找到thead")
            return rooms_data

        header_rows = table.find("thead").find_all("tr")
        if len(header_rows) < 2:
            logging.error("表格头部结构异常，行数不足")
            return rooms_data

        # 获取星期信息（第一行）
        week_headers = []
        for th in header_rows[0].find_all(["th", "td"])[1:]:  # 跳过第一个单元格
            if "colspan" in th.attrs:
                week_name = th.text.strip()
                colspan = int(th.attrs.get("colspan", 1))
                for _ in range(colspan):
                    week_headers.append(week_name)
            else:
                week_headers.append(th.text.strip())

        # 获取节次信息（第二行）
        period_cells = header_rows[1].find_all("td")
        if len(period_cells) < 2:  # 至少需要有"教室\节次"和一个节次
            logging.error("节次信息异常")
            return rooms_data

        periods = []
        for td in period_cells[1:]:  # 跳过第一个单元格
            periods.append(td.text.strip())

        logging.info(f"解析到的节次: {periods}")

        # 计算每天有多少个节次列
        periods_per_day = len(periods) // 7  # 假设一周7天
        if periods_per_day * 7 != len(periods):
            logging.warning(f"节次列数({len(periods)})不是7的整数倍，可能导致解析错误")

        # 解析每个教室行
        room_rows = table.find_all("tr")[2:]  # 跳过表头两行
        logging.info(f"找到 {len(room_rows)} 行教室数据")

        for row in room_rows:
            cells = row.find_all("td")
            if not cells or len(cells) <= 1:
                continue

            # 获取教室名
            current_room_name = cells[0].text.strip()
            logging.info(f"处理教室: {current_room_name}")

            # 检查是否匹配前缀
            if room_name and not current_room_name.startswith(room_name):
                logging.info(f"教室 {current_room_name} 不匹配前缀 {room_name}，跳过")
                continue

            room_schedule = {}
            has_classes = False  # 标记该教室是否有课

            # 遍历每一列（跳过第一列教室名）
            for i, cell in enumerate(cells[1:], 1):
                # 计算当前单元格对应的星期和节次
                day_index = (i - 1) // periods_per_day + 1  # 从1开始，对应周一到周日
                period_index = (i - 1) % periods_per_day

                # 如果指定了特定的星期，且不是当前处理的星期，则跳过
                if specific_day and int(specific_day) != day_index:
                    continue

                # 获取当前节次
                if period_index < len(periods):
                    period = periods[period_index]

                    # 检查节次是否在指定范围内
                    # 注：这里只对标准格式的节次进行过滤，如"0102"表示第1-2节
                    if (jc1 or jc2) and len(period) == 4 and period.isdigit():
                        current_start = int(period[:2])
                        current_end = int(period[2:])

                        if jc1 and current_end < int(jc1):
                            continue  # 当前节次结束早于指定的开始节次
                        if jc2 and current_start > int(jc2):
                            continue  # 当前节次开始晚于指定的结束节次

                # 检查单元格是否有课程内容
                course_divs = cell.find_all("div", class_="kbcontent1")

                if course_divs:
                    for course_div in course_divs:
                        course_text = course_div.text.strip()
                        if course_text and course_text != "&nbsp;":
                            # 解析课程信息
                            class_data = parse_class_info_new(course_text)
                            if class_data:
                                # 保存原始文本
                                class_data["original_text"] = course_text
                                # 保存节次信息
                                class_data["period"] = period

                                # 添加课程信息到课表
                                day_key = str(day_index)
                                if day_key not in room_schedule:
                                    room_schedule[day_key] = {}

                                if period not in room_schedule[day_key]:
                                    room_schedule[day_key][period] = []

                                room_schedule[day_key][period].append(class_data)

                                # 同时为单节次创建映射（例如"0102"表示第1-2节，分别创建"第1节"和"第2节"的映射）
                                if len(period) == 4 and period.isdigit():
                                    start_period = int(period[:2])
                                    end_period = int(period[2:])
                                    for p in range(start_period, end_period + 1):
                                        single_period = f"第{p}节"
                                        if single_period not in room_schedule[day_key]:
                                            room_schedule[day_key][single_period] = []
                                        room_schedule[day_key][single_period].append(
                                            class_data
                                        )

                                has_classes = True
                                logging.info(
                                    f"教室 {current_room_name} 在星期{day_index}的{period}有课: {course_text[:20]}..."
                                )

            # 只有当教室有课时，才添加到结果中
            if has_classes:
                rooms_data.append(
                    {"name": current_room_name, "schedule": room_schedule}
                )
                logging.info(f"教室 {current_room_name} 有课，添加到结果")
            else:
                logging.info(f"教室 {current_room_name} 没有课，不添加到结果")

    except Exception as e:
        logging.error(f"解析课表时出错: {str(e)}")
        import traceback

        logging.error(traceback.format_exc())

    return rooms_data


def parse_class_info_new(info_text):
    """
    解析课程信息文本 - 新算法

    参数:
        info_text: 课程信息文本，例如：
        "通信电子电路张明强
        (1-18周)
        23通信班
        格物楼B203"

    返回:
        dict: 解析后的课程信息
    """
    if not info_text or info_text.strip() == "" or info_text.strip() == "&nbsp;":
        return None

    # 分割文本为行
    lines = [line.strip() for line in info_text.split("\n") if line.strip()]
    if not lines:
        return None

    class_info = {"all_lines": lines}  # 保存所有行，便于前端展示

    # 解析第一行（通常是课程名称和教师名）
    if lines:
        # 尝试从第一行提取课程名和教师名
        first_line = lines[0]
        # 常见模式：课程名+教师名
        course_teacher_match = None
        for i in range(len(first_line) - 1, 0, -1):
            if first_line[i].isalpha():  # 找到最后一个汉字位置
                course_teacher_match = (first_line[: i + 1], "")
                break

        if course_teacher_match:
            class_info["course_name"] = course_teacher_match[0]
            class_info["teacher"] = (
                course_teacher_match[1] if course_teacher_match[1] else []
            )
        else:
            class_info["course_name"] = first_line

    # 解析周次信息（通常在第二行，格式如"(1-18周)"）
    if len(lines) > 1:
        for i, line in enumerate(lines):
            if "周)" in line and "(" in line:
                week_range = line.strip()
                class_info["week_range"] = week_range
                break

    # 解析最后一行（通常是教室信息）
    if len(lines) > 1:
        class_info["room"] = lines[-1]

    # 解析中间行（通常是班级信息）
    if len(lines) > 2:
        # 排除第一行（课程名和教师）和最后一行（教室）
        middle_lines = lines[1:-1]
        # 排除周次信息
        class_lines = [
            line for line in middle_lines if not ("周)" in line and "(" in line)
        ]
        if class_lines:
            class_info["class_info"] = class_lines

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
