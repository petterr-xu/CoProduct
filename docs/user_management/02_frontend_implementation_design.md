# 前端技术落地方案 - user_management
> Version: v0.5.0
> Last Updated: 2026-03-12
> Status: Draft

> Design Priority (v0.5.0): 若旧段落与 v0.5.0 新增规则冲突，以 v0.5.0 为准；v0.4.0 作为兼容基线保留。

## 1. 页面与交互范围

### 1.1 用户侧范围（已完成基础）

1. 登录页（`/login`）：输入 API Key 完成登录。
2. 受保护业务页：未登录自动跳转。
3. 用户信息入口：展示账号与权限角色。
4. v0.4.0 新增：显示“当前组织”并在创建成员时提供组织下拉。
5. v0.5.0 新增：API Key 签发支持“组织选择 + 成员联想搜索”，不再主打手输 `userId`。

### 1.2 管理侧范围（Phase 2 已完成，Phase 4 增强）

1. 已有：用户/密钥/审计基础页面。
2. 新增（Phase 4）：
- 职能角色管理页面（列表/新建/启停用）。
- 成员详情编辑中的“权限角色 + 职能角色 + 成员状态”联动校验。
- 高风险操作前置提示（自操作限制、owner 约束提示）。
3. 新增（Phase 5）：
- 创建成员表单移除 `orgId` 文本输入，改为组织下拉。
- 当 `AuthContext.activeOrg` 为空时，禁用创建成员并展示引导提示。
4. 新增（Phase 6）：
- API Key 签发表单支持按邮箱/显示名前缀搜索成员并选择目标。
- API Key 签发在 `ORG_SCOPED` 下锁定组织，在 `USER_SCOPED` 预留组织切换。
- API Key 列表展示成员可读信息（邮箱/显示名），减少 `userId` 认知负担。

## 2. 前端领域模型

### 2.1 身份模型映射（v0.3.0）

1. 全局身份（`UserAccountView`）
- `id/email/displayName/accountStatus`
2. 组织成员身份（`MembershipView`）
- `membershipId/userId/orgId/permissionRole/memberStatus/functionalRole`
3. 职能角色（`FunctionalRoleView`）
- `id/code/name/isActive/sortOrder`

> Obsolete in v0.3.0: 旧版仅展示 `user.role/status/orgId`，无法表达成员身份与职能角色。

### 2.2 权限与职能分离

1. 权限角色用于门禁判断（OWNER/ADMIN/MEMBER/VIEWER）。
2. 职能角色仅用于协作语义（产品经理/运营等），不直接做权限分支。

## 3. 模块设计与目录建议

1. `src/features/auth/`：认证状态与登录链路。
2. `src/features/auth-context/`：登录上下文加载与组织选择状态。
2. `src/features/admin-members/`：成员列表、成员编辑、高风险操作确认。
3. `src/features/admin-functional-roles/`：职能角色管理。
4. `src/lib/acl.ts`：统一前端权限可见性策略（仅做展示层，不替代后端）。
5. `src/lib/enum-labels.ts`：枚举到文案映射，避免 UI 直接展示原始枚举。

## 4. 数据获取与契约消费

### 4.1 认证链路（沿用）

1. `POST /api/auth/key-login`
2. `POST /api/auth/refresh`
3. `POST /api/auth/logout`
4. `GET /api/auth/me`
5. `GET /api/auth/context`（v0.4.0 新增）

### 4.2 管理链路（Phase 4 增强）

1. 成员接口优先消费 `/api/admin/members/*`；兼容期容忍 `/api/admin/users/*`。
2. 新增职能角色接口：
- `GET /api/admin/functional-roles`
- `POST /api/admin/functional-roles`
- `PATCH /api/admin/members/{id}/functional-role`
3. 管理列表统一分页契约：`items/total/page/pageSize`。

### 4.5 API Key 签发可用性升级（v0.5.0）

1. 签发表单组织规则：
- `ORG_SCOPED`：组织默认 `activeOrg` 且不可编辑。
- `USER_SCOPED`（预留）：组织下拉来源 `availableOrgs`，切换组织后清空成员选择。
2. 成员检索规则：
- 新增调用 `GET /api/admin/member-options?orgId&query&limit`。
- `query` 采用前缀匹配（邮箱/显示名），触发阈值建议 `>=2` 字符。
- 组件仅允许从候选项中选择成员，不允许自由输入 `userId` 直接提交。
3. 签发请求规则：
- `POST /api/admin/api-keys` 提交 `userId/name/expiresAt`，并在 Phase 6 增加 `orgId?` 语义。
- 若上下文无组织，禁用签发按钮并提示 `NO_ACTIVE_ORG`。
4. API Key 列表可读性：
- 在列表中展示 `userDisplayName/userEmail`；`userId` 作为次要信息保留。

### 4.4 上下文驱动组织选择（v0.4.0）

1. 页面初始化顺序：
- 先加载 `auth/me`。
- 再加载 `auth/context`，拿到 `activeOrg` 与 `availableOrgs`。
2. 创建成员表单规则：
- 组织选项来源仅限 `availableOrgs`。
- `ORG_SCOPED` 下默认选中并锁定 `activeOrg`。
- `USER_SCOPED`（未来）允许在下拉中切换组织后提交。
3. 无组织处理：
- `activeOrg == null` 时禁用“创建成员”按钮。
- 页面展示“当前账号无可用组织，请联系管理员”。

> Obsolete in v0.4.0: 创建成员时手工输入 `orgId` 的文本框交互已过时。

### 4.3 契约兼容策略

1. 前端 API client 允许 camelCase/snake_case 双读（兼容过渡期）。
2. 新增字段必须可空容错，待后端完整发布后再提升为必填展示。

## 5. 交互与可读性规范（v0.3.0）

### 5.1 枚举可读化

1. UI 只展示中文标签：
- `OWNER -> 组织拥有者`
- `ADMIN -> 管理员`
- `MEMBER -> 成员`
- `VIEWER -> 只读成员`
2. 状态同理映射为中文，原始值仅在调试或 tooltip 显示。

### 5.2 高风险操作交互

1. 对“禁用成员/修改权限角色/吊销 key”必须二次确认。
2. 被后端拒绝时展示明确原因：
- 不能修改 owner
- 不能禁用最后一个 owner
- 不能自降权/自禁用

### 5.3 门禁规则

1. 页面入口：
- 仅 `OWNER/ADMIN` 可见管理入口。
2. 操作可见性：
- 对 owner 目标对象，非 owner 不展示可操作按钮。
- 对当前登录成员本人的高风险操作默认禁用并标注原因。

## 6. 状态管理与一致性

1. `auth-store` 保留 access token 与当前 `AuthUserView`。
2. 管理页数据由 React Query 管理。
3. 所有成员变更 mutation 成功后必须刷新：
- 成员列表
- 职能角色列表（如受影响）
- 审计日志列表

## 7. 阶段映射（Phase 1..N）

### Phase 1（已完成）

1. 登录、守卫、token 注入、refresh。

### Phase 2（已完成）

1. 最小管理页面（用户/密钥/审计）。

### Phase 3（在研）

1. 邀请制、安全中心、会话管理。

### Phase 4（v0.3.0 新增）

1. 成员模型 UI 升级（全局身份 vs 组织内身份）。
2. 权限角色与职能角色分离展示与编辑。
3. 高风险治理规则前端显式提示与按钮禁用。
4. 枚举文案可读化统一改造。

### Phase 5（v0.4.0 新增）

1. 登录上下文接入（`/api/auth/context`）并完成状态管理。
2. 创建成员组织输入改为下拉选择（上下文驱动）。
3. 无组织场景 UI 引导与错误提示（`NO_ACTIVE_ORG`）。
4. 为未来多组织登录保留 `USER_SCOPED` 展示与交互分支。

### Phase 6（v0.5.0 新增）

1. API Key 签发改为组织上下文驱动的成员联想选择。
2. 新增成员检索 API 消费与自动补全组件。
3. API Key 列表展示成员可读信息并保留 userId 辅助排障。
4. `USER_SCOPED` 场景下保留组织切换分支，不破坏当前 `ORG_SCOPED`。

## 8. 风险与缓解

1. 风险：后端规则先收紧导致前端按钮可点击但请求失败。
- 缓解：前端同步接入 `can*` 字段或本地镜像规则禁用按钮。
2. 风险：过渡期接口路径并存导致调用混乱。
- 缓解：API client 统一封装路由选择，页面层禁止拼接路径。
3. 风险：枚举文案映射漏配导致展示空白。
- 缓解：映射函数提供兜底 `未知(<raw>)`，并打日志告警。
4. 风险：上下文拉取失败导致管理页交互不可用。
- 缓解：上下文加载失败时阻断高风险写操作，仅保留只读视图并提示重试。
5. 风险：成员联想结果与最终签发目标不一致，导致误签发。
- 缓解：候选项强类型绑定 `userId`，提交前必须存在已选候选且与当前组织匹配。
6. 风险：成员检索接口高频触发导致管理页抖动或压测风险。
- 缓解：前端增加防抖、最小输入长度与请求取消；后端 `limit` 上限固定。

## 9. FE 追踪矩阵（v0.5.0 增量）

| TD ID | FE 模块 | API | 状态管理 | 错误处理 | 测试要点 |
|---|---|---|---|---|---|
| TD-401 | `features/auth-context` | `GET /api/auth/context` | `auth-store/context-store` | context 拉取失败降级只读 | context 成功/失败分支 |
| TD-402 | `features/admin-members` | `POST /api/admin/users` | 创建表单本地状态 | 禁止自由输入 orgId | 组织下拉仅来源于 context |
| TD-403 | `features/admin-members` | 同上 | 提交前校验 activeOrg | `NO_ACTIVE_ORG` 提示引导 | 无 activeOrg 禁止创建 |
| TD-404 | `features/auth-context` | `GET /api/auth/context` | `scopeMode` 分支 | 未知模式兜底 ORG_SCOPED | ORG_SCOPED/USER_SCOPED UI 分支 |
| TD-501 | `features/admin-api-keys` | `POST /api/admin/api-keys` | 签发表单改为“已选成员”状态 | 禁止手输 userId 直提 | 候选选择/提交联动 |
| TD-502 | `features/admin-api-keys` | `GET /api/admin/member-options` | 联想查询状态（防抖/取消） | 空候选与异常提示 | 前缀检索准确性 |
| TD-503 | `features/admin-api-keys` | `POST /api/admin/api-keys` | org 上下文与表单双向约束 | 跨组织拒绝提示 | ORG_SCOPED/USER_SCOPED 分支 |
| TD-504 | `features/admin-api-keys` | `GET /api/admin/api-keys` | 列表项视图模型增强 | 缺字段兜底展示 | 可读字段显示正确 |
| TD-505 | `features/admin-api-keys` | `GET /api/auth/context` + 签发接口 | 组织选择分支预埋 | 未知 scopeMode 兜底 | 多组织预埋回归 |
