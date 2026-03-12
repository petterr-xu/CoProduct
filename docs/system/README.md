Title: CoProduct System Documentation Index
Version: v1.0.0
Last Updated: 2026-03-13
Scope: docs/system 全量系统文档导航
Audience: Engineers, reviewers, maintainers

# CoProduct System Documentation

本目录描述当前代码实现（`backend/` + `frontend/`）下的系统现状，按三层组织：

1. 系统级（整体目标、架构、安全治理、运维）
2. 子系统级（前端、后端）
3. 能力模块级（用户与认证、预审 Agent、RAG）

## 1. System-Level Documents

1. [System Overview](./system_overview.md)
2. [System Architecture](./system_architecture.md)
3. [Security and Governance](./security_and_governance.md)
4. [Operations Runbook](./operations_runbook.md)

## 2. Subsystem-Level Documents

1. [Backend Overview](./backend_overview.md)
2. [Frontend Overview](./frontend_overview.md)

## 3. Capability Module Documents

1. [User Management and Auth](./modules/user-management-and-auth.md)
2. [PreReview Agent](./modules/prereview-agent.md)
3. [RAG Retrieval](./modules/rag-retrieval.md)

## Recommended Reading Order

1. 先读 `system_overview.md` 了解系统边界与能力图。
2. 再读 `system_architecture.md` 和 `security_and_governance.md` 理解关键约束。
3. 按角色阅读 `backend_overview.md` / `frontend_overview.md`。
4. 最后深入各模块文档查看 API 与数据模型细节。
