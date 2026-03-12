# 运行与联调手册
> Version: v0.1.0
> Last Updated: 2026-03-12
> Status: Active

## 1. 本地运行前准备

## 1.1 版本建议

1. Python >= 3.10
2. Node.js >= 20（Next.js 15 需要）

## 1.2 目录

- 后端工程根：`backend/`
- 前端工程根：`frontend/`

---

## 2. 后端启动

## 2.1 安装依赖

```bash
cd backend
source ../.venv/bin/activate
pip install -e .
```

## 2.2 配置环境变量

参考 `backend/.env.example`，常用本地示例：

```bash
export COPRODUCT_DATABASE_URL="sqlite+pysqlite:///./coproduct.db"
export COPRODUCT_API_TOKEN="dev-token"
export COPRODUCT_UPLOAD_DIR="./uploaded_files"
export COPRODUCT_CORS_ALLOW_ORIGINS="http://localhost:3000"
```

## 2.3 启动命令

```bash
uvicorn app.main:app --reload --port 8000
```

若端口占用：

```bash
lsof -ti :8000 | xargs kill -9
```

---

## 3. 前端启动

## 3.1 安装依赖

```bash
cd frontend
npm install
```

## 3.2 配置环境变量

参考 `frontend/.env.example`，本地示例：

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_API_TOKEN=dev-token
```

## 3.3 启动命令

```bash
npm run dev
```

若使用 nvm：

```bash
source ~/.nvm/nvm.sh
nvm use 20
npm run dev
```

若端口占用：

```bash
lsof -ti :3000 | xargs kill -9
```

---

## 4. 联调检查清单（MVP）

1. 首页 `/` 能进入统一入口页并可跳转。
2. 新建预审可成功创建，返回 `sessionId`。
3. 详情页轮询能从 `PROCESSING` 进入 `DONE/FAILED`。
4. regenerate 能创建新版本并跳转新 session。
5. 附件上传可返回 `fileId/fileSize/parseStatus`。
6. 历史页筛选和分页可用。

---

## 5. 测试与构建命令

## 5.1 后端

```bash
cd backend
../.venv/bin/python -m pytest -q
../.venv/bin/python -m compileall app
```

## 5.2 前端

```bash
cd frontend
source ~/.nvm/nvm.sh && nvm use 20
npm run typecheck
npm run lint
npm run build
```

---

## 6. 常见问题排查

## 6.1 CORS 报错

1. 检查后端 `COPRODUCT_CORS_ALLOW_ORIGINS` 是否包含前端域名。
2. 检查前端 API Base URL 是否指向同一后端地址。

## 6.2 401 鉴权失败

1. 前端 `NEXT_PUBLIC_API_TOKEN` 与后端 `COPRODUCT_API_TOKEN` 必须一致。
2. `Authorization` 必须是 `Bearer <token>`。

## 6.3 `Address already in use`

- 说明端口已被占用，按上文命令释放 8000/3000 端口。

## 6.4 前端 Node 版本不满足

- Next.js 15 需要 Node >= 18.18，推荐 Node 20。

## 6.5 附件上传成功但解析失败

- 当前后端仅完整支持 txt/md 解析；pdf/docx 会进入解析失败降级路径。

---

## 7. 日志与观测点

后端日志采用 JSON Lines，关键事件包括：

1. `workflow_completed/workflow_failed`
2. `workflow_regenerated/workflow_regenerate_failed`
3. `node_completed/node_degraded`
4. `model_structured_invoke/model_embed_texts/model_rerank`
5. `attachment_parsed/attachment_parse_failed`

定位建议：

1. 先看 session 级事件（是否完成/失败）
2. 再看 node/model 级耗时与错误码
3. 最后对照 DB 中 session/report/evidence 状态
