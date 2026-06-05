import api from './index';

export const contractApi = {
  list: (params?: any) => api.get('/contracts', { params }).then(r => r.data.data),
  get: (id: string) => api.get(`/contracts/${id}`).then(r => r.data.data),
  create: (data: any) => api.post('/contracts', data).then(r => r.data.data),
  update: (id: string, data: any) => api.put(`/contracts/${id}`, data).then(r => r.data.data),
  delete: (id: string) => api.delete(`/contracts/${id}`).then(r => r.data.data),
  getStats: (params?: any) => api.get('/contracts/stats', { params }).then(r => r.data.data),
};
