# 前端任务拆解文档 - user_management
> Version: v0.2.0
> Last Updated: 2026-03-12
> Status: Draft

## 1. Phase 1 任务

目标：完成登录与业务鉴权切换，保证既有预审流程可继续使用。

1. FE-1.1 新增认证类型与枚举
- 定义 `Role/UserStatus` 与认证响应类型。
- 更新 `src/types` 与 schema 校验。
2. FE-1.2 实现认证 API Client
- 新增 `key-login/refresh/logout/me` 请求封装。
- 统一错误码解析。
> Obsolete in v0.2.0: FE-1.2 中“refresh body 传 token”实现路径不再使用。
3. FE-1.2a 刷新/登出 Cookie 化改造（v0.2.0）
- `refresh/logout` 改为 Cookie + `X-CSRF-Token` 方案。
- 删除前端持久化 refresh token 的实现。
4. FE-1.3 接入认证状态管理
- 新建 `auth-store`，管理 token 与当前用户。
- 启动时执行 `me` 校验。
5. FE-1.4 登录页与路由守卫
- 新增 `/login` 页面。
- 为业务页面增加 route guard。
6. FE-1.5 业务请求鉴权改造
- `api-client` 注入动态 `Authorization`。
- 401 场景触发 refresh 并重试一次。
7. FE-1.6 退出登录与异常处理
- `logout` 清理本地状态。
- `USER_DISABLED/PERMISSION_DENIED` UI 提示。
8. FE-1.7 数据可见范围联调（v0.2.0）
- `MEMBER` 仅本人数据、`VIEWER` 只读的前端行为校验。
- 无权限操作按钮禁用并显示原因。

## 2. Phase 2 任务

目标：提供团队管理最小可用前端能力。

1. FE-2.1 管理入口与权限门禁
- 管理入口仅 `OWNER/ADMIN` 可见。
2. FE-2.2 用户管理页面（简版）
- 用户列表、状态筛选、创建用户。
3. FE-2.3 角色与状态操作
- 修改用户状态与角色。
4. FE-2.4 API Key 管理页面（简版）
- 签发 key（一次性展示明文）。
- 吊销 key。
5. FE-2.5 审计日志查询页面（只读）
- 支持基础筛选与分页。
6. FE-2.6 管理列表契约对齐（v0.2.0）
- 用户/API Key 列表统一 `items/total/page/pageSize`。
- 列表筛选参数与后端契约一致。

## 3. Phase 3..N 任务

目标：安全增强与企业化扩展。

1. FE-3.1 邀请制注册与激活 UI。
2. FE-3.2 个人会话管理页面（查看与踢出会话）。
3. FE-3.3 安全中心（异常提示、风控反馈）。
4. FE-3.4 多组织切换与组织级偏好设置（如启用）。

## 4. 依赖与执行顺序

### 4.1 依赖

1. FE-1.2 依赖后端认证接口可用。
2. FE-1.4 依赖 FE-1.3 状态管理完成。
3. FE-1.5 依赖 FE-1.2、FE-1.3 完成。
4. FE-2.x 依赖后端管理 API 与权限模型稳定。

### 4.2 推荐顺序

1. 类型定义 -> API Client -> 状态管理 -> 登录页/守卫 -> 请求注入改造 -> 异常收口。
2. 管理页面放在 Phase 2，避免阻塞鉴权主链路。

## 5. 风险与缓解

1. 风险：token 刷新逻辑导致重复请求或死循环。
- 缓解：全局 refresh 锁 + 单次重试上限。
2. 风险：角色门禁与后端不一致。
- 缓解：以前端“展示控制”为辅，后端“权限判定”为准。
3. 风险：旧页面遗留静态 token 逻辑。
- 缓解：全局检索 `NEXT_PUBLIC_API_TOKEN` 并替换，纳入回归清单。
