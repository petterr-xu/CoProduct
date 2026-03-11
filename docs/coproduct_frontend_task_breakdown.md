# CoProduct 前端任务拆解清单（与后端里程碑同步）

## 1. 范围与原则

- 本清单基于：
  - `docs/coproduct_frontend_technical_design.md`
  - `docs/coproduct_backend_task_breakdown.md`
- 前端固定技术栈：Next.js（App Router）+ TypeScript + Tailwind + shadcn/ui + React Query + 局部 Zustand
- 与后端保持同节奏推进：`M1 -> M2 -> M3`
- 优先打通“可联调主链路”，再补齐“结果质量”和“完整能力”

---

## 2. 前后端里程碑对齐矩阵

1. 后端 M1（主链路可跑通）  
前端 M1（新建 + 结果主链路可跑通）
2. 后端 M2（结果质量可用）  
前端 M2（固定报告结构稳定展示 + 证据可读）
3. 后端 M3（版本/文件/历史/稳定性）  
前端 M3（regenerate/上传/历史/异常体验完整）

---

## 3. 模块任务总览

## 3.1 核心模块

1. `app`：路由与页面入口（`/review/new`、`/review/[sessionId]`、`/history`）
2. `features`：页面级业务编排（create/review-detail/history/regenerate）
3. `components`：基础组件与业务卡片组件
4. `lib`：API Client、Query Client、常量与工具
5. `hooks`：请求封装与状态衔接
6. `stores`：草稿与局部 UI 状态
7. `schemas/types`：表单校验与契约类型

## 3.2 依赖关系（先后顺序）

1. `types/schemas` -> `lib/api-client`
2. `lib/api-client` + `hooks` -> `features`
3. `components` + `features` -> `app pages`
4. `stores` 与页面并行接入（不阻塞主链路）

---

## 4. M1：主链路可联调（第一优先级）

目标：可从前端发起预审并进入详情页，能看到状态与基础结果。

## 4.1 工程骨架

1. 初始化前端目录结构（与技术方案第 9 节一致）
2. 配置 ESLint/TS 严格模式与基础开发脚本
3. 完成 `app/layout.tsx`、全局样式与 providers 装配

## 4.2 契约与请求层

1. 建立 `types`：`CreatePreReviewForm`、`PreReviewReportView`、`HistoryQuery`
2. 建立统一 `api-client.ts`（禁止组件直接 `fetch`）
3. 注入 API Token 与 Base URL 环境变量读取
4. 定义统一错误对象映射（`error_code/message/status`）
5. 锁定 `GET /api/prereview/{sessionId}` 字段级契约，禁止前端消费裸 `report`

## 4.3 新建预审页 `/review/new`

1. 完成表单字段与本地校验（必填、长度、数量限制）
2. 实现提交态、防重复提交与错误提示
3. 成功后跳转 `/review/{sessionId}`
4. 接入草稿存储（LocalStorage 或 Zustand）

## 4.4 结果页 `/review/[sessionId]`

1. 按 `sessionId` 拉取详情
2. 渲染基础状态：`PROCESSING/DONE/FAILED` + `NOT_FOUND(404 映射 UI 态)`
3. `PROCESSING` 状态轮询，直到非 `PROCESSING`
4. 最小可用结果布局（Header + 状态 + 核心摘要）

---

## 5. M2：结果展示质量可用（第二优先级）

目标：结果页稳定展示固定结构，证据与关键信息可读可追踪。

## 5.1 报告区块组件化

1. 按技术方案固定 8 区块落地组件
2. 区块组件 props 全量类型化，避免 `any`
3. 长文本折叠/展开与空态占位

## 5.2 能力判断与证据展示

1. `Capability` 枚举映射颜色与标签（固定语义）
2. `EvidencePanel` 支持来源、片段、展开详情
3. 显示 `confidence` 和能力判断理由
4. 无证据时展示降级文案与提示

## 5.3 状态与交互一致性

1. 加载骨架、错误态、空态统一
2. 结果页刷新后可恢复当前展示状态
3. API 错误按分类展示（鉴权失败/未找到/服务异常）

## 5.4 M2 契约锁定（与后端同步）

1. 对齐后端状态口径：仅处理 `PROCESSING/DONE/FAILED`
2. `NOT_FOUND` 仅由错误分支驱动，不进入正常 status 分支
3. `capability.confidence` 作为必渲染字段加入类型与组件检查

---

## 6. M3：版本、文件、历史与稳定性（第三优先级）

目标：覆盖完整业务闭环并满足交付标准。

## 6.1 regenerate 流程

1. `RegenerateDialog` 补充说明输入
2. 调用 `POST /api/prereview/{session_id}/regenerate`
3. 成功后跳转新 `sessionId` 并提示版本变化
4. 异常时保留输入并可重试

## 6.2 文件上传链路

1. `FileUploader`：类型/数量/大小前置校验
2. 调用 `POST /api/files/upload` 并展示上传进度
3. 将返回 `fileId` 注入创建/再生成请求
4. 上传失败可重试并可移除失败项

## 6.3 历史页 `/history`

1. 列表分页查询与缓存
2. `keyword` 搜索与 `capabilityStatus` 筛选
3. 点击记录进入对应详情页
4. 支持从历史记录继续补充再生成

## 6.4 稳定性与工程质量

1. 关键交互埋点（提交、查询、再生成、上传）
2. Query 超时/重试策略统一
3. 页面级错误边界与兜底提示
4. 补齐基础联调/回归手册（含环境变量与启动步骤）

---

## 7. 任务颗粒度建议（执行方式）

1. 每个页面作为一个主任务卡，拆分“数据层/展示层/交互层”子任务
2. 每个 API 作为一个联调任务卡，包含：
   - 请求/响应契约
   - 错误分支
   - UI 表现
3. 每个里程碑设置冻结点：进入下一阶段前仅修缺陷，不新增功能

---

## 8. 风险前置

1. 后端字段变更导致前端崩溃：以 `types + schema` 做契约收敛
2. 长轮询带来体验抖动：加最小轮询间隔与停止条件
3. 文件上传失败率高：前置校验 + 可重试 + 明确失败原因
4. 历史数据量增大：分页缓存和列表虚拟化作为预留优化点
