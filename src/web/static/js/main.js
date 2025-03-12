// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化页面
    initPage();
    
    // 绑定事件
    bindEvents();
});

// 初始化页面
function initPage() {
    // 获取验证码
    refreshCaptcha();
    
    // 填充周次选择
    const weekSelect = document.getElementById('week');
    for (let i = 1; i <= 20; i++) {
        const option = document.createElement('option');
        option.value = i;
        option.textContent = `第${i}周`;
        weekSelect.appendChild(option);
    }
    
    // 获取当前学期
    fetchCurrentTerm();
    
    // 检查登录状态
    checkLoginStatus();
}

// 绑定事件
function bindEvents() {
    // 刷新验证码按钮
    document.getElementById('refresh-captcha').addEventListener('click', refreshCaptcha);
    
    // 验证码图片点击刷新
    document.getElementById('captcha-image').addEventListener('click', refreshCaptcha);
    
    // 自动识别验证码按钮
    document.getElementById('auto-ocr').addEventListener('click', autoRecognizeCaptcha);
    
    // 登录表单提交
    document.getElementById('login-form').addEventListener('submit', function(e) {
        e.preventDefault();
        handleLogin();
    });
    
    // 退出登录按钮
    document.getElementById('logout-btn').addEventListener('click', handleLogout);
    
    // 查询表单提交
    document.getElementById('query-form').addEventListener('submit', function(e) {
        e.preventDefault();
        handleQuery();
    });
}

// 刷新验证码
function refreshCaptcha() {
    const captchaImage = document.getElementById('captcha-image');
    const timestamp = new Date().getTime(); // 添加时间戳防止缓存
    
    // 显示加载状态
    captchaImage.src = '';
    captchaImage.alt = '加载中...';
    
    // 请求新验证码
    fetch(`/get_captcha?t=${timestamp}`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                captchaImage.src = data.captcha_image;
                captchaImage.alt = '验证码';
                
                // 清空验证码输入框
                document.getElementById('captcha').value = '';
            } else {
                showMessage('login-message', '获取验证码失败: ' + data.message, 'danger');
            }
        })
        .catch(error => {
            showMessage('login-message', '获取验证码出错: ' + error, 'danger');
        });
}

// 自动识别验证码
function autoRecognizeCaptcha() {
    const captchaInput = document.getElementById('captcha');
    const timestamp = new Date().getTime();
    
    // 显示加载状态
    captchaInput.value = '识别中...';
    captchaInput.disabled = true;
    
    // 请求自动识别
    fetch(`/get_captcha?t=${timestamp}&auto_ocr=true`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success' && data.ocr_result) {
                // 更新验证码图片和输入框
                document.getElementById('captcha-image').src = data.captcha_image;
                captchaInput.value = data.ocr_result;
            } else {
                showMessage('login-message', '自动识别失败: ' + (data.message || '无法识别'), 'warning');
                captchaInput.value = '';
            }
            captchaInput.disabled = false;
        })
        .catch(error => {
            showMessage('login-message', '自动识别出错: ' + error, 'danger');
            captchaInput.value = '';
            captchaInput.disabled = false;
        });
}

// 处理登录
function handleLogin() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const captcha = document.getElementById('captcha').value;
    
    if (!username || !password || !captcha) {
        showMessage('login-message', '请填写完整的登录信息', 'warning');
        return;
    }
    
    // 显示加载状态
    const loginBtn = document.querySelector('#login-form button[type="submit"]');
    const originalBtnText = loginBtn.textContent;
    loginBtn.textContent = '登录中...';
    loginBtn.disabled = true;
    
    // 发送登录请求
    fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            username: username,
            password: password,
            captcha: captcha
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showMessage('login-message', '登录成功！', 'success');
            
            // 更新UI状态
            document.getElementById('login-section').classList.add('d-none');
            document.getElementById('user-info-section').classList.remove('d-none');
            document.getElementById('query-btn').disabled = false;
            
            // 清空登录表单
            document.getElementById('login-form').reset();
        } else {
            showMessage('login-message', '登录失败: ' + data.message, 'danger');
            refreshCaptcha(); // 刷新验证码
        }
    })
    .catch(error => {
        showMessage('login-message', '登录请求出错: ' + error, 'danger');
        refreshCaptcha(); // 刷新验证码
    })
    .finally(() => {
        // 恢复按钮状态
        loginBtn.textContent = originalBtnText;
        loginBtn.disabled = false;
    });
}

// 处理登出
function handleLogout() {
    // 显示加载状态
    const logoutBtn = document.getElementById('logout-btn');
    const originalBtnText = logoutBtn.textContent;
    logoutBtn.textContent = '退出中...';
    logoutBtn.disabled = true;
    
    // 发送登出请求
    fetch('/logout', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // 更新UI状态
            document.getElementById('login-section').classList.remove('d-none');
            document.getElementById('user-info-section').classList.add('d-none');
            document.getElementById('query-btn').disabled = true;
            document.getElementById('result-section').classList.add('d-none');
            
            // 刷新验证码
            refreshCaptcha();
        } else {
            showMessage('login-message', '登出失败: ' + data.message, 'danger');
        }
    })
    .catch(error => {
        showMessage('login-message', '登出请求出错: ' + error, 'danger');
    })
    .finally(() => {
        // 恢复按钮状态
        logoutBtn.textContent = originalBtnText;
        logoutBtn.disabled = false;
    });
}

// 处理查询
function handleQuery() {
    const xnxqh = document.getElementById('xnxqh').value;
    const roomName = document.getElementById('room_name').value;
    const week = document.getElementById('week').value;
    const day = document.getElementById('day').value;
    
    if (!xnxqh || !roomName || !week) {
        showMessage('result-container', '请填写完整的查询信息', 'warning');
        return;
    }
    
    // 显示加载状态
    const queryBtn = document.getElementById('query-btn');
    const originalBtnText = queryBtn.textContent;
    queryBtn.textContent = '查询中...';
    queryBtn.disabled = true;
    
    // 显示结果区域
    const resultSection = document.getElementById('result-section');
    resultSection.classList.remove('d-none');
    
    // 清空结果容器并显示加载提示
    const resultContainer = document.getElementById('result-container');
    resultContainer.innerHTML = '<div class="text-center"><div class="spinner-border text-primary" role="status"></div><p class="mt-2">正在查询，请稍候...</p></div>';
    
    // 发送查询请求
    fetch('/query_classtable', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            xnxqh: xnxqh,
            room_name: roomName,
            week: week,
            day: day
        })
    })
    .then(response => {
        if (response.status === 401) {
            // 未登录，显示错误并滚动到登录区域
            showMessage('result-container', '您尚未登录或登录已过期，请先登录', 'danger');
            document.getElementById('login-section').scrollIntoView({ behavior: 'smooth' });
            throw new Error('未登录');
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            // 渲染查询结果
            renderClassTable(data, roomName, week, day);
        } else {
            showMessage('result-container', '查询失败: ' + data.message, 'danger');
        }
    })
    .catch(error => {
        if (error.message !== '未登录') {
            showMessage('result-container', '查询请求出错: ' + error, 'danger');
        }
    })
    .finally(() => {
        // 恢复按钮状态
        queryBtn.textContent = originalBtnText;
        queryBtn.disabled = false;
    });
}

// 渲染课表
function renderClassTable(data, roomName, week, day) {
    const resultContainer = document.getElementById('result-container');
    const roomsData = data.data;
    
    // 如果没有数据
    if (!roomsData || roomsData.length === 0) {
        resultContainer.innerHTML = `<div class="alert alert-info">未找到匹配 "${roomName}" 的教室课表数据</div>`;
        return;
    }
    
    let html = `<div class="alert alert-success">查询成功！找到 ${roomsData.length} 个匹配的教室</div>`;
    
    // 遍历每个教室
    roomsData.forEach(room => {
        html += `<h4 class="room-title">${room.name}</h4>`;
        
        // 创建课表
        if (day) {
            // 单日课表
            html += createDayTable(room, day);
        } else {
            // 整周课表
            html += createWeekTable(room);
        }
    });
    
    resultContainer.innerHTML = html;
}

// 创建单日课表
function createDayTable(room, day) {
    const daySchedule = room.schedule[day];
    if (!daySchedule) {
        return `<div class="alert alert-info">该教室在选定的日期没有课程安排</div>`;
    }
    
    const dayNames = ['', '周一', '周二', '周三', '周四', '周五', '周六', '周日'];
    
    let html = `<table class="timetable">
        <thead>
            <tr>
                <th>${dayNames[parseInt(day)]}</th>
                <th>课程信息</th>
            </tr>
        </thead>
        <tbody>`;
    
    // 遍历时间段
    const periods = Object.keys(daySchedule).sort();
    for (const period of periods) {
        const classes = daySchedule[period];
        if (classes && classes.length > 0) {
            const classInfo = classes[0];
            html += `<tr class="has-class">
                <td>${period}</td>
                <td>
                    <div><strong>${classInfo.course_name || '未知课程'}</strong></div>
                    ${classInfo.teacher ? `<div>教师: ${classInfo.teacher}</div>` : ''}
                    ${classInfo.weeks ? `<div>周次: ${classInfo.weeks}</div>` : ''}
                    ${classInfo.class ? `<div>班级: ${classInfo.class}</div>` : ''}
                </td>
            </tr>`;
        } else {
            html += `<tr class="no-class">
                <td>${period}</td>
                <td>空闲</td>
            </tr>`;
        }
    }
    
    html += `</tbody></table>`;
    return html;
}

// 创建整周课表
function createWeekTable(room) {
    const dayNames = ['', '周一', '周二', '周三', '周四', '周五', '周六', '周日'];
    const periodNames = ['第一节', '第二节', '第三节', '第四节', '第五节', '第六节'];
    
    let html = `<table class="timetable">
        <thead>
            <tr>
                <th>时间/日期</th>`;
    
    // 添加表头（周一至周日）
    for (let i = 1; i <= 7; i++) {
        html += `<th>${dayNames[i]}</th>`;
    }
    
    html += `</tr>
        </thead>
        <tbody>`;
    
    // 遍历每个时间段
    for (let period = 0; period < 6; period++) {
        html += `<tr>
            <td>${periodNames[period]}</td>`;
        
        // 遍历每天
        for (let day = 1; day <= 7; day++) {
            const daySchedule = room.schedule[day.toString()];
            const periodKey = Object.keys(daySchedule || {}).sort()[period];
            
            if (daySchedule && periodKey && daySchedule[periodKey] && daySchedule[periodKey].length > 0) {
                const classInfo = daySchedule[periodKey][0];
                html += `<td class="has-class">
                    <div><strong>${classInfo.course_name || '未知课程'}</strong></div>
                    ${classInfo.teacher ? `<div>${classInfo.teacher}</div>` : ''}
                </td>`;
            } else {
                html += `<td class="no-class">空闲</td>`;
            }
        }
        
        html += `</tr>`;
    }
    
    html += `</tbody></table>`;
    return html;
}

// 获取当前学期
function fetchCurrentTerm() {
    fetch('/get_current_term')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const xnxqhSelect = document.getElementById('xnxqh');
                
                // 清空现有选项
                xnxqhSelect.innerHTML = '';
                
                // 添加当前学期
                const currentOption = document.createElement('option');
                currentOption.value = data.current_term;
                currentOption.textContent = `${data.current_term} (当前学期)`;
                xnxqhSelect.appendChild(currentOption);
                
                // 添加其他学期选项（前后各两个学期）
                const [year1, year2, term] = data.current_term.split('-');
                const baseYear = parseInt(year1);
                
                // 前两个学期
                for (let i = 1; i <= 2; i++) {
                    let prevYear1, prevYear2, prevTerm;
                    
                    if (term === '1') {
                        prevYear1 = baseYear - i;
                        prevYear2 = baseYear - i + 1;
                        prevTerm = '2';
                    } else {
                        prevYear1 = baseYear;
                        prevYear2 = baseYear + 1;
                        prevTerm = '1';
                    }
                    
                    const prevTermValue = `${prevYear1}-${prevYear2}-${prevTerm}`;
                    const prevOption = document.createElement('option');
                    prevOption.value = prevTermValue;
                    prevOption.textContent = prevTermValue;
                    xnxqhSelect.appendChild(prevOption);
                }
                
                // 后两个学期
                for (let i = 1; i <= 2; i++) {
                    let nextYear1, nextYear2, nextTerm;
                    
                    if (term === '1') {
                        nextYear1 = baseYear;
                        nextYear2 = baseYear + 1;
                        nextTerm = '2';
                    } else {
                        nextYear1 = baseYear + i;
                        nextYear2 = baseYear + i + 1;
                        nextTerm = '1';
                    }
                    
                    const nextTermValue = `${nextYear1}-${nextYear2}-${nextTerm}`;
                    const nextOption = document.createElement('option');
                    nextOption.value = nextTermValue;
                    nextOption.textContent = nextTermValue;
                    xnxqhSelect.appendChild(nextOption);
                }
            }
        })
        .catch(error => {
            console.error('获取当前学期失败:', error);
        });
}

// 检查登录状态
function checkLoginStatus() {
    // 这里可以添加检查登录状态的逻辑
    // 如果已登录，显示用户信息区域，隐藏登录区域
    // 如果未登录，显示登录区域，隐藏用户信息区域
}

// 显示消息
function showMessage(containerId, message, type) {
    const container = document.getElementById(containerId);
    container.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
} 