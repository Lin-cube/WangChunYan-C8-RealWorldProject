# WangChunYan_C8_demo —— 课程生产流水线原型（Course Production Pipeline）

> C8 早期验证物（Proof of Capability）｜ 项目方向：**Project C 课程生产体系**
> 一条命令，把教学大纲变成：课程内容框架 → ILT 学习代理 → 交付站点 → 学生作品集。

## 这是什么

这是 Project C「课程生产体系」的**可运行原型**，实现了完整五级流水线：

| 级 | 工作流 | 做了什么 | 产物 |
|----|--------|----------|------|
| 1 | Syllabus → Content（解析） | 教学大纲（.md/.json）→ 结构化课程模型 | `course_model.json` |
| 2 | Syllabus → Content（生成） | 课程模型 → 8 份教学设计 + 种子 FAQ | `content_framework.json` |
| 3 | Content → Agent | 每课时封装为 ILT 学习代理（SKILL.md 规范） | `agents/ilt-*/` |
| 4 | Agent → Delivery | 生成静态课程站点（13 个页面） | `site/` |
| 5 | Delivery → Portfolio | 学生提交自动归档为作品集 + xAPI 风格学习记录 | `portfolio/` |

**已验证状态**（2026-11-22 实测）：
- ✅ 33 个单元/集成测试全部通过（`python -m unittest discover -s tests -t .`）
- ✅ 端到端流水线一键跑通（`python pipeline.py`）
- ✅ 产物已生成在 `output/` 目录（可直接打开查看）

## 目录结构

```
WangChunYan_C8_demo/
├── pipeline.py                 # CLI 入口（一键跑通五级）
├── course_pipeline/            # 流水线核心包（零第三方依赖，纯标准库）
│   ├── models.py               #   统一数据模型（Course/Module/Lesson/Exercise）
│   ├── syllabus_parser.py      #   ① 大纲解析（Markdown / JSON 双格式）
│   ├── content_generator.py    #   ② 内容框架生成（教学设计/幻灯片/讲义/量规）
│   ├── ilt_agent_builder.py    #   ③ ILT 学习代理封装（SKILL.md 规范）
│   ├── delivery_builder.py     #   ④ 静态交付站点生成
│   └── portfolio_archiver.py   #   ⑤ 作品集归档（xAPI 风格学习记录）
├── samples/                    # 样例数据
│   ├── sample_syllabus.md      #   样例大纲（《AI+X 智能应用开发实战》8 周）
│   ├── sample_syllabus.json    #   JSON 格式大纲样例（与 .md 共用数据模型）
│   └── sample_submissions.json #   学生提交记录样例（脱敏）
├── tests/                      # 测试（33 个用例：5 个单元测试文件 + 端到端）
├── output/                     # 流水线实际产物（已生成，验收证据）
├── SETUP.md                    # 安装与运行说明
└── README.md                   # 本文件
```

## 快速开始

```bash
cd WangChunYan_C8_demo

# 1) 一键跑通全部流水线（只需 Python 3.8+，无需安装任何依赖）
python pipeline.py

# 2) 运行全部测试
python -m unittest discover -s tests -t .

# 3) 查看产物
#    课程站点：output/site/index.html          （浏览器直接打开）
#    班级作品集：output/portfolio/index.html
#    学习代理：output/agents/ilt-m2-l2/SKILL.md
```

详细说明见 [SETUP.md](SETUP.md)。

## 输入格式：教学大纲

支持 **Markdown** 与 **JSON** 两种格式（同一数据模型，可互换）。Markdown 格式约定：

```markdown
# 课程标题
course_id: CS-AI201
description: 一句话简介
weeks: 8
instructor: 王老师
tags: AI, Agent

## objectives
- 课程目标一

## module M1 | 模块标题 | W1-2
- objective: 模块目标

### lesson M1-L1 | 课时标题
- summary: 课时简介
- topic: 知识点
- reading: 阅读材料
- exercise: 练习标题 | coding | 30
- assignment: 作业标题 | 作业描述
```

解析器对坏数据**零容忍**（字段拼错、编号不匹配会报出明确行号/原因），保证坏大纲进不了流水线。

## 设计要点（为什么这样做）

1. **Schema-first 解耦**：每一级只通过 `models.py` 定义的结构化数据交换。想把「模板生成」换成「LLM 生成」？只改 `content_generator.py` 一个文件，输入输出契约不变。
2. **零依赖**：只用 Python 标准库——任何机器 `python pipeline.py` 就能跑，验收人零安装成本。
3. **规范对齐**：ILT 代理的 SKILL.md 严格遵守 Agent Skills 规范（name 小写连字符 ≤64 字符、description ≤1024 字符且含"功能+触发时机"），构建时自检、测试时复核——产物真的能被 Claude Code 等 Agent 运行时识别。
4. **学习记录 xAPI 风格**：作品集的 `records.jsonl` 用 actor-verb-object 三元组记录学习行为，是可查询的证据链，不是文件堆。
5. **全程可测试**：33 个测试覆盖解析、生成、封装、渲染、归档与端到端，坏数据路径也有用例。

## 现状边界（诚实声明）

这是**早期验证原型**（对应 proposal Part 5），不是完成品：

| 已实现（可运行） | 未实现（入选后推进） |
|------------------|----------------------|
| 五级流水线端到端跑通 | LLM 扩写内容（预留 llm_hook 接口） |
| Markdown/JSON 双格式解析 | 真实 LMS 对接（Open edX/LTI） |
| SKILL.md 规范的 ILT 代理包 | Agent 运行时联调（Claude Code 实测调用） |
| 静态交付站点 | 用户系统 / 学习进度跟踪 |
| 作品集归档 + xAPI 风格记录 | 自动批改（nbgrader 式闭环） |

## 我从哪里"拿来"（摘要）

| 借鉴对象 | 借了什么 | 在哪体现 |
|----------|----------|----------|
| Open edX | 课程结构层级（section→subsection→unit） | Course→Module→Lesson 模型 |
| Jupyter Book | 内容源与呈现分离 | content_md 与站点渲染分离 |
| nbgrader | assign→release→collect→autograde 循环 | 作业/量规/反馈闭环设计 |
| SCORM/xAPI | 打包清单 + actor-verb-object 学习记录 | course_model.json + records.jsonl |
| LangGraph | 显式节点/边工作流编排 | pipeline.py 阶段编排 + 依赖展开 |
| Agent Skills | SKILL.md 封装规范 | ilt_agent_builder 产物 |

完整取舍分析见 `../WangChunYan_C8_拿来说明.md`。
