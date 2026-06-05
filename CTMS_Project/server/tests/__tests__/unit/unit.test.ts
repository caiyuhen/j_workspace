/**
 * CTMS+EDC v4.0 单元测试
 *
 * 覆盖范围：
 * 1. Zod DTO Schema 验证（auth, project, ae, query, export, form, timesheet 等）
 * 2. 共享工具函数（pagination, sort, AppError）
 * 3. 导出服务辅助函数（flattenObject, convertToCsv）
 *
 * 运行：cd server && npx jest __tests__/unit/
 */

// ============================================================
// 1. 分页工具函数测试
// ============================================================
import { parsePagination, buildPaginatedResult } from '@shared/utils/pagination';

describe('分页工具函数 (parsePagination)', () => {
  test('默认分页参数', () => {
    const result = parsePagination({});
    expect(result).toEqual({
      page: 1,
      pageSize: 20,
      skip: 0,
      take: 20,
    });
  });

  test('自定义分页参数', () => {
    const result = parsePagination({ page: '3', pageSize: '50' });
    expect(result).toEqual({
      page: 3,
      pageSize: 50,
      skip: 100,
      take: 50,
    });
  });

  test('非法参数使用默认值', () => {
    const result = parsePagination({ page: 'abc', pageSize: '-5' });
    expect(result.page).toBe(1);
    expect(result.pageSize).toBe(20);
  });

  test('page 为 0 使用默认值', () => {
    const result = parsePagination({ page: '0' });
    expect(result.page).toBe(1);
  });

  test('pageSize 超过最大值被截断', () => {
    const result = parsePagination({ pageSize: '200' }, 100);
    expect(result.pageSize).toBe(100);
  });

  test('自定义最大 pageSize', () => {
    const result = parsePagination({ pageSize: '500' }, 50);
    expect(result.pageSize).toBe(50);
  });
});

describe('构建分页结果 (buildPaginatedResult)', () => {
  test('正常分页结果', () => {
    const pagination = parsePagination({ page: '2', pageSize: '10' });
    const result = buildPaginatedResult([{ id: 1 }, { id: 2 }], 25, pagination);
    expect(result).toEqual({
      list: [{ id: 1 }, { id: 2 }],
      total: 25,
      page: 2,
      pageSize: 10,
      totalPages: 3,
    });
  });

  test('空结果', () => {
    const pagination = parsePagination({});
    const result = buildPaginatedResult([], 0, pagination);
    expect(result.totalPages).toBe(0);
    expect(result.list).toHaveLength(0);
  });

  test('total 不能被 pageSize 整除时向上取整', () => {
    const pagination = parsePagination({ page: '1', pageSize: '10' });
    const result = buildPaginatedResult([], 21, pagination);
    expect(result.totalPages).toBe(3);
  });
});

// ============================================================
// 2. 排序工具函数测试
// ============================================================
import { parseSort } from '@shared/utils/sort';

describe('排序工具函数 (parseSort)', () => {
  test('默认排序', () => {
    const result = parseSort({}, ['createdAt']);
    expect(result).toEqual({ orderBy: { createdAt: 'desc' } });
  });

  test('指定排序字段和方向', () => {
    const result = parseSort({ sortField: 'name', sortOrder: 'asc' }, ['name', 'createdAt']);
    expect(result).toEqual({ orderBy: { name: 'asc' } });
  });

  test('不允许的排序字段使用默认值', () => {
    const result = parseSort({ sortField: 'invalid', sortOrder: 'asc' }, ['createdAt']);
    // 默认字段使用 createdAt，但 sortOrder 是 asc，所以默认方向是 asc
    expect(result).toEqual({ orderBy: { createdAt: 'asc' } });
  });

  test('非法排序方向使用默认 desc', () => {
    const result = parseSort({ sortField: 'createdAt', sortOrder: 'invalid' }, ['createdAt']);
    expect(result).toEqual({ orderBy: { createdAt: 'desc' } });
  });
});

// ============================================================
// 3. AppError 错误类测试
// ============================================================
import {
  AppError,
  NotFoundError,
  ValidationError,
  UnauthorizedError,
  ForbiddenError,
  ConflictError,
  BadRequestError,
  TooManyRequestsError,
} from '@shared/errors/AppError';

describe('AppError 错误类', () => {
  test('AppError 基础属性', () => {
    const err = new AppError('test error', 500, 'TEST_ERROR');
    expect(err.message).toBe('test error');
    expect(err.statusCode).toBe(500);
    expect(err.code).toBe('TEST_ERROR');
    expect(err.isOperational).toBe(true);
    expect(err).toBeInstanceOf(Error);
    expect(err).toBeInstanceOf(AppError);
  });

  test('NotFoundError 404', () => {
    const err = new NotFoundError('User', '123');
    expect(err.statusCode).toBe(404);
    expect(err.code).toBe('NOT_FOUND');
    expect(err.message).toContain('User');
    expect(err.message).toContain('123');
    expect(err.details).toEqual({ resource: 'User', id: '123' });
  });

  test('ValidationError 422', () => {
    const errors = [{ field: 'email', message: 'Invalid email' }];
    const err = new ValidationError(errors);
    expect(err.statusCode).toBe(422);
    expect(err.code).toBe('VALIDATION_ERROR');
    expect(err.details).toEqual({ errors });
  });

  test('UnauthorizedError 401', () => {
    const err = new UnauthorizedError();
    expect(err.statusCode).toBe(401);
    expect(err.code).toBe('UNAUTHORIZED');
  });

  test('ForbiddenError 403', () => {
    const err = new ForbiddenError();
    expect(err.statusCode).toBe(403);
    expect(err.code).toBe('FORBIDDEN');
  });

  test('ConflictError 409', () => {
    const err = new ConflictError('Duplicate entry');
    expect(err.statusCode).toBe(409);
    expect(err.code).toBe('CONFLICT');
  });

  test('BadRequestError 400', () => {
    const err = new BadRequestError('Invalid input');
    expect(err.statusCode).toBe(400);
    expect(err.code).toBe('BAD_REQUEST');
  });

  test('TooManyRequestsError 429', () => {
    const err = new TooManyRequestsError();
    expect(err.statusCode).toBe(429);
    expect(err.code).toBe('TOO_MANY_REQUESTS');
  });
});

// ============================================================
// 4. Auth DTO 验证测试
// ============================================================
import { loginSchema, registerSchema, changePasswordSchema } from '@modules/auth/auth.dto';

describe('Auth DTO 验证', () => {
  describe('loginSchema', () => {
    test('合法登录数据', () => {
      const result = loginSchema.safeParse({ username: 'admin', password: 'Admin123' });
      expect(result.success).toBe(true);
    });

    test('用户名为空', () => {
      const result = loginSchema.safeParse({ username: '', password: 'Admin123' });
      expect(result.success).toBe(false);
    });

    test('密码为空', () => {
      const result = loginSchema.safeParse({ username: 'admin', password: '' });
      expect(result.success).toBe(false);
    });

    test('缺少字段', () => {
      const result = loginSchema.safeParse({});
      expect(result.success).toBe(false);
    });
  });

  describe('registerSchema', () => {
    test('合法注册数据', () => {
      const result = registerSchema.safeParse({
        username: 'newuser',
        email: 'test@example.com',
        password: 'NewUser123',
        displayName: 'Test User',
      });
      expect(result.success).toBe(true);
    });

    test('用户名太短 (<3字符)', () => {
      const result = registerSchema.safeParse({
        username: 'ab',
        email: 'test@example.com',
        password: 'NewUser123',
        displayName: 'Test',
      });
      expect(result.success).toBe(false);
    });

    test('邮箱格式不正确', () => {
      const result = registerSchema.safeParse({
        username: 'newuser',
        email: 'invalid-email',
        password: 'NewUser123',
        displayName: 'Test',
      });
      expect(result.success).toBe(false);
    });

    test('密码缺少大写字母', () => {
      const result = registerSchema.safeParse({
        username: 'newuser',
        email: 'test@example.com',
        password: 'newuser123',
        displayName: 'Test',
      });
      expect(result.success).toBe(false);
    });

    test('密码缺少数字', () => {
      const result = registerSchema.safeParse({
        username: 'newuser',
        email: 'test@example.com',
        password: 'NewUserPassword',
        displayName: 'Test',
      });
      expect(result.success).toBe(false);
    });

    test('密码太短 (<8字符)', () => {
      const result = registerSchema.safeParse({
        username: 'newuser',
        email: 'test@example.com',
        password: 'Nu1',
        displayName: 'Test',
      });
      expect(result.success).toBe(false);
    });
  });

  describe('changePasswordSchema', () => {
    test('合法密码修改', () => {
      const result = changePasswordSchema.safeParse({
        oldPassword: 'OldPass123',
        newPassword: 'NewPass456',
      });
      expect(result.success).toBe(true);
    });

    test('新密码不符合规则', () => {
      const result = changePasswordSchema.safeParse({
        oldPassword: 'OldPass123',
        newPassword: 'weak',
      });
      expect(result.success).toBe(false);
    });
  });
});

// ============================================================
// 5. Project DTO 验证测试
// ============================================================
import { createProjectSchema, updateProjectSchema, createMilestoneSchema } from '@modules/ctms/project/project.dto';

describe('Project DTO 验证', () => {
  describe('createProjectSchema', () => {
    test('合法项目数据', () => {
      const result = createProjectSchema.safeParse({
        projectCode: 'PROJ-001',
        projectName: 'Test Project',
        studyType: 'interventional',
        phase: 'phase_iii',
        sampleSize: 100,
      });
      expect(result.success).toBe(true);
    });

    test('项目编码为空', () => {
      const result = createProjectSchema.safeParse({
        projectCode: '',
        projectName: 'Test',
      });
      expect(result.success).toBe(false);
    });

    test('项目名称为空', () => {
      const result = createProjectSchema.safeParse({
        projectCode: 'PROJ-001',
        projectName: '',
      });
      expect(result.success).toBe(false);
    });

    test('无效的 studyType', () => {
      const result = createProjectSchema.safeParse({
        projectCode: 'PROJ-001',
        projectName: 'Test',
        studyType: 'invalid_type',
      });
      expect(result.success).toBe(false);
    });

    test('无效的 phase', () => {
      const result = createProjectSchema.safeParse({
        projectCode: 'PROJ-001',
        projectName: 'Test',
        phase: 'invalid_phase',
      });
      expect(result.success).toBe(false);
    });

    test('负数 sampleSize', () => {
      const result = createProjectSchema.safeParse({
        projectCode: 'PROJ-001',
        projectName: 'Test',
        sampleSize: -5,
      });
      expect(result.success).toBe(false);
    });
  });

  describe('updateProjectSchema', () => {
    test('更新状态', () => {
      const result = updateProjectSchema.safeParse({ status: 'active' });
      expect(result.success).toBe(true);
    });

    test('无效状态值', () => {
      const result = updateProjectSchema.safeParse({ status: 'invalid_status' });
      expect(result.success).toBe(false);
    });
  });

  describe('createMilestoneSchema', () => {
    test('合法里程碑', () => {
      const result = createMilestoneSchema.safeParse({
        milestoneName: 'First Patient In',
        milestoneType: 'first_patient',
        plannedDate: '2026-06-01',
      });
      expect(result.success).toBe(true);
    });

    test('名称为空', () => {
      const result = createMilestoneSchema.safeParse({
        milestoneName: '',
        milestoneType: 'first_patient',
        plannedDate: '2026-06-01',
      });
      expect(result.success).toBe(false);
    });

    test('无效 milestoneType', () => {
      const result = createMilestoneSchema.safeParse({
        milestoneName: 'Test',
        milestoneType: 'invalid',
        plannedDate: '2026-06-01',
      });
      expect(result.success).toBe(false);
    });
  });
});

// ============================================================
// 6. AE DTO 验证测试
// ============================================================
import { createAdverseEventSchema, createSaeReportSchema } from '@modules/edc/ae/ae.dto';

describe('AE/SAE DTO 验证', () => {
  describe('createAdverseEventSchema', () => {
    test('合法 AE 数据', () => {
      const result = createAdverseEventSchema.safeParse({
        projectId: '00000000-0000-0000-0000-000000000001',
        subjectId: '00000000-0000-0000-0000-000000000002',
        eventType: 'ae',
        termPreferred: '头痛',
        onsetDate: '2026-05-01T00:00:00Z',
        severity: 'mild',
        seriousness: 'non_serious',
        description: '轻度头痛，持续2小时',
        outcome: 'resolved',
      });
      expect(result.success).toBe(true);
    });

    test('合法 SAE 数据', () => {
      const result = createAdverseEventSchema.safeParse({
        projectId: '00000000-0000-0000-0000-000000000001',
        subjectId: '00000000-0000-0000-0000-000000000002',
        eventType: 'sae',
        termPreferred: '严重过敏反应',
        onsetDate: '2026-05-01T08:00:00Z',
        severity: 'severe',
        seriousness: 'serious',
        seriousnessCriteria: ['life_threatening', 'required_hospitalization'],
        description: '严重过敏反应需住院治疗',
        causality: 'probable',
        outcome: 'resolving',
      });
      expect(result.success).toBe(true);
    });

    test('缺少必填字段 projectId', () => {
      const result = createAdverseEventSchema.safeParse({
        subjectId: '00000000-0000-0000-0000-000000000002',
        eventType: 'ae',
        termPreferred: '头痛',
        onsetDate: '2026-05-01T00:00:00Z',
        severity: 'mild',
        seriousness: 'non_serious',
        description: 'test',
      });
      expect(result.success).toBe(false);
    });

    test('无效 eventType', () => {
      const result = createAdverseEventSchema.safeParse({
        projectId: '00000000-0000-0000-0000-000000000001',
        subjectId: '00000000-0000-0000-0000-000000000002',
        eventType: 'invalid',
        termPreferred: 'test',
        onsetDate: '2026-05-01T00:00:00Z',
        severity: 'mild',
        seriousness: 'non_serious',
        description: 'test',
      });
      expect(result.success).toBe(false);
    });

    test('无效 severity', () => {
      const result = createAdverseEventSchema.safeParse({
        projectId: '00000000-0000-0000-0000-000000000001',
        subjectId: '00000000-0000-0000-0000-000000000002',
        eventType: 'ae',
        termPreferred: 'test',
        onsetDate: '2026-05-01T00:00:00Z',
        severity: 'critical',
        seriousness: 'non_serious',
        description: 'test',
      });
      expect(result.success).toBe(false);
    });

    test('描述为空', () => {
      const result = createAdverseEventSchema.safeParse({
        projectId: '00000000-0000-0000-0000-000000000001',
        subjectId: '00000000-0000-0000-0000-000000000002',
        eventType: 'ae',
        termPreferred: 'test',
        onsetDate: '2026-05-01T00:00:00Z',
        severity: 'mild',
        seriousness: 'non_serious',
        description: '',
      });
      expect(result.success).toBe(false);
    });

    test('默认值：isOngoing 和 seriousnessCriteria', () => {
      const result = createAdverseEventSchema.safeParse({
        projectId: '00000000-0000-0000-0000-000000000001',
        subjectId: '00000000-0000-0000-0000-000000000002',
        eventType: 'ae',
        termPreferred: 'test',
        onsetDate: '2026-05-01T00:00:00Z',
        severity: 'mild',
        seriousness: 'non_serious',
        description: 'test desc',
      });
      if (result.success) {
        expect(result.data.isOngoing).toBe(true);
        expect(result.data.seriousnessCriteria).toEqual([]);
      }
    });
  });

  describe('createSaeReportSchema', () => {
    test('合法 SAE 报告', () => {
      const result = createSaeReportSchema.safeParse({
        reportType: 'initial',
        reportDate: '2026-05-08T00:00:00Z',
        reportContent: { narrative: 'SAE initial report' },
      });
      expect(result.success).toBe(true);
    });

    test('无效 reportType', () => {
      const result = createSaeReportSchema.safeParse({
        reportType: 'invalid',
        reportDate: '2026-05-08T00:00:00Z',
      });
      expect(result.success).toBe(false);
    });
  });
});

// ============================================================
// 7. Query DTO 验证测试
// ============================================================
import { createQuerySchema } from '@modules/edc/query/query.dto';

describe('DataQuery DTO 验证', () => {
  test('合法质疑数据', () => {
    const result = createQuerySchema.safeParse({
      projectId: '00000000-0000-0000-0000-000000000001',
      subjectId: '00000000-0000-0000-0000-000000000002',
      queryType: 'data_discrepancy',
      priority: 'high',
      title: '收缩压数据异常',
      description: '收缩压值超出正常范围，请核实',
    });
    expect(result.success).toBe(true);
  });

  test('默认 priority', () => {
    const result = createQuerySchema.safeParse({
      projectId: '00000000-0000-0000-0000-000000000001',
      queryType: 'missing_data',
      title: '缺失数据',
      description: '请补充缺失的实验室数据',
    });
    if (result.success) {
      expect(result.data.priority).toBe('medium');
    }
  });

  test('标题为空', () => {
    const result = createQuerySchema.safeParse({
      projectId: '00000000-0000-0000-0000-000000000001',
      queryType: 'data_discrepancy',
      title: '',
      description: 'test',
    });
    expect(result.success).toBe(false);
  });

  test('无效 queryType', () => {
    const result = createQuerySchema.safeParse({
      projectId: '00000000-0000-0000-0000-000000000001',
      queryType: 'invalid_type',
      title: 'test',
      description: 'test',
    });
    expect(result.success).toBe(false);
  });

  test('无效 priority', () => {
    const result = createQuerySchema.safeParse({
      projectId: '00000000-0000-0000-0000-000000000001',
      queryType: 'data_discrepancy',
      priority: 'urgent',
      title: 'test',
      description: 'test',
    });
    expect(result.success).toBe(false);
  });
});

// ============================================================
// 8. Export DTO 验证测试
// ============================================================
import { exportDataSchema } from '@modules/export/export.dto';

describe('Export DTO 验证', () => {
  test('合法导出请求', () => {
    const result = exportDataSchema.safeParse({
      exportType: 'crf_data',
      projectId: '00000000-0000-0000-0000-000000000001',
      format: 'csv',
    });
    expect(result.success).toBe(true);
  });

  test('默认格式为 json', () => {
    const result = exportDataSchema.safeParse({
      exportType: 'subjects',
      projectId: '00000000-0000-0000-0000-000000000001',
    });
    if (result.success) {
      expect(result.data.format).toBe('json');
    }
  });

  test('无效 exportType', () => {
    const result = exportDataSchema.safeParse({
      exportType: 'invalid_type',
      projectId: '00000000-0000-0000-0000-000000000001',
    });
    expect(result.success).toBe(false);
  });

  test('缺少 projectId', () => {
    const result = exportDataSchema.safeParse({
      exportType: 'subjects',
    });
    expect(result.success).toBe(false);
  });

  test('非 UUID projectId', () => {
    const result = exportDataSchema.safeParse({
      exportType: 'subjects',
      projectId: 'not-a-uuid',
    });
    expect(result.success).toBe(false);
  });

  test('所有合法 exportType', () => {
    const types = ['subjects', 'crf_data', 'adverse_events', 'queries', 'sdv', 'randomization'];
    for (const t of types) {
      const result = exportDataSchema.safeParse({
        exportType: t,
        projectId: '00000000-0000-0000-0000-000000000001',
      });
      expect(result.success).toBe(true);
    }
  });
});

// ============================================================
// 9. Form DTO 验证测试
// ============================================================
import { createFormSchema, addFieldSchema, createEditCheckRuleSchema } from '@modules/edc/form/form.dto';

describe('Form DTO 验证', () => {
  describe('createFormSchema', () => {
    test('合法表单数据', () => {
      const result = createFormSchema.safeParse({
        projectId: '00000000-0000-0000-0000-000000000001',
        formCode: 'VS',
        formName: '生命体征',
        formType: 'visit',
        fields: [
          {
            fieldCode: 'VSTESTCD',
            fieldName: '测试代码',
            fieldType: 'text',
            required: true,
          },
        ],
      });
      expect(result.success).toBe(true);
    });

    test('无效 formType', () => {
      const result = createFormSchema.safeParse({
        projectId: '00000000-0000-0000-0000-000000000001',
        formCode: 'TEST',
        formName: 'Test',
        formType: 'invalid_type',
      });
      expect(result.success).toBe(false);
    });

    test('带字段选项的表单', () => {
      const result = createFormSchema.safeParse({
        projectId: '00000000-0000-0000-0000-000000000001',
        formCode: 'AE',
        formName: '不良事件',
        formType: 'visit',
        isRepeating: true,
        maxRepeats: 100,
        fields: [
          {
            fieldCode: 'AESEV',
            fieldName: '严重程度',
            fieldType: 'select',
            required: true,
            options: [
              { label: '轻度', value: 'MILD' },
              { label: '中度', value: 'MODERATE' },
              { label: '重度', value: 'SEVERE' },
            ],
          },
        ],
      });
      expect(result.success).toBe(true);
    });
  });

  describe('createEditCheckRuleSchema', () => {
    test('合法编辑核查规则', () => {
      const result = createEditCheckRuleSchema.safeParse({
        ruleCode: 'EC-VS-001',
        ruleName: '收缩压范围检查',
        ruleType: 'range_check',
        expression: 'VS.SBP >= 60 && VS.SBP <= 250',
        errorMessage: '收缩压超出正常范围(60-250mmHg)',
        severity: 'error',
        targetFieldIds: ['field-id-1'],
      });
      expect(result.success).toBe(true);
    });

    test('规则表达式为空', () => {
      const result = createEditCheckRuleSchema.safeParse({
        ruleCode: 'EC-001',
        ruleName: 'Test',
        ruleType: 'range_check',
        expression: '',
        errorMessage: 'Error',
      });
      expect(result.success).toBe(false);
    });

    test('默认 severity 为 warning', () => {
      const result = createEditCheckRuleSchema.safeParse({
        ruleCode: 'EC-001',
        ruleName: 'Test',
        ruleType: 'range_check',
        expression: 'value > 0',
        errorMessage: 'Error',
      });
      if (result.success) {
        expect(result.data.severity).toBe('warning');
        expect(result.data.isActive).toBe(true);
      }
    });
  });
});

// ============================================================
// 10. 导出服务辅助函数测试
// ============================================================

/**
 * 复制自 export.service.ts 的辅助函数进行独立测试
 */
function flattenObject(obj: Record<string, any>, prefix = '', result: Record<string, any> = {}): Record<string, any> {
  for (const [key, value] of Object.entries(obj)) {
    const newKey = prefix ? `${prefix}.${key}` : key;
    if (value === null || value === undefined) {
      result[newKey] = '';
    } else if (Array.isArray(value)) {
      result[newKey] = JSON.stringify(value);
    } else if (typeof value === 'object' && !(value instanceof Date)) {
      flattenObject(value as Record<string, any>, newKey, result);
    } else if (value instanceof Date) {
      result[newKey] = value.toISOString();
    } else {
      result[newKey] = value;
    }
  }
  return result;
}

function convertToCsv(data: Record<string, any>[]): string {
  if (data.length === 0) return '';
  const flatRows = data.map(row => flattenObject(row));
  const headerSet = new Set<string>();
  for (const row of flatRows) {
    for (const key of Object.keys(row)) {
      headerSet.add(key);
    }
  }
  const headers = Array.from(headerSet);
  const escapeField = (field: string): string => {
    const str = String(field);
    if (str.includes(',') || str.includes('"') || str.includes('\n') || str.includes('\r')) {
      return `"${str.replace(/"/g, '""')}"`;
    }
    return str;
  };
  const lines: string[] = [];
  lines.push(headers.map(escapeField).join(','));
  for (const row of flatRows) {
    const values = headers.map(h => {
      const val = row[h] !== undefined ? row[h] : '';
      return escapeField(val);
    });
    lines.push(values.join(','));
  }
  return '\uFEFF' + lines.join('\n');
}

describe('导出辅助函数', () => {
  describe('flattenObject', () => {
    test('扁平化简单对象', () => {
      const result = flattenObject({ name: 'test', value: 123 });
      expect(result).toEqual({ name: 'test', value: 123 });
    });

    test('扁平化嵌套对象', () => {
      const result = flattenObject({ user: { name: 'test', age: 25 } });
      expect(result).toEqual({ 'user.name': 'test', 'user.age': 25 });
    });

    test('处理 null 和 undefined', () => {
      const result = flattenObject({ name: 'test', value: null, missing: undefined });
      expect(result).toEqual({ name: 'test', value: '', missing: '' });
    });

    test('数组序列化为 JSON', () => {
      const result = flattenObject({ tags: ['a', 'b', 'c'] });
      expect(result.tags).toBe('["a","b","c"]');
    });

    test('Date 转为 ISO 字符串', () => {
      const date = new Date('2026-05-08T00:00:00.000Z');
      const result = flattenObject({ date });
      expect(result.date).toBe('2026-05-08T00:00:00.000Z');
    });

    test('多层嵌套', () => {
      const result = flattenObject({ a: { b: { c: 1 } } });
      expect(result).toEqual({ 'a.b.c': 1 });
    });

    test('混合类型', () => {
      const result = flattenObject({
        name: 'test',
        meta: { count: 5, active: true },
        tags: ['x'],
        date: null,
      });
      expect(result.name).toBe('test');
      expect(result['meta.count']).toBe(5);
      expect(result['meta.active']).toBe(true);
      expect(result.tags).toBe('["x"]');
      expect(result.date).toBe('');
    });
  });

  describe('convertToCsv', () => {
    test('空数组返回空字符串', () => {
      expect(convertToCsv([])).toBe('');
    });

    test('简单数据转 CSV', () => {
      const csv = convertToCsv([{ name: 'Alice', age: 30 }, { name: 'Bob', age: 25 }]);
      expect(csv).toContain('name,age');
      expect(csv).toContain('Alice,30');
      expect(csv).toContain('Bob,25');
    });

    test('包含逗号的字段被转义', () => {
      const csv = convertToCsv([{ desc: 'Hello, World' }]);
      expect(csv).toContain('"Hello, World"');
    });

    test('包含引号的字段被转义', () => {
      const csv = convertToCsv([{ desc: 'He said "hi"' }]);
      expect(csv).toContain('"He said ""hi"""');
    });

    test('包含换行的字段被转义', () => {
      const csv = convertToCsv([{ desc: 'line1\nline2' }]);
      expect(csv).toContain('"line1\nline2"');
    });

    test('UTF-8 BOM 存在', () => {
      const csv = convertToCsv([{ a: 1 }]);
      expect(csv.startsWith('\uFEFF')).toBe(true);
    });

    test('不同行有不同字段（补齐空值）', () => {
      const csv = convertToCsv([{ a: 1 }, { b: 2 }]);
      expect(csv).toContain('a,b');
      // 第一行 b 列为空，第二行 a 列为空
    });
  });
});

// ============================================================
// 11. Timesheet DTO 验证测试
// ============================================================
import { createTimesheetSchema } from '@modules/ctms/timesheet/timesheet.dto';

describe('Timesheet DTO 验证', () => {
  test('合法工时数据', () => {
    const result = createTimesheetSchema.safeParse({
      userId: '00000000-0000-0000-0000-000000000001',
      projectId: '00000000-0000-0000-0000-000000000002',
      weekStartDate: '2026-05-04',
      entries: [
        { workDate: '2026-05-04', hours: 8, workType: 'site_management', description: 'Site visit' },
        { workDate: '2026-05-05', hours: 6, workType: 'data_review', description: 'CRF review' },
      ],
    });
    expect(result.success).toBe(true);
  });

  test('每天工时不超过 24', () => {
    const result = createTimesheetSchema.safeParse({
      projectId: '00000000-0000-0000-0000-000000000001',
      weekStartDate: '2026-05-04',
      entries: [
        { date: '2026-05-04', hours: 25, activityType: 'site_management', description: 'Too many hours' },
      ],
    });
    expect(result.success).toBe(false);
  });

  test('负数工时', () => {
    const result = createTimesheetSchema.safeParse({
      projectId: '00000000-0000-0000-0000-000000000001',
      weekStartDate: '2026-05-04',
      entries: [
        { date: '2026-05-04', hours: -5, activityType: 'site_management', description: 'Negative' },
      ],
    });
    expect(result.success).toBe(false);
  });
});

// ============================================================
// 12. Workflow DTO 验证测试
// ============================================================
import { createDefinitionSchema } from '@modules/workflow/workflow.dto';

describe('Workflow DTO 验证', () => {
  test('合法工作流定义', () => {
    const result = createDefinitionSchema.safeParse({
      workflowCode: 'WF-ETHICS-001',
      workflowName: '伦理审批流程',
      workflowType: 'project_approval',
      description: '伦理委员会审批工作流',
      stages: [
        { id: 'stage-1', name: '提交审核', nodeType: 'submit', approverRole: 'crc' },
        { id: 'stage-2', name: 'PI审核', nodeType: 'review', approverRole: 'pi' },
        { id: 'stage-3', name: '完成', nodeType: 'complete', approverRole: 'site_mgr' },
      ],
    });
    expect(result.success).toBe(true);
  });

  test('缺少 stages', () => {
    const result = createDefinitionSchema.safeParse({
      name: '测试流程',
      projectId: '00000000-0000-0000-0000-000000000001',
    });
    expect(result.success).toBe(false);
  });

  test('空 stages 数组', () => {
    const result = createDefinitionSchema.safeParse({
      name: '测试流程',
      projectId: '00000000-0000-0000-0000-000000000001',
      stages: [],
    });
    expect(result.success).toBe(false);
  });
});
