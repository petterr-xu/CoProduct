# 前端检查清单 - agent

> Version: v0.2.0
> Last Updated: 2026-03-13
> Status: Draft

## 1. 功能检查

1. 预审详情页可展示 `modelTrace/retrievalTrace`，缺失时不报错。
2. 新建预审与再生成支持可选 `debugOptions`。
3. 管理页可查看 runtime 信息并触发 reindex。
4. reindex 提交后有明确状态反馈。
5. 预审详情页可展示 `toolTrace`，未知状态不崩溃。

## 2. 契约对齐检查

1. FE endpoint 集合与 BE 契约一致（5 条）。
2. 枚举映射一致：`retrievalMode`、`job status`。
3. optional 字段解析策略符合 BC 说明。
4. `toolPolicy` 请求字段与后端校验规则一致。

## 3. 状态/异常/空态检查

1. `PERMISSION_DENIED`：管理入口禁用并提示。
2. `MODEL_TIMEOUT/MODEL_RATE_LIMIT`：提示重试。
3. 无 trace 数据：显示“未提供 trace”。
4. reindex 失败：显示失败原因并可重试。
5. `TOOL_EXECUTION_ERROR/TOOL_TIMEOUT`：展示可理解提示并保留详情页主体内容。

## 4. 回归检查

1. 旧后端（无新字段）下前端不崩溃。
2. 新后端下所有新字段正常展示。
3. 原有预审创建、历史、登录流程不受影响。

## 5. 追踪矩阵（AC-FE-*）

| AC-ID | 验收项 | 关联 FE-ID | 关联契约项（FC/BC） |
|---|---|---|---|
| AC-FE-001 | 详情页 trace 字段兼容显示 | FE-002, FE-004 | FC-005 / BC-005 |
| AC-FE-002 | debugOptions 请求正确发送 | FE-005 | FC-003, FC-004 / BC-003, BC-004 |
| AC-FE-003 | runtime/reindex 管理交互可用 | FE-003, FE-007, FE-008 | FC-001, FC-002 / BC-001, BC-002 |
| AC-FE-004 | 新错误码映射正确 | FE-006 | FC-001~FC-005 / BC-001~BC-005 |
| AC-FE-005 | 双模式兼容回归通过 | FE-009 | FC-001~FC-005 / BC-001~BC-005 |
| AC-FE-006 | toolTrace 展示与兼容解析通过 | FE-010 | FC-005 / BC-005 |
| AC-FE-007 | toolPolicy 透传与开关行为正确 | FE-011, FE-012 | FC-003, FC-004 / BC-003, BC-004 |
