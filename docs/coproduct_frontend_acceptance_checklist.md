# CoProduct 前端里程碑验收清单（M1/M2/M3，与后端同步）

## 1. 验收原则

- 仅按以下文档判定通过/不通过：
  - `docs/coproduct_frontend_technical_design.md`
  - `docs/coproduct_backend_contracts.md`
  - `docs/coproduct_backend_acceptance_checklist.md`（用于里程碑同步）
- 每条验收项必须可通过页面操作、网络请求或日志截图验证
- 验收结果分为：`PASS` / `FAIL` / `BLOCKED`

---

## 2. M1 验收（主链路可联调）

## 2.1 页面与路由

1. `/` 自动跳转至 `/review/new`
2. `/review/new` 可正常加载且表单可输入
3. `/review/{sessionId}` 可根据有效 `sessionId` 打开详情页

## 2.2 创建预审链路

1. 点击“发起预审”后触发 `POST /api/prereview`
2. 提交时按钮进入 loading，重复点击被阻止
3. 返回成功后跳转到 `/review/{sessionId}`
4. 缺失必填字段时前端阻止提交并显示校验信息

## 2.3 详情查询链路

1. 详情页触发 `GET /api/prereview/{sessionId}`
2. `PROCESSING` 状态下自动轮询
3. 状态变为 `DONE` 或 `FAILED` 时停止轮询
4. 服务返回 `status` 仅为 `PROCESSING|DONE|FAILED`
5. 无效 `sessionId` 时显示 `NOT_FOUND` 语义化提示（来源于 404 错误体）

## 2.4 鉴权与基础错误处理

1. Token 缺失或错误时，前端能显示明确错误
2. 接口 5xx 时显示统一错误提示，不出现白屏
3. 网络失败时允许用户重试

---

## 3. M2 验收（结果展示质量可用）

## 3.1 固定报告结构展示

1. 结果页可稳定展示固定 8 区块
2. 任一区块为空时显示空态文案，不破坏页面结构
3. 长文本支持折叠/展开

## 3.2 能力判断与语义映射

1. 能力判断仅显示固定枚举：
   - `SUPPORTED`
   - `PARTIALLY_SUPPORTED`
   - `NOT_SUPPORTED`
   - `NEED_MORE_INFO`
2. 枚举颜色语义正确（绿/黄/红/蓝）
3. 同步显示能力判断理由与置信度
4. `confidence` 字段缺失时前端有显式降级提示，不出现空白

## 3.3 证据可读性

1. `EvidencePanel` 展示来源、片段、引用关系
2. 多条 evidence 可展开查看，不出现布局错乱
3. 无 evidence 时有降级提示

## 3.4 交互一致性

1. loading skeleton、error alert、empty state 样式统一
2. 刷新页面后能恢复当前 session 的结果展示
3. 前端错误提示不泄露后端内部堆栈信息

## 3.5 契约一致性

1. 详情页仅依赖字段级 view model，不依赖裸 `report`
2. 结果页所需字段可稳定渲染：`summary/capability/evidence/structuredRequirement/missingInfo/risks/impactScope/nextActions/uncertainties`

---

## 4. M3 验收（版本、文件、历史与稳定性）

## 4.1 regenerate

1. 详情页可输入补充说明并触发 regenerate
2. 调用 `POST /api/prereview/{session_id}/regenerate` 成功后跳转新 session
3. 新旧 session 在页面上可区分（至少展示 sessionId 或 version）
4. regenerate 失败时保留用户输入并支持重试

## 4.2 文件上传链路

1. 前端可选择文件并校验数量/大小/类型
2. 调用 `POST /api/files/upload` 成功拿到 `fileId`
3. 创建与 regenerate 请求可带 `attachments.fileId`
4. 上传失败时可删除失败项并重传

## 4.3 历史页

1. `GET /api/history` 可完成分页查询
2. `keyword` 筛选生效
3. `capabilityStatus` 筛选生效
4. 点击某条记录可跳转详情页

## 4.4 稳定性

1. 接口超时/断网时 UI 可恢复，不进入不可操作状态
2. Query 重试策略符合预期，不出现无穷重试
3. 页面级异常由错误边界兜底
4. 联调环境变量缺失时有明确启动提示

---

## 5. 联调回归建议（前后端同步执行，10~15 条）

每条样例至少验证：

1. 请求参数合法性与前端校验行为
2. 状态流转（`PROCESSING -> DONE/FAILED`）
3. 报告结构展示完整性
4. 错误分支提示可读性
5. 页面跳转与版本链正确性

建议覆盖样例：

1. 正常创建并成功完成
2. 创建后返回 `FAILED`
3. 无效 session 查询
4. regenerate 成功创建新版本
5. regenerate 失败并重试
6. 上传合法文件成功
7. 上传超限文件失败
8. 历史筛选命中/未命中

---

## 6. 发布前 Gate（必须全部 PASS）

1. 3 个页面功能完整可用
2. 创建/查询/regenerate/上传/历史均可联调
3. 结果页固定区块稳定展示
4. 状态、错误、空态体验统一
5. 与后端契约字段完全对齐
6. 联调文档可复现完整流程
