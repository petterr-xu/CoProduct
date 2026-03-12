# 前端技术落地方案 - user_management
> Version: v0.2.0
> Last Updated: 2026-03-12
> Status: Draft

## 1. 页面与交互范围

### 1.1 用户侧范围

1. 登录页（`/login`）：输入 API Key，完成登录。
2. 受保护业务页：未登录自动跳转登录页。
3. 个人信息入口：展示当前用户、角色、组织、退出登录。

### 1.2 管理侧范围（本轮最小化）

1. Phase 1 不强制完整管理页面。
2. Phase 2 提供简化管理页：用户列表、创建用户、禁用用户、签发/吊销密钥。

### 1.3 核心用户流

1. 首次访问 -> 检查 token -> 无 token 跳转 `/login`。
2. 输入 API Key 登录成功 -> 保存 token -> 返回来源页。
3. 业务请求遇到 `401 TOKEN_EXPIRED` -> 自动 refresh -> 重试一次。
4. refresh 失败 -> 清理登录态并跳转登录页。

## 2. 模块与组件设计

### 2.1 目录建议

1. `src/features/auth/`：登录表单、用户信息、权限守卫。
2. `src/lib/auth-client.ts`：登录/刷新/登出 API。
3. `src/stores/auth-store.ts`：access token、refresh token、user profile。
4. `src/components/auth/route-guard.tsx`：页面级鉴权。

### 2.2 组件分层

1. 页面层：`app/login/page.tsx`、受保护页面布局。
2. 业务组件层：`login-form`, `user-menu`。
3. 数据层：`use-auth` hooks + `api-client`。

## 3. 状态管理与数据获取

### 3.1 状态模型

`AuthState`：

1. `accessToken: string | null`
2. `refreshToken: string | null`
3. `user: { id, email, displayName, role, orgId } | null`
4. `isAuthenticated: boolean`
5. `isBootstrapping: boolean`

### 3.2 数据获取策略

1. 登录：`POST /api/auth/key-login`
2. 启动校验：`GET /api/auth/me`
3. 刷新：`POST /api/auth/refresh`
4. 登出：`POST /api/auth/logout`

统一在 `api-client` 注入 header：

- `Authorization: Bearer <accessToken>`

### 3.3 Token 存储策略

Phase 1 建议：

1. `accessToken` 存内存（Zustand store）。
2. `refreshToken` 存 HttpOnly Cookie（优先）或短期本地存储（开发态兜底）。

### 3.4 Token 策略澄清（v0.2.0）

> Obsolete in v0.2.0: “refreshToken 可放短期本地存储”不再作为默认方案。

本版本统一策略：

1. `accessToken`：仅存内存，不持久化。
2. `refreshToken`：仅由后端通过 HttpOnly Cookie 管理。
3. 前端调用 `POST /api/auth/refresh` 不传请求体；仅携带 Cookie 与 `X-CSRF-Token`。
4. `POST /api/auth/logout` 不再依赖请求体 refresh token，默认登出当前设备会话。

## 4. 契约消费策略

1. 前端视图模型与后端 DTO 分离，统一在 `api-client` 归一化。
2. 错误码驱动 UI 行为，不用文本 message 做分支。
3. 角色与状态枚举使用前端常量集合，超出枚举范围时回退安全默认值。
4. 对既有业务接口保持兼容：只替换鉴权方式，不改业务 payload。

### 4.1 权限消费策略（v0.2.0）

1. 前端仅做“展示层门禁”，不能替代后端鉴权。
2. 页面级权限建议：
- `OWNER/ADMIN`：可进入管理页面。
- `MEMBER`：无管理页入口，保留业务读写。
- `VIEWER`：仅允许查看详情与历史。
3. 对 `403 PERMISSION_DENIED` 统一进入无权限页，不做静默降级。

## 5. 异常与边界状态处理

### 5.1 登录态异常

1. `AUTH_ERROR`：提示“密钥无效或已失效”。
2. `TOKEN_EXPIRED`：静默触发 refresh。
3. `PERMISSION_DENIED`：展示无权限页。
4. `USER_DISABLED`：提示账号已禁用并退出。

### 5.2 页面状态

1. Loading：登录校验阶段显示全屏骨架。
2. Empty：管理页无用户/无密钥时显示引导。
3. Error：区分“网络错误”和“权限错误”。

### 5.3 回退策略

1. refresh 失败时不无限重试，最多一次。
2. 高风险操作（吊销密钥）需二次确认弹窗。

## 6. 阶段映射（Phase 1..N）

### Phase 1（对齐后端 Phase 1）

1. 登录页与路由守卫。
2. 认证状态管理与 token 注入。
3. 401 刷新与登出链路。
4. 业务页平滑接入新鉴权。

### Phase 2（对齐后端 Phase 2）

1. 最小管理员页面（用户列表、禁用、签发密钥）。
2. 角色展示与权限感知 UI（按钮可见性控制）。

### Phase 3（对齐后端 Phase 3）

1. 邀请制注册页面与激活页。
2. 安全提示与会话管理页（查看并踢出会话）。
