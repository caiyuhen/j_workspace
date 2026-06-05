# eCRF 表单设计器 UI 原型设计

## 一、界面布局设计

### 1.1 整体布局结构

```
┌──────────────────────────────────────────────────────────────────────────┐
│  工具栏 (Toolbar)                                                          │
│  [文件] [编辑] [视图] [帮助]  |  表单名称：EDC 表单 v1.0  |  [保存] [预览] [发布] │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────┐  ┌─────────────────────────────────┐  ┌──────────────┐ │
│  │              │  │                                  │  │              │ │
│  │  组件库      │  │        画布区域                  │  │  属性面板    │ │
│  │              │  │                                  │  │              │ │
│  │  - 文本框   │  │   ┌─────────────────────────┐   │  │  - 基础属性   │ │
│  │  - 数字框   │  │   │        表单标题          │   │  │  - 验证规则   │ │
│  │  - 日期选择 │  │   ├─────────────────────────┤   │  │  - CDASH 映射  │ │
│  │  - 下拉框   │  │   │         表单内容          │   │  │  - 显示设置   │ │
│  │  - 单选     │  │   │                          │   │  │  - 布局配置   │ │
│  │  - 多选     │  │   │    [拖拽区域]            │   │  │              │ │
│  │  - 文本域   │  │   │                          │   │  │              │ │
│  │  - 图片     │  │   └─────────────────────────┘   │  │              │ │
│  │  - 签名     │  │                                  │  │              │ │
│  │  - 分组     │  │                                  │  │              │ │
│  │  - 表格     │  │                                  │  │              │ │
│  │              │  │                                  │  │              │ │
│  │              │  │                                  │  │              │ │
│  │              │  │                                  │  │              │ │
│  │              │  │                                  │  │              │ │
│  └──────────────┘  └─────────────────────────────────┘  └──────────────┘ │
│                                                                           │
│  底部状态栏：已保存 | 15 个字段 | 3 个验证规则 | 100% 显示比例                 │
└──────────────────────────────────────────────────────────────────────────┘
```

### 1.2 响应式设计

- **桌面端**: 三栏布局 (组件库 - 画布 - 属性面板)
- **平板端**: 两栏布局 (可折叠侧边栏)
- **移动端**: 单栏布局 (仅画布)

---

## 二、核心组件设计

### 2.1 组件库面板

```
┌────────────────────────┐
│ 🔍 搜索组件...          │
├────────────────────────┤
│ 基础字段               │
│ ┌──────────────────┐   │
│ │ 📝 文本框         │   │
│ │ 📊 数字框         │   │
│ │ 📅 日期选择       │   │
│ │ 🕐 时间选择       │   │
│ │ 🗓️ 日期时间       │   │
│ └──────────────────┘   │
│                        │
│ 选择字段               │
│ ┌──────────────────┐   │
│ │ ☐ 下拉选择        │   │
│ │ ⚪ 单选按钮       │   │
│ │ ☑️ 多选框          │   │
│ └──────────────────┘   │
│                        │
│ 高级字段               │
│ ┌──────────────────┐   │
│ │ 📝 文本域 (多行)   │   │
│ │ 🖼️ 图片上传       │   │
│ │ ✍️ 签名           │   │
│ │ 📋 表格           │   │
│ │ 🏷️ 标签           │   │
│ └──────────────────┘   │
│                        │
│ 布局组件               │
│ ┌──────────────────┐   │
│ │ 📦 分组框         │   │
│ │ 📑 选项卡         │   │
│ │ 📰 页面           │   │
│ └──────────────────┘   │
│                        │
│ 医学字段 (CDASH)        │
│ ┌──────────────────┐   │
│ │ 🩺 实验室检查     │   │
│ │ 🏥 生命体征       │   │
│ │ ⚠️ 不良事件       │   │
│ │ 💊 合并用药       │   │
│ └──────────────────┘   │
└────────────────────────┘
```

**组件属性:**
- 图标：直观区分组件类型
- 名称：中英文对照
- 拖拽：支持拖拽到画布
- 搜索：快速查找组件

### 2.2 画布区域

```
┌─────────────────────────────────────────────────┐
│ 表单名称：受试者基本信息                          │
│ 版本：v1.0 | 状态：草稿 | 最后保存：2026-01-15   │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌─────────────────────────────────────────┐   │
│  │ 受试者基本信息                          │   │
│  └─────────────────────────────────────────┘   │
│                                                  │
│  ┌─────────────────────────────────────────┐   │
│  │ 基本信息                                 │   │
│  ├─────────────────────────────────────────┤   │
│  │                                         │   │
│  │   受试者编号 [文本框 ]              [必填]│   │
│  │                                         │   │
│  │   出生日期 [日期选择 ]             [必填]│   │
│  │                                         │   │
│  │   性别      [●男 ○女 ○未知]          [必填]│   │
│  │                                         │   │
│  │   民族      [下拉选择 ▼]                │   │
│  │                                         │   │
│  │   身高 (cm) [数字框 ]              [0-250]│   │
│  │                                         │   │
│  │   体重 (kg) [数字框 ]              [0-200]│   │
│  │                                         │   │
│  │   体重指数  [计算字段]                [只读]│   │
│  │                                         │   │
│  └─────────────────────────────────────────┘   │
│                                                  │
│  ┌─────────────────────────────────────────┐   │
│  │ 合并用药                                 │   │
│  ├─────────────────────────────────────────┤   │
│  │ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐     │   │
│  │ │ + 添加用药记录                          │   │
│  │ └──────┘ └──────┘ └──────┘ └──────┘     │   │
│  └─────────────────────────────────────────┘   │
│                                                  │
│  ─────────────────────────────────────────────  │
│  [上一页]                    [下一页]            │
│                                                  │
│  页面 1/3                                        │
└─────────────────────────────────────────────────┘
```

**画布功能:**
- 拖拽放置：从组件库拖拽到画布
- 选中：点击组件选中，显示属性
- 编辑：双击编辑组件属性
- 删除：右键删除组件
- 复制：Ctrl+C/V 复制组件
- 对齐：自动对齐辅助线
- 预览：实时预览效果
- 缩放：10%-200% 缩放

### 2.3 属性面板

```
┌────────────────────────────┐
│ 属性设置                    │
├────────────────────────────┤
│ 基础信息                    │
│ ├────────────────────────┤ │
│ │ 字段编码：SUBJID       │ │
│ │ 字段名称：受试者编号    │ │
│ │ 字段类型：文本框        │ │
│ └────────────────────────┘ │
│                            │
│ 验证设置                    │
│ ├────────────────────────┤ │
│ │ ☑️ 必填                │ │
│ │ 长度限制：[10] 字符     │ │
│ │ 正则验证：              │ │
│ │   [A-Z0-9]{6,12}        │ │
│ │   提示：请输入 6-12 位字母数字 │
│ └────────────────────────┘ │
│                            │
│ CDASH 映射                  │
│ ├────────────────────────┤ │
│ │ CDASH 域：DM           │ │
│ │ 变量名：SUBJID         │ │
│ │ 值集：                │ │
│ │   ─────────────────── │ │
│ │   预定义值：无         │ │
│ └────────────────────────┘ │
│                            │
│ 显示设置                    │
│ ├────────────────────────┤ │
│ │ ☑️ 显示                │ │
│ │ ☑️ 可编辑              │ │
│ │ ☑️ 必填标记            │ │
│ │ 显示顺序：1            │ │
│ │ 占一列：☑️             │ │
│ │ 标签位置：☐ 左侧 ○ 上方│ │
│ └────────────────────────┘ │
│                            │
│ 布局配置                    │
│ ├────────────────────────┤ │
│ │ 宽度：[100%]           │ │
│ │ 间距：[16px]           │ │
│ │ 内边距：[8px]          │ │
│ └────────────────────────┘ │
│                            │
│ 条件显示                    │
│ ├────────────────────────┤ │
│ │ ☐ 根据以下条件显示：   │ │
│ │   IF [其他字段] [等于] [值] │ │
│ │ ─────────────────────── │ │
│ │ ─────────────────────── │ │
│ └────────────────────────┘ │
│                            │
│ 其他设置                    │
│ ├────────────────────────┤ │
│ │ 帮助文本：              │ │
│ │ [请输入受试者唯一编号...]│ │
│ │ 默认值：                │ │
│ │ [自动生成]              │ │
│ └────────────────────────┘ │
│                            │
│ ┌────────────────────────┐ │
│ │  [重置]    [应用]     │ │
│ └────────────────────────┘ │
└────────────────────────────┘
```

---

## 三、关键交互流程

### 3.1 创建新表单流程

```
1. 点击"新建表单"
   ↓
2. 填写表单基本信息
   - 表单编码：SUBJ_INFO
   - 表单名称：受试者基本信息
   - 表单类型：问答题式 / 步骤式
   - 关联访视：BASELINE, V1, V2
   ↓
3. 选择表单模板
   - 从空白开始
   - 从 EDC 模板导入
   - 从 CDASH 标准加载
   ↓
4. 进入设计器界面
   - 拖拽组件到画布
   - 配置字段属性
   - 设置验证规则
   ↓
5. 保存预览
   - 保存草稿
   - 预览效果
   - 发布表单
```

### 3.2 字段编辑流程

```
1. 点击画布上的字段
   ↓
2. 属性面板自动切换
   - 显示该字段所有属性
   ↓
3. 修改属性
   - 基础属性 (名称、类型)
   - 验证规则 (必填、格式)
   - CDASH 映射
   - 显示设置
   ↓
4. 实时预览
   - 属性修改即时生效
   ↓
5. 保存更改
```

### 3.3 验证规则配置流程

```
┌─────────────────────────────────────────┐
│ 添加验证规则                            │
├─────────────────────────────────────────┤
│ 规则类型：                              │
│ [必填] [长度] [范围] [正则] [逻辑]      │
├─────────────────────────────────────────┤
│ 长度验证                                │
│ 最小长度：[6]  最大长度：[12]           │
│ 错误提示：请输入 6-12 位字符              │
├─────────────────────────────────────────┤
│ 正则验证                                │
│ 正则表达式：[A-Z0-9]{6,12}              │
│ 错误提示：请输入大写字母和数字组成的 6-12 位字符 │
├─────────────────────────────────────────┤
│ 逻辑验证                                │
│ IF [结束日期] >= [开始日期]             │
│ 错误提示：结束日期必须晚于开始日期        │
├─────────────────────────────────────────┤
│ [取消] [添加规则]                       │
└─────────────────────────────────────────┘
```

### 3.4 CDASH 映射流程

```
┌─────────────────────────────────────────┐
│ CDASH 字段映射                            │
├─────────────────────────────────────────┤
│ 表单字段：受试者编号                      │
│                                          │
│ CDASH 映射：                              │
│ ☑️ 已映射到 CDASH                       │
│   域：DM                                │
│   变量：SUBJID                          │
│   类型：Character                       │
│   长度：8                               │
│   值集：无                              │
│                                          │
│ SDTM 映射：                               │
│ ☑️ 自动映射到 SDTM                      │
│   域：DM                                │
│   变量：SUBJID                          │
│   标签：Subject Identifier              │
│                                          │
│ 检查一致性：                              │
│ ✅ 符合 CDASH 命名规范                    │
│ ✅ 符合 SDTM 标准                         │
│                                          │
│ [自动检查] [手动修正]                     │
└─────────────────────────────────────────┘
```

---

## 四、UI 组件详细设计

### 4.1 组件库组件

```jsx
// 组件库面板组件
const ComponentLibrary = () => {
  return (
    <div className="component-library">
      {/* 搜索框 */}
      <input 
        type="text" 
        placeholder="搜索组件..." 
        className="search-box"
      />
      
      {/* 组件分类 */}
      <div className="component-category">
        <h3>基础字段</h3>
        <div className="component-item" draggable={true}>
          <Icon name="text" />
          <span>文本框</span>
        </div>
        <div className="component-item" draggable={true}>
          <Icon name="number" />
          <span>数字框</span>
        </div>
        {/* ... 更多组件 */}
      </div>
      
      <div className="component-category">
        <h3>医学字段 (CDASH)</h3>
        <div className="component-item" draggable={true}>
          <Icon name="lab" />
          <span>实验室检查</span>
        </div>
      </div>
    </div>
  );
};
```

### 4.2 画布组件

```jsx
// 画布区域组件
const Canvas = ({ formData, onUpdate }) => {
  return (
    <div className="canvas-container">
      <div className="canvas-toolbar">
        <button onClick={zoomIn}>+ 放大</button>
        <button onClick={zoomOut}>- 缩小</button>
        <button onClick={preview}>👁️ 预览</button>
        <button onClick={save}>💾 保存</button>
      </div>
      
      <div className="canvas-area">
        {formData.pages.map((page, pageIndex) => (
          <div key={pageIndex} className="canvas-page">
            {page.sections.map((section, sectionIndex) => (
              <Section 
                key={sectionIndex}
                data={section}
                onDrag={handleDrag}
                onDrop={handleDrop}
                onSelect={handleSelect}
              />
            ))}
          </div>
        ))}
      </div>
      
      {/* 辅助线 */}
      <GridHelper />
      <AlignmentGuides />
    </div>
  );
};
```

### 4.3 属性面板组件

```jsx
// 属性面板组件
const PropertyPanel = ({ selectedField }) => {
  const [properties, setProperties] = useState(selectedField || {});
  
  const handleChange = (key, value) => {
    setProperties(prev => ({ ...prev, [key]: value }));
  };
  
  return (
    <div className="property-panel">
      <h3>属性设置</h3>
      
      {/* 基础信息 */}
      <Section title="基础信息">
        <Input 
          label="字段编码" 
          value={properties.fieldCode}
          onChange={(v) => handleChange('fieldCode', v)}
          placeholder="CDASH 标准命名"
        />
        <Input 
          label="字段名称" 
          value={properties.fieldName}
          onChange={(v) => handleChange('fieldName', v)}
        />
        <Select 
          label="字段类型" 
          value={properties.fieldType}
          options={fieldTypes}
          onChange={(v) => handleChange('fieldType', v)}
        />
      </Section>
      
      {/* 验证设置 */}
      <Section title="验证设置">
        <Checkbox 
          label="必填" 
          checked={properties.required}
          onChange={(v) => handleChange('required', v)}
        />
        <InputGroup 
          label="长度限制"
          min={properties.minLength}
          max={properties.maxLength}
          onChange={(v) => handleChange('length', v)}
        />
        <RegexValidator 
          pattern={properties.pattern}
          message={properties.patternMessage}
          onChange={(v) => handleChange('pattern', v)}
        />
      </Section>
      
      {/* CDASH 映射 */}
      <Section title="CDASH 映射">
        <Select 
          label="CDASH 域" 
          options={cdashDomains}
          value={properties.cdashDomain}
          onChange={(v) => handleChange('cdashDomain', v)}
        />
        <Input 
          label="变量名" 
          value={properties.sdtmVariable}
          onChange={(v) => handleChange('sdtmVariable', v)}
        />
      </Section>
      
      {/* 操作按钮 */}
      <div className="panel-actions">
        <Button onClick={reset}>重置</Button>
        <Button onClick={apply} variant="primary">应用</Button>
      </div>
    </div>
  );
};
```

---

## 五、表单预览功能

### 5.1 预览模式

```
┌─────────────────────────────────────────┐
│ 表单预览                                 │
├─────────────────────────────────────────┤
│                                          │
│  受试者基本信息                          │
│                                          │
│  ┌─────────────────────────────────────┐│
│  │ 基本信息                             ││
│  ├─────────────────────────────────────┤│
│  │                                     ││
│  │   受试者编号：[                ] *  ││
│  │                                     ││
│  │   出生日期：[  年  月  日      ] *  ││
│  │                                     ││
│  │   性别：  ○男  ○女  ○未知          ││
│  │                                     ││
│  │   民族：  [请选择 ▼]                ││
│  │                                     ││
│  │   身高 (cm)：[               ]      ││
│  │                                     ││
│  │   体重 (kg)：[               ]      ││
│  │                                     ││
│  └─────────────────────────────────────┘│
│                                          │
│  ─────────────────────────────────────  │
│  [上一页]                      [下一页]   │
│                                          │
│  此预览仅供查看，无法提交数据             │
└─────────────────────────────────────────┘
```

### 5.2 交互预览

```javascript
// 预览模式下的交互
const PreviewMode = {
  // 实时验证
  validateOnBlur: true,
  
  // 显示帮助文本
  showHelpText: true,
  
  // 条件显示
  conditionalRendering: true,
  
  // 数据计算
  calculateFields: true,
  
  // 阻止提交
  preventSubmission: true
};
```

---

## 六、CDASH 智能辅助

### 6.1 字段命名检查

```javascript
const CDASHValidator = {
  // 检查字段名是否符合 CDASH 规范
  validateFieldName: (name) => {
    const patterns = {
      // 标准字段
      'SUBJID': { pattern: '^[A-Z][A-Z0-9]{0,11}$', msg: '符合 CDASH SUBJID 规范' },
      'AGE': { pattern: '^AGE$', msg: '符合 CDASH AGE 规范' },
      'SEX': { pattern: '^SEX$', msg: '符合 CDASH SEX 规范' },
      
      // 自定义字段
      'custom': { pattern: '^[A-Z][A-Z0-9]{2,23}$', msg: '自定义字段需符合规范' }
    };
    
    return Object.entries(patterns).some(([key, rule]) => {
      const isValid = new RegExp(rule.pattern).test(name);
      return isValid;
    });
  },
  
  // 建议字段名
  suggestFieldName: (chineseName) => {
    const mapping = {
      '受试者编号': 'SUBJID',
      '年龄': 'AGE',
      '性别': 'SEX',
      '体重': 'WEIGHT',
      '身高': 'HEIGHT'
    };
    
    return mapping[chineseName] || generateFieldName(chineseName);
  }
};
```

### 6.2 自动映射

```javascript
// 自动 CDASH 映射
const autoMapToCDASH = (formFields) => {
  const cdashRegistry = loadCDASHRegistry();
  
  return formFields.map(field => {
    // 匹配标准字段
    const matched = cdashRegistry.find(reg => 
      reg.chineseName === field.fieldName ||
      field.fieldName.includes(reg.cdashVariable)
    );
    
    if (matched) {
      return {
        ...field,
        cdashDomain: matched.domain,
        cdashVariable: matched.variable,
        isStandard: true
      };
    }
    
    return field;
  });
};
```

---

## 七、模板管理

### 7.1 模板库

```
┌─────────────────────────────────────────┐
│ 模板库                                  │
├─────────────────────────────────────────┤
│ 搜索模板...                             │
├─────────────────────────────────────────┤
│ CDASH 标准模板                           │
│ ☐ DM - 受试者特征                        │
│ ☐ EX - 暴露                              │
│ ☐ CE - 中心生命体征                      │
│ ☐ LB - 实验室检查                        │
│ ☐ AE - 不良事件                          │
│ ☐ DS - 生存状态                          │
│ ☐ QS - 问卷量表                          │
│                                         │
│ 常用表单模板                             │
│ ☐ 受试者基本信息                         │
│ ☐ 病史采集                               │
│ ☐ 体格检查                               │
│ ☐ 实验室检查记录                         │
│ ☐ 合并用药                               │
│ ☐ 不良事件记录                           │
│                                         │
│ 我的模板                                 │
│ ☐ 心血管试验基线表                       │
│ ☐ 肿瘤试验随访表                         │
│                                         │
│ [导入模板] [新建模板]                     │
└─────────────────────────────────────────┘
```

### 7.2 模板导入

```javascript
// 导入 EDC 模板
const importTemplate = (templateId) => {
  return axios.get(`/api/templates/${templateId}`)
    .then(response => {
      const template = response.data;
      
      // 转换为当前表单结构
      const formSchema = {
        formCode: `TEMP_${templateId}`,
        formName: template.name,
        pages: template.sections.map(section => ({
          title: section.name,
          fields: section.fields.map(field => ({
            ...field,
            id: generateUUID()
          }))
        }))
      };
      
      return formSchema;
    });
};
```

---

## 八、响应式与适配

### 8.1 移动端适配

```css
/* 平板端样式 */
@media (max-width: 1024px) {
  .component-library {
    width: 200px;
  }
  
  .property-panel {
    width: 250px;
  }
  
  .canvas-area {
    flex: 1;
  }
}

/* 移动端样式 */
@media (max-width: 768px) {
  .component-library {
    position: fixed;
    left: -100%;
    transition: left 0.3s;
  }
  
  .component-library.active {
    left: 0;
  }
  
  .property-panel {
    position: fixed;
    right: -100%;
    transition: right 0.3s;
  }
  
  .property-panel.active {
    right: 0;
  }
  
  .canvas-toolbar {
    display: flex;
    justify-content: center;
  }
}
```

---

## 九、用户体验优化

### 9.1 快捷键支持

```javascript
const shortcuts = {
  'Ctrl+S': '保存表单',
  'Ctrl+Z': '撤销',
  'Ctrl+Y': '重做',
  'Ctrl+C': '复制组件',
  'Ctrl+V': '粘贴组件',
  'Delete': '删除选中组件',
  'Escape': '取消选择',
  '?: ': '显示快捷键帮助'
};
```

### 9.2 智能提示

```javascript
// 智能提示服务
const SmartSuggestions = {
  // 字段类型建议
  suggestFieldType: (fieldName, context) => {
    if (fieldName.includes('年龄') || fieldName.includes('AGE')) {
      return { type: 'number', label: '数字框' };
    }
    if (fieldName.includes('日期') || fieldName.includes('DATE')) {
      return { type: 'date', label: '日期选择' };
    }
    if (fieldName.includes('性别') || fieldName.includes('SEX')) {
      return { type: 'radio', options: ['男', '女', '未知'] };
    }
    return null;
  },
  
  // 验证规则建议
  suggestValidation: (fieldType, fieldName) => {
    if (fieldType === 'date') {
      return {
        required: true,
        format: 'YYYY-MM-DD'
      };
    }
    if (fieldName.includes('电话') || fieldName.includes('PHONE')) {
      return {
        required: true,
        pattern: '^1[3-9]\\d{9}$',
        message: '请输入有效的手机号'
      };
    }
    return null;
  }
};
```

---

## 十、数据导出

### 10.1 导出格式

```javascript
// 导出表单设计
const exportFormSchema = (formId) => {
  return {
    version: '1.0',
    form: {
      code: form.code,
      name: form.name,
      version: form.version,
      fields: form.fields.map(field => ({
        code: field.code,
        name: field.name,
        type: field.type,
        required: field.required,
        validation: field.validation,
        cdash: {
          domain: field.cdashDomain,
          variable: field.cdashVariable
        },
        sdtm: {
          variable: field.sdtmVariable
        }
      }))
    },
    cdashMapping: form.cdashMappings,
    sdtmMapping: form.sdtmMappings,
    exportTime: new Date().toISOString()
  };
};
```

---

## 十一、示例表单设计

### 11.1 受试者基本信息表单

```javascript
const subjectInfoForm = {
  formCode: 'SUBJ_INFO',
  formName: '受试者基本信息',
  version: '1.0',
  cdashDomain: 'DM',
  pages: [
    {
      title: '基本信息',
      fields: [
        {
          fieldCode: 'SUBJID',
          fieldName: '受试者编号',
          fieldType: 'text',
          required: true,
          maxLength: 12,
          pattern: '^[A-Z0-9]{6,12}$',
          cdashDomain: 'DM',
          sdtmVariable: 'SUBJID'
        },
        {
          fieldCode: 'RANDDT',
          fieldName: '随机化日期',
          fieldType: 'date',
          required: true,
          cdashDomain: 'DM',
          sdtmVariable: 'RANDDT'
        },
        {
          fieldCode: 'AGE',
          fieldName: '年龄',
          fieldType: 'number',
          required: true,
          min: 18,
          max: 85,
          cdashDomain: 'DM',
          sdtmVariable: 'AGE'
        },
        {
          fieldCode: 'SEX',
          fieldName: '性别',
          fieldType: 'radio',
          required: true,
          options: [
            { value: 'M', label: '男' },
            { value: 'F', label: '女' },
            { value: 'U', label: '未知' }
          ],
          cdashDomain: 'DM',
          sdtmVariable: 'SEX'
        }
      ]
    }
  ]
};
```

---

*文档版本：v1.0*
*创建日期：2026 年*
*维护人：蔡宇恒*
