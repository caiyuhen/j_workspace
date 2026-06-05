/**
 * 分页工具函数
 * 统一分页参数解析，确保所有列表接口行为一致
 */

export interface PaginationParams {
  page: number;
  pageSize: number;
  skip: number;
  take: number;
}

export interface PrismaPaginationArgs {
  skip: number;
  take: number;
}

export interface PaginatedResult<T> {
  list: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

const DEFAULT_PAGE = 1;
const DEFAULT_PAGE_SIZE = 20;
const MAX_PAGE_SIZE = 100;

/**
 * 从 query 参数解析分页配置
 * @param query Express Request.query 对象
 * @param maxPageSize 最大每页数量，默认 100
 */
export function parsePagination(
  query: Record<string, any>,
  maxPageSize: number = MAX_PAGE_SIZE
): PaginationParams {
  let page = parseInt(query.page, 10);
  let pageSize = parseInt(query.pageSize, 10);

  if (isNaN(page) || page < 1) page = DEFAULT_PAGE;
  if (isNaN(pageSize) || pageSize < 1) pageSize = DEFAULT_PAGE_SIZE;
  if (pageSize > maxPageSize) pageSize = maxPageSize;

  return {
    page,
    pageSize,
    skip: (page - 1) * pageSize,
    take: pageSize,
  };
}

/**
 * 构建 Prisma 查询的分页参数（仅 skip + take，不包含 page/pageSize）
 */
export function prismaPagination(pagination: PaginationParams): PrismaPaginationArgs {
  return { skip: pagination.skip, take: pagination.take };
}

/**
 * 构建分页结果
 */
export function buildPaginatedResult<T>(
  list: T[],
  total: number,
  pagination: PaginationParams
): PaginatedResult<T> {
  return {
    list,
    total,
    page: pagination.page,
    pageSize: pagination.pageSize,
    totalPages: Math.ceil(total / pagination.pageSize),
  };
}
