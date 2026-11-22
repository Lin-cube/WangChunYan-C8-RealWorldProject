# WangChunYan_C8_拿来说明.md —— 参考来源与取舍分析

> **项目**：Project C 课程生产体系 ｜ **验证物**：`WangChunYan_C8_demo/`
> **调研方式**：联网检索 + 链接核实（2026-11-22），全部来源为官方文档/官方仓库/权威厂商文档。
> 本文是 proposal Part 2「拿来主义分析」的完整版，按"检索 → 判断 → 重构"链路记录。

---

## 一、参考来源总表

| # | 来源 | 链接 | 核心思想 | 调研确认 |
|---|------|------|----------|----------|
| 1 | Open edX | https://docs.openedx.org/ | 课程结构标准化：chapter/section → sequential/subsection → vertical/unit → component 四级；创作端 Studio 与学习端 LMS 分离 | 官方文档确认（docs.openedx.org 课程结构术语页） |
| 2 | Jupyter Book | https://jupyterbook.org/ | 内容源（Markdown/Notebook）与呈现分离，单一来源多格式发布；可执行内容 | 官方站确认（当前 1.x 成熟、2.x 基于 mystmd 演进中） |
| 3 | nbgrader | https://github.com/jupyter/nbgrader | 作业生命周期闭环：assign → release → collect → autograde → formgrade | 官方仓库确认（BSD-3，文档在 nbgrader.readthedocs.io） |
| 4 | SCORM / xAPI / cmi5（ADL） | https://www.intellum.com/resources/blog/what-is-scorm | SCORM：课程打包清单（imsmanifest.xml）+ 运行时 API；xAPI：actor-verb-object 学习语句入 LRS（IEEE 9274.1.1-2023）；cmi5：xAPI 的 LMS 启动规范 | 权威厂商文档 + 标准信息确认（xAPI 2023 年成 IEEE 标准） |
| 5 | LangGraph | https://docs.langchain.com/ | 工作流显式编排：StateGraph 节点 + 边 + 状态传递；支持条件路由、持久化、调试 | 官方文档确认（docs.langchain.com） |
| 6 | Claude Agent Skills | https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview | SKILL.md 封装规范：YAML frontmatter（name ≤64 字符小写连字符、description ≤1024 字符含触发时机）+ 渐进式披露（元数据→正文→参考文件） | 官方平台文档确认（platform.claude.com） |

**备选淘汰说明**（检索到但未采用）：
- **Moodle**：与 Open edX 同赛道（LMS），结构思想重叠且更偏"平台运营"，取 Open edX 的结构文档更清晰；
- **Quarto**：与 Jupyter Book 同赛道，但绑定 Posit 单一公司生态，我们只借"内容与呈现分离"思想，无须绑定渲染链；
- **Wechaty / 微信群方案**（材料包中的 C8 WeChat 挑战）：与 Project C 方向不符，未采用（该方向已由选择其他项目的同学覆盖）。

---

## 二、逐来源取舍分析（Adopted / Removed / Improved）

### 来源 1：Open edX —— 课程结构层级

| 处理 | 内容 | 原因 |
|------|------|------|
| ✅ Adopted | 课程必须有**标准结构层级**（章→节→单元）——结构化是一切自动化生产的前提 | Open edX 用四级结构支撑了全球大量 MOOC，证明"结构先行"可规模化 |
| ✅ Adopted | 创作端（Studio）与学习端（LMS）**分离**的架构思想 | 对应我们"生产流水线（教师侧）"与"交付站点（学生侧）"分离 |
| ❌ Removed | OLX（Open Learning XML）、XBlock、LMS/Studio 全套平台 | 太重（需服务器/数据库/账号体系）；C8 验证物要求"可独立运行"，不重造 LMS |
| 🔧 Improved | 四级结构简化为 **Course → Module → Lesson 三级**，并补充 Lesson → ILT Agent 的映射 | 教学场景里"单元/组件"两级收益递减；而 Open edX 没有"课时→学习代理"这一层，这是本项目新增的自动化环节 |

### 来源 2：Jupyter Book —— 内容源与呈现分离

| 处理 | 内容 | 原因 |
|------|------|------|
| ✅ Adopted | **单一内容源 → 多形态呈现**：内容写一遍，渲染成站点/讲义/代理指令 | 复用性的核心；避免"课件、讲义、网页各写一遍" |
| ✅ Adopted | 内容以 Markdown/结构化文本为源（可版本管理、可 diff） | 大纲与讲义都是文本，天然适合 Git 管理与流水线处理 |
| ❌ Removed | Sphinx / MyST / mystmd 构建链 | 依赖重（Node + Python 双生态）、构建慢；本项目只借"源与呈现分离"思想 |
| 🔧 Improved | 用 **course_model.json / content_framework.json** 作为中间表示（schema-first） | Jupyter Book 用 myst.yml 管配置，但没有"课程级"的数据模型；我们把课程模型显式化，使五级流水线可独立替换实现 |

### 来源 3：nbgrader —— 作业闭环与评分量规

| 处理 | 内容 | 原因 |
|------|------|------|
| ✅ Adopted | **作业生命周期闭环**：布置→发布→收集→批改→反馈 | 这是"Delivery → Portfolio"回路的骨架 |
| ✅ Adopted | 评分量规（rubric）作为独立产物随任务下发 | 教学公平性与 Agent 反馈都需要统一量规 |
| ❌ Removed | 与 Jupyter Notebook 的强绑定（.ipynb 提交格式） | 真实课程产出物形态多样（报告/代码/链接/数据集），不能绑死 Notebook |
| 🔧 Improved | 量规模块化为 **rubric.json**，同时被交付站点（学生看）与 ILT 代理（反馈用）复用 | nbgrader 的量规服务于打分；我们让量规成为"教、学、评、Agent 反馈"四方共享的契约 |

### 来源 4：SCORM / xAPI（ADL）—— 打包与学习记录

| 处理 | 内容 | 原因 |
|------|------|------|
| ✅ Adopted | **清单式打包**（imsmanifest.xml → 我们的 course_model.json）：一份清单描述整个课程结构，可移植 | "换平台不重写"的标准化基础 |
| ✅ Adopted | **actor-verb-object 学习记录语句**（xAPI）→ records.jsonl | 作品集升级为可查询的证据链；语义对齐 IEEE 标准，未来可直连 LRS |
| ❌ Removed | SCORM 运行时 API（LMSInitialize 等浏览器内嵌模型）与 64KB 数据上限 | 年代久远、限制多；现代静态站点 + HTTP 记录已覆盖需求 |
| 🔧 Improved | 用 **JSONL 文件**承载学习记录（代替独立 LRS 服务） | 单人项目阶段零运维；文件即数据库，随时可迁移到真 LRS |

### 来源 5：LangGraph —— 工作流显式编排

| 处理 | 内容 | 原因 |
|------|------|------|
| ✅ Adopted | **节点 + 边 + 状态传递**的显式编排思想：每级是一个节点，级间传递有类型的结构化状态 | 流水线可调试、可单跑某级、可替换某节点 |
| ✅ Adopted | "workflow（确定性路径）与 agent（动态决策）分开"的观念 | 我们的流水线是确定性 workflow（可测试），LLM 扩写只是其中节点的可替换实现 |
| ❌ Removed | LangGraph 运行时本身（库依赖、状态持久化、流式） | 我们的五级是确定性转换，无须动态路由；引入框架反而增加验收成本 |
| 🔧 Improved | **阶段依赖自动展开**（`_expand_stages()`）：只跑某级时自动补齐前置级 | LangGraph 靠图定义保证顺序；CLI 场景下我们用依赖推导实现同等保证（已配测试用例） |

### 来源 6：Claude Agent Skills —— 代理封装规范

| 处理 | 内容 | 原因 |
|------|------|------|
| ✅ Adopted | **SKILL.md 规范**：YAML frontmatter（name/description）+ Instructions + Examples 的结构 | 这是 Agent 运行时识别与调用的事实标准，产物直接可被 Claude Code 等消费 |
| ✅ Adopted | 命名硬约束（name 小写连字符 ≤64 字符；description ≤1024 字符且含"功能+触发时机"）+ 渐进式披露 | 我们在构建时自检 + 测试复核这些约束，保证产物"真的合规" |
| ❌ Removed | zip 打包上传 / 平台绑定（claude.ai 上传流程） | 教学场景代理应随课程仓库版本管理，而非手工上传 |
| 🔧 Improved | 每个代理包附 **agent_config.json**（输入/输出 schema + KSTAR 认知循环）与 **rubric.json** | 规范只定义了"说明书"，我们补充"接口契约"，让代理可被程序化调用与评测 |

---

## 三、对比分析：六个来源解决的是哪一环

| 生产环节 | 谁在解决 | 我们拿的 |
|----------|----------|----------|
| 课程结构 | Open edX | 三级结构模型 |
| 内容生产 | Jupyter Book | 源/呈现分离 |
| 评测反馈 | nbgrader | 作业闭环 + 量规 |
| 学习记录 | SCORM/xAPI | 清单打包 + 语句记录 |
| 流程编排 | LangGraph | 节点+边+状态 |
| 代理封装 | Agent Skills | SKILL.md 规范 |

**关键判断**：六个来源各占一环，**没有一个提供"从大纲到成套课程"的端到端流水线**。单独拿来任何一个都只是单点工具——这正是"创造性组合"的切入点（对应评分标准最高档：多个来源 + 对比分析 + 创造性组合）。

---

## 四、创造性组合：粘合层是自己的

组合后的流水线（已在 Demo 中实现并测试通过）：

```
教学大纲(.md/.json)
   │  ① 结构（Open edX 思想）→ 简化三级 + schema 校验
   ▼
course_model.json  ←—— SCORM 清单思想（一份清单描述整门课）
   │  ② 内容（Jupyter Book 思想）→ 内容源与呈现分离
   ▼
content_framework.json（教学设计 + 量规 + 种子 FAQ）←—— nbgrader 量规思想
   │  ③ 代理（Agent Skills 规范）→ SKILL.md + 接口契约
   ▼
agents/ilt-*/（8 个学习代理包）
   │  ④ 呈现（轻量静态站点）
   ▼
site/（13 页交付站点）
   │  ⑤ 证据（xAPI 语句）→ actor-verb-object
   ▼
portfolio/（作品集 + records.jsonl 学习记录流）

全流程由 LangGraph 式显式编排（pipeline.py 节点 + 依赖展开）串联；
新增的"粘合层"（models.py 课程模型 + schema 校验 + 种子 FAQ）是各家都没有的部分。
```

**组合的验证不是形容词，是命令**：
```bash
python -m unittest discover -s tests -t .   # 33 tests OK
python pipeline.py                          # 五级端到端 [OK]
```

---

## 五、入选后持续拿来计划（对应每周 AAR 要求）

| 待评估方向 | 候选 | 目的 |
|------------|------|------|
| 自动批改 | nbgrader 深度用法 / CodeGrade 类方案 | W7-8 自动批改闭环 |
| LMS 对接 | SCORM 导出器（Rustici 云 API）/ cmi5 打包 | 产物直接进学校 LMS |
| 内容扩写 | DeepSeek（已验证）/ RAGFlow 课程知识库 | llm_hook 的具体实现选型 |
| 学习分析 | xAPI LRS（Learning Locker 等） | records.jsonl 升级为真 LRS |

找不到更好方案时，也会在 AAR 中写明"本周评估了 X 与 Y，现有方案仍最优，因为……"——持续检索与判断本身就是拿来主义的一部分。
