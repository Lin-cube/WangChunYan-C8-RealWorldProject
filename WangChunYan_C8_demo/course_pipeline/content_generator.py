# -*- coding: utf-8 -*-
"""
content_generator.py —— 第 2 级：课程模型 → 课程内容框架（Syllabus → Content）

输入：models.Course（结构化课程模型）
输出：ContentFramework（字典），包含：
  - course_map   ：学习路径图（模块 → 课时 → 练习链）
  - faq_seed     ：每个模块的种子 FAQ（后续可喂给 Agent 做自动问答）
  - lessons[]    ：每课时的"教学设计包"：
        slide_outline  幻灯片大纲（标题页/目标页/知识点页/练习页/总结页）
        content_md     课堂讲义初稿（Markdown）
        teaching_flow  教学流程与时间分配
        rubric         评分量规（四维度）

内容从哪来？
  本阶段是"模板化生成"——用确定性模板把大纲字段扩写成教学设计骨架。
  这是刻意的设计决策（见 AI 日志）：模板生成保证可测试、可重复、零依赖；
  真正的"AI 扩写"留给 llm_hook 接口（可插拔），接入后不改变本级的输入输出契约。

参考借鉴（详见《拿来说明》）：
  - Open edX：课程结构层级（section/subsection/unit）→ 我们的 Module/Lesson 两级
  - Jupyter Book：内容与呈现分离（内容源 → 多格式发布）→ content_md 与站点分离
"""

from __future__ import annotations

from typing import Any, Dict, List

from .models import Course, Lesson, Module

# 教学流程模板：环节名称 + 默认时长（分钟）；"练习"环节时长按习题实际时长计算
TEACHING_FLOW_TEMPLATE = [
    ("导入", 5),      # 问题引入、上节回顾
    ("讲解", 20),     # 知识点讲解
    ("演示", 15),     # 案例/操作演示
    ("练习", 0),      # 课堂练习（时长 = 练习时长之和，最少 10 分钟）
    ("总结", 10),     # 要点回顾、作业布置
]

# 评分量规四维度模板（权重和为 1.0）
RUBRIC_TEMPLATE = [
    ("概念理解", 0.30, "能准确复述核心概念，并解释其适用边界"),
    ("实践完成", 0.30, "按要求完成练习/作业，结果可运行或可验证"),
    ("表达清晰", 0.20, "产出物结构清晰，说明文档完整可读"),
    ("复盘改进", 0.20, "能指出不足并给出具体改进动作"),
]


def generate_content(course: Course) -> Dict[str, Any]:
    """对整门课执行内容框架生成，返回 ContentFramework 字典。"""
    course.validate()  # 防御性校验：坏数据不允许进入生成环节

    lessons_design: List[Dict[str, Any]] = []
    for module in course.modules:
        for lesson in module.lessons:
            lessons_design.append(_design_lesson(course, module, lesson))

    framework: Dict[str, Any] = {
        "course_id": course.course_id,
        "course_title": course.title,
        "generator": "template-v1",          # 生成器版本号，便于追溯
        "course_map": _build_course_map(course),
        "faq_seed": _build_faq_seed(course),
        "lessons": lessons_design,
    }
    return framework


# ---------------------------------------------------------------------------
# 单课时教学设计
# ---------------------------------------------------------------------------
def _design_lesson(course: Course, module: Module, lesson: Lesson) -> Dict[str, Any]:
    """为单个课时生成教学设计包。"""
    # 1) 教学流程：练习环节时长 = 习题时长之和（不足 10 分钟补到 10 分钟）
    exercise_minutes = sum(ex.minutes for ex in lesson.exercises)
    flow = []
    for name, minutes in TEACHING_FLOW_TEMPLATE:
        if name == "练习":
            minutes = max(exercise_minutes, 10)
        flow.append({"stage": name, "minutes": minutes})

    # 2) 幻灯片大纲：标题页 + 目标页 + 每个知识点一页 + 练习页 + 总结页
    slides = [{"slide": 1, "title": lesson.title, "bullets": [f"{course.title} · {module.title}", lesson.summary or "（待补充简介）"]}]
    slides.append({"slide": 2, "title": "本节目标", "bullets": [f"掌握：{t}" for t in lesson.topics] or ["（大纲未填写知识点）"]})
    slide_no = 3
    for topic in lesson.topics:
        slides.append({"slide": slide_no, "title": topic, "bullets": [f"要点：{topic}", "结合案例说明适用场景", "常见误区提醒"]})
        slide_no += 1
    if lesson.exercises:
        slides.append({"slide": slide_no, "title": "课堂练习", "bullets": [f"{ex.title}（{ex.ex_type}，约 {ex.minutes} 分钟）" for ex in lesson.exercises]})
        slide_no += 1
    assignment_titles = [a["title"] for a in lesson.assignments]
    summary_bullets = ["回顾本节要点"] + (assignment_titles if assignment_titles else ["（无课后作业）"])
    slides.append({"slide": slide_no, "title": "小结与作业", "bullets": summary_bullets})

    # 3) 讲义初稿（Markdown）：把结构化字段扩写成讲义骨架
    content_md = _render_lesson_markdown(course, module, lesson)

    # 4) 评分量规：模板四维度 + 具体化到本课时
    rubric = _build_rubric(lesson)

    return {
        "lesson_id": lesson.lesson_id,
        "module_id": module.module_id,
        "title": lesson.title,
        "summary": lesson.summary,
        "topics": list(lesson.topics),
        "teaching_flow": flow,
        "slide_outline": slides,
        "content_md": content_md,
        "readings": list(lesson.readings),
        "exercises": [ex.to_dict() for ex in lesson.exercises],
        "assignments": list(lesson.assignments),
        "rubric": rubric,
    }


def _render_lesson_markdown(course: Course, module: Module, lesson: Lesson) -> str:
    """生成单课时的讲义 Markdown 初稿。"""
    lines: List[str] = []
    lines.append(f"# {lesson.title}")
    lines.append("")
    lines.append(f"> 课程：{course.title}（{course.course_id}） ｜ 模块：{module.title} ｜ 课时：{lesson.lesson_id}")
    lines.append("")
    if lesson.summary:
        lines.append(lesson.summary)
        lines.append("")
    lines.append("## 学习目标")
    if lesson.topics:
        lines.extend([f"- 掌握 **{t}**" for t in lesson.topics])
    else:
        lines.append("- （请在大纲中补充知识点）")
    lines.append("")
    if module.objectives:
        lines.append("## 模块目标对照")
        lines.extend([f"- {o}" for o in module.objectives])
        lines.append("")
    lines.append("## 知识讲解")
    for topic in lesson.topics:
        lines.append(f"### {topic}")
        lines.append(f"（讲义正文待扩写：围绕「{topic}」展开概念定义、典型示例、易错点。）")
        lines.append("")
    if lesson.readings:
        lines.append("## 阅读材料")
        lines.extend([f"- {r}" for r in lesson.readings])
        lines.append("")
    if lesson.exercises:
        lines.append("## 课堂练习")
        for ex in lesson.exercises:
            lines.append(f"### {ex.title}（{ex.ex_type}，约 {ex.minutes} 分钟）")
            lines.append(ex.description or "（练习说明待补充）")
            lines.append("")
    if lesson.assignments:
        lines.append("## 课后作业")
        for a in lesson.assignments:
            lines.append(f"- **{a['title']}**：{a.get('description', '')}")
        lines.append("")
    lines.append("## 小结")
    lines.append(f"本节围绕 {len(lesson.topics)} 个知识点展开，课后请完成作业并记录学习过程（将自动归档进个人作品集）。")
    return "\n".join(lines)


def _build_rubric(lesson: Lesson) -> List[Dict[str, Any]]:
    """基于模板生成本课时的评分量规。"""
    rubric = []
    for dimension, weight, base_criteria in RUBRIC_TEMPLATE:
        rubric.append({
            "dimension": dimension,
            "weight": weight,
            "criteria": f"{base_criteria}（针对本课时知识点：{'、'.join(lesson.topics) or '见大纲'}）",
        })
    return rubric


# ---------------------------------------------------------------------------
# 课程级产物：学习路径图 + 种子 FAQ
# ---------------------------------------------------------------------------
def _build_course_map(course: Course) -> Dict[str, Any]:
    """生成学习路径：模块 → 课时 → 练习，供交付站点导航和 Agent 规划使用。"""
    path = []
    for module in course.modules:
        lessons = []
        for lesson in module.lessons:
            lessons.append({
                "lesson_id": lesson.lesson_id,
                "title": lesson.title,
                "exercise_titles": [ex.title for ex in lesson.exercises],
            })
        path.append({
            "module_id": module.module_id,
            "title": module.title,
            "week_range": module.week_range,
            "objectives": list(module.objectives),
            "lessons": lessons,
        })
    return {"course_id": course.course_id, "modules": path}


def _build_faq_seed(course: Course) -> List[Dict[str, str]]:
    """为每个模块生成 3 条种子 FAQ，作为问答 Agent 的初始知识。"""
    faq: List[Dict[str, str]] = []
    for module in course.modules:
        lesson_titles = "、".join(l.title for l in module.lessons)
        faq.append({
            "module_id": module.module_id,
            "question": f"{module.title}（{module.week_range}）主要学什么？",
            "answer": f"本模块覆盖：{lesson_titles}。目标：{'；'.join(module.objectives) or '见课程大纲'}",
        })
        faq.append({
            "module_id": module.module_id,
            "question": f"{module.title}怎么练习？",
            "answer": f"每个课时都配有课堂练习与课后作业，完成后会自动归档进作品集。课时：{lesson_titles}。",
        })
        faq.append({
            "module_id": module.module_id,
            "question": f"如何检验我掌握了 {module.title}？",
            "answer": "按评分量规自评四维度：概念理解 30% + 实践完成 30% + 表达清晰 20% + 复盘改进 20%。",
        })
    return faq
