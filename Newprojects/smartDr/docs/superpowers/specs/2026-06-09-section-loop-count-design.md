# 分组循环次数配置设计

## 背景
- 当前 `FormSection` 只支持单次渲染。
- 业务要求允许在表单设计器中按分组配置循环次数。
- 当循环次数为 `0` 时，分组保持现有单次渲染逻辑，不启用循环机制。
- 当循环次数大于 `0` 时，分组在运行时按配置次数重复显示，并分别收集数据。

## 目标
- 在表单设计器中为分组新增 `loopCount` 配置，默认值为 `0`。
- 在 EDC 填写页基于 `loopCount` 动态渲染多个同样样式和校验逻辑的分组实例。
- 保证循环实例之间字段值隔离，提交数据无冲突，可回填、可查看详情。
- 保持非循环分组行为不变，兼容已有模板和历史数据。

## 非目标
- 不引入运行时动态增删循环实例，循环次数完全由设计器配置驱动。
- 不修改单字段配置模型，不为字段单独增加循环能力。
- 不改变现有访视任务编排和模板选择逻辑。

## 术语
- `普通分组`：`loopCount` 为 `0` 的分组。
- `循环分组`：`loopCount` 大于 `0` 的分组。
- `循环实例`：某个循环分组在运行时生成的单个重复块。

## 现状摘要
- 设计器分组模型定义在 `frontend/src/types/formDesigner.ts` 的 `FormSection`。
- 设计器画布分组编辑在 `frontend/src/components/FormDesigner/FormCanvas.tsx`。
- EDC 运行时表单渲染与提交在 `frontend/src/pages/edc/EdcDataCapture.tsx`。
- 后端 `CrfData.data` 当前保存为扁平 `Json`，控制器在 `backend/src/controllers/edcController.ts` 中对字段名集合和数据做处理。

## 方案选择
### 备选方案
- 方案 A：按分组配置循环次数，运行时用嵌套路径渲染，提交时将循环数据聚合到 `sectionLoops`。
- 方案 B：按分组名直接存数组。
- 方案 C：运行时重复 UI，但提交时继续用扁平字段名加索引。

### 决策
- 采用方案 A。

### 选择原因
- 分组配置与需求表述一致，心智模型最稳定。
- `section.id` 可作为稳定键，避免分组改名导致数据不稳。
- 嵌套结构天然避免字段名冲突，便于回填和详情展示。
- 非循环分组继续保留扁平结构，兼容性最好。

## 数据模型设计
### 前端设计器模型
- `FormSection` 新增字段：
  - `loopCount?: number`
- 规则：
  - 未配置时视为 `0`
  - 保存前归一化为整数
  - 最小值为 `0`

### 运行时提交结构
- 普通分组字段继续保持当前扁平结构。
- 循环分组统一放入 `sectionLoops`：

```ts
type SectionLoopPayload = {
  sectionName: string;
  items: Array<Record<string, any>>;
};

type CrfDataPayload = Record<string, any> & {
  sectionLoops?: Record<string, SectionLoopPayload>;
};
```

- 示例：

```json
{
  "SUBJID": "S001",
  "VISIT": "BASELINE",
  "sectionLoops": {
    "section-lab": {
      "sectionName": "实验室检查信息",
      "items": [
        {
          "LBTEST": "ALT",
          "LBORRES": "35"
        },
        {
          "LBTEST": "AST",
          "LBORRES": "40"
        },
        {
          "LBTEST": "TBIL",
          "LBORRES": "12"
        }
      ]
    }
  }
}
```

## 设计器变更
### 配置入口
- 在分组级编辑区域新增“循环次数”配置项。
- 该配置属于分组，不属于字段。
- 分组标题仍维持现有结构、样式和交互。

### 行为规则
- `0`：不启用循环机制。
- `>0`：仅保存配置，不在设计器内部克隆字段定义。
- 预览模式可按运行时效果展示重复分组，便于设计确认。

### 数据兼容
- 读取旧模板时，如分组不存在 `loopCount`，按 `0` 处理。

## 运行时渲染设计
### 渲染原则
- 普通分组按原逻辑渲染一次。
- 循环分组按 `loopCount` 渲染 `N` 个实例。
- 每个实例的样式、字段、校验、说明、标签、交互逻辑与原分组完全一致。

### 标题展示
- 分组主标题沿用原名称。
- 循环实例显示为 `分组名 1`、`分组名 2`、`分组名 3`。

### 表单命名路径
- 普通分组字段仍使用当前扁平字段名。
- 循环分组字段使用嵌套路径：

```ts
['sectionLoops', section.id, 'items', loopIndex, fieldCode]
```

### 原因
- 利用 Ant Design `Form` 原生嵌套能力隔离每个循环实例数据。
- 避免字段同名覆盖。
- 回填和校验都可复用统一路径。

## 提交与回填设计
### 提交
- 获取表单值后，普通字段保留在根层。
- `sectionLoops` 保持嵌套结构直接提交。
- 对循环分组做轻量清洗：
  - 保留 `sectionName`
  - `items` 数组长度与 `loopCount` 一致
  - 日期类型沿用现有序列化逻辑

### 草稿编辑
- 加载草稿时，如果记录包含 `sectionLoops`，直接按嵌套路径回填。
- 普通字段继续按现有逻辑回填。

### 已提交详情
- 详情展示页新增循环分组渲染。
- 每个循环分组显示分组名及其各实例内容。
- 普通字段展示逻辑保持不变。

### 历史兼容
- 历史数据如果没有 `sectionLoops`，页面仍按原模式展示与编辑。
- 旧模板与旧数据无需迁移。

## 校验设计
### 字段校验
- 循环分组内每个字段实例复用原有：
  - 必填校验
  - 范围校验
  - 格式校验
  - 自定义规则

### 分组校验
- 不额外增加“至少填写一组”之类的新规则。
- 循环次数本身决定渲染数量，字段是否必填仍由字段配置控制。

### 结果
- `loopCount = 1` 时表现为 1 个独立实例，规则与普通分组一致，但数据进入 `sectionLoops`。
- `loopCount = 0` 时完全走旧逻辑。

## 后端兼容设计
### 存储
- `CrfData.data` 继续使用现有 `Json` 字段，无需 Prisma 结构变更。

### 字段名校验
- 当前后端存在基于模板提取 `validFieldNames` 的逻辑。
- 需要扩展该逻辑，使其同时接受：
  - 根层普通字段
  - `sectionLoops[sectionId].items[*]` 中的字段键

### 更新逻辑
- 创建和更新接口均需兼容 `sectionLoops`。
- 不对 `sectionLoops` 的容器键做模板字段名校验，仅校验其中每个 item 的字段键是否合法。

## 影响范围
### 前端
- `frontend/src/types/formDesigner.ts`
- `frontend/src/components/FormDesigner/FormCanvas.tsx`
- `frontend/src/components/FormDesigner/index.tsx`
- `frontend/src/pages/edc/EdcDataCapture.tsx`

### 后端
- `backend/src/controllers/edcController.ts`

## 测试方案
### 场景 0
- 将某分组 `loopCount` 设为 `0`
- 填写页仅显示 1 次原始分组
- 提交后 payload 不产生该分组的 `sectionLoops` 数据

### 场景 1
- 将某分组 `loopCount` 设为 `1`
- 填写页显示 1 个循环实例
- 填写并提交后，`sectionLoops[sectionId].items.length === 1`
- 草稿编辑和已提交详情可正确回填与展示

### 场景 3
- 将某分组 `loopCount` 设为 `3`
- 填写页显示 3 个循环实例
- 三组填写不同值后提交
- 提交结果中 `items.length === 3`
- 三组值互不覆盖，无字段冲突
- 草稿编辑、详情页展示均完整

### 回归
- 非循环分组的渲染、保存、提交、编辑不受影响
- 旧记录无 `sectionLoops` 时不报错
- 样式与布局不被破坏

## 风险与缓解
- 风险：现有详情页和编辑页默认按扁平字段读取，可能遗漏循环数据。
- 缓解：将循环分组作为显式分支统一渲染，不依赖扁平字段遍历。

- 风险：后端字段合法性判断只针对顶层键。
- 缓解：增加针对 `sectionLoops.items` 内字段的递归校验。

- 风险：设计器只支持字段级编辑，分组配置入口不明显。
- 缓解：在分组卡片头部附近增加分组级配置入口，避免混入字段编辑器。

## 实施顺序建议
1. 扩展 `FormSection` 类型与默认值。
2. 在设计器中加入分组级 `loopCount` 配置。
3. 在 EDC 填写页实现循环分组渲染与嵌套命名。
4. 适配提交、草稿回填、已提交详情展示。
5. 调整后端 `CrfData` 接口对 `sectionLoops` 的兼容处理。
6. 完成 `0/1/3` 三种场景验证与回归检查。
