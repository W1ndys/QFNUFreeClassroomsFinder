# QFNUFreeClassroomsFinder
曲阜师范大学空闲教室查询

## 功能介绍

本项目提供曲阜师范大学教室课表查询功能，可以查询指定教室在特定周次和日期的课程安排，帮助学生找到空闲教室进行自习或活动。

项目提供两种使用方式：
1. 命令行模式：通过运行main.py脚本进行查询
2. 网页模式：通过运行run_web.py启动网页服务，在浏览器中进行查询

## 安装与使用

### 环境要求
- Python 3.7+
- 依赖包：见requirements.txt

### 安装步骤

1. 克隆仓库
```bash
git clone https://github.com/W1ndys/QFNUNoClassFinder.git
cd QFNUNoClassFinder
```

2. 安装依赖
```bash
# Windows
create_venv_windows.bat

# Linux/Mac
bash create_venv_linux.sh
```

3. 配置账号信息
编辑config.json文件，填入教务系统账号和密码：
```json
{
    "user_account": "你的学号",
    "user_password": "你的密码"
}
```

### 使用方法

#### 命令行模式
```bash
# Windows
run_app_in_venv_windows.bat

# Linux/Mac
bash run_app_in_venv_linux.sh
```

#### 网页模式
```bash
# Windows
python run_web.py

# Linux/Mac
python3 run_web.py
```

启动后，在浏览器中访问 http://127.0.0.1:5000 即可使用网页版查询系统。

## 网页版功能说明

网页版提供了更友好的用户界面，主要功能包括：

1. **用户登录**：
   - 支持手动输入验证码
   - 提供自动识别验证码功能（可选）
   - 验证码图片支持点击刷新

2. **课表查询**：
   - 支持选择学年学期
   - 支持按教室名称前缀查询（如输入"格物楼B"将匹配所有以"格物楼B"开头的教室）
   - 支持选择周次（1-20周）
   - 支持选择星期几（可选，不选则显示整周课表）

3. **查询结果展示**：
   - 清晰展示匹配的教室课表
   - 区分有课和空闲时段
   - 显示课程详细信息（课程名称、教师、周次等）

## 注意事项

1. 本项目仅供学习交流使用，请勿用于非法用途
2. 使用教务系统账号登录时，请确保在安全的环境下使用
3. 自动识别验证码功能准确率不保证100%，如遇识别错误请手动输入

## 贡献与反馈

如有问题或建议，欢迎提交Issue或Pull Request。

## 许可证

本项目采用MIT许可证。详见LICENSE文件。
