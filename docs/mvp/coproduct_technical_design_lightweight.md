# CoProduct 技术设计方案（轻量迭代版 / Agent-first）

> 版本：V2  
> 面向场景：个人项目 / 小团队 / 从简单到复杂逐步迭代  
> 核心目标：优先把 **核心 Agent** 做出来，充分复用现有框架与成熟能力；对权限、治理、平台化、复杂协作等支撑模块仅做最小预留，不做过度设计。

---

## 1. 设计背景与本版目标

在重新审视产品方案后，可以明确 CoProduct 一期的本质不是“做一个通用 AI 平台”，而是做一个：

- 以 **需求预审** 为目标的垂直 Agent
- 以 **证据驱动判断** 为核心能力的工作流应用
- 以 **逐步迭代** 为实现方式的轻量系统

结合产品方案，一期 MVP 必须围绕以下三件事展开：

1. 回答“当前系统有没有这个能力”
2. 将模糊需求整理成结构化草案
3. 提示缺失信息、风险点和影响范围

同时，产品方案也明确了一期必须支持：

- 自然语言输入
- 基于知识检索的预审分析
- 结构化预审报告
- 补充信息后重新生成
- 历史记录保存与查看
- 有限知识源接入

因此，本版技术设计将贯彻以下策略：

- **以 Agent 主链路为中心**
- **优先使用现成框架与托管能力**
- **不做重量级平台化**
- **支撑模块只做“够用”**
- **架构预留扩展点，但不提前实现复杂能力**

---

## 2. 产品需求映射

根据产品设计方案，CoProduct 的主流程是：

```text
用户输入原始需求
→ Agent 解析需求
→ 检索相关知识
→ 分析支持程度 / 缺失信息 / 风险 / 影响范围
→ 输出结构化预审报告
→ 用户补充信息
→ 重新生成结果
→ 保存历史
```

对应的核心产品能力是：

### 2.1 输入侧
- 一句话或长文本需求输入
- 可带背景说明
- 可选业务域 / 模块
- 可附带上下文文本或链接

### 2.2 引擎侧
- 需求解析器
- 知识检索器
- 能力判断器
- 缺失项识别器
- 风险识别器
- 影响范围分析器
- 报告生成器

### 2.3 输出侧
- 需求摘要
- 当前能力判断
- 判断依据
- 结构化需求草案
- 待补充信息
- 风险提示
- 影响范围

### 2.4 交互闭环
- 用户补充信息后重跑
- 保存历史结果
- 支持后续逐步扩展更多知识源和外部系统

---

## 3. 设计原则（本版重构后的核心原则）

### 3.1 先做“可信 Agent”，不是“完整平台”

本项目首期的价值，不在于有多少系统模块，而在于是否能让用户相信：

- 这个结论不是瞎猜的
- 它能指出依据
- 它能承认不确定
- 它能引导用户补充信息

因此，最重要的不是 RBAC、复杂审计、图谱平台或工作流编排后台，而是：

- 解析是否稳定
- 检索是否靠谱
- 证据是否清晰
- 报告是否可用

### 3.2 先复用现有框架，再自研抽象

个人项目或早期产品不应该在底层重复造轮子。优先使用：

- 现成 Agent 编排框架
- 托管检索 / 向量能力
- 结构化输出能力
- 现成 tracing / eval / logging 能力
- 现成部署平台

只有在业务模型稳定后，再考虑抽象成平台。

### 3.3 单主控 Agent + 工作流，优先于多 Agent 协商

CoProduct 一期是典型的 **Evidence-first Workflow Agent** 场景，不需要复杂的社会化多 Agent 协作。主流程应由一个主控 Agent 或状态图驱动，再将不同分析任务拆成明确步骤，而不是放任多个 Agent 自由对话。

### 3.4 支撑模块最小化设计

以下能力只做最小可用：

- 用户体系：单用户 / 简单登录即可
- 权限：先不做复杂多角色
- 监控：基础日志 + trace 即可
- 缓存：只针对高频重复步骤
- 审计：保留核心请求与结果即可
- 外部系统集成：暂不做，只留接入点

### 3.5 从简单到复杂的演进顺序

建议严格按这个顺序建设：

```text
固定输入
→ 稳定解析
→ 有依据的检索
→ 结构化报告
→ 补充信息重跑
→ 历史沉淀
→ 规则增强
→ 案例推荐
→ 外部系统连接
→ 平台化
```

---

## 4. 调研结论：当前 AI Agent 生态对 CoProduct 的启示

本版方案以“现成可用、适合迭代”为选择标准，重点关注当前主流 Agent 技术路线。

### 4.1 OpenAI：适合做单 Agent + 工具调用 + 托管检索的快速落地

OpenAI 的 Responses API 已将多轮推理、结构化输出、工具调用、web/file search、MCP 等统一到一个 agent-native 接口里，非常适合构建以单主控 Agent 为核心的产品。对 CoProduct 来说，这意味着很多“Agent 基建”可以直接复用，而不是自己造。  
**启示**：如果你希望快速落地、尽量少写底层 glue code，OpenAI 路线非常适合作为首期核心能力层。  
**适合用在**：结构化输出、工具调用、内置 file/web search、后续 MCP 扩展。  

### 4.2 LangGraph：适合把“可控的工作流 Agent”做稳

LangGraph 的定位非常明确：为长流程、有状态、可中断、可恢复的 workflow / agent 提供底层运行时。它不强行规定你的 Agent 形态，因此很适合 CoProduct 这种“不是对话机器人，而是工作流型 Agent”的场景。  
**启示**：如果你希望把“解析 → 检索 → 判断 → 生成”做成一条清晰可调试的图式流程，LangGraph 是很合适的首选编排层。  
**适合用在**：主流程编排、节点重试、状态管理、后续子图扩展。  

### 4.3 Anthropic MCP：适合做后续工具扩展的开放接口层

MCP 已成为当前工具接入的重要开放协议之一。Anthropic 官方和 MCP 官方资料都在强化一个方向：Agent 不应为每个外部系统单独写一套耦合逻辑，而应通过统一协议接入工具、数据源和工作流。  
**启示**：CoProduct 一期不用强依赖 MCP，但工具层设计最好 MCP-compatible。这样后续接 Jira、飞书、Confluence、文档库、数据库时，迁移成本会低很多。  
**适合用在**：后续外部工具适配层设计，不建议作为 MVP 的复杂交付项。  

### 4.4 Google ADK / A2A：适合未来多 Agent 协作，但不是一期重点

Google 的 Agent Development Kit（ADK）和 A2A 协议更偏向“面向生产的多 Agent / 多组件协作”路线。对今天的 CoProduct 而言，它带来的最大价值是提供了“未来可互通”的方向，而不是 MVP 必需品。  
**启示**：现在不需要为了未来的多 Agent 做过多复杂设计，但可以保留 `tool adapter` 与 `agent adapter` 的接口抽象。  
**适合用在**：中后期平台化、跨 Agent 协作、跨系统联动。  

### 4.5 CrewAI：适合快速搭 demo，但不一定适合作为长期核心骨架

CrewAI 在多 Agent、流程、可视化和 observability 上迭代很快，适合快速原型和自动化任务编排。但 CoProduct 一期其实不需要“crew”式角色协作，更多需要“单主控 + 明确步骤 + 高解释性”。  
**启示**：CrewAI 可以作为快速 demo 方案参考，但若你追求可控性和后续逐步演进，LangGraph 往往更适合作为核心工作流骨架。  

### 4.6 最终调研结论

对 CoProduct 当前阶段，最合理的技术路线不是“追最全”，而是：

- **模型层**：使用支持 structured output + tool calling 的主流模型
- **Agent 编排层**：优先 LangGraph
- **工具 / 协议层**：保留 MCP-compatible 接口，但不在首期深做
- **知识检索层**：优先使用托管 / 简化的 RAG 方案
- **产品形态**：单主控 Agent + 若干确定性分析步骤

---

## 5. 一期推荐架构（轻量版）

### 5.1 总体思路

本版推荐采用：

**Web 应用 + 单体后端 + LangGraph 工作流 + 托管/轻量检索 + 单主控 Agent**

整体上不再采用重量级分层，而采用“够用即好”的结构：

```text
[Web UI]
   ↓
[App Server / BFF]
   ↓
[PreReview Agent Workflow]
   ├── 输入标准化
   ├── 需求解析
   ├── 检索规划
   ├── 知识检索
   ├── 证据筛选
   ├── 能力判断
   ├── 缺失项识别
   ├── 风险识别
   ├── 影响范围分析
   ├── 报告生成
   └── 结果落库
   ↓
[Model + Retrieval + DB]
```

### 5.2 设计取舍

#### 一期保留
- Web 页面
- Agent 工作流
- 知识检索
- 证据引用
- 报告生成
- 补充信息再生成
- 历史记录

#### 一期弱化
- 权限体系
- 审计体系
- 高级缓存
- 复杂消息队列
- 多 Agent 协同
- 外部系统联动
- 图谱系统

#### 一期预留，不实现复杂版本
- MCP tool adapter
- 相似案例推荐
- 风险规则配置后台
- 模块依赖图谱

---

## 6. 技术选型建议

### 6.1 推荐主选型

#### 前端
- **Next.js**
- **Tailwind CSS**
- 可搭配 shadcn/ui 作为基础组件库

原因：
- 页面数量少
- 既能做 UI，也能做轻量 BFF
- 适合个人项目快速迭代与部署

#### 后端
有两个推荐路径：

##### 路径 A：Next.js 一体化
- Next.js Route Handlers / Server Actions
- 适合前后端都想保持轻量、快速上线

##### 路径 B：FastAPI + Next.js
- 前端：Next.js
- 后端：FastAPI
- 更适合 AI / 工作流逻辑较重时

**建议**：如果你更熟悉 Python 生态和 Agent 框架，优先 **FastAPI + LangGraph + Next.js**。

#### Agent 编排
- **LangGraph**

原因：
- 明确适合 stateful workflow
- 非常契合“单主控 Agent + 明确步骤”
- 后续可扩成子图与多 Agent，但不会过度复杂
- 对调试和追踪更友好

#### 模型层
选择要求：
- 支持结构化输出
- 支持工具调用
- 推理质量够稳定
- 成本可控

因此建议：
- 主模型：支持 structured output / tool calling 的通用模型
- 辅助模型：可配置一个更便宜模型用于简单重写 / 分类任务

#### 向量与检索
优先级建议：

##### 最推荐（个人项目友好）
- **PostgreSQL + pgvector**
- 或 **Supabase（Postgres + pgvector）**

优点：
- 一个库解决存储 + 向量
- 复杂度低
- 容易部署
- 足够支持 MVP

##### 全文检索
首期不建议直接上 Elasticsearch / OpenSearch。  
优先考虑：
- PostgreSQL 全文检索
- 或简单 BM25 / 关键词召回实现

#### ORM / 数据访问
- Python：SQLAlchemy / SQLModel
- TypeScript：Prisma

#### 缓存
- 首期可不做 Redis
- 或只在需要时引入 Upstash Redis / 本地 Redis 做最小缓存

#### 部署
- 前端：Vercel
- 后端：Render / Railway / Fly.io / 云服务器
- 数据库：Supabase / Neon / Railway Postgres

---

## 7. 系统模块设计（以核心 Agent 为中心）

### 7.1 模块划分

本版只保留 5 个核心模块：

1. **输入模块**
2. **Agent 工作流模块**
3. **知识检索模块**
4. **报告模块**
5. **历史模块**

#### 7.1.1 输入模块
职责：
- 接收需求文本
- 接收背景说明
- 接收可选模块 / 业务域
- 接收补充上下文
- 发起预审任务

#### 7.1.2 Agent 工作流模块
职责：
- 驱动整个预审分析流程
- 管理中间状态
- 调用模型与工具
- 生成结构化中间结果

#### 7.1.3 知识检索模块
职责：
- 文档切片
- embedding 生成
- 关键词召回
- 向量召回
- 证据重排 / 去重

#### 7.1.4 报告模块
职责：
- 汇总结论
- 绑定证据
- 输出结构化报告
- 转换为前端可展示内容

#### 7.1.5 历史模块
职责：
- 保存预审记录
- 保存版本
- 保存补充生成链路
- 展示历史详情

---

## 8. Agent 架构设计

### 8.1 一期推荐：单主控 Agent + 明确步骤节点

不建议一期采用：

- 多个自治 Agent 对话协商
- Planner/Executor/Reviewer 多角色复杂互调
- 完全开放式的 tool loop

建议结构：

```text
PreReview Agent
├── Parse Step
├── Retrieve Step
├── Analyze Step
├── Compose Step
└── Persist Step
```

每个 Step 内部可以调用模型或工具，但从系统设计上仍是“一条可控主链路”。

### 8.2 为什么这样设计最适合当前阶段

因为 CoProduct 的核心任务不是探索开放世界，而是对一个有限问题做高质量判断：

- 输入比较短
- 目标明确
- 知识域相对有限
- 需要引用证据
- 需要承认不确定性
- 输出模板固定

这类任务天然适合 **workflow agent**，而不是 **open-ended autonomous agent**。

---

## 9. Agent 工作流设计

### 9.1 主流程节点

推荐 LangGraph 中定义如下节点：

#### Node 1：InputNormalizer
输入：
- 原始需求
- 背景说明
- 业务域 / 模块
- 补充上下文
- 是否为 regenerate

输出：
- 标准化输入对象 `normalized_request`

职责：
- 清理冗余空白
- 合并上下文
- 统一字段结构
- 生成 trace id / session id

#### Node 2：RequirementParser
输入：
- `normalized_request`

输出：
- `parsed_requirement`

职责：
- 提取需求目标
- 提取业务对象 / 数据对象
- 提取约束条件
- 提取隐含前提
- 标记不明确项

建议输出字段：

```json
{
  "goal": "",
  "background": "",
  "actors": [],
  "business_objects": [],
  "data_objects": [],
  "target_capability": "",
  "constraints": [],
  "scope_hints": [],
  "uncertain_points": []
}
```

#### Node 3：RetrievalPlanner
输入：
- `parsed_requirement`

输出：
- `retrieval_plan`

职责：
- 生成检索 query
- 判断应重点查哪些知识源
- 生成过滤条件
- 判断是否需要查历史记录

首期建议不要让这一步过于复杂。输出 2–5 个 query 即可。

#### Node 4：KnowledgeRetriever
输入：
- `retrieval_plan`

输出：
- `retrieved_candidates`

职责：
- 执行关键词召回
- 执行向量召回
- 合并结果
- 初步去重
- 附带文档元数据

#### Node 5：EvidenceSelector
输入：
- `parsed_requirement`
- `retrieved_candidates`

输出：
- `evidence_pack`

职责：
- 对候选证据排序
- 删除弱相关片段
- 聚合来自同一文档的相邻切片
- 形成最终证据包

建议输出格式：

```json
[
  {
    "doc_id": "",
    "doc_title": "",
    "chunk_id": "",
    "snippet": "",
    "source_type": "product_doc|tech_doc|api_doc|case",
    "relevance_score": 0.0,
    "supporting_claims": []
  }
]
```

#### Node 6：CapabilityJudge
输入：
- `parsed_requirement`
- `evidence_pack`

输出：
- `capability_judgement`

职责：
- 判断当前能力支持程度
- 输出结论与依据
- 明确不确定原因

结论枚举建议：

- `SUPPORTED`
- `PARTIALLY_SUPPORTED`
- `NOT_SUPPORTED`
- `NEED_MORE_INFO`

#### Node 7：MissingInfoAnalyzer
输入：
- `parsed_requirement`
- `evidence_pack`

输出：
- `missing_info_items`

职责：
- 识别缺失信息
- 以问题列表形式输出
- 给出优先级

#### Node 8：RiskAnalyzer
输入：
- `parsed_requirement`
- `evidence_pack`

输出：
- `risk_items`

职责：
- 识别风险点
- 输出原因
- 必要时绑定证据或规则

#### Node 9：ImpactAnalyzer
输入：
- `parsed_requirement`
- `evidence_pack`

输出：
- `impact_items`

职责：
- 识别可能影响的模块 / 服务 / 角色
- 首期可通过“模块关键词命中 + 规则表”实现
- 不必首期上真正的依赖图谱

#### Node 10：ReportComposer
输入：
- 前面所有分析结果

输出：
- `pre_review_report`

职责：
- 统一组装结果
- 区分“事实 / 推断 / 不确定”
- 组织前端展示结构

#### Node 11：PersistenceNode
输入：
- 完整结果对象

输出：
- 持久化后的 report id / session id

职责：
- 落库
- 建立版本记录
- 记录请求耗时等基础元信息

---

## 10. 报告结构设计

### 10.1 一期报告模板

建议固定为以下结构：

1. **需求摘要**  
2. **当前能力判断**  
3. **判断依据**  
4. **结构化需求草案**  
5. **待补充信息**  
6. **风险提示**  
7. **影响范围**  
8. **下一步建议**  

### 10.2 报告数据结构建议

```json
{
  "summary": "",
  "capability": {
    "status": "PARTIALLY_SUPPORTED",
    "reason": "",
    "confidence": "medium"
  },
  "evidence": [],
  "structured_requirement": {
    "goal": "",
    "scope": [],
    "actors": [],
    "constraints": [],
    "expected_output": ""
  },
  "missing_info": [],
  "risks": [],
  "impact_scope": [],
  "next_actions": [],
  "uncertainties": []
}
```

---

## 11. 检索与知识设计

### 11.1 一期知识源范围

本版建议只接入：

- 产品能力说明
- 模块说明文档
- API 说明文档
- 常见限制 / 约束文档
- 典型历史需求案例（少量）

不建议首期接入：
- 全量企业知识库
- 所有会议纪要
- 杂乱的聊天记录
- 实时同步的多系统内容

### 11.2 文档处理策略

#### 文档切片
建议：
- 采用中等粒度切片
- 保留标题层级
- 保留来源文档名
- 保留章节路径

#### 元数据
建议最少保留：
- `doc_id`
- `title`
- `source_type`
- `module_tags`
- `updated_at`
- `trust_level`

#### trust_level
建议首期做简单文档可信等级：

- `HIGH`：正式产品/技术文档
- `MEDIUM`：较可信案例或整理文档
- `LOW`：零散资料

### 11.3 检索策略

首期建议使用 **Hybrid Retrieval**，但实现要克制：

- 关键词召回
- 向量召回
- 去重
- 简单 rerank

不建议首期做：
- 复杂 query decomposition
- 多跳检索
- 图谱推理检索
- 大规模 rerank pipeline

### 11.4 Evidence-first 原则

任何关键结论都尽量绑定 evidence。  
没有足够 evidence 时，允许输出：

- 需要更多信息
- 当前证据不足
- 只能给出弱推断

---

## 12. 数据库设计（轻量版）

### 12.1 核心表

建议只做 5 张主表：

#### 1）requests
记录原始输入。

#### 2）sessions
记录一次预审会话。

#### 3）reports
记录最终报告。

#### 4）evidence_items
记录引用证据。

#### 5）knowledge_documents
记录知识文档元信息。

### 12.2 为什么不建议首期做更多表

因为现在最重要的是跑通产品闭环，不是把数据平台设计得多完整。  
只要这些表能支持：

- 回看输入
- 回看结果
- 回看证据
- 支持 regenerate
- 支持历史页展示

就足够。

---

## 13. API 设计（最小可行）

### POST /api/prereview
创建新的预审任务。

### GET /api/prereview/{id}
获取预审结果详情。

### POST /api/prereview/{id}/regenerate
基于已有结果补充信息后重跑。

### GET /api/history
查询历史记录列表。

### POST /api/knowledge/reindex
手动触发知识重建（管理接口即可）。

---

## 14. 前端页面设计（只保留 3 页）

### 14.1 新建预审页
包含：
- 需求输入框
- 背景说明
- 可选模块/业务域
- 可选上下文补充
- 提交按钮

### 14.2 结果页
展示：
- 需求摘要
- 当前能力判断
- 判断依据
- 结构化草案
- 待补充信息
- 风险提示
- 影响范围
- 补充信息后二次生成入口

### 14.3 历史页
展示：
- 历史列表
- 创建时间
- 当前结论
- 是否有补充版本
- 进入详情

---

## 15. 结果质量控制设计

### 15.1 结构化输出优先

每个重要节点都尽量输出 JSON Schema，而不是自由文本。

### 15.2 简单规则兜底

#### 能力判断兜底
- 无证据时不能直接判“已支持”
- 证据强但信息缺失时判“部分支持”或“需要更多信息”

#### 缺失项兜底
默认从以下维度检查：
- 目标用户
- 数据范围
- 触发条件
- 输出形式
- 权限边界
- 时间要求
- 性能要求

#### 风险兜底
默认从以下维度检查：
- 权限与安全
- 数据一致性
- 边界条件
- 依赖模块
- 兼容性
- 实施复杂度

### 15.3 事实 / 推断 / 不确定分层

结果页建议明确区分：

- **事实依据**
- **模型推断**
- **尚不确定**

---

## 16. regenerate 设计

### 16.1 为什么这是一期重点

产品方案明确要求：用户在看到待确认项后，可以补充信息并重新生成。  
这意味着 CoProduct 不是一次性问答工具，而是一个 **人机协作迭代器**。

### 16.2 实现方式

首期建议做“简单重跑”，不要做复杂增量推理：

```text
旧会话 + 用户补充信息
→ 合并为新的 normalized_request
→ 重新走完整 workflow
→ 新建一个 version
```

---

## 17. 支撑模块设计（只做最小版）

### 17.1 认证
首期可选：
- 不做登录，仅本地使用
- 或使用最简单的邮箱/第三方登录

### 17.2 权限
首期不做复杂权限体系。  
只需区分：
- 普通用户
- 管理/开发者（可重建知识索引）

### 17.3 日志与 Trace
建议只做：
- 请求日志
- workflow 节点耗时
- 模型调用耗时
- 失败原因
- 最终结果状态

### 17.4 缓存
仅缓存以下内容：
- 文档 embedding
- 热门 query 的检索结果
- 相同文档的重复切片结果

### 17.5 评测
首期不做完整评测平台。  
只保留：
- 一组固定测试样本
- 人工 badcase 记录
- 关键输出对比

---

## 18. 分阶段迭代路线图

### Phase 1：MVP（最小闭环）
只做：
- 输入页
- 单主控 Agent
- 文档检索
- 证据引用
- 结构化报告
- regenerate
- 历史记录

### Phase 2：增强可用性
新增：
- 相似案例召回
- 风险规则增强
- 模块影响规则增强
- 更好的结果 diff
- 更多知识源

### Phase 3：开放工具层
新增：
- MCP-compatible tool adapter
- Jira / 飞书 / Wiki 接入
- 外部 API 调用
- 案例库沉淀

### Phase 4：平台化
新增：
- 多 Agent 协作
- A2A / agent adapter
- 更细粒度权限
- 评测/治理后台
- 反馈闭环训练

---

## 19. 最终推荐方案（结论）

### 19.1 最优落地路线

对于当前阶段的 CoProduct，推荐采用下面这套组合：

- **前端**：Next.js + Tailwind
- **后端**：FastAPI
- **Agent 编排**：LangGraph
- **模型能力**：支持 structured output + tool calling 的主流模型
- **知识检索**：PostgreSQL + pgvector + 简单全文检索
- **部署**：Vercel + Supabase / Railway / Render

### 19.2 为什么这套方案最适合你当前诉求

因为它满足了你提出的全部关键要求：

1. **从简单到复杂慢慢迭代**  
2. **尽量复用已有框架/解决方案**  
3. **当前以核心 Agent 开发为主**  
4. **支撑性模块不过度设计**  
5. **仍然保留未来升级空间**  

---

## 20. 你现在最应该先做的 5 件事

1. 固定一期报告 schema  
2. 建立首批高质量知识文档集  
3. 用 LangGraph 搭出主流程节点  
4. 先把 evidence 绑定与结果页做清楚  
5. 用 10–20 条真实需求样本反复调解析与检索  

---

## 21. 参考项目与资料

### 产品输入依据
- CoProduct 产品方案 README（本地）
- 既有技术方案（本地）

### 近期 Agent 生态参考
- OpenAI Responses API / tools / agents
- LangGraph 官方文档
- Anthropic MCP / MCP 官方协议
- Google Vertex AI Agent Builder / ADK / A2A
- CrewAI 官方文档

### 参考建议
本方案对这些技术路线做了“个人项目 / 轻量迭代 / Agent-first”视角下的取舍，并非推荐全部采用，而是强调：
- 能复用就复用
- 能托管就托管
- 能简单就不要复杂
- 架构先服务产品主链路，再服务未来想象空间
