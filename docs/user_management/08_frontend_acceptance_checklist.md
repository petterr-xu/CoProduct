# 前端检查清单 - user_management
> Version: v0.2.0
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

## 2. 契约对齐检查

1. `04_frontend_contract.md` 中请求/响应类型与实际调用一致。
2. 登录接口路径与方法为 `POST /api/auth/key-login`。
3. 枚举值大小写完全一致（`OWNER/ADMIN/MEMBER/VIEWER`）。
4. 业务接口统一使用 `Authorization: Bearer <accessToken>`。
5. `POST /api/auth/refresh` 与 `POST /api/auth/logout` 契约采用 Cookie 方案且实现一致。

## 3. 状态/异常/空态检查

1. `AUTH_ERROR` 显示密钥错误提示。
2. `TOKEN_EXPIRED` 触发 refresh；refresh 失败自动回登录页。
3. `PERMISSION_DENIED` 显示无权限提示页。
4. `USER_DISABLED` 显示禁用提示并退出登录。
5. 管理页空列表时显示空态引导。
6. 网络错误与服务错误展示区分明确。
7. `VIEWER` 用户无写操作入口，`MEMBER` 不可访问他人数据入口。

## 4. 回归检查

1. 预审创建、详情、再生成、历史查询、文件上传在登录后可正常使用。
2. 前端已移除静态 `NEXT_PUBLIC_API_TOKEN` 依赖。
3. 旧功能页面不存在死循环重定向或重复请求风暴。
4. 在不同角色账号下，按钮与页面可见性符合权限设计。
