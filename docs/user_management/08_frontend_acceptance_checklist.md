# 前端检查清单 - user_management
> Version: v0.5.0
> Last Updated: 2026-03-12
> Status: Draft

## 1. 功能检查

### 1.1 Phase 1 功能

1. `/login` 可输入 API Key 完成登录。
2. 登录后访问业务页无需手工配置 `NEXT_PUBLIC_API_TOKEN`。
3. 未登录访问受保护页会跳转登录。
4. 登出后 token 清理，无法继续访问受保护页。
5. access token 过期时可自动 refresh 并恢复请求。
6. refresh 请求不携带 body token，基于 Cookie + `X-CSRF-Token` 正常工作。

### 1.2 Phase 2 功能

1. 管理入口仅 `OWNER/ADMIN` 可见。
2. 用户列表加载、筛选与分页正常。
3. 创建用户、禁用用户、角色变更功能可用。
4. API Key 签发时能一次性展示明文 key。
5. API Key 吊销后页面状态及时更新。
6. 用户/API Key 列表均使用统一分页字段（`items/total/page/pageSize`）。

### 1.3 Phase 4 功能（v0.3.0 新增）

1. 管理页可区分展示“权限角色”与“职能角色”。
2. 成员仅可绑定一个职能角色，UI 不允许多选。
3. `OWNER/ADMIN` 显示为中文可读标签，不再裸展示枚举值。
4. 对高风险操作（自降权/自禁用/操作 owner）按钮禁用并有明确原因提示。
5. 职能角色管理页可完成基础维护（查看/新增/启停用）。
6. 成员列表支持按职能角色筛选。

### 1.4 Phase 5 功能（v0.4.0 新增）

1. AC-FE-501：登录后可成功请求 `GET /api/auth/context` 并渲染当前组织信息。
2. AC-FE-502：创建成员表单不再出现 `orgId` 文本输入框，只能使用组织下拉。
3. AC-FE-503：`scopeMode=ORG_SCOPED` 时组织下拉默认选中并不可编辑。
4. AC-FE-504：`activeOrg=null` 时创建成员按钮禁用并显示引导提示。
5. AC-FE-505：后端返回 `NO_ACTIVE_ORG` 时前端提示文案清晰且无静默失败。
6. AC-FE-506：在不改接口结构的前提下，页面可兼容未来 `USER_SCOPED`（多组织选项渲染不报错）。

### 1.5 Phase 6 功能（v0.5.0 新增）

1. AC-FE-601：API Key 签发表单不再以手工 `userId` 文本输入作为主路径，改为成员联想选择。
2. AC-FE-602：成员联想可按邮箱/显示名前缀返回候选，并支持空结果提示。
3. AC-FE-603：`ORG_SCOPED` 下签发组织固定为当前组织；组织变化会清空已选成员。
4. AC-FE-604：签发成功后可展示明文 key；列表中可展示目标成员邮箱/显示名。
5. AC-FE-605：`NO_ACTIVE_ORG/PERMISSION_DENIED/RESOURCE_NOT_FOUND` 在签发场景下提示明确。
6. AC-FE-606：未来 `USER_SCOPED` 分支下，组织下拉与成员候选联动不报错。

## 2. 契约对齐检查

1. `04_frontend_contract.md` 中请求/响应类型与实际调用一致。
2. 登录接口路径与方法为 `POST /api/auth/key-login`。
3. 枚举值大小写完全一致（`OWNER/ADMIN/MEMBER/VIEWER`）。
4. 业务接口统一使用 `Authorization: Bearer <accessToken>`。
5. `POST /api/auth/refresh` 与 `POST /api/auth/logout` 契约采用 Cookie 方案且实现一致。
6. 成员接口路径演进（`users` -> `members`）在兼容期可双栈运行且前端封装一致。
7. 职能角色字段（`functionalRoleId/name/code`）与后端契约一致。
8. `GET /api/auth/context` 响应字段与 `04_frontend_contract.md` 一致（`activeOrg/availableOrgs/scopeMode`）。
9. 创建成员请求中的 `orgId` 若存在，来源必须是下拉选项，不允许任意文本。
10. `GET /api/admin/member-options` 请求/响应字段与契约一致（`query/orgId/limit` + `items[]`）。
11. `POST /api/admin/api-keys` 在 Phase 6 支持 `orgId?` 语义且前端行为与 `scopeMode` 对齐。
12. `GET /api/admin/api-keys` 扩展字段 `userEmail/userDisplayName` 可兼容渲染。

## 3. 状态/异常/空态检查

1. `AUTH_ERROR` 显示密钥错误提示。
2. `TOKEN_EXPIRED` 触发 refresh；refresh 失败自动回登录页。
3. `PERMISSION_DENIED` 显示无权限提示页。
4. `USER_DISABLED` 显示禁用提示并退出登录。
5. 管理页空列表时显示空态引导。
6. 网络错误与服务错误展示区分明确。
7. `VIEWER` 用户无写操作入口，`MEMBER` 不可访问他人数据入口。
8. 联想输入快速变更时不会造成请求风暴或候选错位提交。

## 4. 回归检查

1. 预审创建、详情、再生成、历史查询、文件上传在登录后可正常使用。
2. 前端已移除静态 `NEXT_PUBLIC_API_TOKEN` 依赖。
3. 旧功能页面不存在死循环重定向或重复请求风暴。
4. 在不同角色账号下，按钮与页面可见性符合权限设计。
5. 权限红线相关失败场景展示正确文案，不出现静默失败。

## 5. 追踪映射（v0.5.0 增量）

| 验收项 | 关联任务 | 关联契约 |
|---|---|---|
| AC-FE-501 | FE-5.1 | FC-401 |
| AC-FE-502 | FE-5.2 | FC-402 |
| AC-FE-503 | FE-5.3 | FC-401/FC-402 |
| AC-FE-504 | FE-5.4 | FC-403 |
| AC-FE-505 | FE-5.4 | FC-403 |
| AC-FE-506 | FE-5.5 | FC-401 |
| AC-FE-601 | FE-6.3 | FC-501 |
| AC-FE-602 | FE-6.2 | FC-501 |
| AC-FE-603 | FE-6.1 | FC-502 |
| AC-FE-604 | FE-6.4 | FC-503 |
| AC-FE-605 | FE-6.5 | FC-502 |
| AC-FE-606 | FE-6.6 | FC-501/FC-502/FC-503 |
