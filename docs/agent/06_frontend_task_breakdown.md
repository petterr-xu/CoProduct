# 前端任务拆解文档 - agent

> Version: v0.2.3
> Last Updated: 2026-03-13
> Status: Draft

## 1. Phase 1 任务

> Obsolete in v0.2.0: Phase 1 包含 FE-003（runtime/reindex hooks）。  
> Replacement in v0.2.1: FE-003 下沉到 Phase 3，与 BE-009 同步交付。

1. FE-001：扩展 `types/index.ts`，新增 `modelTrace/retrievalTrace/toolTrace/debugOptions` 类型。
2. FE-002：扩展 `api-client.ts`，完成 optional 字段兼容解析与请求透传兼容。

## 1.5 Phase 1.5 任务（紧急）

1. FE-013：提交链路改造为“受理成功即进入 PROCESSING 态 + 轮询详情”，不等待完整报告返回。
2. FE-014：补充 `SUBMISSION_TIMEOUT/SUBMISSION_QUEUE_FULL` 错误提示与重试交互。
3. FE-015：实现提交态机与防重复提交（`SUBMITTING` 态禁用按钮，受理后阻止重复发起）。
4. FE-016：实现分段轮询策略（立即拉取 + 2s/5s 退避）并在终态自动停止。

## 2. Phase 2 任务

1. FE-004：预审详情页新增 Trace 面板组件（模型/检索观测）。
2. FE-005：新建/再生成表单增加 `debugOptions` 可选输入（管理员可见）。
3. FE-006：错误码映射增量（MODEL_* / RAG_*）。

## 3. Phase 3..N 任务

1. Phase 3（对应 BE-008/BE-009/BE-010）：
- FE-003：新增 `hooks/use-agent-api.ts`（runtime query + reindex mutation）。
- FE-007：管理页新增 Agent Runtime/Reindex 页面或区块。
- FE-008：reindex job 状态轮询与结果提示。
2. Phase 4（对应 BE-012）：
- FE-009：联调回归与兼容测试（旧后端/新后端双场景）。
3. Phase 5（对应 BE-013/BE-014）：
- FE-010：详情页新增 `toolTrace` 面板与错误提示。
- FE-011：`debugOptions.toolPolicy` 表单透传能力。
- FE-012：tool 模式开关联调回归（enable/disable tools）。

## 4. 依赖与执行顺序

推荐顺序：

1. FE-001 -> FE-002（先契约与数据兼容层）
2. FE-013 -> FE-014 -> FE-015 -> FE-016（先解决提交超时的紧急链路）
3. FE-004 -> FE-005 -> FE-006（再详情页与表单能力）
4. FE-003 -> FE-007 -> FE-008（管理与运维能力，等待 BE-009）
5. FE-009（双模式联调回归）
6. FE-010 -> FE-011 -> FE-012（Tool 能力展示与回归）

跨端依赖：

1. FE-001/FE-002 可先行，不阻塞于 BE-009。
2. FE-013/FE-014 依赖 BE-016/BE-017/BE-018（后端提交异步化与受理错误码）。
3. FE-015/FE-016 依赖 BE-019（runner 生命周期稳定，轮询不会出现长时间“僵尸处理中”）。
4. FE-004/FE-005 依赖 BE-006/BE-007（trace/debugOptions 在主链路稳定）。
5. FE-003/FE-007/FE-008 依赖 BE-009（runtime/reindex API）。
6. FE-009 依赖 BE-012（回滚开关与监控信号）。
7. FE-010 依赖 BE-013（RAG Tool 化与 `toolTrace` 返回字段）。
8. FE-011/FE-012 依赖 BE-014（tool calling adapter 预留与开关）。

## 5. 风险与缓解

1. 风险：后端尚未返回 trace 字段导致渲染错误。
- 缓解：FE 统一 optional parse，缺失即 `null`。
2. 风险：reindex 接口耗时长导致 UI 卡顿。
- 缓解：异步提交 + 轮询 job 状态。
3. 风险：新错误码未映射影响用户理解。
- 缓解：统一落在 `getApiErrorMessage` 并补充回归用例。
4. 风险：toolTrace 字段结构变化导致前端崩溃。
- 缓解：严格 optional parse + 未知状态兜底映射。
5. 风险：提交接口超时导致用户重复提交。
- 缓解：Phase 1.5 强制“受理即跳转轮询”并提供重复提交提示。
6. 风险：轮询策略过于激进导致不必要请求压力。
- 缓解：FE-016 使用分段退避并在终态及时停止。

## 6. 追踪矩阵（FE-*）

| FE-ID | 任务描述 | 关联 TD-ID | 关联契约项（FC/BC） | 依赖任务（FE/BE） |
|---|---|---|---|---|
| FE-001 | 扩展前端类型定义 | TD-004, TD-008 | FC-001~FC-005 | - |
| FE-002 | API client 兼容解析 | TD-008 | FC-003, FC-004, FC-005 | FE-001 |
| FE-013 | 提交成功快速跳转 + 轮询过渡 | TD-013 | FC-003, FC-004, FC-005 | FE-002, BE-016 |
| FE-014 | 提交受理错误码提示与重试 | TD-013 | FC-003, FC-004 | FE-013, BE-017 |
| FE-015 | 提交态机与防重复提交 | TD-013 | FC-003, FC-004 | FE-013, FE-014, BE-018 |
| FE-016 | 分段轮询退避与终态停止 | TD-013 | FC-005 | FE-013, FE-015, BE-019 |
| FE-003 | Agent API hooks | TD-009 | FC-001, FC-002 | FE-002, BE-009 |
| FE-004 | 详情页 Trace 面板 | TD-004 | FC-005 | FE-002, BE-006 |
| FE-005 | debugOptions 表单能力 | TD-008 | FC-003, FC-004 | FE-002, BE-007 |
| FE-006 | 错误码映射增强 | TD-010 | FC-001~FC-005 | FE-002, BE-010 |
| FE-007 | 管理页 Agent 运维入口 | TD-009 | FC-001, FC-002 | FE-003, BE-009 |
| FE-008 | Reindex 状态轮询 | TD-009, TD-010 | FC-002 | FE-007, BE-009 |
| FE-009 | 双模式联调回归 | TD-010 | FC-001~FC-005 | FE-008, BE-012 |
| FE-010 | 详情页 Tool Trace 展示 | TD-011 | FC-005 | FE-002, BE-013 |
| FE-011 | debugOptions toolPolicy 透传 | TD-012 | FC-003, FC-004 | FE-005, BE-014 |
| FE-012 | Tool 模式回归验证 | TD-011, TD-012 | FC-003~FC-005 | FE-010, FE-011, BE-014 |
