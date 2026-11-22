# -*- coding: utf-8 -*-
"""
models.py —— 统一数据模型（流水线的"中间表示"，IR）

为什么需要这一层？
  教学大纲（Syllabus）是给人看的文本，而内容生成器、Agent 构建器、站点生成器
  都是程序。中间必须有一个"结构化的课程模型"作为桥梁。
  这一层借鉴了 Open edX 的课程结构思想（课程 → 章节 → 小节 → 单元），
  但做了一定简化：Course → Module（模块）→ Lesson（课时）三级。

数据流向：
  大纲(.md/.json) --parse--> Course --generate--> ContentFramework
  ContentFramework --build--> ILT Agents / 交付站点 / 作品集
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List


# ---------------------------------------------------------------------------
# 校验辅助函数
# ---------------------------------------------------------------------------
def _require(condition: bool, message: str) -> None:
    """断言式校验：不满足条件就抛出带中文提示的 ValueError。"""
    if not condition:
        raise ValueError(f"[课程数据校验失败] {message}")


# ---------------------------------------------------------------------------
# 练习（Exercise）：课时内的最小练习单元
# ---------------------------------------------------------------------------
@dataclass
class Exercise:
    title: str                 # 练习标题
    ex_type: str = "practice"  # 练习类型：quiz / coding / discussion / practice
    minutes: int = 15          # 预估完成时长（分钟）
    description: str = ""      # 练习说明

    def validate(self) -> None:
        _require(bool(self.title.strip()), "练习标题不能为空")
        _require(self.minutes > 0, f"练习 {self.title} 的时长必须为正整数")

    def to_dict(self) -> Dict[str, Any]:
        """转换为普通字典（便于写 JSON）。"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Exercise":
        """从字典还原 Exercise 对象。"""
        return cls(
            title=str(data.get("title", "")),
            ex_type=str(data.get("ex_type", "practice")),
            minutes=int(data.get("minutes", 15)),
            description=str(data.get("description", "")),
        )


# ---------------------------------------------------------------------------
# 课时（Lesson）：一次可交付的教学单元，是内容生成与 Agent 封装的最小单位
# ---------------------------------------------------------------------------
@dataclass
class Lesson:
    lesson_id: str                       # 课时编号，必须形如 M1-L1（与所属模块前缀一致）
    title: str                           # 课时标题
    summary: str = ""                    # 一句话简介
    topics: List[str] = field(default_factory=list)      # 知识点列表
    readings: List[str] = field(default_factory=list)    # 阅读材料
    exercises: List[Exercise] = field(default_factory=list)  # 练习列表
    assignments: List[Dict[str, str]] = field(default_factory=list)  # 课后作业 [{title, description}]

    def validate(self, module_id: str | None = None) -> None:
        """校验课时数据合法性；若给出所属模块 ID，还会校验编号前缀一致性。"""
        _require(bool(self.lesson_id.strip()), "课时编号不能为空")
        _require(bool(self.title.strip()), f"课时 {self.lesson_id} 的标题不能为空")
        if module_id is not None:
            _require(
                self.lesson_id.startswith(module_id + "-"),
                f"课时编号 {self.lesson_id} 应以 {module_id}- 开头（属于模块 {module_id}）",
            )
        for ex in self.exercises:
            ex.validate()
        for a in self.assignments:
            _require(bool(a.get("title", "").strip()), f"课时 {self.lesson_id} 存在没有标题的作业")

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Lesson":
        return cls(
            lesson_id=str(data.get("lesson_id", "")),
            title=str(data.get("title", "")),
            summary=str(data.get("summary", "")),
            topics=[str(t) for t in data.get("topics", [])],
            readings=[str(r) for r in data.get("readings", [])],
            exercises=[Exercise.from_dict(e) for e in data.get("exercises", [])],
            assignments=[dict(a) for a in data.get("assignments", [])],
        )


# ---------------------------------------------------------------------------
# 模块（Module）：一组相关课时的集合，对应教学大纲中的一个"周次/主题"段落
# ---------------------------------------------------------------------------
@dataclass
class Module:
    module_id: str                  # 模块编号，必须形如 M1
    title: str                      # 模块标题
    week_range: str = ""            # 覆盖周次，如 "W1-2"
    objectives: List[str] = field(default_factory=list)   # 模块教学目标
    lessons: List[Lesson] = field(default_factory=list)

    def validate(self) -> None:
        _require(bool(self.module_id.strip()), "模块编号不能为空")
        _require(self.module_id.upper().startswith("M"), f"模块编号 {self.module_id} 应以 M 开头（如 M1）")
        _require(bool(self.title.strip()), f"模块 {self.module_id} 的标题不能为空")
        _require(len(self.lessons) > 0, f"模块 {self.module_id} 至少要包含一个课时")
        for lesson in self.lessons:
            lesson.validate(module_id=self.module_id)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Module":
        return cls(
            module_id=str(data.get("module_id", "")),
            title=str(data.get("title", "")),
            week_range=str(data.get("week_range", "")),
            objectives=[str(o) for o in data.get("objectives", [])],
            lessons=[Lesson.from_dict(l) for l in data.get("lessons", [])],
        )


# ---------------------------------------------------------------------------
# 课程（Course）：整门课的根对象
# ---------------------------------------------------------------------------
@dataclass
class Course:
    course_id: str                  # 课程编号，如 CS-AI101
    title: str                      # 课程名称
    description: str = ""           # 课程简介
    weeks: int = 8                  # 课程总周数
    instructor: str = ""            # 授课教师
    tags: List[str] = field(default_factory=list)          # 课程标签
    objectives: List[str] = field(default_factory=list)    # 课程总目标
    modules: List[Module] = field(default_factory=list)

    def validate(self) -> None:
        """整体校验：课程元信息 + 所有模块。任何一处不合法都会抛 ValueError。"""
        _require(bool(self.course_id.strip()), "课程编号不能为空")
        _require(bool(self.title.strip()), "课程名称不能为空")
        _require(self.weeks > 0, "课程周数必须大于 0")
        _require(len(self.modules) > 0, "课程至少要包含一个模块")
        seen_module_ids = set()
        seen_lesson_ids = set()
        for module in self.modules:
            module.validate()
            _require(module.module_id not in seen_module_ids, f"模块编号重复：{module.module_id}")
            seen_module_ids.add(module.module_id)
            for lesson in module.lessons:
                _require(lesson.lesson_id not in seen_lesson_ids, f"课时编号重复：{lesson.lesson_id}")
                seen_lesson_ids.add(lesson.lesson_id)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Course":
        return cls(
            course_id=str(data.get("course_id", "")),
            title=str(data.get("title", "")),
            description=str(data.get("description", "")),
            weeks=int(data.get("weeks", 8)),
            instructor=str(data.get("instructor", "")),
            tags=[str(t) for t in data.get("tags", [])],
            objectives=[str(o) for o in data.get("objectives", [])],
            modules=[Module.from_dict(m) for m in data.get("modules", [])],
        )

    # 便捷查询：根据课时编号找到课时（作品集归档时要用）
    def find_lesson(self, lesson_id: str) -> Lesson | None:
        for module in self.modules:
            for lesson in module.lessons:
                if lesson.lesson_id == lesson_id:
                    return lesson
        return None

    def all_lessons(self) -> List[Lesson]:
        """返回全部课时（按模块顺序、课时顺序）。"""
        result: List[Lesson] = []
        for module in self.modules:
            result.extend(module.lessons)
        return result


# ---------------------------------------------------------------------------
# 模块级工具函数
# ---------------------------------------------------------------------------
def course_to_dict(course: Course) -> Dict[str, Any]:
    """Course → 可序列化字典。"""
    return course.to_dict()


def course_from_dict(data: Dict[str, Any]) -> Course:
    """字典 → Course，并自动做整体校验。"""
    course = Course.from_dict(data)
    course.validate()
    return course
