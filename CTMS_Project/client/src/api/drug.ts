<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
import api from './index';
import type { ApiResponse, PaginatedResponse } from '@/types';
import type {
  Drug,
  CreateDrugParams,
  SupplyPlan,
  Shipment,
  Inventory,
  Destruction,
} from '@/types';

export const drugApi = {
  // 药物信息
  list: (params?: Record<string, any>) =>
    api.get<ApiResponse<PaginatedResponse<Drug>>>('/drugs', { params }).then((r) => r.data.data),

  create: (data: CreateDrugParams) =>
    api.post<ApiResponse<Drug>>('/drugs', data).then((r) => r.data.data),

  getById: (id: string) =>
    api.get<ApiResponse<Drug>>(`/drugs/${id}`).then((r) => r.data.data),

  update: (id: string, data: Partial<CreateDrugParams>) =>
    api.put<ApiResponse<Drug>>(`/drugs/${id}`, data).then((r) => r.data.data),

  // 供应计划
  getSupplyPlans: (drugId: string) =>
    api.get<ApiResponse<SupplyPlan[]>>(`/drugs/${drugId}/supply-plans`).then((r) => r.data.data),

  createSupplyPlan: (drugId: string, data: Partial<SupplyPlan>) =>
    api.post<ApiResponse<SupplyPlan>>(`/drugs/${drugId}/supply-plans`, data).then((r) => r.data.data),

  // 发运跟踪
  getShipments: (drugId: string) =>
    api.get<ApiResponse<Shipment[]>>(`/drugs/${drugId}/shipments`).then((r) => r.data.data),

  createShipment: (drugId: string, data: Partial<Shipment>) =>
    api.post<ApiResponse<Shipment>>(`/drugs/${drugId}/shipments`, data).then((r) => r.data.data),

  receiveShipment: (shipmentId: string, data: { receivedDate?: string; temperatureLog?: string }) =>
    api.post<ApiResponse<Shipment>>(`/drugs/shipments/${shipmentId}/receive`, data).then((r) => r.data.data),

  // 库存管理
  getInventories: (drugId: string) =>
    api.get<ApiResponse<Inventory[]>>(`/drugs/${drugId}/inventories`).then((r) => r.data.data),

  createInventory: (drugId: string, data: Partial<Inventory>) =>
    api.post<ApiResponse<Inventory>>(`/drugs/${drugId}/inventories`, data).then((r) => r.data.data),

  adjustInventory: (drugId: string, inventoryId: string, data: Partial<Inventory>) =>
    api.put<ApiResponse<Inventory>>(`/drugs/${drugId}/inventories/${inventoryId}`, data).then((r) => r.data.data),

  // 回收销毁
  getDestructions: (drugId: string) =>
    api.get<ApiResponse<Destruction[]>>(`/drugs/${drugId}/destructions`).then((r) => r.data.data),

  createDestruction: (drugId: string, data: Partial<Destruction>) =>
    api.post<ApiResponse<Destruction>>(`/drugs/${drugId}/destructions`, data).then((r) => r.data.data),
};
=======
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
>>>>>>> origin/main
import api from './index';
import type { ApiResponse, PaginatedResponse } from '@/types';
import type {
  Drug,
  CreateDrugParams,
  SupplyPlan,
  Shipment,
  Inventory,
  Destruction,
} from '@/types';

export const drugApi = {
  // 药物信息
  list: (params?: Record<string, any>) =>
    api.get<ApiResponse<PaginatedResponse<Drug>>>('/drugs', { params }).then((r) => r.data.data),

  create: (data: CreateDrugParams) =>
    api.post<ApiResponse<Drug>>('/drugs', data).then((r) => r.data.data),

  getById: (id: string) =>
    api.get<ApiResponse<Drug>>(`/drugs/${id}`).then((r) => r.data.data),

  update: (id: string, data: Partial<CreateDrugParams>) =>
    api.put<ApiResponse<Drug>>(`/drugs/${id}`, data).then((r) => r.data.data),

  // 供应计划
  getSupplyPlans: (drugId: string) =>
    api.get<ApiResponse<SupplyPlan[]>>(`/drugs/${drugId}/supply-plans`).then((r) => r.data.data),

  createSupplyPlan: (drugId: string, data: Partial<SupplyPlan>) =>
    api.post<ApiResponse<SupplyPlan>>(`/drugs/${drugId}/supply-plans`, data).then((r) => r.data.data),

  // 发运跟踪
  getShipments: (drugId: string) =>
    api.get<ApiResponse<Shipment[]>>(`/drugs/${drugId}/shipments`).then((r) => r.data.data),

  createShipment: (drugId: string, data: Partial<Shipment>) =>
    api.post<ApiResponse<Shipment>>(`/drugs/${drugId}/shipments`, data).then((r) => r.data.data),

  receiveShipment: (shipmentId: string, data: { receivedDate?: string; temperatureLog?: string }) =>
    api.post<ApiResponse<Shipment>>(`/drugs/shipments/${shipmentId}/receive`, data).then((r) => r.data.data),

  // 库存管理
  getInventories: (drugId: string) =>
    api.get<ApiResponse<Inventory[]>>(`/drugs/${drugId}/inventories`).then((r) => r.data.data),

  createInventory: (drugId: string, data: Partial<Inventory>) =>
    api.post<ApiResponse<Inventory>>(`/drugs/${drugId}/inventories`, data).then((r) => r.data.data),

  adjustInventory: (drugId: string, inventoryId: string, data: Partial<Inventory>) =>
    api.put<ApiResponse<Inventory>>(`/drugs/${drugId}/inventories/${inventoryId}`, data).then((r) => r.data.data),

  // 回收销毁
  getDestructions: (drugId: string) =>
    api.get<ApiResponse<Destruction[]>>(`/drugs/${drugId}/destructions`).then((r) => r.data.data),

  createDestruction: (drugId: string, data: Partial<Destruction>) =>
    api.post<ApiResponse<Destruction>>(`/drugs/${drugId}/destructions`, data).then((r) => r.data.data),
};
<<<<<<< HEAD
<<<<<<< HEAD
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
>>>>>>> origin/main
