# 前端契约文档 - context_system

> Version: v0.1.0
> Last Updated: 2026-03-13
> Status: Draft

## 1. 请求模型（前端视角）

### 1.1 上传文件

`POST /api/context/files/upload`

```json
{
  "file": "binary",
  "orgId": "org_xxx",
  "visibilityScope": "TEAM_ONLY",
  "selectedMemberIds": []
}
```

规则：

1. `visibilityScope=SELECTED_USERS` 时 `selectedMemberIds` 必填且至少 1 个。
2. `visibilityScope!=SELECTED_USERS` 时 `selectedMemberIds` 必须为空。

### 1.2 文件列表

`GET /api/context/files?page=1&pageSize=20&keyword=abc&status=ACTIVE&visibility=TEAM_ONLY`

### 1.3 文件详情

`GET /api/context/files/{fileId}`

### 1.4 可见性更新

`PATCH /api/context/files/{fileId}/visibility`

```json
{
  "visibilityScope": "SELECTED_USERS",
  "selectedMemberIds": ["mem_1", "mem_2"]
}
```

### 1.5 状态更新（下线/恢复）

`PATCH /api/context/files/{fileId}/status`

```json
{
  "status": "OFFLINE"
}
```

### 1.6 候选成员搜索

`GET /api/context/files/{fileId}/acl-candidates?query=alice&limit=10`

### 1.7 触发重建索引

`POST /api/context/files/{fileId}/reindex`

### 1.8 审计事件查询

`GET /api/context/files/{fileId}/events?page=1&pageSize=20`

## 2. 响应模型（前端视图模型）

### 2.1 ContextFileItem

```json
{
  "id": "ctx_file_001",
  "name": "pricing_policy.pdf",
  "orgId": "org_default",
  "uploader": {"userId": "usr_1", "displayName": "Alice"},
  "visibilityScope": "TEAM_ONLY",
  "selectedUsersCount": 0,
  "status": "ACTIVE",
  "ingestionStatus": "SUCCESS",
  "createdAt": "2026-03-13T10:00:00Z",
  "updatedAt": "2026-03-13T10:10:00Z"
}
```

### 2.2 ContextFileDetail

在 `ContextFileItem` 基础上补充：

1. `storageUri`：存储位置。
2. `sizeBytes`：文件大小。
3. `selectedMemberIds`：仅 `SELECTED_USERS` 时返回。
4. `latestIngestionJob`：最近任务状态与错误。

### 2.3 ReindexResponse

```json
{
  "jobId": "ing_job_001",
  "status": "PENDING"
}
```

## 3. 状态与枚举映射

1. `visibilityScope`
- `PRIVATE_SELF` -> 仅个人
- `TEAM_ONLY` -> 仅团队
- `SELECTED_USERS` -> 部分用户
- `ALL_USERS` -> 所有用户

2. `status`
- `ACTIVE` -> 已启用
- `OFFLINE` -> 已下线

3. `ingestionStatus`
- `PENDING`/`RUNNING`/`SUCCESS`/`FAILED`

## 4. 错误码到 UI 行为映射

1. `PERMISSION_DENIED`：toast + 禁用对应操作。
2. `VISIBILITY_POLICY_INVALID`：高亮可见性表单字段。
3. `FILE_STATUS_CONFLICT`：刷新详情并提示“状态已变化”。
4. `INGESTION_JOB_CONFLICT`：提示“已有运行中任务”。
5. `FILE_UPLOAD_TOO_LARGE`：上传控件内联错误。

## 5. 与后端契约对齐说明

1. FE 与 BE 使用一致的路径、枚举与错误码。
2. FE 不生成权限判断真值，权限以 BE 返回为准。
3. FE 对未知新增字段保持容错，不阻断渲染。

## 6. 接口明细（FC-*）

| FC-ID | Method | Path | 请求字段 | 响应字段 | 枚举/错误码 | 权限/数据范围 |
|---|---|---|---|---|---|---|
| FC-001 | POST | /api/context/files/upload | multipart(file), orgId, visibilityScope, selectedMemberIds | ContextFileDetail | visibilityScope, FILE_UPLOAD_* | 认证用户；仅可上传到有权限 org |
| FC-002 | GET | /api/context/files | page,pageSize,keyword,status,visibility | items,total,page,pageSize | status/visibility | 仅返回当前 actor 可见文件 |
| FC-003 | GET | /api/context/files/{fileId} | path:fileId | ContextFileDetail | PERMISSION_DENIED, NOT_FOUND | 仅可访问有权限文件 |
| FC-004 | PATCH | /api/context/files/{fileId}/visibility | visibilityScope, selectedMemberIds | ContextFileDetail | VISIBILITY_POLICY_INVALID | owner/admin 或文件上传者（受策略限制） |
| FC-005 | PATCH | /api/context/files/{fileId}/status | status(ACTIVE/OFFLINE) | ContextFileDetail | FILE_STATUS_CONFLICT | owner/admin 或文件上传者 |
| FC-006 | GET | /api/context/files/{fileId}/acl-candidates | query,limit | member candidates[] | PERMISSION_DENIED | 仅组织内可选成员 |
| FC-007 | POST | /api/context/files/{fileId}/reindex | path:fileId | jobId,status | INGESTION_JOB_CONFLICT | owner/admin 或文件上传者 |
| FC-008 | GET | /api/context/files/{fileId}/events | page,pageSize | event items,total | PERMISSION_DENIED | owner/admin 或文件上传者 |
