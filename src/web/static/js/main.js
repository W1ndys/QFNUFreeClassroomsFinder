// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化页面
    initPage();
    
    // 绑定事件
    bindEvents();
    
    // 初始化广告/宣传区域
    initAnnouncements();
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
    fetchCurrentTerm()
        .then(term => {
            // 获取当前周次和星期
            fetchCurrentWeekDay(term);
        });
    
    // 获取教学楼列表
    fetchBuildings();
    
    // 检查登录状态
    checkLoginStatus();
}

// 获取教学楼列表
function fetchBuildings() {
    fetch('/api/classrooms')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const buildingSelect = document.getElementById('free-building');
                
                // 清空现有选项（保留提示选项）
                const defaultOption = buildingSelect.querySelector('option[value=""]');
                buildingSelect.innerHTML = '';
                buildingSelect.appendChild(defaultOption);
                
                // 添加教学楼选项
                const buildings = Object.keys(data.data).sort((a, b) => {
                    // 将纯字母的教学楼排在前面
                    const aIsLetter = /^[A-Za-z]+$/.test(a);
                    const bIsLetter = /^[A-Za-z]+$/.test(b);
                    if (aIsLetter && !bIsLetter) return -1;
                    if (!aIsLetter && bIsLetter) return 1;
                    return a.localeCompare(b);
                });
                
                buildings.forEach(building => {
                    const option = document.createElement('option');
                    option.value = building;
                    // 获取该教学楼的教室数量
                    const roomCount = data.data[building].length;
                    option.textContent = `${building}楼 (${roomCount}间)`;
                    buildingSelect.appendChild(option);
                });
            }
        })
        .catch(error => {
            console.error('获取教学楼列表失败:', error);
        });
}

// 获取当前学期
function fetchCurrentTerm() {
    return fetch('/get_current_term')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const xnxqhSelect = document.getElementById('xnxqh');
                
                // 清空现有选项
                xnxqhSelect.innerHTML = '';
                
                // 生成学期列表（前后各两个学期）
                const [year1, year2, term] = data.current_term.split('-');
                const baseYear = parseInt(year1);
                
                // 创建学期列表数组
                let termsList = [];
                
                // 添加当前学期
                termsList.push({
                    value: data.current_term,
                    text: `${data.current_term} (当前学期)`,
                    isCurrent: true,
                    sortKey: `${year1}-${year2}-${term}`
                });
                
                // 前两个学期
                for (let i = 1; i <= 2; i++) {
                    let prevYear1, prevYear2, prevTerm;
                    
                    if (term === '1') {
                        prevYear1 = baseYear - Math.ceil(i/2);
                        prevYear2 = baseYear - Math.ceil(i/2) + 1;
                        prevTerm = i % 2 === 0 ? '1' : '2';
                    } else {
                        prevYear1 = baseYear - Math.ceil(i/2);
                        prevYear2 = baseYear - Math.ceil(i/2) + 1;
                        prevTerm = i % 2 === 1 ? '1' : '2';
                    }
                    
                    const prevTermValue = `${prevYear1}-${prevYear2}-${prevTerm}`;
                    termsList.push({
                        value: prevTermValue,
                        text: prevTermValue,
                        isCurrent: false,
                        sortKey: `${prevYear1}-${prevYear2}-${prevTerm}`
                    });
                }
                
                // 后两个学期
                for (let i = 1; i <= 2; i++) {
                    let nextYear1, nextYear2, nextTerm;
                    
                    if (term === '1') {
                        nextYear1 = baseYear + Math.floor(i/2);
                        nextYear2 = baseYear + Math.floor(i/2) + 1;
                        nextTerm = i % 2 === 1 ? '2' : '1';
                    } else {
                        nextYear1 = baseYear + Math.ceil(i/2);
                        nextYear2 = baseYear + Math.ceil(i/2) + 1;
                        nextTerm = i % 2 === 1 ? '1' : '2';
                    }
                    
                    const nextTermValue = `${nextYear1}-${nextYear2}-${nextTerm}`;
                    termsList.push({
                        value: nextTermValue,
                        text: nextTermValue,
                        isCurrent: false,
                        sortKey: `${nextYear1}-${nextYear2}-${nextTerm}`
                    });
                }
                
                // 按时间顺序排序（从早到晚）
                termsList.sort((a, b) => a.sortKey.localeCompare(b.sortKey));
                
                // 将排序后的学期添加到下拉框
                termsList.forEach(termItem => {
                    const option = document.createElement('option');
                    option.value = termItem.value;
                    option.textContent = termItem.text;
                    option.selected = termItem.isCurrent;
                    xnxqhSelect.appendChild(option);
                });
                
                // 立即获取当前周次和星期
                fetchCurrentWeekDay(data.current_term);
                
                return data.current_term;
            }
            return null;
        })
        .catch(error => {
            console.error('获取当前学期失败:', error);
            return null;
        });
}

// 获取当前周次和星期
function fetchCurrentWeekDay(term) {
    if (!term) return;
    
    fetch(`/get_current_week_day?term=${term}`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // 设置当前周次
                const weekSelect = document.getElementById('week');
                if (weekSelect && data.current_week) {
                    weekSelect.value = data.current_week;
                }
                
                // 设置当前星期
                const daySelect = document.getElementById('day');
                if (daySelect && data.current_day) {
                    daySelect.value = data.current_day;
                }
                
                // 显示当前周次和星期的提示
                const weekInfo = document.getElementById('week-info');
                const weekDayInfo = document.getElementById('week-day-info');
                if (weekInfo) {
                    weekInfo.style.display = 'block';
                }
                if (weekDayInfo) {
                    weekDayInfo.textContent = `当前是第${data.current_week}周，星期${getDayName(data.current_day)}`;
                }
            }
        })
        .catch(error => {
            console.error('获取当前周次和星期失败:', error);
        });
}

// 获取星期几的名称
function getDayName(day) {
    const dayNames = ['一', '二', '三', '四', '五', '六', '日'];
    return dayNames[day - 1] || '';
}

// 初始化广告/宣传区域
function initAnnouncements() {
    // 顶部公告关闭按钮
    const closeAnnouncementBtn = document.getElementById('close-announcement');
    if (closeAnnouncementBtn) {
        closeAnnouncementBtn.addEventListener('click', function() {
            const announcementCard = document.getElementById('announcement-card');
            announcementCard.style.display = 'none';
            
            // 记住用户关闭了公告
            localStorage.setItem('announcement_closed', 'true');
        });
    }
    
    // 从本地存储中检查是否已关闭过公告
    if (localStorage.getItem('announcement_closed') === 'true') {
        const announcementCard = document.getElementById('announcement-card');
        if (announcementCard) {
            announcementCard.style.display = 'none';
        }
    }
    
    // 加载广告内容
    loadAnnouncementContent();
}

// 加载广告/宣传内容
function loadAnnouncementContent() {
    // 从服务器获取最新的广告/宣传内容
    fetch('/api/announcements')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // 更新顶部公告
                const topAnnouncement = data.data.top;
                if (topAnnouncement) {
                    const announcementCard = document.getElementById('announcement-card');
                    const announcementContent = document.getElementById('announcement-content');
                    
                    if (announcementCard && announcementContent) {
                        // 更新标题
                        const headerTitle = announcementCard.querySelector('.card-header h5');
                        if (headerTitle) {
                            headerTitle.textContent = topAnnouncement.title;
                        }
                        
                        // 更新内容
                        announcementContent.innerHTML = topAnnouncement.content;
                    }
                }
                
                // 更新底部广告
                const bottomAd = data.data.bottom;
                if (bottomAd) {
                    const bottomAdCard = document.getElementById('bottom-ad-card');
                    const bottomAdContent = document.getElementById('bottom-ad-content');
                    
                    if (bottomAdCard && bottomAdContent) {
                        // 更新标题
                        const headerTitle = bottomAdCard.querySelector('.card-header h5');
                        if (headerTitle) {
                            headerTitle.textContent = bottomAd.title;
                        }
                        
                        // 更新内容
                        bottomAdContent.innerHTML = bottomAd.content;
                    }
                }
            }
        })
        .catch(error => {
            console.error('获取公告内容失败:', error);
        });
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
    
    // 空闲教室查询表单提交
    document.getElementById('free-classroom-form').addEventListener('submit', function(e) {
        e.preventDefault();
        handleFreeClassroomQuery();
    });
    
    // 学期选择变化时，重新获取当前周次和星期
    const xnxqhSelect = document.getElementById('xnxqh');
    if (xnxqhSelect) {
        xnxqhSelect.addEventListener('change', function() {
            fetchCurrentWeekDay(this.value);
        });
    }
}

// 处理空闲教室查询
function handleFreeClassroomQuery() {
    const xnxqh = document.getElementById('xnxqh').value;
    const week = document.getElementById('week').value;
    const day = document.getElementById('day').value || document.getElementById('day').options[1].value; // 如果未选择，默认为周一
    const buildingPrefix = document.getElementById('free-building').value;
    
    // 检查是否选择了教学楼
    if (!buildingPrefix) {
        showMessage('free-classroom-container', '请选择教学楼', 'warning');
        return;
    }
    
    // 获取选中的时间段
    const selectedPeriods = [];
    for (let i = 1; i <= 6; i++) {
        const checkbox = document.getElementById(`period${i}`);
        if (checkbox && checkbox.checked) {
            selectedPeriods.push(checkbox.value);
        }
    }
    
    // 显示/隐藏警告信息
    const periodWarning = document.getElementById('period-warning');
    if (selectedPeriods.length === 0) {
        periodWarning.style.display = 'block';
        return;
    } else {
        periodWarning.style.display = 'none';
    }
    
    if (!xnxqh || !week || !day) {
        showMessage('free-classroom-container', '请填写完整的查询信息', 'warning');
        return;
    }
    
    // 显示加载状态
    const freeClassroomBtn = document.getElementById('free-classroom-btn');
    const originalBtnText = freeClassroomBtn.textContent;
    freeClassroomBtn.textContent = '查询中...';
    freeClassroomBtn.disabled = true;
    
    // 显示结果区域
    const freeClassroomSection = document.getElementById('free-classroom-section');
    freeClassroomSection.classList.remove('d-none');
    
    // 清空结果容器并显示加载提示
    const freeClassroomContainer = document.getElementById('free-classroom-container');
    freeClassroomContainer.innerHTML = '<div class="text-center"><div class="spinner-border text-primary" role="status"></div><p class="mt-2">正在查询空闲教室，请稍候...</p></div>';
    
    // 隐藏普通查询结果区域
    document.getElementById('result-section').classList.add('d-none');
    
    // 发送查询请求
    fetch('/api/free_classrooms', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            xnxqh: xnxqh,
            week: week,
            day: day,
            periods: selectedPeriods,
            building_prefix: buildingPrefix
        })
    })
    .then(response => {
        if (response.status === 401) {
            // 未登录，显示错误并滚动到登录区域
            showMessage('free-classroom-container', '您尚未登录或登录已过期，请先登录', 'danger');
            document.getElementById('login-section').scrollIntoView({ behavior: 'smooth' });
            throw new Error('未登录');
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            // 渲染空闲教室结果
            renderFreeClassrooms(data, selectedPeriods, day);
        } else {
            showMessage('free-classroom-container', '查询失败: ' + data.message, 'danger');
        }
    })
    .catch(error => {
        if (error.message !== '未登录') {
            showMessage('free-classroom-container', '查询请求出错: ' + error, 'danger');
        }
    })
    .finally(() => {
        // 恢复按钮状态
        freeClassroomBtn.textContent = originalBtnText;
        freeClassroomBtn.disabled = false;
    });
}

// 渲染空闲教室结果
function renderFreeClassrooms(data, periods, day) {
    const freeClassroomContainer = document.getElementById('free-classroom-container');
    const freeClassrooms = data.free_classrooms;
    const occupiedClassrooms = data.occupied_classrooms;
    
    // 获取星期几的名称
    const dayName = getDayName(day);
    
    // 计算总空闲教室数量
    let totalFreeCount = 0;
    Object.values(freeClassrooms).forEach(rooms => {
        totalFreeCount += rooms.length;
    });
    
    // 如果没有数据
    if (totalFreeCount === 0) {
        freeClassroomContainer.innerHTML = `<div class="alert alert-info">未找到在选定时间段都空闲的教室</div>`;
        return;
    }
    
    // 格式化时间段显示
    const periodsText = periods.join('、');
    
    let html = `
        <div class="alert alert-success">
            查询成功！星期${dayName}的 ${periodsText} 时间段内共找到 <strong>${totalFreeCount}</strong> 个空闲教室
        </div>
        <div class="row">
            <div class="col-12">
                <div class="card mb-4">
                    <div class="card-header bg-success text-white">
                        <h5 class="mb-0">空闲教室列表</h5>
                    </div>
                    <div class="card-body">
    `;
    
    // 按建筑物分组显示空闲教室
    const buildings = Object.keys(freeClassrooms).sort();
    
    buildings.forEach(building => {
        const rooms = freeClassrooms[building];
        if (rooms.length > 0) {
            html += `
                <div class="building-section">
                    <div class="building-title">
                        ${building}楼
                        <span class="free-classroom-highlight">空闲 ${rooms.length} 间</span>
                    </div>
                    <div class="classroom-list">
            `;
            
            // 添加空闲教室
            rooms.sort().forEach(room => {
                html += `<div class="classroom-item free-classroom" onclick="selectClassroom('${room}')">${room}</div>`;
            });
            
            html += `
                    </div>
                </div>
            `;
        }
    });
    
    html += `
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // 添加有课教室部分（折叠起来）
    let totalOccupiedCount = 0;
    Object.values(occupiedClassrooms).forEach(rooms => {
        totalOccupiedCount += rooms.length;
    });
    
    if (totalOccupiedCount > 0) {
        html += `
            <div class="row">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header bg-light">
                            <button class="btn btn-link collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#occupiedClassrooms" aria-expanded="false" aria-controls="occupiedClassrooms">
                                显示有课教室 (${totalOccupiedCount} 间)
                            </button>
                        </div>
                        <div id="occupiedClassrooms" class="collapse">
                            <div class="card-body">
        `;
        
        // 按建筑物分组显示有课教室
        buildings.forEach(building => {
            const rooms = occupiedClassrooms[building];
            if (rooms && rooms.length > 0) {
                html += `
                    <div class="building-section">
                        <div class="building-title">
                            ${building}楼
                            <span class="classroom-count">有课 ${rooms.length} 间</span>
                        </div>
                        <div class="classroom-list">
                `;
                
                // 添加有课教室
                rooms.sort().forEach(room => {
                    html += `<div class="classroom-item occupied-classroom" onclick="selectClassroom('${room}')">${room}</div>`;
                });
                
                html += `
                        </div>
                    </div>
                `;
            }
        });
        
        html += `
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    freeClassroomContainer.innerHTML = html;
}

// 选择教室并填充到查询表单
function selectClassroom(roomName) {
    document.getElementById('room_name').value = roomName;
    document.getElementById('query-btn').click();
    
    // 滚动到查询结果
    document.getElementById('result-section').scrollIntoView({ behavior: 'smooth' });
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
            document.getElementById('free-classroom-section').classList.add('d-none');
            
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
    
    // 隐藏空闲教室结果区域
    document.getElementById('free-classroom-section').classList.add('d-none');
    
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