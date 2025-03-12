import os
import json
import re
from bs4 import BeautifulSoup

# 获取当前目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# HTML文件路径
html_file_path = os.path.join(current_dir, "all_classromms.html")

# 读取HTML文件
with open(html_file_path, "r", encoding="utf-8") as file:
    html_content = file.read()

# 使用BeautifulSoup解析HTML
soup = BeautifulSoup(html_content, "html.parser")

# 查找所有教室名称
classrooms = set()  # 使用集合去重

# 在表格中查找教室名称
rows = soup.select("#kbtable tbody tr")
for row in rows:
    # 第一个单元格通常包含教室名称
    first_cell = row.find("td")
    if first_cell:
        classroom_text = first_cell.text.strip()
        # 确保提取的是教室名称（通常是字母+数字的组合）
        if classroom_text and not classroom_text.startswith("教室"):
            classrooms.add(classroom_text)

# 将教室名称列表转换为JSON
classrooms_list = sorted(list(classrooms))

# 按前缀分类教室
classroom_by_prefix = {}


# 定义一个函数来提取前缀
def extract_prefix(classroom_name):
    # 匹配字母前缀
    match = re.match(r"^([A-Za-z]+)", classroom_name)
    if match:
        return match.group(1)

    # 匹配中文前缀（取第一个词或前两个字）
    match = re.match(r"^([\u4e00-\u9fa5]+)(?:\d|楼|场|馆)", classroom_name)
    if match:
        return match.group(1)

    # 如果没有明确前缀，使用第一个字符
    if classroom_name:
        return classroom_name[0]

    return "其他"


# 对每个教室进行分类
for classroom in classrooms_list:
    prefix = extract_prefix(classroom)
    if prefix not in classroom_by_prefix:
        classroom_by_prefix[prefix] = []
    classroom_by_prefix[prefix].append(classroom)

# 保存为JSON文件
output_file_path = os.path.join(current_dir, "classrooms_by_prefix.json")
with open(output_file_path, "w", encoding="utf-8") as json_file:
    json.dump(classroom_by_prefix, json_file, ensure_ascii=False, indent=4)

# 同时保存原始列表
original_output_file_path = os.path.join(current_dir, "classrooms.json")
with open(original_output_file_path, "w", encoding="utf-8") as json_file:
    json.dump({"classrooms": classrooms_list}, json_file, ensure_ascii=False, indent=4)

print(f"已提取 {len(classrooms_list)} 个教室名称")
print(f"按前缀分类为 {len(classroom_by_prefix)} 个类别")
print(f"分类结果已保存到 {output_file_path}")
print(f"原始列表已保存到 {original_output_file_path}")
