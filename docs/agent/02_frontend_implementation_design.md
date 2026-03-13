# 前端技术落地方案 - agent

> Version: v0.2.3
> Last Updated: 2026-03-13
> Status: Draft

## 1. 页面与交互范围

本需求前端改造采用“最小侵入”策略，优先保证现有预审流程可用：

1. 预审详情页新增 Agent 运行信息（模型与检索 trace）。
2. 管理页新增“索引重建”操作入口与任务状态展示。
3. 新建预审与再生成表单支持可选 `debugOptions`（仅管理员可见）。
4. 预审详情页新增工具调用轨迹 `toolTrace`（可选显示）。

不新增复杂新导航，沿用当前 `AppShell + /admin/* + /prereview/*`。

## 2. 模块与组件设计

新增/调整模块：

1. `features/review-detail/trace-panel.tsx`
- 展示 `modelTrace` 与 `retrievalTrace`。
2. `features/admin/agent-admin-view.tsx`
- 展示 runtime capability、触发 reindex、查看 job 状态。
3. `components/business/debug-options.tsx`
- 新建/再生成表单中可选 debug 参数。
4. `hooks/use-agent-api.ts`
- 管理 Agent runtime/reindex 相关 query/mutation。
5. `components/business/tool-trace-panel.tsx`
- 展示 `retrieve_knowledge` 等 tool 调用轨迹。

保持不变：

1. 现有 `use-prereview-api` 主流程。
2. 鉴权与 route guard 体系。

## 3. 状态管理与数据获取

1. 服务端状态：继续使用 React Query。
2. 本地状态：
- debugOptions 临时状态放表单内部。
- 不引入新的全局 store。
3. Query keys 增量扩展：
- `agentRuntime`
- `agentReindexJobs`

> Obsolete in v0.2.0: runtime/reindex hooks 在前端 Phase 1 即默认接入。  
> Replacement in v0.2.1: 仅在 BE-009 完成后启用 runtime/reindex query keys 与 hooks。

关键策略：

1. Trace 字段全部 optional 解析，防止旧后端返回缺失导致崩溃。
2. reindex mutation 成功后自动刷新 runtime/jobs 查询。
3. `toolTrace` 与 `modelTrace/retrievalTrace` 同级可选解析。

## 4. 契约消费策略

1. 新接口均走 `api-client.ts`，保持统一错误处理。
2. 预审详情兼容策略：
- 若 `modelTrace/retrievalTrace` 缺失，UI 显示“未提供 trace”。
> Obsolete in v0.2.0: 仅处理 `modelTrace/retrievalTrace`。  
> Replacement in v0.2.0: 同时处理 `toolTrace` 缺失场景，三类 trace 统一可选渲染。
3. debugOptions 策略：
- 默认不发送。
- 只有显式开启时才下发，避免影响旧后端。
4. toolPolicy 策略：
- 前端只透传 `debugOptions.toolPolicy`，不在前端做复杂裁决。

## 5. 异常与边界状态处理

1. `403 PERMISSION_DENIED`
- 管理页按钮禁用并提示权限不足。
2. `422 VALIDATION_ERROR`
- 表单字段级提示（例如非法检索模式）。
3. `500 WORKFLOW_ERROR`
- 复用现有预审失败提示，新增 trace 缺失提示。
4. reindex 长任务
- 提示“任务已提交”，轮询 job 状态直到 `DONE/FAILED`。
5. 提交请求超时/受理失败
- `SUBMISSION_TIMEOUT/SUBMISSION_QUEUE_FULL`：提示“任务未受理成功”，允许用户重试。
- 受理成功后立即进入详情页 `PROCESSING` 态，不等待最终报告。

### 5.1 Phase 1.5 提交解耦交互模型（紧急）

1. 前端提交状态机：
- `IDLE -> SUBMITTING -> ACCEPTED -> POLLING -> (COMPLETED | FAILED)`。
- `ACCEPTED` 仅表示后端已受理，不代表已产出报告。

2. 提交请求策略：
- 提交接口超时阈值应短于旧同步流程（例如 8~12s），用于快速识别“未受理”。
- 仅在收到 `sessionId + PROCESSING` 时视为受理成功并跳转详情页。
- 失败分支统一映射：`SUBMISSION_TIMEOUT` / `SUBMISSION_QUEUE_FULL` / 默认错误。

3. 轮询策略：
- 进入详情页后立即触发一次 `GET /api/prereview/{session_id}`。
- 轮询间隔建议：前 60s 每 2s，之后每 5s（上限退避）。
- 命中终态 `COMPLETED/FAILED` 立即停止轮询。

4. 防重复提交策略：
- `SUBMITTING` 态禁用提交按钮。
- 若重复点击，前端提示“任务已受理，请在详情页查看进度”。
- 触发路由跳转后，不再保留原页重发逻辑。

## 6. 阶段映射（Phase 1..N）

> Obsolete in v0.2.0: Phase 1 包含 runtime endpoint 接入。  
> Replacement in v0.2.1: runtime/reindex 接入下沉到 Phase 3，对齐 BE-009。

1. Phase 1（配合 BE Phase 1）
- 扩展类型定义与 API optional 兼容解析（不依赖 runtime/reindex 接口可用）。
2. Phase 1.5（配合 BE Phase 1.5）
- 提交链路改为“受理成功即跳转 + 轮询状态”，消除前端固定超时导致的假失败。
- 增加提交态机、防重复提交、分段轮询退避策略。
3. Phase 2（配合 BE Phase 2）
- 预审详情页展示 model/retrieval trace；表单支持 debugOptions；错误码映射增强。
4. Phase 3（配合 BE Phase 3）
- 接入 runtime/reindex hooks；提供管理页入口与 job 状态轮询。
5. Phase 4（配合 BE Phase 4）
- 双模式联调回归（heuristic/cloud, legacy/layered）与回滚演练。
6. Phase 5（配合 BE Phase 5）
- 展示 toolTrace，透传 toolPolicy，完成 tool 模式开关联调回归。

## 7. 设计实现映射（TD-* -> FE）

| TD-ID | FE 实现模块/页面 | 状态与数据策略 | 契约依赖（接口/字段） | 观测与测试 |
|---|---|---|---|---|
| TD-004 | `trace-panel.tsx` + detail 页面 | React Query + optional render | `GET /api/prereview/{session_id}` trace 字段 | FE-UT-Trace-001 |
| TD-008 | `api-client.ts` 兼容解析 | optional field normalize | `POST /api/prereview`, `POST /regenerate`, `GET /detail` | FE-IT-Compat-001 |
| TD-009 | `agent-admin-view.tsx` | mutation + polling | `GET /api/agent/runtime`, `POST /api/admin/agent/reindex` | FE-IT-AdminAgent-001 |
| TD-010 | 错误码映射与回退显示 | `getApiErrorMessage` 增量映射 | `WORKFLOW_ERROR/VALIDATION_ERROR/PERMISSION_DENIED` | FE-E2E-Release-001 |
| TD-011 | `tool-trace-panel.tsx` + detail 页面 | optional trace render | `GET /api/prereview/{session_id}` `toolTrace` | FE-IT-ToolTrace-001 |
| TD-012 | `debug-options.tsx` 透传 toolPolicy | 透传且默认关闭 | `POST /api/prereview*` debugOptions | FE-IT-ToolPolicy-001 |
| TD-013 | 提交受理快速返回 + 轮询态过渡 | 提交状态机 + 防重 + 分段轮询退避 | `POST /api/prereview*`, `GET /api/prereview/{session_id}` | FE-IT-AsyncSubmit-001 |
