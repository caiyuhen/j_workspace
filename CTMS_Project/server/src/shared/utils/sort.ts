/**
 * 排序工具函数
 * 安全解析排序参数，防止 Prisma 注入
 */

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type OrderByInput = any;

interface SortOptions {
  orderBy: OrderByInput;
}

/**
 * 从 query 参数解析排序配置
 */
export function parseSort(
  query: Record<string, any>,
  allowedFields: string[],
  defaultField: string = 'createdAt',
  defaultOrder: 'asc' | 'desc' = 'desc'
): SortOptions {
  const sortField = query.sortField as string || defaultField;
  const sortOrder = (query.sortOrder as string || defaultOrder) as 'asc' | 'desc';

  const field = allowedFields.includes(sortField) ? sortField : defaultField;
  const order = ['asc', 'desc'].includes(sortOrder) ? sortOrder : defaultOrder;

  return {
    orderBy: {
      [field]: order,
    },
  };
}
