# 后端任务拆解文档 - agent

> Version: v0.2.0
> Last Updated: 2026-03-13
> Status: Draft

## 1. Phase 1 任务

1. BE-001：重构 `model_client` 接口层，拆分 structured/embed/rerank 协议。
2. BE-002：实现 OpenAI-compatible provider adapter。
3. BE-003：`factory.py` 支持 `heuristic/cloud` 模式切换与配置装配。
4. BE-004：结构化输出 validate + retry + repair 框架。

## 2. Phase 2 任务

1. BE-005：实现 model router（主备 provider、超时、重试、fallback）。
2. BE-006：新增模型调用观测字段（latency/token/cost/fallback path）。
3. BE-007：接入 workflow 节点到新 router，保证旧行为兼容。

## 3. Phase 3..N 任务

1. BE-008：RAG 分层重构（ingestion/index/retrieval/fusion/rerank/orchestrator）。
2. BE-009：新增 runtime/reindex API（`/api/agent/runtime`, `/api/admin/agent/reindex`）。
3. BE-010：新增 RAG/Model 错误码并统一映射。
4. BE-011：新增知识源与 reindex job 数据模型（或最小落库方案）。
5. BE-012：发布开关与回滚策略落地（model/rag 双开关）。
6. BE-013：Tool 抽象层落地（registry/executor/rag tool）。
7. BE-014：tool-calling adapter 预留（默认关闭）。
8. BE-015：tool 调用观测与审计（toolTrace + logs）。

## 4. 依赖与执行顺序

推荐顺序：

1. BE-001 -> BE-002 -> BE-003 -> BE-004
2. BE-005 -> BE-006 -> BE-007
3. BE-008 -> BE-009 -> BE-010 -> BE-011 -> BE-012

跨端依赖：

1. BE-008/BE-009 完成后 FE-002/FE-003 才能稳定联调。
2. BE-012 完成后 FE-009 才能完成双模式回归。
3. BE-013 完成后 FE-010 才能展示 toolTrace。
4. BE-014 完成后 FE-011/FE-012 才能验证 toolPolicy 与开关。

## 5. 风险与缓解

1. 风险：云模型 schema 漂移导致节点失败。
- 缓解：BE-004 validate + repair/retry + fallback。
2. 风险：RAG 分层改造性能回退。
- 缓解：保留 legacy 模式并增加 benchmark。
3. 风险：多 provider 行为不一致。
- 缓解：adapter 统一返回结构 + 观测字段标准化。
4. 风险：索引重建影响在线服务。
- 缓解：reindex job 异步化与限流。
5. 风险：Tool 执行器引入后请求延迟上升。
- 缓解：`max_tool_calls`、per-tool timeout、短路降级策略。

## 6. 追踪矩阵（BE-*）

| BE-ID | 任务描述 | 关联 TD-ID | 关联契约项（FC/BC） | 依赖任务（FE/BE） |
|---|---|---|---|---|
| BE-001 | ModelClient 抽象重构 | TD-001 | BC-003~BC-005 | - |
| BE-002 | 云 provider adapter | TD-001, TD-002 | BC-003~BC-005 | BE-001 |
| BE-003 | 运行模式配置装配 | TD-002, TD-010 | BC-001 | BE-002 |
| BE-004 | schema 校验与恢复 | TD-003 | BC-005 | BE-001 |
| BE-005 | router/fallback/retry | TD-002 | BC-001 | BE-003, BE-004 |
| BE-006 | 模型 trace 埋点 | TD-004 | BC-005 | BE-005 |
| BE-007 | workflow 节点接入新 client | TD-001, TD-008 | BC-003~BC-005 | BE-005 |
| BE-008 | RAG 分层与 hybrid 检索 | TD-005, TD-006, TD-007 | BC-005 | BE-007 |
| BE-009 | runtime/reindex API | TD-009 | BC-001, BC-002 | BE-005, BE-008 |
| BE-010 | 错误码体系扩展 | TD-010 | BC-001~BC-005 | BE-009 |
| BE-011 | 索引任务落库模型 | TD-007, TD-009 | BC-002 | BE-008 |
| BE-012 | feature flag + 回滚链路 | TD-010 | BC-001~BC-005 | BE-010, BE-011 |
| BE-013 | Tool 抽象层 + RAG Tool 化 | TD-011 | BC-003~BC-005 | BE-008 |
| BE-014 | tool-calling adapter 预留 | TD-012 | BC-003, BC-004 | BE-013 |
| BE-015 | Tool trace 与审计埋点 | TD-011, TD-012 | BC-005 | BE-013, BE-014 |
