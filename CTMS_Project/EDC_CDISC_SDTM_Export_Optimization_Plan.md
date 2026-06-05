# EDC CDISC/SDTM导出功能优化实施规划

## 1. 性能优化实施方案

### 1.1 当前问题分析
- 单次导出任务可能一次性加载全部符合条件的数据到内存
- 数据库查询未采用分页机制，导致查询效率低下
- 表单转换处理为串行执行，未充分利用系统资源
- 缺乏流式处理机制，大文件导出容易导致内存溢出

### 1.2 优化措施详细说明

#### 1.2.1 数据库分页查询实现
```typescript
// 在etl-process.ts中的extractCrfData方法中实现分页
private async extractCrfData(exportConfig: ExportConfig, page = 1, pageSize = 1000): Promise<any> {
  const whereClause: any = {
    projectId: exportConfig.projectId,
    status: 'published'
  };
  
  // ... 过滤条件逻辑保持不变 ...
  
  const forms = await prisma.crfForm.findMany({
    where: whereClause,
    include: {
      // ... 包含字段定义 ...
    },
    skip: (page - 1) * pageSize,
    take: pageSize
  });
  
  return {
    forms,
    metadata: {
      project: exportConfig.projectId,
      exportDate: new Date(),
      filters: exportConfig.filters,
      page,
      pageSize,
      hasMore: forms.length === pageSize
    }
  };
}
```

#### 1.2.2 数据库索引优化
为以下字段添加数据库索引：
- `projectId` (用于项目筛选)
- `createdAt` (用于时间范围筛选)
- `cdiscDomain` (用于域筛选)
- `status` (用于状态筛选)

#### 1.2.3 并行处理优化
```typescript
// 优化transformToSdtm方法，实现并行转换
private async transformToSdtm(extractedData: any): Promise<SdtmData> {
  const sdtmDatasets: SdtmDataset[] = [];
  const formIds = extractedData.forms.map((f: any) => f.id);
  
  // 使用Promise.all()并行转换所有表单
  const conversionPromises = formIds.map(id => 
    this.converter.convertFormToSdtm(id)
  );
  
  try {
    const results = await Promise.all(conversionPromises);
    sdtmDatasets.push(...results.filter(Boolean) as SdtmDataset[]);
  } catch (error) {
    console.error('并行转换失败:', error);
    // 如果部分转换失败，记录日志并继续处理其他表单
  }
  
  return this.mergeSdtmDatasets(sdtmDatasets);
}
```

#### 1.2.4 流式处理实现
对于大型导出任务，实现流式处理：
```typescript
// 在loadSdtmData方法中实现流式写入
private async loadSdtmData(sdtmData: SdtmData, exportConfig: ExportConfig): Promise<any> {
  // 实现流式文件生成（例如CSV格式）
  const stream = fs.createWriteStream(filePath);
  
  // 分批写入数据
  for (const dataset of sdtmData.datasets) {
    const line = this.generateCsvLine(dataset);
    stream.write(line + '\n');
  }
  
  stream.end();
  return { success: true, filePath };
}
```

## 2. 用户体验优化实施方案

### 2.1 错误处理增强
为前端添加详细的错误分类和用户提示：

```typescript
// 错误处理增强
const handleExportSubmit = async (values) => {
  setLoading(true);
  try {
    const response = await axios.post('/api/edc/export/batch-to-sdtm', {
      // ... 导出配置 ...
    });
    
    if (response.data.success) {
      // 成功处理
      fetchExportHistory();
      message.success('导出任务提交成功');
    } else {
      // 处理业务逻辑错误
      if (response.data.error.code === 'VALIDATION_ERROR') {
        message.error('配置参数验证失败：' + response.data.error.message);
      } else if (response.data.error.code === 'PERMISSION_DENIED') {
        message.error('权限不足，无法执行导出操作');
      } else {
        message.error('导出任务提交失败：' + response.data.error.message);
      }
    }
  } catch (error) {
    // 网络错误处理
    if (error.code === 'NETWORK_ERROR') {
      message.error('网络连接失败，请检查网络设置');
    } else {
      message.error('服务器错误，请稍后重试');
    }
  } finally {
    setLoading(false);
  }
};
```

### 2.2 导出进度跟踪
增加实时进度反馈：
```typescript
// 在导出配置页面增加进度显示
const [exportProgress, setExportProgress] = useState(0);
const [isExporting, setIsExporting] = useState(false);

const handleExportSubmit = async (values) => {
  setIsExporting(true);
  setExportProgress(0);
  
  try {
    // 使用长轮询或WebSocket实现进度跟踪
    const response = await axios.post('/api/edc/export/batch-to-sdtm', {
      // ... 配置 ...
    });
    
    // 轮询获取进度
    const pollProgress = async () => {
      const progress = await axios.get(`/api/edc/export/status/${response.data.exportId}`);
      setExportProgress(progress.data.progress);
      
      if (progress.data.status !== 'completed') {
        setTimeout(pollProgress, 2000); // 每2秒轮询一次
      } else {
        setIsExporting(false);
        fetchExportHistory();
      }
    };
    
    pollProgress();
  } catch (error) {
    setIsExporting(false);
    message.error('导出失败：' + error.message);
  }
};
```

### 2.3 响应式设计改进
- 适配不同屏幕尺寸
- 增加加载状态指示器
- 优化表单验证反馈
- 改善移动端显示效果

## 3. 导出模板管理功能实施方案

### 3.1 功能需求分析
用户需要能够：
- 保存常用导出配置为模板
- 管理已有的导出模板
- 快速应用已保存的模板
- 对模板进行分类和标签

### 3.2 技术实现方案
1. 创建新的模板实体：
```typescript
// 在Prisma schema中添加模板表
model ExportTemplate {
  id            String    @id @default(cuid())
  name          String
  description   String?
  projectId     String
  config        Json
  createdAt     DateTime  @default(now())
  updatedAt     DateTime  @updatedAt
}
```

2. 添加模板管理API：
```typescript
// 模板控制器
export class ExportTemplateController {
  // 创建模板
  static async createTemplate(req, res) {
    // 实现模板创建逻辑
  }
  
  // 获取模板列表
  static async getTemplates(req, res) {
    // 实现模板获取逻辑
  }
  
  // 应用模板
  static async applyTemplate(req, res) {
    // 实现模板应用逻辑
  }
}
```

3. 前端模板管理组件：
```typescript
// 模板列表页面
const TemplateListPage = () => {
  const [templates, setTemplates] = useState([]);
  const [isModalVisible, setIsModalVisible] = useState(false);
  
  // 管理模板CRUD操作
  const handleCreateTemplate = async (templateData) => {
    // 创建新模板
  };
  
  const handleApplyTemplate = async (templateId) => {
    // 应用模板配置
  };
  
  return (
    <div>
      {/* 模板列表组件 */}
      {/* 模板创建模态框 */}
    </div>
  );
};
```

## 4. 数据安全机制增强方案

### 4.1 API安全加固
1. **增强JWT验证**：
   - 添加请求签名验证
   - 实现API请求频率限制
   - 增加操作时间戳验证

2. **访问控制增强**：
   ```typescript
   // 在路由中添加详细的权限检查
   const checkExportPermission = (req, res, next) => {
     const userRole = req.user.role;
     const projectId = req.body.projectId;
     
     // 检查用户是否具有该项目的导出权限
     if (!hasExportPermission(userRole, projectId)) {
       return res.status(403).json({
         success: false,
         message: '权限不足，无法执行导出操作'
       });
     }
     
     next();
   };
   ```

### 4.2 审计追踪增强
1. **增加操作人信息记录**：
```typescript
// 修改审计日志结构
export interface AuditLogEntry {
  timestamp: Date;
  userId: string;           // 操作人ID
  username: string;         // 操作人姓名
  action: string;           // 操作类型
  details: string;          // 操作详情
  status: 'success' | 'failed';
  ip: string;               // 请求IP地址
  userAgent: string;        // 浏览器信息
}
```

2. **完整操作记录**：
   - 记录每次导出的完整配置信息
   - 记录导出执行时间和耗时
   - 记录导出结果和输出文件信息

### 4.3 数据保护措施
1. **敏感数据处理**：
   - 为个人隐私数据添加脱敏逻辑
   - 实现数据加密存储机制
   - 增加数据访问记录

2. **操作确认机制**：
   - 关键导出操作增加二次确认
   - 批量导出前显示数据量预估
   - 支持导出任务取消功能

## 5. 实施优先级建议

### 第一阶段（短期）：性能优化
- 完成分页查询优化
- 实现并行处理机制
- 添加数据库索引

### 第二阶段（中期）：用户体验优化
- 实现详细的错误提示
- 增加进度跟踪功能
- 优化前端响应性

### 第三阶段（长期）：功能扩展
- 实现导出模板管理
- 完善安全机制
- 添加高级导出选项

### 第四阶段（可选）：高级功能
- 导出任务调度功能
- 邮件通知功能
- 云存储集成