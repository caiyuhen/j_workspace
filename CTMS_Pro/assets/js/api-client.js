<<<<<<< HEAD
/**
 * CTMS Pro - API 客户端
 * 统一封装所有后端接口调用
 * 支持自动携带 JWT Token、错误处理、Token 刷新
 */

// 自动适配后端地址：
// 1) 优先读取 localStorage 手动配置 `ctms_api_base`
// 2) 当前前端在 8899 时，默认后端走 8898
// 3) 其他场景优先同源 `/api/v1`（如 Nginx 反代）
// 4) localhost 无同源反代时再回退到 8000
const API_BASE_URL = (function() {
    let hostname = window.location.hostname;
    // 强制将 localhost 转为 127.0.0.1，避免 uvicorn 绑定的 IPv4 与浏览器默认 IPv6(::1) 冲突
    if (hostname === 'localhost') {
        hostname = '127.0.0.1';
    }
    const port = window.location.port;

    if (port === '8899') {
        return `http://${hostname}:8898/api/v1`;
    }
    
    const stored = localStorage.getItem('ctms_api_base');
    if (stored) return stored;

    if (window.location.protocol.startsWith('http')) {
        return '/api/v1';
    }

    return `http://${hostname}:8000/api/v1`;
})();

// ─── Token 管理 ─────────────────────────────────────────────────
const TokenManager = {
    getAccessToken: () => localStorage.getItem('access_token'),
    getRefreshToken: () => localStorage.getItem('refresh_token'),
    setTokens: (access, refresh) => {
        localStorage.setItem('access_token', access);
        if (refresh) localStorage.setItem('refresh_token', refresh);
    },
    clearTokens: () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('ctms_user');
    },
    getCurrentUser: () => {
        const u = localStorage.getItem('ctms_user');
        return u ? JSON.parse(u) : null;
    },
    setCurrentUser: (user) => {
        localStorage.setItem('ctms_user', JSON.stringify(user));
    },
};

// ─── HTTP 核心请求 ───────────────────────────────────────────────
async function apiRequest(method, path, body = null, options = {}) {
    const url = `${API_BASE_URL}${path}`;
    const token = TokenManager.getAccessToken();

    const headers = {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        ...options.headers,
    };

    const config = {
        method,
        headers,
        cache: 'no-cache',
        ...(body ? { body: JSON.stringify(body) } : {}),
    };

    try {
        let response = await fetch(url, config);

        // Token 过期，尝试刷新
        if (response.status === 401) {
            const refreshed = await tryRefreshToken();
            if (refreshed) {
                headers['Authorization'] = `Bearer ${TokenManager.getAccessToken()}`;
                response = await fetch(url, { ...config, headers });
            } else {
                TokenManager.clearTokens();
                window.location.hash = '#login';
                throw new Error('登录已过期，请重新登录');
            }
        }

        const rawText = await response.text();
        let data = {};
        try {
            data = rawText ? JSON.parse(rawText) : {};
        } catch {
            data = {};
        }

        if (!response.ok) {
            const detail = data.detail ?? data.message;
            let message = '';
            if (typeof detail === 'string') {
                message = detail;
            } else if (Array.isArray(detail)) {
                message = detail.map((item) => {
                    if (typeof item === 'string') return item;
                    if (item && typeof item === 'object') {
                        const loc = Array.isArray(item.loc) ? item.loc.join('.') : '';
                        return [loc, item.msg].filter(Boolean).join(': ');
                    }
                    return String(item);
                }).join('; ');
            } else if (detail && typeof detail === 'object') {
                message = detail.msg || JSON.stringify(detail);
            }
            if (!message && rawText) {
                message = rawText.length > 300 ? rawText.slice(0, 300) : rawText;
            }
            throw new Error(message ? `HTTP ${response.status}: ${message}` : `HTTP ${response.status}: 请求失败`);
        }

        return data;
    } catch (err) {
        if (err instanceof TypeError && err.message.includes('Failed to fetch')) {
            throw new Error('网络请求失败 (Failed to fetch)：请检查服务器是否正常运行、网络连接是否正常或跨域配置是否正确。');
        }
        throw err;
    }
}

async function tryRefreshToken() {
    const refreshToken = TokenManager.getRefreshToken();
    if (!refreshToken) return false;
    try {
        const res = await fetch(`${API_BASE_URL}/auth/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken }),
        });
        if (!res.ok) return false;
        const data = await res.json();
        TokenManager.setTokens(data.access_token, data.refresh_token);
        return true;
    } catch {
        return false;
    }
}

// ─── 便捷方法 ────────────────────────────────────────────────────
const api = {
    get: (path, params = {}) => {
        params._t = Date.now();
        const qs = new URLSearchParams(params).toString();
        return apiRequest('GET', qs ? `${path}?${qs}` : path);
    },
    post: (path, body) => apiRequest('POST', path, body),
    put: (path, body) => apiRequest('PUT', path, body),
    patch: (path, body) => apiRequest('PATCH', path, body),
    delete: (path) => apiRequest('DELETE', path),
};

// ═══════════════════════════════════════════════════════════════
// 认证 API
// ═══════════════════════════════════════════════════════════════
const AuthAPI = {
    async login(username, password, mfaCode = null) {
        const data = await api.post('/auth/login', { username, password, mfa_code: mfaCode });
        if (data) {
            TokenManager.setTokens(data.access_token, data.refresh_token);
            TokenManager.setCurrentUser(data.user);
        }
        return data;
    },

    async logout() {
        try {
            await api.post('/auth/logout');
        } finally {
            TokenManager.clearTokens();
        }
    },

    async getMe() {
        return api.get('/auth/me');
    },

    async changePassword(oldPassword, newPassword, confirmPassword) {
        return api.put('/auth/change-password', {
            old_password: oldPassword,
            new_password: newPassword,
            confirm_password: confirmPassword,
        });
    },

    isLoggedIn() {
        return !!TokenManager.getAccessToken();
    },
};

// ═══════════════════════════════════════════════════════════════
// 试验管理 API
// ═══════════════════════════════════════════════════════════════
const TrialAPI = {
    list: (params = {}) => api.get('/trials', params),
    get: (id) => api.get(`/trials/${id}`),
    create: (data) => api.post('/trials', data),
    update: (id, data) => api.put(`/trials/${id}`, data),
    delete: (id) => api.delete(`/trials/${id}`),
    statistics: () => api.get('/trials/statistics'),
    getMilestones: (trialId) => api.get(`/trials/${trialId}/milestones`),
    createMilestone: (trialId, data) => api.post(`/trials/${trialId}/milestones`, data),
    updateMilestone: (trialId, milestoneId, data) => api.put(`/trials/${trialId}/milestones/${milestoneId}`, data),
};

// ═══════════════════════════════════════════════════════════════
// 受试者管理 API
// ═══════════════════════════════════════════════════════════════
const PatientAPI = {
    list: (params = {}) => api.get('/patients', params),
    get: (id) => api.get(`/patients/${id}`),
    create: (data) => api.post('/patients', data),
    update: (id, data) => api.put(`/patients/${id}`, data),
    statistics: (trialId = null) => api.get('/patients/statistics', trialId ? { trial_id: trialId } : {}),
    createEConsent: (patientId, data) => api.post(`/patients/${patientId}/econsent`, data),
    signEConsent: (patientId, consentId, data) => api.post(`/patients/${patientId}/econsent/${consentId}/sign`, data),
};

// ═══════════════════════════════════════════════════════════════
// 访视管理 API
// ═══════════════════════════════════════════════════════════════
const VisitAPI = {
    list: (params = {}) => api.get('/visits', params),
    create: (data) => api.post('/visits', data),
    update: (id, data) => api.put(`/visits/${id}`, data),
    upcoming: (params = {}) => api.get('/visits/upcoming', params),
};

// ═══════════════════════════════════════════════════════════════
// SAE / 不良事件 API
// ═══════════════════════════════════════════════════════════════
const AEAPI = {
    list: (params = {}) => api.get('/adverse-events', params),
    get: (id) => api.get(`/adverse-events/${id}`),
    create: (data) => api.post('/adverse-events', data),
    update: (id, data) => api.put(`/adverse-events/${id}`, data),
    statistics: (trialId = null) => api.get('/adverse-events/statistics', trialId ? { trial_id: trialId } : {}),
};

// ═══════════════════════════════════════════════════════════════
// 药品管理 API
// ═══════════════════════════════════════════════════════════════
const DrugAPI = {
    listBatches: (params = {}) => api.get('/drugs/batches', params),
    createBatch: (data) => api.post('/drugs/batches', data),
    dispense: (data) => api.post('/drugs/dispense', data),
    return: (data) => api.post('/drugs/return', data),
    inventorySummary: (trialId = null) => api.get('/drugs/inventory-summary', trialId ? { trial_id: trialId } : {}),
    listLogs: (params = {}) => api.get('/drugs/logs', params),
    updateDestructionStatus: (logId, data) => api.put(`/drugs/logs/${logId}/destruction`, data),
};

// ═══════════════════════════════════════════════════════════════
// 经费管理 API
// ═══════════════════════════════════════════════════════════════
const FinanceAPI = {
    listContracts: (params = {}) => api.get('/contracts/contracts', params),
    createContract: (data) => api.post('/contracts/contracts', data),
    listPayments: (params = {}) => api.get('/contracts/payments', params),
    createPayment: (data) => api.post('/contracts/payments', data),
    updatePayment: (id, data) => api.put(`/contracts/payments/${id}`, data),
    budgetSummary: (trialId = null) => api.get('/contracts/budget-summary', trialId ? { trial_id: trialId } : {}),
};

// ═══════════════════════════════════════════════════════════════
// 质控监查 API
// ═══════════════════════════════════════════════════════════════
const MonitoringAPI = {
    listReports: (params = {}) => api.get('/monitoring/reports', params),
    createReport: (data) => api.post('/monitoring/reports', data),
    deleteReport: (id) => api.delete(`/monitoring/reports/${id}`),
    listIssues: (params = {}) => api.get('/monitoring/issues', params),
    createIssue: (data) => api.post('/monitoring/issues', data),
    updateIssue: (id, data) => api.put(`/monitoring/issues/${id}`, data),
};

// ═══════════════════════════════════════════════════════════════
// 文档管理 API
// ═══════════════════════════════════════════════════════════════
const DocumentAPI = {
    list: (params = {}) => api.get('/documents', params),
    create: (data) => api.post('/documents', data),
    delete: (id) => api.delete(`/documents/${id}`),
    sign: (id, certInfo) => api.post(`/documents/${id}/sign`, { cert_info: certInfo }),
};

// ═══════════════════════════════════════════════════════════════
// 统计报表 API
// ═══════════════════════════════════════════════════════════════
const ReportAPI = {
    dashboard: () => api.get('/reports/dashboard'),
    enrollmentTrend: (params = {}) => api.get('/reports/enrollment-trend', params),
    siteEnrollment: (params = {}) => api.get('/reports/site-enrollment', params),
    aeSummary: (params = {}) => api.get('/reports/ae-summary', params),
    auditLogs: (params = {}) => api.get('/reports/audit-logs', params),
};

// ═══════════════════════════════════════════════════════════════
// 机构/中心管理 API
// ═══════════════════════════════════════════════════════════════
const SiteAPI = {
    list: (params = {}) => api.get('/sites', params),
    get: (id) => api.get(`/sites/${id}`),
    create: (data) => api.post('/sites', data),
    update: (id, data) => api.put(`/sites/${id}`, data),
    delete: (id) => api.delete(`/sites/${id}`),
};

// ═══════════════════════════════════════════════════════════════
// 工时管理 API
// ═══════════════════════════════════════════════════════════════
const TimesheetAPI = {
    list: (params = {}) => api.get('/timesheets', params),
    create: (data) => api.post('/timesheets', data),
    update: (id, data) => api.put(`/timesheets/${id}`, data),
    delete: (id) => api.delete(`/timesheets/${id}`),
};

// ═══════════════════════════════════════════════════════════════
// 用户管理 API
// ═══════════════════════════════════════════════════════════════
const UserAPI = {
    list: (params = {}) => api.get('/users', params),
    get: (id) => api.get(`/users/${id}`),
    create: (data) => api.post('/users', data),
    update: (id, data) => api.put(`/users/${id}`, data),
    delete: (id) => api.delete(`/users/${id}`),
    getRoles: () => api.get('/users/roles'),
};

// ─── 通知 API ─────────────────────────────────────────────────────
const NotificationAPI = {
    list: (params = {}) => api.get('/notifications', params),
    markRead: (id) => api.put(`/notifications/${id}/read`),
    markAllRead: () => api.put('/notifications/read-all'),
    sendEmail: (data) => api.post('/notifications/send-email', data),
};

// ─── IWRS 随机化 API ─────────────────────────────────────────────
const IWRSAPI = {
    // 随机化方案
    listSchemes: (params = {}) => api.get('/iwrs/schemes', params),
    getScheme: (id) => api.get(`/iwrs/schemes/${id}`),
    createScheme: (data) => api.post('/iwrs/schemes', data),
    updateScheme: (id, data) => api.patch(`/iwrs/schemes/${id}`, data),
    activateScheme: (id) => api.post(`/iwrs/schemes/${id}/activate`),
    getSchemeStats: (id) => api.get(`/iwrs/schemes/${id}/stats`),
    
    // 受试者随机化分配
    assignRandomization: (data) => api.post('/iwrs/assign', data),
    listRandomizations: (params = {}) => api.get('/iwrs/subjects', params),
    unblindSubject: (id, reason) => api.post(`/iwrs/subjects/${id}/unblind`, { reason }),
};

// ─── 导出 ─────────────────────────────────────────────────────────
window.CTMS_API = {
    Auth: AuthAPI,
    Trial: TrialAPI,
    Patient: PatientAPI,
    Visit: VisitAPI,
    AE: AEAPI,
    Drug: DrugAPI,
    Finance: FinanceAPI,
    Monitoring: MonitoringAPI,
    Document: DocumentAPI,
    Report: ReportAPI,
    User: UserAPI,
    Site: SiteAPI,
    Timesheet: TimesheetAPI,
    Notification: NotificationAPI,
    IWRS: IWRSAPI,
    Token: TokenManager,
};

window.API = {
    auth: AuthAPI,
    trials: TrialAPI,
    patients: PatientAPI,
    visits: VisitAPI,
    ae: AEAPI,
    drugs: DrugAPI,
    finance: FinanceAPI,
    monitoring: MonitoringAPI,
    documents: DocumentAPI,
    reports: ReportAPI,
    users: UserAPI,
    sites: SiteAPI,
    timesheets: TimesheetAPI,
    notifications: NotificationAPI,
    iwrs: IWRSAPI,
    token: TokenManager,
};

console.log('✅ CTMS Pro API 客户端已加载');
console.log(`   后端地址: ${API_BASE_URL}`);
=======
/**
 * CTMS Pro - API 客户端
 * 统一封装所有后端接口调用
 * 支持自动携带 JWT Token、错误处理、Token 刷新
 */

// 自动适配后端地址：
// 1) 优先读取 localStorage 手动配置 `ctms_api_base`
// 2) 当前前端在 8899 时，默认后端走 8898
// 3) 其他场景优先同源 `/api/v1`（如 Nginx 反代）
// 4) localhost 无同源反代时再回退到 8000
const API_BASE_URL = (function() {
    let hostname = window.location.hostname;
    // 强制将 localhost 转为 127.0.0.1，避免 uvicorn 绑定的 IPv4 与浏览器默认 IPv6(::1) 冲突
    if (hostname === 'localhost') {
        hostname = '127.0.0.1';
    }
    const port = window.location.port;

    if (port === '8899') {
        return `http://${hostname}:8898/api/v1`;
    }
    
    const stored = localStorage.getItem('ctms_api_base');
    if (stored) return stored;

    if (window.location.protocol.startsWith('http')) {
        return '/api/v1';
    }

    return `http://${hostname}:8000/api/v1`;
})();

// ─── Token 管理 ─────────────────────────────────────────────────
const TokenManager = {
    getAccessToken: () => localStorage.getItem('access_token'),
    getRefreshToken: () => localStorage.getItem('refresh_token'),
    setTokens: (access, refresh) => {
        localStorage.setItem('access_token', access);
        if (refresh) localStorage.setItem('refresh_token', refresh);
    },
    clearTokens: () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('ctms_user');
    },
    getCurrentUser: () => {
        const u = localStorage.getItem('ctms_user');
        return u ? JSON.parse(u) : null;
    },
    setCurrentUser: (user) => {
        localStorage.setItem('ctms_user', JSON.stringify(user));
    },
};

// ─── HTTP 核心请求 ───────────────────────────────────────────────
async function apiRequest(method, path, body = null, options = {}) {
    const url = `${API_BASE_URL}${path}`;
    const token = TokenManager.getAccessToken();

    const headers = {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        ...options.headers,
    };

    const config = {
        method,
        headers,
        cache: 'no-cache',
        ...(body ? { body: JSON.stringify(body) } : {}),
    };

    try {
        let response = await fetch(url, config);

        // Token 过期，尝试刷新
        if (response.status === 401) {
            const refreshed = await tryRefreshToken();
            if (refreshed) {
                headers['Authorization'] = `Bearer ${TokenManager.getAccessToken()}`;
                response = await fetch(url, { ...config, headers });
            } else {
                TokenManager.clearTokens();
                window.location.hash = '#login';
                throw new Error('登录已过期，请重新登录');
            }
        }

        const rawText = await response.text();
        let data = {};
        try {
            data = rawText ? JSON.parse(rawText) : {};
        } catch {
            data = {};
        }

        if (!response.ok) {
            const detail = data.detail ?? data.message;
            let message = '';
            if (typeof detail === 'string') {
                message = detail;
            } else if (Array.isArray(detail)) {
                message = detail.map((item) => {
                    if (typeof item === 'string') return item;
                    if (item && typeof item === 'object') {
                        const loc = Array.isArray(item.loc) ? item.loc.join('.') : '';
                        return [loc, item.msg].filter(Boolean).join(': ');
                    }
                    return String(item);
                }).join('; ');
            } else if (detail && typeof detail === 'object') {
                message = detail.msg || JSON.stringify(detail);
            }
            if (!message && rawText) {
                message = rawText.length > 300 ? rawText.slice(0, 300) : rawText;
            }
            throw new Error(message ? `HTTP ${response.status}: ${message}` : `HTTP ${response.status}: 请求失败`);
        }

        return data;
    } catch (err) {
        if (err instanceof TypeError && err.message.includes('Failed to fetch')) {
            throw new Error('网络请求失败 (Failed to fetch)：请检查服务器是否正常运行、网络连接是否正常或跨域配置是否正确。');
        }
        throw err;
    }
}

async function tryRefreshToken() {
    const refreshToken = TokenManager.getRefreshToken();
    if (!refreshToken) return false;
    try {
        const res = await fetch(`${API_BASE_URL}/auth/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken }),
        });
        if (!res.ok) return false;
        const data = await res.json();
        TokenManager.setTokens(data.access_token, data.refresh_token);
        return true;
    } catch {
        return false;
    }
}

// ─── 便捷方法 ────────────────────────────────────────────────────
const api = {
    get: (path, params = {}) => {
        params._t = Date.now();
        const qs = new URLSearchParams(params).toString();
        return apiRequest('GET', qs ? `${path}?${qs}` : path);
    },
    post: (path, body) => apiRequest('POST', path, body),
    put: (path, body) => apiRequest('PUT', path, body),
    patch: (path, body) => apiRequest('PATCH', path, body),
    delete: (path) => apiRequest('DELETE', path),
};

// ═══════════════════════════════════════════════════════════════
// 认证 API
// ═══════════════════════════════════════════════════════════════
const AuthAPI = {
    async login(username, password, mfaCode = null) {
        const data = await api.post('/auth/login', { username, password, mfa_code: mfaCode });
        if (data) {
            TokenManager.setTokens(data.access_token, data.refresh_token);
            TokenManager.setCurrentUser(data.user);
        }
        return data;
    },

    async logout() {
        try {
            await api.post('/auth/logout');
        } finally {
            TokenManager.clearTokens();
        }
    },

    async getMe() {
        return api.get('/auth/me');
    },

    async changePassword(oldPassword, newPassword, confirmPassword) {
        return api.put('/auth/change-password', {
            old_password: oldPassword,
            new_password: newPassword,
            confirm_password: confirmPassword,
        });
    },

    isLoggedIn() {
        return !!TokenManager.getAccessToken();
    },
};

// ═══════════════════════════════════════════════════════════════
// 试验管理 API
// ═══════════════════════════════════════════════════════════════
const TrialAPI = {
    list: (params = {}) => api.get('/trials', params),
    get: (id) => api.get(`/trials/${id}`),
    create: (data) => api.post('/trials', data),
    update: (id, data) => api.put(`/trials/${id}`, data),
    delete: (id) => api.delete(`/trials/${id}`),
    statistics: () => api.get('/trials/statistics'),
    getMilestones: (trialId) => api.get(`/trials/${trialId}/milestones`),
    createMilestone: (trialId, data) => api.post(`/trials/${trialId}/milestones`, data),
    updateMilestone: (trialId, milestoneId, data) => api.put(`/trials/${trialId}/milestones/${milestoneId}`, data),
};

// ═══════════════════════════════════════════════════════════════
// 受试者管理 API
// ═══════════════════════════════════════════════════════════════
const PatientAPI = {
    list: (params = {}) => api.get('/patients', params),
    get: (id) => api.get(`/patients/${id}`),
    create: (data) => api.post('/patients', data),
    update: (id, data) => api.put(`/patients/${id}`, data),
    statistics: (trialId = null) => api.get('/patients/statistics', trialId ? { trial_id: trialId } : {}),
    createEConsent: (patientId, data) => api.post(`/patients/${patientId}/econsent`, data),
    signEConsent: (patientId, consentId, data) => api.post(`/patients/${patientId}/econsent/${consentId}/sign`, data),
};

// ═══════════════════════════════════════════════════════════════
// 访视管理 API
// ═══════════════════════════════════════════════════════════════
const VisitAPI = {
    list: (params = {}) => api.get('/visits', params),
    create: (data) => api.post('/visits', data),
    update: (id, data) => api.put(`/visits/${id}`, data),
    upcoming: (params = {}) => api.get('/visits/upcoming', params),
};

// ═══════════════════════════════════════════════════════════════
// SAE / 不良事件 API
// ═══════════════════════════════════════════════════════════════
const AEAPI = {
    list: (params = {}) => api.get('/adverse-events', params),
    get: (id) => api.get(`/adverse-events/${id}`),
    create: (data) => api.post('/adverse-events', data),
    update: (id, data) => api.put(`/adverse-events/${id}`, data),
    statistics: (trialId = null) => api.get('/adverse-events/statistics', trialId ? { trial_id: trialId } : {}),
};

// ═══════════════════════════════════════════════════════════════
// 药品管理 API
// ═══════════════════════════════════════════════════════════════
const DrugAPI = {
    listBatches: (params = {}) => api.get('/drugs/batches', params),
    createBatch: (data) => api.post('/drugs/batches', data),
    dispense: (data) => api.post('/drugs/dispense', data),
    return: (data) => api.post('/drugs/return', data),
    inventorySummary: (trialId = null) => api.get('/drugs/inventory-summary', trialId ? { trial_id: trialId } : {}),
    listLogs: (params = {}) => api.get('/drugs/logs', params),
    updateDestructionStatus: (logId, data) => api.put(`/drugs/logs/${logId}/destruction`, data),
};

// ═══════════════════════════════════════════════════════════════
// 经费管理 API
// ═══════════════════════════════════════════════════════════════
const FinanceAPI = {
    listContracts: (params = {}) => api.get('/contracts/contracts', params),
    createContract: (data) => api.post('/contracts/contracts', data),
    listPayments: (params = {}) => api.get('/contracts/payments', params),
    createPayment: (data) => api.post('/contracts/payments', data),
    updatePayment: (id, data) => api.put(`/contracts/payments/${id}`, data),
    budgetSummary: (trialId = null) => api.get('/contracts/budget-summary', trialId ? { trial_id: trialId } : {}),
};

// ═══════════════════════════════════════════════════════════════
// 质控监查 API
// ═══════════════════════════════════════════════════════════════
const MonitoringAPI = {
    listReports: (params = {}) => api.get('/monitoring/reports', params),
    createReport: (data) => api.post('/monitoring/reports', data),
    deleteReport: (id) => api.delete(`/monitoring/reports/${id}`),
    listIssues: (params = {}) => api.get('/monitoring/issues', params),
    createIssue: (data) => api.post('/monitoring/issues', data),
    updateIssue: (id, data) => api.put(`/monitoring/issues/${id}`, data),
};

// ═══════════════════════════════════════════════════════════════
// 文档管理 API
// ═══════════════════════════════════════════════════════════════
const DocumentAPI = {
    list: (params = {}) => api.get('/documents', params),
    create: (data) => api.post('/documents', data),
    delete: (id) => api.delete(`/documents/${id}`),
    sign: (id, certInfo) => api.post(`/documents/${id}/sign`, { cert_info: certInfo }),
};

// ═══════════════════════════════════════════════════════════════
// 统计报表 API
// ═══════════════════════════════════════════════════════════════
const ReportAPI = {
    dashboard: () => api.get('/reports/dashboard'),
    enrollmentTrend: (params = {}) => api.get('/reports/enrollment-trend', params),
    siteEnrollment: (params = {}) => api.get('/reports/site-enrollment', params),
    aeSummary: (params = {}) => api.get('/reports/ae-summary', params),
    auditLogs: (params = {}) => api.get('/reports/audit-logs', params),
};

// ═══════════════════════════════════════════════════════════════
// 机构/中心管理 API
// ═══════════════════════════════════════════════════════════════
const SiteAPI = {
    list: (params = {}) => api.get('/sites', params),
    get: (id) => api.get(`/sites/${id}`),
    create: (data) => api.post('/sites', data),
    update: (id, data) => api.put(`/sites/${id}`, data),
    delete: (id) => api.delete(`/sites/${id}`),
};

// ═══════════════════════════════════════════════════════════════
// 工时管理 API
// ═══════════════════════════════════════════════════════════════
const TimesheetAPI = {
    list: (params = {}) => api.get('/timesheets', params),
    create: (data) => api.post('/timesheets', data),
    update: (id, data) => api.put(`/timesheets/${id}`, data),
    delete: (id) => api.delete(`/timesheets/${id}`),
};

// ═══════════════════════════════════════════════════════════════
// 用户管理 API
// ═══════════════════════════════════════════════════════════════
const UserAPI = {
    list: (params = {}) => api.get('/users', params),
    get: (id) => api.get(`/users/${id}`),
    create: (data) => api.post('/users', data),
    update: (id, data) => api.put(`/users/${id}`, data),
    delete: (id) => api.delete(`/users/${id}`),
    getRoles: () => api.get('/users/roles'),
};

// ─── 通知 API ─────────────────────────────────────────────────────
const NotificationAPI = {
    list: (params = {}) => api.get('/notifications', params),
    markRead: (id) => api.put(`/notifications/${id}/read`),
    markAllRead: () => api.put('/notifications/read-all'),
    sendEmail: (data) => api.post('/notifications/send-email', data),
};

// ─── IWRS 随机化 API ─────────────────────────────────────────────
const IWRSAPI = {
    // 随机化方案
    listSchemes: (params = {}) => api.get('/iwrs/schemes', params),
    getScheme: (id) => api.get(`/iwrs/schemes/${id}`),
    createScheme: (data) => api.post('/iwrs/schemes', data),
    updateScheme: (id, data) => api.patch(`/iwrs/schemes/${id}`, data),
    activateScheme: (id) => api.post(`/iwrs/schemes/${id}/activate`),
    getSchemeStats: (id) => api.get(`/iwrs/schemes/${id}/stats`),
    
    // 受试者随机化分配
    assignRandomization: (data) => api.post('/iwrs/assign', data),
    listRandomizations: (params = {}) => api.get('/iwrs/subjects', params),
    unblindSubject: (id, reason) => api.post(`/iwrs/subjects/${id}/unblind`, { reason }),
};

// ─── 导出 ─────────────────────────────────────────────────────────
window.CTMS_API = {
    Auth: AuthAPI,
    Trial: TrialAPI,
    Patient: PatientAPI,
    Visit: VisitAPI,
    AE: AEAPI,
    Drug: DrugAPI,
    Finance: FinanceAPI,
    Monitoring: MonitoringAPI,
    Document: DocumentAPI,
    Report: ReportAPI,
    User: UserAPI,
    Site: SiteAPI,
    Timesheet: TimesheetAPI,
    Notification: NotificationAPI,
    IWRS: IWRSAPI,
    Token: TokenManager,
};

window.API = {
    auth: AuthAPI,
    trials: TrialAPI,
    patients: PatientAPI,
    visits: VisitAPI,
    ae: AEAPI,
    drugs: DrugAPI,
    finance: FinanceAPI,
    monitoring: MonitoringAPI,
    documents: DocumentAPI,
    reports: ReportAPI,
    users: UserAPI,
    sites: SiteAPI,
    timesheets: TimesheetAPI,
    notifications: NotificationAPI,
    iwrs: IWRSAPI,
    token: TokenManager,
};

console.log('✅ CTMS Pro API 客户端已加载');
console.log(`   后端地址: ${API_BASE_URL}`);
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
