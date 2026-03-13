# 后端技术落地方案 - context_system

> Version: v0.1.0
> Last Updated: 2026-03-13
> Status: Draft

## 1. 模块边界与服务分层

### 1.1 模块划分

```text
backend/app/api/context_files.py                 # Context API
backend/app/services/context_file_service.py     # 文件业务编排
backend/app/services/context_acl_service.py      # 可见性与 ACL 计算
backend/app/services/context_ingestion_service.py # ingest/reindex 调度
backend/app/repositories/context_file_repository.py
backend/app/models/context_file.py
backend/app/models/context_acl_entry.py
backend/app/models/context_ingestion_job.py
backend/app/rag/filters/context_acl_filter.py    # RAG 检索 ACL 过滤
```

### 1.2 分层职责

1. API 层
- 参数解析、权限校验入口、错误码映射。

2. Service 层
- 规则编排：可见性变更、状态变更、下线语义、重建任务。

3. Repository 层
- 数据访问与查询优化（分页、筛选、ACL 联表）。

4. RAG Filter 层
- 将 actor context 转换为检索可执行过滤条件。

## 2. 接口与流程编排

### 2.1 上传流程

1. 认证通过后校验文件类型/大小。
2. 保存文件（本地或对象存储）。
3. 创建 `context_files` 记录与默认 ACL。
4. 创建 `context_ingestion_jobs(PENDING)`。
5. 返回文件 ID 与 ingest 状态。

### 2.2 可见性更新流程

1. 校验操作者是否有权限修改目标文件。
2. 校验 `visibility_scope` 与 `selected_member_ids` 一致性。
3. 更新文件主表可见性字段。
4. 重写 ACL entries（事务内）。
5. 写审计事件。

### 2.3 下线/恢复流程

1. 更新 `file_status` 为 `OFFLINE/ACTIVE`。
2. 写审计事件。
3. 检索链路实时按状态过滤，无需等待索引删除完成。

### 2.4 重建索引流程

1. 创建 `context_ingestion_jobs(PENDING, reindex=true)`。
2. 调度 ingest worker（同步实现或异步任务队列）。
3. worker 完成后回写 `SUCCESS/FAILED` 与错误信息。

## 3. 持久化与一致性策略

### 3.1 数据表

1. `context_files`
- `id`, `org_id`, `uploader_user_id`, `name`, `mime_type`, `size_bytes`, `storage_uri`, `visibility_scope`, `file_status`, `created_at`, `updated_at`。

2. `context_file_acl_entries`
- `id`, `file_id`, `org_id`, `subject_type(USER/ROLE/ORG/GLOBAL)`, `subject_id`, `created_at`。

3. `context_ingestion_jobs`
- `id`, `file_id`, `job_type(INGEST/REINDEX)`, `status`, `error_message`, `started_at`, `finished_at`。

4. `context_file_events`
- `id`, `file_id`, `actor_user_id`, `event_type`, `payload_json`, `created_at`。

### 3.2 一致性策略

1. 可见性更新与 ACL entry 更新必须在单事务内完成。
2. 状态更新成功后检索立即生效（查询层过滤），索引异步清理可延后。
3. 重建任务采用幂等策略：同一文件同类型运行中任务禁止重复创建。

## 4. 模型/工具接入策略

1. 与现有预审流程集成点
- 在 `RagOrchestrator.search()` 入参追加 actor context。
- 调用 `context_acl_filter.build_filter(actor)` 生成 DB-level filter。

2. 与用户系统集成
- 依赖登录态中的 `user_id/org_id/role`。
- `ALL_USERS` 策略受系统配置开关和角色限制控制。

3. 未来扩展
- 段落级 ACL（chunk metadata）
- 基于文档标签/项目维度的 ABAC 扩展

## 5. 错误处理与可观测性

1. 错误码分类
- 参数类：`FILE_UPLOAD_INVALID`, `VISIBILITY_POLICY_INVALID`
- 权限类：`PERMISSION_DENIED`
- 状态类：`FILE_STATUS_CONFLICT`
- 任务类：`INGESTION_JOB_FAILED`, `INGESTION_JOB_CONFLICT`

2. 指标
- 上传成功率、可见性更新成功率、下线生效时延、重建成功率。

3. 日志字段
- `request_id`, `actor_user_id`, `org_id`, `file_id`, `visibility_scope`, `file_status`。

## 6. 阶段映射（Phase 1..N）

1. Phase 1：数据模型与基础 API（上传/列表/详情）。
2. Phase 2：可见性与 ACL entry 管理、下线/恢复。
3. Phase 3：RAG ACL 过滤与重建索引任务。
4. Phase 4：审计日志与可观测性增强。

## 7. 设计实现映射（TD-* -> BE）

| TD-ID | BE 实现模块/服务 | 数据与一致性实现 | 契约依赖（接口/字段） | 观测与测试 |
|---|---|---|---|---|
| TD-001 | `models/context_*` + repository | 四张核心表建模 | BC-001~BC-008 | BE-UT-Model-001 |
| TD-002 | `context_file_service.upload` | 文件与任务记录一致落库 | BC-001 | BE-IT-Upload-001 |
| TD-003 | `list/detail` 查询服务 | 分页 + ACL 范围过滤 | BC-002, BC-003 | BE-IT-List-001 |
| TD-004 | `context_acl_service.update_visibility` | ACL entry 事务更新 | BC-004, BC-006 | BE-IT-Visibility-001 |
| TD-005 | `update_status` | ACTIVE/OFFLINE 状态机 | BC-005 | BE-UT-Status-001 |
| TD-006 | `rag/filters/context_acl_filter.py` | 检索前强制过滤 | BC-002, BC-003 | BE-IT-RagAcl-001 |
| TD-007 | `acl_candidates` 查询 | 组织内成员搜索约束 | BC-006 | BE-IT-Candidate-001 |
| TD-008 | `reindex` + ingestion service | 任务幂等与状态回写 | BC-007 | BE-IT-Reindex-001 |
| TD-009 | `context_file_events` 写入 | 审计事件完整记录 | BC-008 | BE-IT-Audit-001 |
| TD-011 | 统一异常映射中间件 | error code 稳定输出 | BC-008 | BE-UT-ErrorCode-001 |
| TD-012 | schema 预留字段 | 向后兼容 | BC-003 | BE-UT-Compat-001 |

## 8. 风险点实现计划（对应 01）

| Risk-ID | 技术实现细节 | 配置与开关 | 回滚动作 | 验收信号 |
|---|---|---|---|---|
| R-001 | 检索层强制 ACL + default deny | `COPRODUCT_CONTEXT_ACL_ENFORCED=true` | 关闭 context 检索入口并回退内部白名单 | AC-BE-004 |
| R-002 | `ALL_USERS` 仅 admin/owner 可设 | `COPRODUCT_CONTEXT_ALLOW_GLOBAL_VISIBILITY=false`(默认) | 全量迁移为 `TEAM_ONLY` | AC-BE-006 |
| R-003 | 下线状态查询层实时过滤 | 无 | 临时冻结相关文件 ID 结果集 | AC-BE-005 |
| R-004 | reindex 幂等与失败重试接口 | `COPRODUCT_CONTEXT_REINDEX_MAX_RETRY` | 关闭自动重试改人工触发 | AC-BE-007 |
| R-005 | 契约检查脚本纳入 CI | `check_doc_pack_consistency.sh` | 阻断发布并回退合同变更 | AC-E2E-001 |
