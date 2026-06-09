<<<<<<< HEAD
// CTMS 核心应用逻辑
const CTMS = {
  currentPage: 'dashboard',
  currentTrial: null,
  sidebarCollapsed: false,

  init() {
    this.renderSidebar();
    this.renderHeader();
    this.navigate('dashboard');
    this.initDropdowns();
  },


  formatDateTime(dateStr) {
    if (!dateStr) return '-';
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    const pad = n => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
  },

  getPhaseName(val) {
    const mapping = {
      '8': 'I期', '9': 'II期', '10': 'III期', '11': 'IV期', '12': '上市后临床研究',
      '1': '药物临床试验', '2': '中保研究', '3': '医疗器械临床试验', '4': '科研项目其他',
      '5': '药物上市后再评价', '6': '医疗器械上市后再评价', '7': '其他'
    };
    return mapping[String(val)] || val || '-';
  },

  navigate(page, params = {}) {
    this.currentPage = page;
    this.currentTrial = params.trialId || null;
    document.querySelectorAll('.nav-item, .nav-sub-item').forEach(el => el.classList.remove('active'));
    const navEl = document.querySelector(`[data-page="${page}"]`);
    if (navEl) navEl.classList.add('active');
    document.getElementById('main-content').innerHTML = '';
    const fn = PAGES[page];
    if (fn) fn(params);
    else document.getElementById('main-content').innerHTML = `<div class="empty-state"><div class="empty-icon">🚧</div><p>页面建设中...</p></div>`;
    // 更新面包屑
    document.getElementById('breadcrumb').textContent = NAV_MAP[page] || page;
    document.getElementById('page-title').textContent = NAV_MAP[page] || '临床试验管理系统';
  },

  renderSidebar() {
    document.getElementById('sidebar').innerHTML = `
      <div class="sidebar-logo" onclick="CTMS.toggleSidebar()">
        <div class="logo-icon">🧬</div>
        <div>
          <div class="logo-text">CTMS Pro</div>
          <div class="logo-sub">临床试验管理平台</div>
        </div>
      </div>
      <div class="nav-section">
        <div class="nav-section-title">工作台</div>
        <div class="nav-item" data-page="dashboard" onclick="CTMS.navigate('dashboard')">
          <span class="nav-icon">📊</span><span class="nav-label">数据概览</span>
        </div>
        <div class="nav-item" data-page="workbench" onclick="CTMS.navigate('workbench')">
          <span class="nav-icon">🗂️</span><span class="nav-label">我的工作台</span>
        </div>
      </div>
      <div class="nav-section">
        <div class="nav-section-title">试验管理</div>
        <div class="nav-item" data-page="trials" onclick="CTMS.navigate('trials')">
          <span class="nav-icon">🔬</span><span class="nav-label">我的试验</span>
        </div>
        <div class="nav-item" data-page="trial-startup" onclick="CTMS.navigate('trial-startup')">
          <span class="nav-icon">🚀</span><span class="nav-label">项目启动</span>
        </div>
        <div class="nav-item" data-page="milestone" onclick="CTMS.navigate('milestone')">
          <span class="nav-icon">🎯</span><span class="nav-label">里程碑管理</span>
        </div>
        <div class="nav-item" data-page="meetings" onclick="CTMS.navigate('meetings')">
          <span class="nav-icon">📋</span><span class="nav-label">会议安排</span>
        </div>
      </div>
      <div class="nav-section">
        <div class="nav-section-title">随机化与分配</div>
        <div class="nav-item" data-page="iwrs" onclick="CTMS.navigate('iwrs')">
          <span class="nav-icon">🎲</span><span class="nav-label">随机化系统(IWRS)</span>
        </div>
      </div>
      <div class="nav-section">
        <div class="nav-section-title">患者管理</div>
        <div class="nav-item" data-page="patients" onclick="CTMS.navigate('patients')">
          <span class="nav-icon">👥</span><span class="nav-label">受试者管理</span>
        </div>
        <div class="nav-item" data-page="icf" onclick="CTMS.navigate('icf')">
          <span class="nav-icon">✍️</span><span class="nav-label">电子知情同意</span>
        </div>
        <div class="nav-item" data-page="visits" onclick="CTMS.navigate('visits')">
          <span class="nav-icon">🏥</span><span class="nav-label">访视管理</span>
        </div>
        <div class="nav-item" data-page="sae" onclick="CTMS.navigate('sae')">
          <span class="nav-icon">⚠️</span><span class="nav-label">SAE管理</span>
        </div>
      </div>
      <div class="nav-section">
        <div class="nav-section-title">物资与药品</div>
        <div class="nav-item" data-page="drug-inbound" onclick="CTMS.navigate('drug-inbound')">
          <span class="nav-icon">📦</span><span class="nav-label">药品入库</span>
        </div>
        <div class="nav-item" data-page="drug-dispatch" onclick="CTMS.navigate('drug-dispatch')">
          <span class="nav-icon">💊</span><span class="nav-label">药品发放</span>
        </div>
        <div class="nav-item" data-page="drug-recover" onclick="CTMS.navigate('drug-recover')">
          <span class="nav-icon">♻️</span><span class="nav-label">回收销毁</span>
        </div>
      </div>
      <div class="nav-section">
        <div class="nav-section-title">经费管理</div>
        <div class="nav-item" data-page="contracts" onclick="CTMS.navigate('contracts')">
          <span class="nav-icon">🤝</span><span class="nav-label">合同管理</span>
        </div>
        <div class="nav-item" data-page="invoice" onclick="CTMS.navigate('invoice')">
          <span class="nav-icon">🧾</span><span class="nav-label">开票进度</span>
        </div>
      </div>
      <!--
      <div class="nav-section">
        <div class="nav-section-title">质控&合规</div>
        <div class="nav-item" data-page="qc" onclick="CTMS.navigate('qc')">
          <span class="nav-icon">✅</span><span class="nav-label">质量控制</span>
        </div>
        <div class="nav-item" data-page="etmf" onclick="CTMS.navigate('etmf')">
          <span class="nav-icon">🗄️</span><span class="nav-label">eTMF文档</span>
        </div>
        <div class="nav-item" data-page="audit-trail" onclick="CTMS.navigate('audit-trail')">
          <span class="nav-icon">🔐</span><span class="nav-label">稽查痕迹</span>
        </div>
      </div>
      -->
      <div class="nav-section">
        <div class="nav-section-title">统计报表</div>
        <div class="nav-item" data-page="reports" onclick="CTMS.navigate('reports')">
          <span class="nav-icon">📈</span><span class="nav-label">统计报表</span>
        </div>
        <div class="nav-item" data-page="risk-dashboard" onclick="CTMS.navigate('risk-dashboard')">
          <span class="nav-icon">🎛️</span><span class="nav-label">风险仪表盘</span>
        </div>
      </div>
      <div class="nav-section">
        <div class="nav-section-title">系统管理</div>
        <div class="nav-item" data-page="centers" onclick="CTMS.navigate('centers')">
          <span class="nav-icon">🏢</span><span class="nav-label">中心管理</span>
        </div>
        <div class="nav-item" data-page="users" onclick="CTMS.navigate('users')">
          <span class="nav-icon">👤</span><span class="nav-label">人员管理</span>
        </div>
        <div class="nav-item" data-page="timesheet" onclick="CTMS.navigate('timesheet')">
          <span class="nav-icon">⏳</span><span class="nav-label">填写工时</span>
        </div>
        <div class="nav-item" data-page="settings" onclick="CTMS.navigate('settings')">
          <span class="nav-icon">⚙️</span><span class="nav-label">系统设置</span>
        </div>
      </div>
    `;
  },

  renderHeader() {
    document.getElementById('header').innerHTML = `
      <button class="btn-icon" onclick="CTMS.toggleSidebar()" title="折叠菜单">☰</button>
      <div>
        <div id="page-title" class="header-title">数据概览</div>
        <div id="breadcrumb" class="header-breadcrumb text-muted" style="font-size:11px">工作台 / 数据概览</div>
      </div>
      <div style="flex:1"></div>
      <div class="header-actions">
        <div class="dropdown" style="position:relative">
          <button class="header-btn" onclick="this.closest('.dropdown').querySelector('.notif-panel').classList.toggle('show')" title="消息通知">
            🔔
          </button>
          <div class="notif-panel">
            <div class="notif-header"><span>通知消息</span><span class="text-primary" style="font-size:12px;cursor:pointer">全部已读</span></div>
            ${CTMS_DATA.announcements.map(a => `
              <div class="notif-item ${a.read ? '' : 'unread'}">
                <div class="notif-dot" style="${a.read ? 'background:var(--gray-300)' : ''}"></div>
                <div><div class="notif-text">${a.title}</div><div class="notif-time">${a.time}</div></div>
              </div>
            `).join('')}
          </div>
        </div>
        <button class="header-btn" title="全屏">⊞</button>
        <div class="dropdown">
          <div class="user-avatar" onclick="this.closest('.dropdown').querySelector('.dropdown-menu').classList.toggle('show')" title="${CTMS_DATA.currentUser.name}">${CTMS_DATA.currentUser.avatar}</div>
          <div class="dropdown-menu">
            <div class="dropdown-item" onclick="CTMS.showProfileModal()">👤 个人信息</div>
            <div class="dropdown-item" onclick="CTMS.showChangePasswordModal()">🔑 修改密码</div>
            <div class="dropdown-divider"></div>
            <div class="dropdown-item" onclick="CTMS.logout()">🚪 退出登录</div>
          </div>
        </div>
      </div>
    `;
  },

  toggleSidebar() {
    this.sidebarCollapsed = !this.sidebarCollapsed;
    document.getElementById('sidebar').classList.toggle('collapsed', this.sidebarCollapsed);
  },

  initDropdowns() {
    document.addEventListener('click', e => {
      if (!e.target.closest('.dropdown')) document.querySelectorAll('.dropdown-menu, .notif-panel').forEach(el => el.classList.remove('show'));
    });
  },

  async logout() {
    try {
      if (window.CTMS_API) await CTMS_API.Auth.logout();
    } catch (e) {}
    if (window.CTMS_API) CTMS_API.Token.clearTokens();
    document.getElementById('app').innerHTML = '';
    document.getElementById('app').innerHTML = `<div id="login-screen"></div>`;
    renderLogin();
  },

  showModal(title, contentHTML, footerHTML = '') {
    const el = document.createElement('div');
    el.className = 'modal-overlay';
    el.id = 'ctms-modal';
    el.innerHTML = `
      <div class="modal modal-lg">
        <div class="modal-header">
          <span class="modal-title">${title}</span>
          <button class="modal-close" onclick="CTMS.closeModal()">✕</button>
        </div>
        <div class="modal-body">${contentHTML}</div>
        ${footerHTML ? `<div class="modal-footer">${footerHTML}</div>` : ''}
      </div>
    `;
    el.addEventListener('click', e => { if (e.target === el) this.closeModal(); });
    document.body.appendChild(el);
  },

  closeModal(id) {
    if (id && typeof id === 'string') {
      // 如果指定了ID，只关闭特定的模态框
      const modal = document.getElementById(id);
      if (modal) {
        if (modal.classList.contains('modal-overlay')) {
          modal.remove();
        } else {
          modal.classList.remove('active');
        }
      }
    } else {
      // 如果没有指定ID，关闭所有活动的模态框
      const overlays = document.querySelectorAll('.modal-overlay');
      overlays.forEach(el => el.remove());
      
      const modals = document.querySelectorAll('.modal.active');
      modals.forEach(modal => {
        modal.classList.remove('active');
      });
    }
  },

  showProfileModal() {
    const user = (window.CTMS_API && CTMS_API.Token.getCurrentUser()) || CTMS_DATA.currentUser;
    const userName = user.full_name || user.name || '未知用户';
    const email = user.email || '暂无邮箱';
    const phone = user.phone || '暂无手机号';
    const org = user.organization_id ? `机构ID: ${user.organization_id}` : '未绑定机构';
    const role = user.role || '用户';

    const html = `
      <div style="padding:10px">
        <div style="display:flex; align-items:center; gap:20px; margin-bottom:20px">
          <div style="width:80px;height:80px;border-radius:50%;background:var(--primary);color:#fff;display:flex;align-items:center;justify-content:center;font-size:36px">
            ${userName.substring(0,1).toUpperCase()}
          </div>
          <div>
            <h3 style="margin:0 0 5px 0;font-size:20px">${userName}</h3>
            <span class="badge badge-blue">${role}</span>
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">手机号</label>
          <input type="text" class="form-input" value="${phone}" readonly disabled style="background:var(--gray-50)">
        </div>
        <div class="form-group">
          <label class="form-label">登录账号 (邮箱)</label>
          <input type="text" class="form-input" value="${email}" readonly disabled style="background:var(--gray-50)">
        </div>
        <div class="form-group">
          <label class="form-label">所属机构 / 中心</label>
          <input type="text" class="form-input" value="${org}" readonly disabled style="background:var(--gray-50)">
        </div>
      </div>
    `;
    this.showModal('个人信息', html, '<button class="btn btn-primary" onclick="CTMS.closeModal()">关闭</button>');
  },

  showChangePasswordModal() {
    const html = `
      <div class="form-group">
        <label class="form-label required">原密码</label>
        <input type="password" id="cp-old" class="form-input" placeholder="输入当前密码">
      </div>
      <div class="form-group">
        <label class="form-label required">新密码</label>
        <input type="password" id="cp-new" class="form-input" placeholder="输入新密码">
      </div>
      <div class="form-group">
        <label class="form-label required">确认新密码</label>
        <input type="password" id="cp-confirm" class="form-input" placeholder="再次输入新密码">
      </div>
    `;
    const footer = `
      <button class="btn btn-secondary" onclick="CTMS.closeModal()">取消</button>
      <button class="btn btn-primary" onclick="CTMS.submitChangePassword()">确认修改</button>
    `;
    this.showModal('修改密码', html, footer);
  },

  async submitChangePassword() {
    const oldP = document.getElementById('cp-old').value;
    const newP = document.getElementById('cp-new').value;
    const confP = document.getElementById('cp-confirm').value;

    if(!oldP || !newP || !confP) return this.showToast('请填写完整信息', 'error');
    if(newP !== confP) return this.showToast('两次输入的新密码不一致', 'error');
    if(newP.length < 6) return this.showToast('新密码长度不能少于6位', 'error');

    try {
      // 模拟调用修改密码 API
      if (window.API && window.API.users && window.API.users.changePassword) {
         // await window.API.users.changePassword({old_password: oldP, new_password: newP});
      }
      this.showToast('密码修改成功，请妥善保管新密码！', 'success');
      this.closeModal();
    } catch (e) {
      this.showToast(e.message || '密码修改失败', 'error');
    }
  },

  showToast(msg, type = 'success') {
    const el = document.createElement('div');
    el.style.cssText = `position:fixed;top:20px;right:20px;background:${type==='success'?'#22c55e':type==='error'?'#ef4444':'#3b82f6'};color:#fff;padding:12px 20px;border-radius:8px;z-index:9999;font-size:13px;box-shadow:0 4px 12px rgba(0,0,0,0.2);animation:fadeIn 0.2s ease`;
    el.textContent = msg;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 2800);
  },

  formatDate(dateStr) {
    if (!dateStr) return '-';
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return String(dateStr).substring(0, 10); // fallback
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  },

  formatDateTime(dateStr) {
    if (!dateStr) return '-';
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return String(dateStr).replace('T', ' ').substring(0, 19); // fallback
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const h = String(d.getHours()).padStart(2, '0');
    const min = String(d.getMinutes()).padStart(2, '0');
    const s = String(d.getSeconds()).padStart(2, '0');
    return `${y}-${m}-${day} ${h}:${min}:${s}`;
  }
};

window.CTMS = CTMS;

const NAV_MAP = {
  dashboard: '数据概览', workbench: '我的工作台', schedule: '日程任务', trials: '我的试验',
  'trial-startup': '项目启动', milestone: '里程碑管理', meetings: '会议安排',
  patients: '受试者管理', screening: '患者筛选', icf: '电子知情同意', visits: '访视管理', sae: 'SAE管理',
  'drug-inbound': '药品入库', 'drug-dispatch': '药品发放', 'drug-inventory': '库存管理', 'drug-recover': '回收销毁',
  contracts: '合同管理', budget: '预算费控', invoice: '开票进度',
  qc: '质量控制', etmf: 'eTMF文档', 'audit-trail': '稽查痕迹',
  reports: '统计报表', 'risk-dashboard': '风险仪表盘',
  centers: '中心管理', users: '人员管理', timesheet: '填写工时', settings: '系统设置',
  'trial-detail': '试验详情', 'patient-detail': '受试者详情'
};
=======
// CTMS 核心应用逻辑
const CTMS = {
  currentPage: 'dashboard',
  currentTrial: null,
  sidebarCollapsed: false,

  init() {
    this.renderSidebar();
    this.renderHeader();
    this.navigate('dashboard');
    this.initDropdowns();
  },


  formatDateTime(dateStr) {
    if (!dateStr) return '-';
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    const pad = n => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
  },

  navigate(page, params = {}) {
    this.currentPage = page;
    this.currentTrial = params.trialId || null;
    document.querySelectorAll('.nav-item, .nav-sub-item').forEach(el => el.classList.remove('active'));
    const navEl = document.querySelector(`[data-page="${page}"]`);
    if (navEl) navEl.classList.add('active');
    document.getElementById('main-content').innerHTML = '';
    const fn = PAGES[page];
    if (fn) fn(params);
    else document.getElementById('main-content').innerHTML = `<div class="empty-state"><div class="empty-icon">🚧</div><p>页面建设中...</p></div>`;
    // 更新面包屑
    document.getElementById('breadcrumb').textContent = NAV_MAP[page] || page;
    document.getElementById('page-title').textContent = NAV_MAP[page] || '临床试验管理系统';
  },

  renderSidebar() {
    document.getElementById('sidebar').innerHTML = `
      <div class="sidebar-logo" onclick="CTMS.toggleSidebar()">
        <div class="logo-icon">🧬</div>
        <div>
          <div class="logo-text">CTMS Pro</div>
          <div class="logo-sub">临床试验管理平台</div>
        </div>
      </div>
      <div class="nav-section">
        <div class="nav-section-title">工作台</div>
        <div class="nav-item" data-page="dashboard" onclick="CTMS.navigate('dashboard')">
          <span class="nav-icon">📊</span><span class="nav-label">数据概览</span>
        </div>
        <div class="nav-item" data-page="workbench" onclick="CTMS.navigate('workbench')">
          <span class="nav-icon">🗂️</span><span class="nav-label">我的工作台</span>
        </div>
      </div>
      <div class="nav-section">
        <div class="nav-section-title">试验管理</div>
        <div class="nav-item" data-page="trials" onclick="CTMS.navigate('trials')">
          <span class="nav-icon">🔬</span><span class="nav-label">我的试验</span>
        </div>
        <div class="nav-item" data-page="trial-startup" onclick="CTMS.navigate('trial-startup')">
          <span class="nav-icon">🚀</span><span class="nav-label">项目启动</span>
        </div>
        <div class="nav-item" data-page="milestone" onclick="CTMS.navigate('milestone')">
          <span class="nav-icon">🎯</span><span class="nav-label">里程碑管理</span>
        </div>
        <div class="nav-item" data-page="meetings" onclick="CTMS.navigate('meetings')">
          <span class="nav-icon">📋</span><span class="nav-label">会议安排</span>
        </div>
      </div>
      <div class="nav-section">
        <div class="nav-section-title">随机化与分配</div>
        <div class="nav-item" data-page="iwrs" onclick="CTMS.navigate('iwrs')">
          <span class="nav-icon">🎲</span><span class="nav-label">随机化系统(IWRS)</span>
        </div>
      </div>
      <div class="nav-section">
        <div class="nav-section-title">患者管理</div>
        <div class="nav-item" data-page="patients" onclick="CTMS.navigate('patients')">
          <span class="nav-icon">👥</span><span class="nav-label">受试者管理</span>
        </div>
        <div class="nav-item" data-page="icf" onclick="CTMS.navigate('icf')">
          <span class="nav-icon">✍️</span><span class="nav-label">电子知情同意</span>
        </div>
        <div class="nav-item" data-page="visits" onclick="CTMS.navigate('visits')">
          <span class="nav-icon">🏥</span><span class="nav-label">访视管理</span>
        </div>
        <div class="nav-item" data-page="sae" onclick="CTMS.navigate('sae')">
          <span class="nav-icon">⚠️</span><span class="nav-label">SAE管理</span>
        </div>
      </div>
      <div class="nav-section">
        <div class="nav-section-title">物资与药品</div>
        <div class="nav-item" data-page="drug-inbound" onclick="CTMS.navigate('drug-inbound')">
          <span class="nav-icon">📦</span><span class="nav-label">药品入库</span>
        </div>
        <div class="nav-item" data-page="drug-dispatch" onclick="CTMS.navigate('drug-dispatch')">
          <span class="nav-icon">💊</span><span class="nav-label">药品发放</span>
        </div>
        <div class="nav-item" data-page="drug-recover" onclick="CTMS.navigate('drug-recover')">
          <span class="nav-icon">♻️</span><span class="nav-label">回收销毁</span>
        </div>
      </div>
      <div class="nav-section">
        <div class="nav-section-title">经费管理</div>
        <div class="nav-item" data-page="contracts" onclick="CTMS.navigate('contracts')">
          <span class="nav-icon">🤝</span><span class="nav-label">合同管理</span>
        </div>
        <div class="nav-item" data-page="invoice" onclick="CTMS.navigate('invoice')">
          <span class="nav-icon">🧾</span><span class="nav-label">开票进度</span>
        </div>
      </div>
      <!--
      <div class="nav-section">
        <div class="nav-section-title">质控&合规</div>
        <div class="nav-item" data-page="qc" onclick="CTMS.navigate('qc')">
          <span class="nav-icon">✅</span><span class="nav-label">质量控制</span>
        </div>
        <div class="nav-item" data-page="etmf" onclick="CTMS.navigate('etmf')">
          <span class="nav-icon">🗄️</span><span class="nav-label">eTMF文档</span>
        </div>
        <div class="nav-item" data-page="audit-trail" onclick="CTMS.navigate('audit-trail')">
          <span class="nav-icon">🔐</span><span class="nav-label">稽查痕迹</span>
        </div>
      </div>
      -->
      <div class="nav-section">
        <div class="nav-section-title">统计报表</div>
        <div class="nav-item" data-page="reports" onclick="CTMS.navigate('reports')">
          <span class="nav-icon">📈</span><span class="nav-label">统计报表</span>
        </div>
        <div class="nav-item" data-page="risk-dashboard" onclick="CTMS.navigate('risk-dashboard')">
          <span class="nav-icon">🎛️</span><span class="nav-label">风险仪表盘</span>
        </div>
      </div>
      <div class="nav-section">
        <div class="nav-section-title">系统管理</div>
        <div class="nav-item" data-page="centers" onclick="CTMS.navigate('centers')">
          <span class="nav-icon">🏢</span><span class="nav-label">中心管理</span>
        </div>
        <div class="nav-item" data-page="users" onclick="CTMS.navigate('users')">
          <span class="nav-icon">👤</span><span class="nav-label">人员管理</span>
        </div>
        <div class="nav-item" data-page="timesheet" onclick="CTMS.navigate('timesheet')">
          <span class="nav-icon">⏳</span><span class="nav-label">填写工时</span>
        </div>
        <div class="nav-item" data-page="settings" onclick="CTMS.navigate('settings')">
          <span class="nav-icon">⚙️</span><span class="nav-label">系统设置</span>
        </div>
      </div>
    `;
  },

  renderHeader() {
    document.getElementById('header').innerHTML = `
      <button class="btn-icon" onclick="CTMS.toggleSidebar()" title="折叠菜单">☰</button>
      <div>
        <div id="page-title" class="header-title">数据概览</div>
        <div id="breadcrumb" class="header-breadcrumb text-muted" style="font-size:11px">工作台 / 数据概览</div>
      </div>
      <div style="flex:1"></div>
      <div class="header-actions">
        <div class="dropdown" style="position:relative">
          <button class="header-btn" onclick="this.closest('.dropdown').querySelector('.notif-panel').classList.toggle('show')" title="消息通知">
            🔔
          </button>
          <div class="notif-panel">
            <div class="notif-header"><span>通知消息</span><span class="text-primary" style="font-size:12px;cursor:pointer">全部已读</span></div>
            ${CTMS_DATA.announcements.map(a => `
              <div class="notif-item ${a.read ? '' : 'unread'}">
                <div class="notif-dot" style="${a.read ? 'background:var(--gray-300)' : ''}"></div>
                <div><div class="notif-text">${a.title}</div><div class="notif-time">${a.time}</div></div>
              </div>
            `).join('')}
          </div>
        </div>
        <button class="header-btn" title="全屏">⊞</button>
        <div class="dropdown">
          <div class="user-avatar" onclick="this.closest('.dropdown').querySelector('.dropdown-menu').classList.toggle('show')" title="${CTMS_DATA.currentUser.name}">${CTMS_DATA.currentUser.avatar}</div>
          <div class="dropdown-menu">
            <div class="dropdown-item" onclick="CTMS.showProfileModal()">👤 个人信息</div>
            <div class="dropdown-item" onclick="CTMS.showChangePasswordModal()">🔑 修改密码</div>
            <div class="dropdown-divider"></div>
            <div class="dropdown-item" onclick="CTMS.logout()">🚪 退出登录</div>
          </div>
        </div>
      </div>
    `;
  },

  toggleSidebar() {
    this.sidebarCollapsed = !this.sidebarCollapsed;
    document.getElementById('sidebar').classList.toggle('collapsed', this.sidebarCollapsed);
  },

  initDropdowns() {
    document.addEventListener('click', e => {
      if (!e.target.closest('.dropdown')) document.querySelectorAll('.dropdown-menu, .notif-panel').forEach(el => el.classList.remove('show'));
    });
  },

  async logout() {
    try {
      if (window.CTMS_API) await CTMS_API.Auth.logout();
    } catch (e) {}
    if (window.CTMS_API) CTMS_API.Token.clearTokens();
    document.getElementById('app').innerHTML = '';
    document.getElementById('app').innerHTML = `<div id="login-screen"></div>`;
    renderLogin();
  },

  showModal(title, contentHTML, footerHTML = '') {
    const el = document.createElement('div');
    el.className = 'modal-overlay';
    el.id = 'ctms-modal';
    el.innerHTML = `
      <div class="modal modal-lg">
        <div class="modal-header">
          <span class="modal-title">${title}</span>
          <button class="modal-close" onclick="CTMS.closeModal()">✕</button>
        </div>
        <div class="modal-body">${contentHTML}</div>
        ${footerHTML ? `<div class="modal-footer">${footerHTML}</div>` : ''}
      </div>
    `;
    el.addEventListener('click', e => { if (e.target === el) this.closeModal(); });
    document.body.appendChild(el);
  },

  closeModal() {
    const m = document.getElementById('ctms-modal');
    if (m) m.remove();
  },

  showProfileModal() {
    const user = (window.CTMS_API && CTMS_API.Token.getCurrentUser()) || CTMS_DATA.currentUser;
    const userName = user.full_name || user.name || '未知用户';
    const email = user.email || '暂无邮箱';
    const org = user.organization_id ? `机构ID: ${user.organization_id}` : '未绑定机构';
    const role = user.role || '用户';

    const html = `
      <div style="padding:10px">
        <div style="display:flex; align-items:center; gap:20px; margin-bottom:20px">
          <div style="width:80px;height:80px;border-radius:50%;background:var(--primary);color:#fff;display:flex;align-items:center;justify-content:center;font-size:36px">
            ${userName.substring(0,1).toUpperCase()}
          </div>
          <div>
            <h3 style="margin:0 0 5px 0;font-size:20px">${userName}</h3>
            <span class="badge badge-blue">${role}</span>
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">登录账号</label>
          <input type="text" class="form-input" value="${email}" readonly disabled style="background:var(--gray-50)">
        </div>
        <div class="form-group">
          <label class="form-label">所属机构 / 中心</label>
          <input type="text" class="form-input" value="${org}" readonly disabled style="background:var(--gray-50)">
        </div>
      </div>
    `;
    this.showModal('个人信息', html, '<button class="btn btn-primary" onclick="CTMS.closeModal()">关闭</button>');
  },

  showChangePasswordModal() {
    const html = `
      <div class="form-group">
        <label class="form-label required">原密码</label>
        <input type="password" id="cp-old" class="form-input" placeholder="输入当前密码">
      </div>
      <div class="form-group">
        <label class="form-label required">新密码</label>
        <input type="password" id="cp-new" class="form-input" placeholder="输入新密码">
      </div>
      <div class="form-group">
        <label class="form-label required">确认新密码</label>
        <input type="password" id="cp-confirm" class="form-input" placeholder="再次输入新密码">
      </div>
    `;
    const footer = `
      <button class="btn btn-secondary" onclick="CTMS.closeModal()">取消</button>
      <button class="btn btn-primary" onclick="CTMS.submitChangePassword()">确认修改</button>
    `;
    this.showModal('修改密码', html, footer);
  },

  async submitChangePassword() {
    const oldP = document.getElementById('cp-old').value;
    const newP = document.getElementById('cp-new').value;
    const confP = document.getElementById('cp-confirm').value;

    if(!oldP || !newP || !confP) return this.showToast('请填写完整信息', 'error');
    if(newP !== confP) return this.showToast('两次输入的新密码不一致', 'error');
    if(newP.length < 6) return this.showToast('新密码长度不能少于6位', 'error');

    try {
      // 模拟调用修改密码 API
      if (window.API && window.API.users && window.API.users.changePassword) {
         // await window.API.users.changePassword({old_password: oldP, new_password: newP});
      }
      this.showToast('密码修改成功，请妥善保管新密码！', 'success');
      this.closeModal();
    } catch (e) {
      this.showToast(e.message || '密码修改失败', 'error');
    }
  },

  showToast(msg, type = 'success') {
    const el = document.createElement('div');
    el.style.cssText = `position:fixed;top:20px;right:20px;background:${type==='success'?'#22c55e':type==='error'?'#ef4444':'#3b82f6'};color:#fff;padding:12px 20px;border-radius:8px;z-index:9999;font-size:13px;box-shadow:0 4px 12px rgba(0,0,0,0.2);animation:fadeIn 0.2s ease`;
    el.textContent = msg;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 2800);
  },

  formatDate(dateStr) {
    if (!dateStr) return '-';
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return String(dateStr).substring(0, 10); // fallback
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  },

  formatDateTime(dateStr) {
    if (!dateStr) return '-';
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return String(dateStr).replace('T', ' ').substring(0, 19); // fallback
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const h = String(d.getHours()).padStart(2, '0');
    const min = String(d.getMinutes()).padStart(2, '0');
    const s = String(d.getSeconds()).padStart(2, '0');
    return `${y}-${m}-${day} ${h}:${min}:${s}`;
  }
};

const NAV_MAP = {
  dashboard: '数据概览', workbench: '我的工作台', schedule: '日程任务', trials: '我的试验',
  'trial-startup': '项目启动', milestone: '里程碑管理', meetings: '会议安排',
  patients: '受试者管理', screening: '患者筛选', icf: '电子知情同意', visits: '访视管理', sae: 'SAE管理',
  'drug-inbound': '药品入库', 'drug-dispatch': '药品发放', 'drug-inventory': '库存管理', 'drug-recover': '回收销毁',
  contracts: '合同管理', budget: '预算费控', invoice: '开票进度',
  qc: '质量控制', etmf: 'eTMF文档', 'audit-trail': '稽查痕迹',
  reports: '统计报表', 'risk-dashboard': '风险仪表盘',
  centers: '中心管理', users: '人员管理', timesheet: '填写工时', settings: '系统设置',
  'trial-detail': '试验详情', 'patient-detail': '受试者详情'
};
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
