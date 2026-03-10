# CoProduct 后端里程碑验收清单（M1/M2/M3）

## 1. 验收原则

- 仅按 `docs/coproduct_backend_technical_design.md` 判定通过/不通过
- 每条验收项必须可通过 API 调用或数据库查询验证
- 验收结果分为：`PASS` / `FAIL` / `BLOCKED`

---

## 2. M1 验收（主链路可跑通）

## 2.1 API 与鉴权

1. 未携带 API Token 调用任一受保护接口，返回鉴权失败
2. `POST /api/prereview` 参数合法时可创建 session 并返回 `PROCESSING`
3. `GET /api/prereview/{session_id}` 可查询到状态和基础报告结构

## 2.2 工作流执行

1. LangGraph 工作流可执行完整节点链路
2. 任一节点失败时 session 最终为 `FAILED`
3. 失败时能定位到具体节点并记录错误码

## 2.3 持久化

1. `requests/sessions/reports/evidence_items` 成功写入
2. `sessions` 可看到 `started_at/finished_at/status`
3. workflow 中间结果可在数据库中回查

---

## 3. M2 验收（结果质量可用）

## 3.1 RAG 检索

1. `KnowledgeRetriever` 按固定流程执行：
   - FTS top20
   - 向量 top20
   - 合并去重
2. `EvidenceSelector` 最终输出 top8 evidence

## 3.2 报告结构

1. 报告固定 8 区块全部存在
2. `CapabilityJudge` 输出必须是固定枚举之一
3. 无高质量证据时，能力判断不能是 `SUPPORTED`

## 3.3 可追溯性

1. 报告中的 evidence 引用可映射到 `evidence_items`
2. 每条 evidence 能追溯到 `doc_id + chunk_id`
3. 关键节点有 latency 日志

---

## 4. M3 验收（版本、文件、历史与稳定性）

## 4.1 regenerate

1. 调用 `POST /api/prereview/{session_id}/regenerate` 后创建新 session
2. 新 session 的 `version = 旧 version + 1`
3. 新 session 的 `parent_session_id = 旧 session_id`
4. 新 session 重走完整 workflow 并可查询结果

## 4.2 文件链路

1. `POST /api/files/upload` 返回稳定 `file_id`
2. 文件元信息写入 `uploaded_files`
3. 非白名单文件类型被拒绝
4. 超出大小限制被拒绝
5. 创建预审时可读取 file 文本并并入 `normalized_request`

## 4.3 历史查询

1. `GET /api/history` 支持分页
2. `keyword` 过滤可用
3. `capabilityStatus` 过滤可用
4. 可返回版本信息（含 version）

## 4.4 错误与降级

1. 检索为空时仍返回可用报告，且能力判断符合降级规则
2. `RiskAnalyzer` 异常时风险区块为空，不影响主流程返回
3. `ImpactAnalyzer` 异常时影响区块为空，不影响主流程返回
4. `ReportComposer` 异常时 session 标记 `FAILED`

---

## 5. 典型样例回归（10~20 条）

每条样例至少验证：

1. 能力判断枚举合法
2. 报告结构完整
3. evidence 可回溯
4. session 状态正确
5. 日志可定位关键节点耗时

建议样例覆盖：

1. 已支持能力（高证据）
2. 部分支持（约束缺失）
3. 不支持（证据不足）
4. 需补充信息（需求不完整）
5. 导出+敏感字段（风险高）
6. 批量+大数据量（性能风险）

---

## 6. 发布前 Gate（必须全部 PASS）

1. 5 个 API 均可正常调用
2. regenerate 版本链正确
3. 文件上传与解析最小能力可用
4. 报告 8 区块稳定输出
5. evidence 全链路可追溯
6. 失败可定位到 workflow 节点
7. PostgreSQL 数据可回查
