# CoProduct 前端技术设计方案（确定版）

> 适用范围：CoProduct 一期 / MVP  
> 目标：为“需求预审”提供稳定、清晰、可解释的 Web 前端，仅承担输入、展示、交互，不承载核心 AI 逻辑。  
> 本方案是唯一落地方案，不是备选集合。

## 1. 方案结论

CoProduct 前端固定采用：

- 框架：Next.js 15（App Router）
- 语言：TypeScript
- 样式：Tailwind CSS
- 组件：shadcn/ui
- 状态管理：React Query + 局部 Zustand
- 表单：React Hook Form + Zod
- 请求层：统一 API Client
- 部署：Vercel
- 页面数量：3 页
  - 新建预审页
  - 结果页
  - 历史记录页

前端不实现：
- Prompt 拼装
- RAG 检索
- Agent 编排
- 证据排序
- 文件解析
- 复杂权限

## 2. 前端职责边界

前端只承担：

1. 收集输入
2. 触发动作
3. 展示结果
4. 管理交互状态

### 2.1 收集输入
- 原始需求
- 背景说明
- 业务域 / 模块提示
- 附件上传
- 补充说明

### 2.2 触发动作
- 创建预审
- 查询结果
- 重新生成
- 查询历史

### 2.3 展示结果
- 结构化报告
- 证据引用
- 历史版本
- 任务状态

### 2.4 管理交互状态
- loading / empty / error
- 提交中 / 生成中 / 完成 / 失败
- 表单校验提示
- 二次生成弹层

## 3. 信息架构

### 3.1 页面 1：新建预审页 `/review/new`

固定两栏布局：

- 左侧：输入区域
- 右侧：输入建议 / 示例输入 / 注意事项

表单字段：

```ts
type CreatePreReviewForm = {
  requirementText: string;
  backgroundText?: string;
  businessDomain?: string;
  moduleHint?: string;
  attachments?: UploadedFileRef[];
};
```

字段规则：

- `requirementText`：必填，长度 10~5000
- `backgroundText`：选填，长度 0~5000
- `businessDomain`：选填
- `moduleHint`：选填
- `attachments`：最多 5 个，总大小不超过 20MB

必做能力：

- 本地表单校验
- 草稿保存到 LocalStorage
- 示例输入一键填充
- 附件上传进度展示
- 防重复提交

### 3.2 页面 2：结果页 `/review/[sessionId]`

固定结构：

1. 需求摘要
2. 当前能力判断
3. 判断依据
4. 结构化需求草案
5. 待补充信息
6. 风险提示
7. 影响范围
8. 下一步建议
9. 补充信息再生成

状态只允许：

- `PROCESSING`
- `DONE`
- `FAILED`
- `NOT_FOUND`

数据结构：

```ts
type PreReviewReportView = {
  sessionId: string;
  version: number;
  status: "PROCESSING" | "DONE" | "FAILED";
  summary: string;
  capability: {
    status: "SUPPORTED" | "PARTIALLY_SUPPORTED" | "NOT_SUPPORTED" | "NEED_MORE_INFO";
    reason: string;
    confidence: "high" | "medium" | "low";
  };
  evidence: EvidenceItem[];
  structuredRequirement: {
    goal: string;
    actors: string[];
    scope: string[];
    constraints: string[];
    expectedOutput: string;
  };
  missingInfo: string[];
  risks: Array<{ title: string; description: string; level: "high" | "medium" | "low" }>;
  impactScope: string[];
  nextActions: string[];
  uncertainties: string[];
};
```

区块组件固定为：

- `ReviewHeader`
- `CapabilityCard`
- `SummaryCard`
- `EvidencePanel`
- `StructuredRequirementCard`
- `MissingInfoCard`
- `RiskListCard`
- `ImpactScopeCard`
- `NextActionsCard`
- `RegeneratePanel`

### 3.3 页面 3：历史记录页 `/history`

支持：

- 关键字搜索
- 能力判断状态筛选
- 分页
- 点击进入详情
- 继续补充生成

查询结构：

```ts
type HistoryQuery = {
  keyword?: string;
  capabilityStatus?: "SUPPORTED" | "PARTIALLY_SUPPORTED" | "NOT_SUPPORTED" | "NEED_MORE_INFO";
  page: number;
  pageSize: number;
};
```

## 4. 组件设计

### 4.1 基础组件
- `PageContainer`
- `SectionCard`
- `StatusBadge`
- `LoadingSkeleton`
- `ErrorAlert`
- `EmptyState`
- `SubmitButton`
- `EvidenceSnippet`
- `FileUploader`

### 4.2 业务组件
- `CreateReviewForm`
- `ReviewResultLayout`
- `CapabilityBadge`
- `EvidenceDrawer`
- `RiskLevelTag`
- `HistoryList`
- `RegenerateDialog`

规则：

- 所有组件 props 必须显式定义类型
- 组件内不硬编码业务枚举
- 证据组件必须支持标题、来源、片段、展开查看

## 5. 路由设计

固定目录：

```text
app/
  review/
    new/
      page.tsx
    [sessionId]/
      page.tsx
  history/
    page.tsx
  layout.tsx
  page.tsx
```

规则：

- `/` 跳转到 `/review/new`
- 不做后台管理路由
- 不做复杂嵌套路由

## 6. 状态管理设计

### 6.1 React Query
负责：

- `getReviewDetail(sessionId)`
- `getHistoryList(query)`
- `createPreReview()`
- `regeneratePreReview(sessionId)`

规则：

- 结果页详情使用轮询，直到状态不是 `PROCESSING`
- 历史列表使用分页缓存
- regenerate 成功后跳转新版本结果页

### 6.2 Zustand
只保留本地状态：

- 新建页草稿
- 证据抽屉开关
- regenerate 弹层开关
- 全局 toast 队列

## 7. API 调用设计

统一使用 `lib/api-client.ts`，不允许组件直接写 `fetch`。

固定接口：

- `POST /api/prereview`
- `GET /api/prereview/:sessionId`
- `POST /api/prereview/:sessionId/regenerate`
- `GET /api/history`
- `POST /api/files/upload`

## 8. 文件上传设计

前端只负责：

- 选择文件
- 大小与数量校验
- 上传进度展示
- 获取后端返回的 `fileId`

返回结构：

```ts
type UploadedFileRef = {
  fileId: string;
  fileName: string;
  fileSize: number;
};
```

## 9. 目录结构（确定版）

```text
src/
  app/
    review/
      new/
        page.tsx
      [sessionId]/
        page.tsx
    history/
      page.tsx
    layout.tsx
    page.tsx
  components/
    base/
    business/
    layout/
  features/
    create-review/
    review-detail/
    history/
    regenerate/
  lib/
    api-client.ts
    query-client.ts
    constants.ts
    utils.ts
  hooks/
  stores/
  schemas/
  types/
  styles/
```

## 10. UI 规范

固定视觉原则：

- 简洁
- 重点突出能力判断与证据
- 风险与待补充信息高可见
- 长文本支持折叠
- 历史列表优先可扫描性

固定颜色语义：

- `SUPPORTED`：绿色
- `PARTIALLY_SUPPORTED`：黄色
- `NOT_SUPPORTED`：红色
- `NEED_MORE_INFO`：蓝色

## 11. 交付标准

前端完成判定标准：

1. 3 个页面可用
2. 能发起预审并跳转结果页
3. 能轮询结果状态
4. 能展示报告 8 个区块
5. 能展示证据
6. 能上传文件并回传 `fileId`
7. 能发起 regenerate
8. 能查看历史列表与详情

## 12. 最终结论

CoProduct 前端的目标只有四件事：

- 把输入收干净
- 把结果展示清楚
- 把证据挂明白
- 把补充生成走通

因此，本方案固定为 **Next.js + TypeScript + Tailwind + shadcn/ui + React Query** 的轻量实现。
