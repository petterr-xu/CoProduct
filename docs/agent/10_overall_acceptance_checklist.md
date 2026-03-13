# 总体检查清单 - agent

> Version: v0.2.1
> Last Updated: 2026-03-13
> Status: Draft

## 1. 端到端链路检查

1. 登录 -> 新建预审 -> 详情展示 trace -> 再生成，全链路可用。
2. 提交预审后应快速受理并进入 `PROCESSING`，不因长耗时模型调用导致前端超时假失败。
3. 管理员可查看 runtime 并触发 reindex，状态可见。
4. 切换到 fallback 模式后（heuristic/legacy）业务链路仍可用。
5. 启用 Tool 模式后，`retrieve_knowledge` 路径可用且可回退。

## 2. 前后端契约兼容性检查

1. FC/BC endpoint 集合一致。
2. 新增字段 optional 行为一致。
3. 枚举和错误码语义一致。
4. `toolPolicy` 字段语义在 FE/BE 两侧一致。

## 3. 阶段完成度检查（Phase 1..N）

1. Phase 1：云模型接入与兼容运行完成。
2. Phase 1.5：提交异步受理与前端轮询链路完成（关闭超时缺陷）。
3. Phase 2：路由可靠性与可观测完成。
4. Phase 3：分层 RAG 与 hybrid 检索完成。
5. Phase 4：运维入口与回滚机制完成。
6. Phase 5：RAG Tool 化与 tool-calling 预留完成。

## 4. 发布 Gate

满足以下条件才允许上线：

1. AC-FE/AC-BE/AC-E2E 全部通过。
2. fallback 演练通过（至少一次切换成功）。
3. 关键错误码告警规则已配置。
4. 回滚脚本和开关说明已确认。
5. Tool 模式压测结果满足延迟预算（或有明确降级策略）。

## 5. 追踪矩阵（AC-E2E-*）

| AC-ID | 验收项 | 关联 TD-ID | 关联 FE-ID | 关联 BE-ID |
|---|---|---|---|---|
| AC-E2E-001 | 云模型主路径可稳定完成预审 | TD-001, TD-002 | FE-002, FE-004 | BE-001, BE-002, BE-005, BE-007 |
| AC-E2E-002 | 前后端契约完全对齐且兼容旧数据 | TD-008 | FE-001, FE-002, FE-009 | BE-007, BE-010 |
| AC-E2E-003 | 分层 RAG 在 hybrid 模式下输出高质量证据 | TD-005, TD-006, TD-007 | FE-004 | BE-008 |
| AC-E2E-004 | fallback 与回滚开关可在故障时生效 | TD-010 | FE-009 | BE-005, BE-012 |
| AC-E2E-005 | 管理端 runtime/reindex 运维闭环可用 | TD-009 | FE-003, FE-007, FE-008 | BE-009, BE-011 |
| AC-E2E-006 | RAG Tool 化后业务链路稳定 | TD-011 | FE-010, FE-012 | BE-013, BE-015 |
| AC-E2E-007 | tool-calling 适配层默认关闭且可灰度启用 | TD-012 | FE-011, FE-012 | BE-014, BE-015 |
| AC-E2E-008 | 提交接口异步受理生效，前端不再出现固定超时假失败 | TD-013 | FE-013, FE-014 | BE-016, BE-017, BE-018 |
