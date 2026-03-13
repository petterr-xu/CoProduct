# 前端技术落地方案 - context_system

> Version: v0.1.0
> Last Updated: 2026-03-13
> Status: Draft

## 1. 页面与交互范围

1. `GET /context/files` 文件管理页
- 文件列表（名称、上传人、可见性、状态、更新时间、ingest 状态）。
- 筛选维度（状态、可见性、上传人、关键字）。

2. 上传交互
- 上传文件 -> 设置可见性 -> 提交。
- 可选：`SELECTED_USERS` 时展示成员搜索与多选。

3. 文件操作
- 修改可见性。
- 下线/恢复文件。
- 触发重建索引。

4. 文件详情侧栏
- 展示文件元数据、ACL 配置、最近任务状态、审计摘要。

## 2. 模块与组件设计

```text
frontend/src/app/context/files/page.tsx            # 文件管理页
frontend/src/components/context/file-table.tsx     # 列表表格
frontend/src/components/context/upload-dialog.tsx  # 上传弹窗
frontend/src/components/context/visibility-dialog.tsx # 可见性配置
frontend/src/components/context/status-action.tsx  # 下线/恢复按钮
frontend/src/components/context/reindex-action.tsx # 重建索引按钮
frontend/src/hooks/use-context-files.ts            # 列表/详情查询
frontend/src/hooks/use-context-mutations.ts        # 上传/更新/重建
frontend/src/lib/context-api-client.ts             # Context API 客户端
```

设计原则：

1. 页面状态与 API 结构解耦，组件使用视图模型。
2. 所有突变操作必须有 optimistic 错误回滚策略。
3. 影响范围大的操作（可见性、下线）必须二次确认。

## 3. 状态管理与数据获取

1. 使用 `react-query`：
- Query keys：`context-files`, `context-file-detail`, `context-ingestion-jobs`。
- Mutation 成功后按粒度失效缓存。

2. 本地 UI 状态：
- 上传中、提交中、可见性编辑草稿、确认弹窗状态。

3. 权限相关状态：
- 当前登录态角色决定是否可见 `ALL_USERS` 选项。
- 非 admin/owner 隐藏高风险操作按钮。

## 4. 契约消费策略

1. 前端仅消费 `04_frontend_contract.md` 中定义的字段，不直接透传后端实体。
2. `visibility_scope` 使用映射字典转换为可读文案。
3. `SELECTED_USERS` 模式下，必须先调用候选成员接口并做去重。
4. 下线/恢复接口使用幂等按钮策略，防止重复提交。

## 5. 异常与边界状态处理

1. 上传失败：展示 `FILE_UPLOAD_INVALID` 或 `FILE_UPLOAD_TOO_LARGE` 具体提示。
2. 可见性更新失败：展示 `VISIBILITY_POLICY_INVALID`、`PERMISSION_DENIED`。
3. 下线冲突：展示 `FILE_STATUS_CONFLICT` 并刷新详情。
4. 任务失败：展示 ingest 失败原因和“重试重建”入口。
5. 空态：无文件时提示“上传首个上下文文件”。

## 6. 阶段映射（Phase 1..N）

1. Phase 1：列表/详情/上传最小可用界面。
2. Phase 2：可见性策略编辑、成员搜索、下线/恢复。
3. Phase 3：重建索引、任务状态展示、审计摘要。
4. Phase 4：交互优化与可观测埋点（操作成功率、失败率）。

## 7. 设计实现映射（TD-* -> FE）

| TD-ID | FE 实现模块/页面 | 状态与数据策略 | 契约依赖（接口/字段） | 观测与测试 |
|---|---|---|---|---|
| TD-002 | `upload-dialog` + `use-context-mutations` | mutation + loading/rollback | FC-001 | FE-UT-Upload-001 |
| TD-003 | `file-table` + detail panel | query + pagination + filter | FC-002, FC-003 | FE-IT-List-001 |
| TD-004 | `visibility-dialog` | 表单校验 + 确认弹窗 | FC-004, FC-006 | FE-IT-Visibility-001 |
| TD-005 | `status-action` | 幂等 mutation + 刷新详情 | FC-005 | FE-IT-Status-001 |
| TD-007 | 成员联想选择器 | debounced query | FC-006 | FE-UT-MemberSearch-001 |
| TD-008 | `reindex-action` | 提交后轮询任务状态 | FC-007 | FE-IT-Reindex-001 |
| TD-010 | 高风险策略提示组件 | 本地确认状态机 | FC-004, FC-005 | FE-UT-Confirm-001 |
| TD-011 | 全局错误提示映射 | error code -> i18n 文案 | FC-008 | FE-UT-ErrorMap-001 |
| TD-012 | 预留扩展字段渲染 | unknown field tolerant parsing | FC-003 | FE-UT-ForwardCompat-001 |
