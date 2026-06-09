// 登录页面
function renderLogin() {
  document.getElementById('login-screen').innerHTML = `
    <div class="login-box">
      <div class="login-logo">
        <div class="logo-badge">🧬</div>
        <h1>CTMS Pro</h1>
        <p>临床试验管理系统 · Clinical Trial Management System</p>
      </div>

      <div id="login-form">
        <div class="form-group">
          <label class="form-label">用户名 / 邮箱</label>
          <input class="form-input" type="text" id="login-user" placeholder="请输入用户名 / 邮箱" value="admin@ctms-pro.com">
        </div>
        <div class="form-group">
          <label class="form-label">密码</label>
          <input class="form-input" type="password" id="login-pass" placeholder="请输入密码" value="Admin@CTMS2026!">
        </div>
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">
          <label style="display:flex;align-items:center;gap:6px;font-size:13px;cursor:pointer">
            <input type="checkbox" checked> 记住登录状态
          </label>
          <span style="font-size:13px;color:var(--primary);cursor:pointer">忘记密码?</span>
        </div>
        <button class="btn btn-primary btn-lg" style="width:100%" onclick="doLogin()">
          🔐 登录系统
        </button>
        <div style="margin-top:12px;text-align:center">
          <div style="font-size:12px;color:var(--gray-400)">— 或使用以下方式登录 —</div>
          <div style="display:flex;gap:8px;margin-top:10px">
            <button class="btn btn-secondary" style="flex:1;font-size:12px" onclick="doLogin()">🔑 单点登录 (SSO)</button>
            <button class="btn btn-secondary" style="flex:1;font-size:12px" onclick="doLogin()">📱 二维码登录</button>
          </div>
        </div>
      </div>

      <div style="margin-top:24px;padding-top:16px;border-top:1px solid var(--gray-200);text-align:center">
        <div style="font-size:11px;color:var(--gray-400)">系统版本 v3.2.0 · GCP合规 · FDA 21 CFR Part 11认证</div>
        <div style="font-size:11px;color:var(--gray-400);margin-top:4px">© 2026 CTMS Pro · 数据安全保障 AES-256 TLS 1.3</div>
      </div>
    </div>
  `;
}

async function doLogin() {
  const btn = event?.target;
  if (btn) { btn.textContent = '⏳ 验证中...'; btn.disabled = true; }

  const username = document.getElementById('login-user')?.value?.trim();
  const password = document.getElementById('login-pass')?.value || '';

  try {
    if (!window.CTMS_API) throw new Error('API 客户端未加载');
    const result = await CTMS_API.Auth.login(username, password);
    const user = result?.user || {};
    CTMS_DATA.currentUser = {
      name: user.full_name || user.username || '用户',
      role: user.role_name || user.role || '-',
      dept: user.department || '-',
      avatar: (user.full_name || user.username || '用').slice(0, 1),
    };
    if (window.syncCTMSDataFromPostgreSQL) {
      await window.syncCTMSDataFromPostgreSQL();
    }
    
    // 在控制台输出临时保存的 user_token（调试用）
    const userToken = sessionStorage.getItem('user_token');
    if (userToken) {
      console.log('--- Debug: Login Success ---');
      console.log('user_token:', userToken);
    }
    
    mountMainLayout();
  } catch (e) {
    if (btn) { btn.textContent = '🔐 登录系统'; btn.disabled = false; }
    const msg = e?.message || '登录失败';
    alert(msg);
  }
}

function mountMainLayout() {
  document.getElementById('app').innerHTML = `
    <div id="main-layout">
      <div id="header"></div>
      <div id="content-wrapper">
        <div id="sidebar"></div>
        <main id="main-content"></main>
      </div>
    </div>
  `;
  CTMS.init();
}
