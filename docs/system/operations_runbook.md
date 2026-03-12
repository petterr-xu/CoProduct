Title: Operations Runbook
Version: v1.0.0
Last Updated: 2026-03-13
Scope: 本地开发与联调的启动、配置、排障、发布回滚基线
Audience: Developers, QA, maintainers

# Operations Runbook

## Environment and Dependencies

基础依赖：

1. Python >= 3.10
2. Node.js >= 18.18（推荐 20.x）
3. npm >= 9

后端关键依赖：

1. FastAPI / SQLAlchemy / LangGraph
2. `psycopg`（PostgreSQL 可选）

前端关键依赖：

1. Next.js 15
2. React 19
3. React Query + Zustand + Zod

## Start and Stop Procedures

### Backend (SQLite 本地模式)

```bash
cd backend
source ../.venv/bin/activate
pip install -e .

export COPRODUCT_DATABASE_URL="sqlite+pysqlite:///./coproduct.db"
export COPRODUCT_AUTH_MODE="jwt"
export COPRODUCT_API_TOKEN="dev-token"
export COPRODUCT_JWT_SECRET="dev-jwt-secret-change-me"
export COPRODUCT_REFRESH_TOKEN_SECRET="dev-refresh-secret-change-me"
export COPRODUCT_CSRF_SECRET="dev-csrf-secret-change-me"
export COPRODUCT_API_KEY_PEPPER="dev-api-key-pepper-change-me"
export COPRODUCT_BOOTSTRAP_OWNER_API_KEY="cpk_dev_bootstrap_owner_key_change_me"
export COPRODUCT_UPLOAD_DIR="./uploaded_files"
export COPRODUCT_CORS_ALLOW_ORIGINS="http://localhost:3000"

uvicorn app.main:app --reload --host localhost --port 8000
```

### Frontend

```bash
cd frontend
source ~/.nvm/nvm.sh
nvm use 20
npm install
cp .env.example .env.local
npm run dev
```

`frontend/.env.local` 示例：

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### Stop Services

前台运行时直接 `Ctrl+C`。若端口残留：

```bash
lsof -ti :8000 | xargs kill -9
lsof -ti :3000 | xargs kill -9
```

## Configuration Reference

### Backend (`COPRODUCT_*`)

| Key | Meaning | Notes |
|---|---|---|
| `COPRODUCT_AUTH_MODE` | `jwt/hybrid/legacy` | 生产建议只用 `jwt` |
| `COPRODUCT_DATABASE_URL` | DB 连接串 | 可切 SQLite/PostgreSQL |
| `COPRODUCT_CORS_ALLOW_ORIGINS` | CORS 白名单 | 多个 origin 用逗号分隔 |
| `COPRODUCT_BOOTSTRAP_OWNER_API_KEY` | 初始 owner 登录 key | 新环境首登依赖该值 |
| `COPRODUCT_UPLOAD_DIR` | 上传文件落盘目录 | 需可写权限 |

### Frontend

| Key | Meaning | Notes |
|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | 后端 API 地址 | 建议与后端统一 `localhost` |

## Incident Cases and Diagnostics

### Case A: `OPTIONS /api/auth/* 400 Bad Request`

常见原因：CORS origin 未放行。

排查步骤：

1. 检查前端实际 origin（例如 `http://localhost:3000` 或临时端口）。
2. 将该 origin 加入 `COPRODUCT_CORS_ALLOW_ORIGINS`。
3. 重启后端并重试。

### Case B: `Address already in use`

原因：端口 8000/3000 已被旧进程占用。

处理：使用 `lsof` 找到并结束进程。

### Case C: `no such column: sessions.org_id`

原因：历史 SQLite 库结构落后于当前模型。

处理：

1. 优先确认启动日志里是否执行了 `schema_compat_applied`。
2. 如仍失败，备份后删除旧 `coproduct.db` 重新初始化。

### Case D: 刷新后频繁掉登录

常见原因：前后端 host 不一致（`localhost` vs `127.0.0.1`）。

处理：

1. 前后端统一使用 `localhost`。
2. 确认 refresh/csrf cookies 实际写入。
3. 检查 `X-CSRF-Token` 是否携带。

## Backup, Restore, and Migration

### SQLite

备份：

```bash
cp backend/coproduct.db backend/coproduct.db.bak.$(date +%Y%m%d%H%M%S)
```

恢复：

```bash
cp backend/coproduct.db.bak.<timestamp> backend/coproduct.db
```

### PostgreSQL

建议使用 `pg_dump/pg_restore` 做逻辑备份恢复。

迁移现状：

1. 当前未引入 Alembic。
2. 仅有启动时 runtime schema compatibility（开发兜底，不等同正式迁移）。

## Release and Rollback

当前建议的最小发布流程：

1. 预发布前检查
- 后端：`python -m pytest -q`（如测试已配置）
- 前端：`npm run typecheck && npm run lint && npm run build`
2. 发布
- 先后端后前端，保证 API 先可用。
3. 回滚
- 前端回滚到上一个可用构建。
- 后端代码回滚并按需要恢复数据库备份。

发布后回归建议：

1. 登录 / 刷新 / 登出
2. 新建预审 / 详情轮询 / 再生成
3. 管理页成员更新 / API key 签发吊销 / 审计查询
