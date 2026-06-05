import api from './index';

export const vendorApi = {
  list: (params?: any) => api.get('/vendors', { params }).then(r => r.data.data),
  get: (id: string) => api.get(`/vendors/${id}`).then(r => r.data.data),
  create: (data: any) => api.post('/vendors', data).then(r => r.data.data),
  update: (id: string, data: any) => api.put(`/vendors/${id}`, data).then(r => r.data.data),
  delete: (id: string) => api.delete(`/vendors/${id}`).then(r => r.data.data),
};
