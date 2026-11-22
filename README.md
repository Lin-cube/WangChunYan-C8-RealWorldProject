# C8 提交包 —— WangChunYan（2023105110151）

> **挑战**：C8 Real-World Project Execution（真实项目落地）
> **项目方向**：Project C 课程生产体系 ｜ **提交日期**：2026-11-22 ｜ **挑战截止**：2026-12-31

## 一、提交物清单（对照 CHALLENGE.md 命名规范）

| 规范要求 | 本包文件 | 说明 | 状态 |
|----------|----------|------|------|
| `姓名_C8_proposal.md` | `WangChunYan_C8_proposal.md` | 完整 5 部分申请书 | ✅ |
| `姓名_C8_demo.*` | `WangChunYan_C8_demo/` | 早期验证物：可运行的课程生产流水线原型 | ✅ |
| `姓名_C8_AI日志.md` | `WangChunYan_C8_AI日志.md` | Proposal + Demo 开发全过程 AI 使用记录 | ✅ |
| `姓名_C8_拿来说明.md` | `WangChunYan_C8_拿来说明.md` | 6 个参考来源的检索→判断→重构链路 | ✅ |
| （建议附） | `README.md`（本文件） | 提交包导航与验收指引 | ✅ |

## 二、30 秒验收指引（评审人可自行复核）

```bash
cd WangChunYan_C8_demo

# 1) 测试：预期 Ran 33 tests ... OK
python -m unittest discover -s tests -t .

# 2) 流水线：预期五级全部 [OK]
python pipeline.py

# 3) 看产物（浏览器直接打开）
#    output/site/index.html        课程交付站点（13 页）
#    output/portfolio/index.html   班级作品集 + 学习记录流
#    output/agents/ilt-m2-l2/SKILL.md  ILT 学习代理（Agent Skills 规范）
```

环境要求：Python 3.8+（零第三方依赖，无需 pip install）。

## 三、一分钟看懂这个项目

**要解决的问题**：一门课的内容生产（大纲→课件→练习→作业→评分标准→答疑）全靠教师手工，重复劳动、质量不一、学生产出不沉淀。

**我的方案**：一条五级课程生产流水线——

| 级 | 输入 → 输出 | 借鉴 |
|----|-------------|------|
| ① 解析 | 教学大纲 → 课程模型 | Open edX 结构层级 |
| ② 生成 | 课程模型 → 教学设计 + 量规 + FAQ | Jupyter Book 源/呈现分离 + nbgrader 量规 |
| ③ 封装 | 教学设计 → ILT 学习代理（SKILL.md） | Claude Agent Skills 规范 |
| ④ 交付 | 内容框架 → 静态课程站点 | 轻量静态呈现 |
| ⑤ 归档 | 学生提交 → 作品集 + 学习记录 | xAPI actor-verb-object 语句 |

**现状**（2026-11-22 实测）：原型已跑通 ✅ 33 测试通过 ✅ 产物已生成 ✅；LLM 扩写、Agent 运行时联调、真实学生试用三件事列入入选后 W1-4 计划（见 proposal 执行方案）。

## 四、文件结构

```
WangChunYan_C8_提交包/
├── README.md                      ← 本文件
├── WangChunYan_C8_proposal.md     ← 申请书（5 部分）
├── WangChunYan_C8_AI日志.md        ← AI 使用记录
├── WangChunYan_C8_拿来说明.md      ← 参考来源与取舍
└── WangChunYan_C8_demo/           ← 早期验证物（可运行）
    ├── README.md / SETUP.md       ←   使用文档
    ├── pipeline.py                ←   流水线入口
    ├── course_pipeline/           ←   核心代码（6 个模块，纯标准库）
    ├── samples/                   ←   样例大纲 ×2 + 提交记录
    ├── tests/                     ←   33 个测试用例
    └── output/                    ←   实际运行产物（验收证据）
```

## 五、提交前自检（对照 CHALLENGE.md 第十一节）

```
☑ 选择了具体项目（Project C）并说明了原因
☑ 拿来主义分析列了 6 个参考来源（要求 ≥3）
☑ 每个来源有 adopted / removed / improved 分析
☑ 执行方案用 KSTAR 结构（K→S→T→Â→R̂）
☑ R̂ 足够具体（4 项可交付物 + 4 条成功标准 + 4 种验证方法）
☑ 定义了明确角色和边界（Builder 主 + Architect 兼）
☑ 至少有一个早期验证物（可运行 Demo，33 测试通过）
☑ 有 AI 日志和拿来说明
```

> 说明：proposal 中 C1–C7 具体产出物名称留有"按实际补全"标注，提交前请补充你各挑战的真实交付物名称；其余内容均为可验证事实。
