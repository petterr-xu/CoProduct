# 前端任务拆解文档 - agent

> Version: v0.2.0
> Last Updated: 2026-03-13
> Status: Draft

## 1. Phase 1 任务

1. FE-001：扩展 `types/index.ts`，新增 `modelTrace/retrievalTrace/runtime/reindex` 类型。
2. FE-002：扩展 `api-client.ts`，适配新字段解析与 optional 兼容。
3. FE-003：新增 `hooks/use-agent-api.ts`（runtime query + reindex mutation）。

## 2. Phase 2 任务

1. FE-004：预审详情页新增 Trace 面板组件（模型/检索观测）。
2. FE-005：新建/再生成表单增加 `debugOptions` 可选输入（管理员可见）。
3. FE-006：错误码映射增量（MODEL_* / RAG_*）。

## 3. Phase 3..N 任务

1. FE-007：管理页新增 Agent Runtime/Reindex 页面或区块。
2. FE-008：reindex job 状态轮询与结果提示。
3. FE-009：联调回归与兼容测试（旧后端/新后端双场景）。
4. FE-010：详情页新增 `toolTrace` 面板与错误提示。
5. FE-011：`debugOptions.toolPolicy` 表单透传能力。
6. FE-012：tool 模式开关联调回归（enable/disable tools）。

## 4. 依赖与执行顺序

推荐顺序：

1. FE-001 -> FE-002 -> FE-003（先契约与数据层）
2. FE-004 -> FE-005 -> FE-006（再业务界面）
3. FE-007 -> FE-008 -> FE-009（最后管理运维能力）

跨端依赖：

1. FE-002 依赖 BE-006/BE-008（详情字段和接口落地）。
2. FE-003/FE-007 依赖 BE-009（runtime/reindex API）。
3. FE-009 依赖 BE-012（回滚开关与监控信号）。
4. FE-010/FE-011 依赖 BE-013（RAG Tool 化与返回字段落地）。
5. FE-012 依赖 BE-014（tool calling adapter 预留与开关）。

## 5. 风险与缓解

1. 风险：后端尚未返回 trace 字段导致渲染错误。
- 缓解：FE 统一 optional parse，缺失即 `null`。
2. 风险：reindex 接口耗时长导致 UI 卡顿。
- 缓解：异步提交 + 轮询 job 状态。
3. 风险：新错误码未映射影响用户理解。
- 缓解：统一落在 `getApiErrorMessage` 并补充回归用例。
4. 风险：toolTrace 字段结构变化导致前端崩溃。
- 缓解：严格 optional parse + 未知状态兜底映射。

## 6. 追踪矩阵（FE-*）

| FE-ID | 任务描述 | 关联 TD-ID | 关联契约项（FC/BC） | 依赖任务（FE/BE） |
|---|---|---|---|---|
| FE-001 | 扩展前端类型定义 | TD-004, TD-008 | FC-001~FC-005 | BE-006 |
| FE-002 | API client 兼容解析 | TD-008 | FC-003, FC-004, FC-005 | FE-001, BE-008 |
| FE-003 | Agent API hooks | TD-009 | FC-001, FC-002 | FE-002, BE-009 |
| FE-004 | 详情页 Trace 面板 | TD-004 | FC-005 | FE-002, BE-008 |
| FE-005 | debugOptions 表单能力 | TD-008 | FC-003, FC-004 | FE-002, BE-008 |
| FE-006 | 错误码映射增强 | TD-010 | FC-001~FC-005 | FE-002, BE-010 |
| FE-007 | 管理页 Agent 运维入口 | TD-009 | FC-001, FC-002 | FE-003, BE-009 |
| FE-008 | Reindex 状态轮询 | TD-009, TD-010 | FC-002 | FE-007, BE-009 |
| FE-009 | 双模式联调回归 | TD-010 | FC-001~FC-005 | FE-008, BE-012 |
| FE-010 | 详情页 Tool Trace 展示 | TD-011 | FC-005 | FE-002, BE-013 |
| FE-011 | debugOptions toolPolicy 透传 | TD-012 | FC-003, FC-004 | FE-005, BE-014 |
| FE-012 | Tool 模式回归验证 | TD-011, TD-012 | FC-003~FC-005 | FE-010, FE-011, BE-014 |
