import axios from 'axios';

// Auth Service API 基础 URL
const API_BASE_URL = 'http://localhost:3001/api';

// 创建 Axios 实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器 - 添加 Token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器 - 处理错误
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token 过期或无效，清除本地存储并跳转登录
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user_info');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// 登录请求
export const login = async (username: string, password: string) => {
  const response = await apiClient.post('/auth/login', { username, password });
  return response.data;
};

// 登出
export const logout = async () => {
  const response = await apiClient.post('/auth/logout');
  return response.data;
};

// 获取当前用户信息
export const getCurrentUser = async () => {
  const response = await apiClient.get('/auth/me');
  return response.data;
};

// 刷新 Token
export const refreshToken = async () => {
  const response = await apiClient.post('/auth/refresh');
  return response.data;
};

// 忘记密码 - 发送重置邮件
export const forgotPassword = async (email: string) => {
  const response = await apiClient.post('/auth/forgot-password', { email });
  return response.data;
};

// 重置密码
export const resetPassword = async (token: string, newPassword: string) => {
  const response = await apiClient.post('/auth/reset-password', { 
    token, 
    newPassword 
  });
  return response.data;
};

export default apiClient;
