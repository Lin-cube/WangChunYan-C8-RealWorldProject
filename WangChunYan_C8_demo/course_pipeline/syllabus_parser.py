# -*- coding: utf-8 -*-
"""
syllabus_parser.py —— 第 1 级：教学大纲 → 结构化课程模型

支持两种输入格式：
  1. Markdown（.md）：老师用纯文本写的大纲，按约定的轻量格式书写（见 README）
  2. JSON（.json）：与 Course.to_dict() 相同结构的规范化数据

设计要点：
  - 解析器只做"语法 → 结构"的转换，不做内容创作（创作在 content_generator）
  - 解析错误必须给出明确的行号/原因，方便老师改大纲（而不是程序崩溃看不懂）
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from .models import Course, Exercise, Lesson, Module, course_from_dict


# ---------------------------------------------------------------------------
# 对外入口：根据文件扩展名自动选择解析器
# ---------------------------------------------------------------------------
def parse_syllabus(path: str | Path) -> Course:
    """解析教学大纲文件（.md / .markdown / .json），返回 Course 对象。"""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"找不到教学大纲文件：{p}")
    text = p.read_text(encoding="utf-8")
    suffix = p.suffix.lower()
    if suffix in (".md", ".markdown"):
        return parse_markdown_syllabus(text)
    if suffix == ".json":
        return parse_json_syllabus(text)
    raise ValueError(f"不支持的大纲格式：{suffix}（仅支持 .md / .markdown / .json）")


# ---------------------------------------------------------------------------
# JSON 解析：直接走 models 的 from_dict + 校验
# ---------------------------------------------------------------------------
def parse_json_syllabus(text: str) -> Course:
    """解析 JSON 格式的大纲。"""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"大纲 JSON 解析失败：{exc}") from exc
    return course_from_dict(data)


# ---------------------------------------------------------------------------
# Markdown 解析：行扫描状态机
#
# 约定格式（示例）：
#   # 课程标题
#   course_id: CS-AI101
#   description: 一句话简介
#   weeks: 8
#   instructor: 王老师
#   tags: AI, Python
#
#   ## objectives
#   - 课程目标一
#   - 课程目标二
#
#   ## module M1 | 模块标题 | W1-2
#   - objective: 模块目标一
#
#   ### lesson M1-L1 | 课时标题
#   - summary: 课时简介
#   - topic: 知识点一
#   - reading: 《参考书》第 1 章
#   - exercise: 练习标题 | coding | 30
#   - assignment: 作业标题 | 作业描述
# ---------------------------------------------------------------------------
def parse_markdown_syllabus(text: str) -> Course:
    """解析 Markdown 轻量大纲格式，返回经过校验的 Course。"""
    title: str | None = None
    meta: Dict[str, str] = {}
    objectives: List[str] = []
    modules: List[Module] = []

    section: str | None = None       # 当前处于哪个区：objectives / module / lesson / None
    cur_module: Module | None = None
    cur_lesson: Lesson | None = None

    lines = text.splitlines()
    for lineno, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line:
            continue

        # ---- 一级标题：课程名 ----
        if line.startswith("# "):
            if title is None:
                title = line[2:].strip()
            continue

        # ---- 三级标题：课时 ----
        if line.lower().startswith("### lesson"):
            head = line[len("### lesson"):].strip()
            parts = [x.strip() for x in head.split("|")]
            if not parts or not parts[0]:
                raise ValueError(f"第 {lineno} 行：课时标题格式应为 '### lesson M1-L1 | 标题'")
            if cur_module is None:
                raise ValueError(f"第 {lineno} 行：lesson 必须写在某个 '## module' 之下")
            cur_lesson = Lesson(
                lesson_id=parts[0],
                title=parts[1] if len(parts) > 1 and parts[1] else parts[0],
            )
            cur_module.lessons.append(cur_lesson)
            section = "lesson"
            continue

        # ---- 二级标题：模块 / objectives / 其他 ----
        if line.startswith("## "):
            head = line[3:].strip()
            if head.lower().startswith("module"):
                body = head[len("module"):].strip()
                parts = [x.strip() for x in body.split("|")]
                if not parts or not parts[0]:
                    raise ValueError(f"第 {lineno} 行：模块标题格式应为 '## module M1 | 标题 | W1-2'")
                cur_module = Module(
                    module_id=parts[0],
                    title=parts[1] if len(parts) > 1 and parts[1] else parts[0],
                    week_range=parts[2] if len(parts) > 2 else "",
                )
                modules.append(cur_module)
                cur_lesson = None
                section = "module"
            elif head.lower() == "objectives":
                section = "objectives"
                cur_lesson = None
            else:
                # 未知二级标题：跳过其内容（允许大纲里有其他说明性段落）
                section = None
                cur_lesson = None
            continue

        # ---- 列表项：根据所在区解释含义 ----
        if line.startswith("- ") or line.startswith("* "):
            item = line[2:].strip()
            if section == "objectives":
                objectives.append(item)
            elif section == "module" and cur_lesson is None and cur_module is not None:
                # 模块下的列表项只接受 objective: 前缀
                if item.lower().startswith("objective:"):
                    cur_module.objectives.append(item.split(":", 1)[1].strip())
            elif section == "lesson" and cur_lesson is not None:
                _apply_lesson_item(cur_lesson, item, lineno)
            # 其他情况（例如未知段落里的列表）直接忽略
            continue

        # ---- 顶层元信息：key: value（只在进入任何 section 之前收集）----
        if section is None and cur_module is None and ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip().lower()] = value.strip()
            continue

    # ---- 汇总构造 Course ----
    if title is None:
        raise ValueError("大纲缺少一级标题（'# 课程名称'）")
    if not modules:
        raise ValueError("大纲中没有解析到任何模块（'## module M1 | ...'）")

    course = Course(
        course_id=meta.get("course_id", "COURSE-001"),
        title=title,
        description=meta.get("description", ""),
        weeks=_to_int(meta.get("weeks", "8"), "weeks"),
        instructor=meta.get("instructor", ""),
        tags=[t.strip() for t in meta.get("tags", "").split(",") if t.strip()],
        objectives=objectives,
        modules=modules,
    )
    course.validate()  # 统一走校验，保证坏数据不出流水线
    return course


def _apply_lesson_item(lesson: Lesson, item: str, lineno: int) -> None:
    """把 '- key: value' 形式的列表项写入课时对象。"""
    if ":" not in item:
        raise ValueError(f"第 {lineno} 行：课时列表项应为 '- key: value' 形式，实际为：{item}")
    key, value = item.split(":", 1)
    key = key.strip().lower()
    value = value.strip()

    if key == "summary":
        lesson.summary = value
    elif key == "topic":
        lesson.topics.append(value)
    elif key == "reading":
        lesson.readings.append(value)
    elif key == "exercise":
        # 形如：标题 | 类型 | 分钟
        parts = [x.strip() for x in value.split("|")]
        title = parts[0] if parts else ""
        ex_type = parts[1] if len(parts) > 1 and parts[1] else "practice"
        minutes = _to_int(parts[2], f"第 {lineno} 行的练习时长") if len(parts) > 2 and parts[2] else 15
        lesson.exercises.append(Exercise(title=title, ex_type=ex_type, minutes=minutes))
    elif key == "assignment":
        # 形如：标题 | 描述
        parts = [x.strip() for x in value.split("|")]
        lesson.assignments.append({
            "title": parts[0] if parts else "",
            "description": parts[1] if len(parts) > 1 else "",
        })
    else:
        raise ValueError(f"第 {lineno} 行：不认识的课时字段 '{key}'（支持 summary/topic/reading/exercise/assignment）")


def _to_int(value: str, field_name: str) -> int:
    """安全地把字符串转成整数，失败时给出中文报错。"""
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"字段 {field_name} 应为整数，实际为：{value!r}") from exc
