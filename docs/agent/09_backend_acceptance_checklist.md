# 后端检查清单 - agent

> Version: v0.2.1
> Last Updated: 2026-03-13
> Status: Draft

## 1. 功能检查

1. 云模型 provider 可被调用，失败时 fallback 生效。
2. 结构化输出在 schema 不匹配场景下能自动恢复或降级。
3. RAG 分层 pipeline 可运行并返回稳定 evidence 结构。
4. runtime/reindex API 行为符合契约。
5. feature flag 可切换 `heuristic/cloud` 与 `legacy/layered`。
6. Tool Executor 可执行 `retrieve_knowledge` 并受策略约束。
7. prereview/regenerate 提交接口具备“快速受理 + 后台执行”语义。

## 2. 契约对齐检查

1. BC endpoint 与 FC endpoint 一致。
2. 新增响应字段为 optional，不破坏旧消费端。
3. 错误码与状态码映射稳定。
4. `debugOptions.toolPolicy` 校验规则与 BC 定义一致。

## 3. 持久化与流程检查

1. `report_json` 可持久化 trace 字段。
2. reindex job 状态可追踪（至少 QUEUED->DONE/FAILED）。
3. workflow 节点在新 ModelClient 下执行稳定。
4. `toolTrace` 可出现在详情响应且字段语义稳定。
5. 提交接口不再阻塞等待 workflow 完成，session 状态机可追踪。

## 4. 错误与可观测性检查

1. 模型调用日志包含 provider/model/latency/token/cost。
2. 检索日志包含 mode/backend/hit/fusion/rerank。
3. fallback 路径可在日志或 trace 字段中复现。
4. 关键错误码可被稳定触发并识别。
5. tool 调用日志包含 toolName/status/latency/callCount。

## 5. 追踪矩阵（AC-BE-*）

| AC-ID | 验收项 | 关联 BE-ID | 关联契约项（FC/BC） |
|---|---|---|---|
| AC-BE-001 | provider adapter 与 factory 模式切换可用 | BE-001, BE-002, BE-003 | BC-001, BC-003~BC-005 |
| AC-BE-002 | 结构化输出恢复链路有效 | BE-004 | BC-005 |
| AC-BE-003 | router fallback/重试/超时策略有效 | BE-005 | BC-001, BC-005 |
| AC-BE-004 | 模型 trace 完整写入详情响应 | BE-006, BE-007 | BC-005 |
| AC-BE-005 | RAG 分层与 hybrid 检索可用 | BE-008 | BC-005 |
| AC-BE-006 | runtime/reindex API 权限与校验正确 | BE-009 | BC-001, BC-002 |
| AC-BE-007 | 错误码体系与监控字段稳定 | BE-010 | BC-001~BC-005 |
| AC-BE-008 | 索引任务数据可持久化追踪 | BE-011 | BC-002 |
| AC-BE-009 | feature flag 回滚链路可演练 | BE-012 | BC-001~BC-005 |
| AC-BE-010 | Tool 抽象层与 RAG Tool 调用有效 | BE-013 | BC-003~BC-005 |
| AC-BE-011 | tool-calling adapter 关闭/开启行为可控 | BE-014 | BC-003, BC-004 |
| AC-BE-012 | toolTrace 与工具观测埋点完整 | BE-015 | BC-005 |
| AC-BE-013 | prereview/regenerate 提交异步受理生效且响应时延达标 | BE-016, BE-017 | BC-003, BC-004 |
| AC-BE-014 | 受理失败错误码稳定（超时/队列满） | BE-018 | BC-003, BC-004 |
