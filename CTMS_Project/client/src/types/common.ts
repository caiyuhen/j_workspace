// 通用分页参数
export interface PaginationParams {
  page?: number;
  pageSize?: number;
}

// 通用分页响应
export interface PaginatedResponse<T> {
  list: T[];
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
}

// 通用 API 响应
export interface ApiResponse<T = any> {
  success: boolean;
  data: T;
  message?: string;
}

// 通用排序参数
export interface SortParams {
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

// 通用筛选
export interface FilterParams {
  status?: string;
  keyword?: string;
  [key: string]: any;
}
