# CoProduct 系统文档索引
> Version: v0.1.1
> Last Updated: 2026-03-12
> Status: Active

本目录用于沉淀当前 **MVP（后端 M3 + 前端 M3.1）** 的系统级说明，内容基于 `docs/mvp` 文档与当前代码实现（`backend/` + `frontend/`）对齐。

## 文档列表

1. [系统全景介绍](./system_overview.md)
2. [后端架构与模块关系](./backend_architecture.md)
3. [后端 Service 层详解](./backend_services.md)
4. [后端 API 参考（重要接口详解）](./backend_api_reference.md)
5. [核心 Agent 编排器（PreReview Orchestrator）](./agent_orchestrator.md)
6. [RAG 模块设计与演进方向](./rag_design.md)
7. [数据模型与持久化设计](./data_and_persistence.md)
8. [前端架构与交互链路](./frontend_architecture.md)
9. [运行与联调手册](./ops_and_runbook.md)
10. [系统现状评估与下一期开发方向](./improvement_and_next_phase.md)

## 阅读建议

1. 首先阅读「系统全景介绍」，快速建立整体认知。  
2. 其次阅读「后端架构」+「Service 层详解」+「核心 Agent 编排器」，理解服务主链路。  
3. 再阅读「RAG 模块」与「后端 API 参考」，理解证据与接口契约。  
4. 最后阅读「前端架构」「数据模型与持久化」「运行手册」「下一期方向」。

## 版本说明

- 本目录首版聚焦“当前可运行实现”，强调 **代码事实**，不再重复纯规划内容。
- 若后续对接口、状态枚举、工作流节点顺序、数据结构有修改，应同步更新对应文档。
