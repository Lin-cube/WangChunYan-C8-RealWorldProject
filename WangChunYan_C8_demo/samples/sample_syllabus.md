# AI+X 智能应用开发实战

course_id: CS-AI201
description: 以真实问题为起点，走完「问题定义 → 数据/知识库 → 智能体开发 → 交付复盘」的完整链路，8 周产出一个可上线的 AI 应用与个人作品集。
weeks: 8
instructor: 王老师
tags: AI, Agent, RAG, 项目制

## objectives

- 能把一个真实场景模糊需求，转化为可验证的 AI 功能需求
- 能独立完成数据准备与 RAG 知识库搭建
- 能设计并实现一个可交互的智能体应用并部署上线
- 能基于真实用户反馈迭代产品，并把全过程沉淀为作品集

## module M1 | AI+X 问题定义与需求分析 | W1-2

- objective: 理解 AI 能力边界，学会选择「AI 做得成」的真问题
- objective: 掌握用户画像与痛点排序方法

### lesson M1-L1 | 从真实场景到 AI 需求

- summary: 学会把「老师想做个智能批改」这类模糊想法，拆成可验证的 AI 需求。
- topic: AI 能力边界与典型失败模式
- topic: 需求拆解：场景—用户—任务—验收标准
- topic: 可验证需求的写法（输入/输出/成功标准）
- reading: 《AI 需求分析清单》（讲义第 1 章）
- exercise: 把 3 个模糊需求改写为可验证需求 | discussion | 25
- exercise: 画出你的项目场景—用户—任务图 | practice | 20
- assignment: 项目需求说明书 v1 | 提交你选题的需求说明书，含 3 个核心痛点与验收标准

### lesson M1-L2 | 用户画像与痛点排序

- summary: 用访谈与画像把「我觉得用户需要」变成「用户真的需要」。
- topic: 用户画像要素与访谈提纲设计
- topic: 痛点强度 × 频率 × AI 适配度三维排序
- topic: 竞品与替代方案分析
- reading: 《用户访谈 10 问》（讲义第 2 章）
- exercise: 两两互访并输出画像卡 | discussion | 30
- assignment: 用户画像与痛点排序表 | 提交至少 2 个画像与排序后的痛点清单

## module M2 | 数据与知识库 | W3-4

- objective: 能独立完成数据收集、清洗、标注
- objective: 能搭建一个可查询的 RAG 知识库并评估效果

### lesson M2-L1 | 数据收集、清洗与标注

- summary: 数据质量决定 AI 应用上限——本节学会低成本拿到可用数据。
- topic: 数据来源盘点与合规红线
- topic: 清洗流水线：去重、纠错、脱敏、格式统一
- topic: 标注规范与一致性检查
- reading: 《数据清洗检查表》（讲义第 3 章）
- exercise: 对 100 条原始数据跑完清洗流水线 | coding | 40
- assignment: 项目数据集 v1 | 提交清洗后的数据集与数据说明卡

### lesson M2-L2 | RAG 知识库搭建

- summary: 从文档到可问答的知识库：切分、向量化、检索、评估。
- topic: 文档切分策略与 chunk 设计
- topic: 向量检索与混合检索（关键词 + 语义）
- topic: RAG 效果评估：命中率、忠实度、坏例分析
- reading: 《RAG 调优手册》（讲义第 4 章）
- exercise: 用 20 篇文档搭出知识库并回答 10 个测试问题 | coding | 45
- assignment: RAG 知识库 Demo 与评估报告 | 提交知识库构建脚本与 10 题评估结果

## module M3 | 智能体与应用开发 | W5-6

- objective: 掌握 Prompt 工程与 Agent 工作流设计
- objective: 能把智能体集成进 Web 应用并部署上线

### lesson M3-L1 | Prompt 工程与 Agent 设计

- summary: 从「一句话指令」到「可复用的智能体工作流」。
- topic: 结构化 Prompt：角色、约束、示例、输出格式
- topic: Agent 工作流：感知—规划—行动—反思
- topic: 工具调用与失败兜底设计
- reading: 《Agent 设计模式》（讲义第 5 章）
- exercise: 把你的 Prompt 迭代 3 版并记录差异 | coding | 35
- exercise: 画出你的 Agent 工作流图 | practice | 20
- assignment: Agent 工作流设计文档 | 提交工作流图 + 3 版 Prompt 迭代记录

### lesson M3-L2 | 应用集成与部署上线

- summary: 让真实用户能打开并使用你的应用——集成、测试、部署一条龙。
- topic: 前后端集成与 API 设计
- topic: 部署方案选型：静态托管 / 云服务 / 容器
- topic: 上线检查清单：日志、限流、异常兜底
- reading: 《部署上线检查表》（讲义第 6 章）
- exercise: 把 Demo 部署到公网并让同桌访问 | coding | 45
- assignment: 可访问的线上应用链接 | 提交部署链接与 3 条运行日志截图

## module M4 | 交付、复盘与作品集 | W7-8

- objective: 能组织真实用户测试并完成一轮有效迭代
- objective: 能把项目全过程沉淀为可展示的作品集

### lesson M4-L1 | 真实用户测试与迭代

- summary: 用真实反馈检验产品——不是「我觉得好用」，而是「用户用得成」。
- topic: 测试任务设计与观察记录
- topic: 反馈聚类与迭代优先级
- topic: ΔR 复盘法：预期 vs 实际的差值分析
- reading: 《用户测试脚本模板》（讲义第 7 章）
- exercise: 完成 2 场真实用户测试并输出问题清单 | discussion | 40
- assignment: 迭代报告 v2 | 提交测试记录、问题清单与迭代后的版本说明

### lesson M4-L2 | 作品集锻造与路演

- summary: 把 8 周的过程变成别人看得懂、信得过的作品集。
- topic: 作品集结构：背景—方法—产出—证据—复盘
- topic: 证据链设计：代码、截图、数据、用户反馈
- topic: 3 分钟路演叙事与常见问答
- reading: 《作品集评优案例 3 则》（讲义第 8 章）
- exercise: 按模板搭出作品集初版 | practice | 35
- exercise: 3 分钟路演彩排与互评 | discussion | 25
- assignment: 个人作品集终稿 | 提交作品集链接与 3 分钟路演文稿
