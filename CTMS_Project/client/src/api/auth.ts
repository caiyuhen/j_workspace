import api from '@/api';

export interface LoginParams {
  username: string;
  password: string;
}

export interface RegisterParams {
  username: string;
  password: string;
  email: string;
  displayName?: string;
}

export const authApi = {
  login: (params: LoginParams) =>
    api.post('/auth/login', params).then((r) => r.data),

  register: (params: RegisterParams) =>
    api.post('/auth/register', params).then((r) => r.data),

  me: () => api.get('/auth/me').then((r) => r.data),

  refresh: (refreshToken: string) =>
    api.post('/auth/refresh', { refreshToken }).then((r) => r.data),

  changePassword: (data: { oldPassword: string; newPassword: string }) =>
    api.post('/auth/change-password', data).then((r) => r.data),
};
