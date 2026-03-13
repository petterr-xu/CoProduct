# 后端契约文档 - context_system

> Version: v0.1.0
> Last Updated: 2026-03-13
> Status: Draft

## 1. API 列表（Method + Path）

1. POST /api/context/files/upload
2. GET /api/context/files
3. GET /api/context/files/{fileId}
4. PATCH /api/context/files/{fileId}/visibility
5. PATCH /api/context/files/{fileId}/status
6. GET /api/context/files/{fileId}/acl-candidates
7. POST /api/context/files/{fileId}/reindex
8. GET /api/context/files/{fileId}/events

## 2. 请求结构与校验规则

### BC-001 POST /api/context/files/upload

请求：`multipart/form-data`

1. `file`：必填，允许扩展名白名单。
2. `orgId`：可选；为空时默认使用当前会话组织。
3. `visibilityScope`：必填，枚举见第 4 节。
4. `selectedMemberIds`：仅 `SELECTED_USERS` 时必填。

校验：

1. 文件大小限制（配置项）。
2. `ALL_USERS` 仅 owner/admin 可设。

### BC-002 GET /api/context/files

查询参数：

1. `page`>=1，`pageSize` in [1,100]
2. `keyword` 可选
3. `status` 可选
4. `visibility` 可选

行为：

1. 结果必须经过 ACL 与 `file_status` 过滤。

### BC-003 GET /api/context/files/{fileId}

行为：

1. 无权限返回 `403 PERMISSION_DENIED`。
2. 不存在返回 `404 RESOURCE_NOT_FOUND`。

### BC-004 PATCH /api/context/files/{fileId}/visibility

请求体：

```json
{
  "visibilityScope": "SELECTED_USERS",
  "selectedMemberIds": ["mem_1"]
}
```

校验：

1. `SELECTED_USERS` 需校验成员归属同组织且有效。
2. 非 owner/admin 时禁止设置 `ALL_USERS`。

### BC-005 PATCH /api/context/files/{fileId}/status

请求体：

```json
{
  "status": "OFFLINE"
}
```

校验：

1. 仅允许 `ACTIVE <-> OFFLINE` 转换。

### BC-006 GET /api/context/files/{fileId}/acl-candidates

查询参数：`query`、`limit`。

校验：

1. 仅返回当前组织激活成员。
2. `limit` 默认 10，最大 20。

### BC-007 POST /api/context/files/{fileId}/reindex

校验：

1. 若有运行中同类任务，返回 `409 INGESTION_JOB_CONFLICT`。

### BC-008 GET /api/context/files/{fileId}/events

查询参数：`page`、`pageSize`。

返回最近事件倒序列表。

## 3. 响应结构与字段语义

统一响应体：

```json
{
  "ok": true,
  "data": {},
  "error": null,
  "requestId": "req_xxx"
}
```

错误体：

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "...",
    "details": {}
  },
  "requestId": "req_xxx"
}
```

`ContextFileDetail` 字段语义：

1. `visibilityScope`：文件可见策略。
2. `status`：文件在线状态，影响检索可见性。
3. `ingestionStatus`：最近入库任务状态，不等同于文件状态。
4. `selectedMemberIds`：仅在 `SELECTED_USERS` 返回。

## 4. 状态/错误码规则

枚举：

1. `visibilityScope`: `PRIVATE_SELF` | `TEAM_ONLY` | `SELECTED_USERS` | `ALL_USERS`
2. `status`: `ACTIVE` | `OFFLINE`
3. `ingestionStatus`: `PENDING` | `RUNNING` | `SUCCESS` | `FAILED`

错误码：

1. `PERMISSION_DENIED`
2. `RESOURCE_NOT_FOUND`
3. `VISIBILITY_POLICY_INVALID`
4. `FILE_UPLOAD_INVALID`
5. `FILE_UPLOAD_TOO_LARGE`
6. `FILE_STATUS_CONFLICT`
7. `INGESTION_JOB_CONFLICT`
8. `INGESTION_JOB_FAILED`

## 5. 与前端契约对齐说明

1. FE/BE 端点集合、方法、路径完全一致。
2. 枚举值保持后端原值，前端只做展示映射。
3. 错误码稳定，禁止在不升级版本情况下复用旧码表达新语义。

## 6. 接口明细（BC-*）

| BC-ID | Method | Path | 请求校验 | 响应语义 | 错误码/状态码 | 权限/数据范围 |
|---|---|---|---|---|---|---|
| BC-001 | POST | /api/context/files/upload | file/visibility/size 校验 | 创建文件与 ingest 任务 | 400 FILE_UPLOAD_*, 403 PERMISSION_DENIED | 认证用户，按组织权限上传 |
| BC-002 | GET | /api/context/files | 分页与筛选参数校验 | 返回 actor 可见文件分页 | 400 参数错误 | ACL + status 过滤 |
| BC-003 | GET | /api/context/files/{fileId} | path 存在性校验 | 返回文件详情 | 403/404 | ACL 控制单文件访问 |
| BC-004 | PATCH | /api/context/files/{fileId}/visibility | scope 与成员列表一致性 | 更新可见性并重写 ACL | 400/403/404 | 上传者或管理角色 |
| BC-005 | PATCH | /api/context/files/{fileId}/status | 状态转换校验 | 更新在线状态并写事件 | 400 FILE_STATUS_CONFLICT | 上传者或管理角色 |
| BC-006 | GET | /api/context/files/{fileId}/acl-candidates | query/limit 校验 | 返回成员候选列表 | 403/404 | 限当前组织成员 |
| BC-007 | POST | /api/context/files/{fileId}/reindex | 重复任务冲突校验 | 创建重建任务 | 409 INGESTION_JOB_CONFLICT | 上传者或管理角色 |
| BC-008 | GET | /api/context/files/{fileId}/events | 分页参数校验 | 返回审计事件分页 | 403/404 | 上传者或管理角色 |
