# SETUP.md —— 安装与运行说明

## 环境要求

| 项目 | 要求 | 说明 |
|------|------|------|
| Python | 3.8 及以上 | 只用标准库，**无需 pip install 任何第三方包** |
| 操作系统 | Windows / macOS / Linux | 已在 Windows + Python 3.13 实测 |
| 浏览器 | 任意现代浏览器 | 查看交付站点与作品集 |

验证 Python 版本：

```bash
python --version    # 应显示 3.8+
```

## 三步跑通

### 1. 运行流水线

```bash
cd WangChunYan_C8_demo
python pipeline.py
```

预期输出（末尾）：

```
[OK] parse      课程《AI+X 智能应用开发实战》：4 个模块 / 8 个课时
[OK] content    生成 8 份教学设计 + 12 条种子 FAQ
[OK] agents     封装 8 个 ILT 学习代理（含 SKILL.md）
[OK] delivery   生成 13 个静态页面
[OK] portfolio  归档 7 条学习记录 / 3 名学生
```

### 2. 运行测试（33 个用例）

```bash
python -m unittest discover -s tests -t .
```

预期输出：`Ran 33 tests ... OK`

### 3. 查看产物

| 产物 | 打开方式 |
|------|----------|
| 课程站点 | 浏览器打开 `output/site/index.html` |
| 班级作品集 | 浏览器打开 `output/portfolio/index.html` |
| 某课时学习代理 | 查看 `output/agents/ilt-m2-l2/SKILL.md` |
| 学习记录流 | 查看 `output/portfolio/records.jsonl`（每行一条） |

> 提示：站点是纯静态 HTML，双击 file:// 直接打开即可；也可以 `python -m http.server 8000` 后访问 `http://localhost:8000/output/site/`。

## 常用命令

```bash
# 指定自己的大纲与输出目录
python pipeline.py --syllabus path/to/my_syllabus.md --out my_output

# 只跑某一级（调试）
python pipeline.py --stage parse       # 只解析大纲
python pipeline.py --stage content     # 解析 + 内容生成（自动补依赖）
python pipeline.py --stage agents      # 解析 + 内容 + 代理封装
python pipeline.py --stage delivery    # 解析 + 内容 + 站点
python pipeline.py --stage portfolio   # 解析 + 作品集归档

# 使用 JSON 格式大纲
python pipeline.py --syllabus samples/sample_syllabus.json --out output_json

# 使用自己的学生提交记录（注意 lesson_id 必须存在于大纲中）
python pipeline.py --submissions path/to/my_submissions.json
```

## 输入文件说明

### 教学大纲（.md 或 .json）

- Markdown 格式约定见 README「输入格式」一节
- JSON 格式与 `course_model.json` 结构相同（参考 `samples/sample_syllabus.json`）
- 解析失败会给出明确的中文错误（含行号），便于修正

### 学生提交记录（.json）

```json
{
  "submissions": [
    {
      "student_id": "2023105110151",
      "student_name": "WangChunYan",
      "lesson_id": "M1-L1",
      "artifact": "路径或链接",
      "artifact_type": "report",
      "submitted_at": "2026-09-15T21:30:00+08:00",
      "note": "备注"
    }
  ]
}
```

约束：`lesson_id` 必须能在大纲中找到，否则归档报错（这是刻意的数据完整性校验）。

## 常见问题

**Q：运行报 `找不到教学大纲文件`？**
A：确认在 `WangChunYan_C8_demo` 目录下运行，或用 `--syllabus` 传绝对路径。

**Q：报 `[课程数据校验失败]`？**
A：数据校验拦截了坏数据，错误信息会指出具体字段，按提示修正大纲即可。

**Q：能把模板生成换成 LLM 生成吗？**
A：可以。`content_generator.py` 是唯一的"内容创作"模块，替换它的实现即可，输入输出契约（ContentFramework 结构）不变，其他四级零改动。

**Q：Windows 下中文乱码？**
A：用 `python`（而非 `py -2`）运行；终端请使用 UTF-8 编码（Windows Terminal / PowerShell 默认即可）。
