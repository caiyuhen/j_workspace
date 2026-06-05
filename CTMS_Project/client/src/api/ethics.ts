import api from './index';

export const ethicsApi = {
  list: (params?: any) => api.get('/ethics', { params }).then(r => r.data.data),
  get: (id: string) => api.get(`/ethics/${id}`).then(r => r.data.data),
  create: (data: any) => api.post('/ethics', data).then(r => r.data.data),
  update: (id: string, data: any) => api.put(`/ethics/${id}`, data).then(r => r.data.data),
  transition: (id: string, status: string) => api.post(`/ethics/${id}/transition`, { targetStatus: status }).then(r => r.data.data),
  getStats: (params?: any) => api.get('/ethics/stats', { params }).then(r => r.data.data),
};
