# -*- coding: utf-8 -*-
"""syllabus_parser 单元测试：Markdown / JSON 两种输入路径 + 错误处理。"""
import os
import sys
import unittest
from pathlib import Path

# 让测试可以从任意工作目录运行：把 demo 根目录加入模块搜索路径
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from course_pipeline.syllabus_parser import (  # noqa: E402
    parse_json_syllabus,
    parse_markdown_syllabus,
    parse_syllabus,
)

DEMO_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_MD = DEMO_ROOT / "samples" / "sample_syllabus.md"
SAMPLE_JSON = DEMO_ROOT / "samples" / "sample_syllabus.json"


class TestMarkdownParser(unittest.TestCase):
    """Markdown 大纲解析测试。"""

    def test_parse_sample_md(self):
        """样例 Markdown 大纲能解析出完整课程结构。"""
        course = parse_syllabus(SAMPLE_MD)
        self.assertEqual(course.course_id, "CS-AI201")
        self.assertEqual(course.title, "AI+X 智能应用开发实战")
        self.assertEqual(course.weeks, 8)
        self.assertEqual(len(course.modules), 4)
        self.assertEqual(len(course.all_lessons()), 8)

    def test_lesson_ids_follow_module_prefix(self):
        """课时编号必须与其所属模块前缀一致（M1-L1 属于 M1）。"""
        course = parse_syllabus(SAMPLE_MD)
        for module in course.modules:
            for lesson in module.lessons:
                self.assertTrue(
                    lesson.lesson_id.startswith(module.module_id + "-"),
                    f"{lesson.lesson_id} 应属于 {module.module_id}",
                )

    def test_exercise_fields_parsed(self):
        """练习行 '标题 | 类型 | 分钟' 被正确拆解。"""
        course = parse_syllabus(SAMPLE_MD)
        lesson = course.find_lesson("M1-L1")
        self.assertIsNotNone(lesson)
        self.assertEqual(len(lesson.exercises), 2)
        self.assertEqual(lesson.exercises[0].ex_type, "discussion")
        self.assertEqual(lesson.exercises[0].minutes, 25)

    def test_error_on_lesson_before_module(self):
        """lesson 写在 module 之前必须报错。"""
        bad = "# 课\n\n### lesson M1-L1 | 标题\n- summary: x\n"
        with self.assertRaises(ValueError):
            parse_markdown_syllabus(bad)

    def test_error_on_unknown_lesson_field(self):
        """课时下出现未知字段必须报错（防止拼写错误被静默吞掉）。"""
        bad = (
            "# 课\ncourse_id: X\nweeks: 1\n\n"
            "## module M1 | 模块 | W1\n\n"
            "### lesson M1-L1 | 课时\n- foo: bar\n"
        )
        with self.assertRaises(ValueError):
            parse_markdown_syllabus(bad)

    def test_error_on_missing_title(self):
        """缺少一级标题必须报错。"""
        with self.assertRaises(ValueError):
            parse_markdown_syllabus("course_id: X\nweeks: 1\n")


class TestJsonParser(unittest.TestCase):
    """JSON 大纲解析测试。"""

    def test_parse_sample_json(self):
        course = parse_syllabus(SAMPLE_JSON)
        self.assertEqual(course.course_id, "CS-DEMO01")
        self.assertEqual(len(course.all_lessons()), 2)

    def test_bad_json_raises(self):
        with self.assertRaises(ValueError):
            parse_json_syllabus("{不是合法 JSON")

    def test_unsupported_extension(self):
        """不支持的文件扩展名必须报错。"""
        p = DEMO_ROOT / "samples" / "_tmp_test.txt"
        p.write_text("hello", encoding="utf-8")
        try:
            with self.assertRaises(ValueError):
                parse_syllabus(p)
        finally:
            p.unlink()


if __name__ == "__main__":
    unittest.main()
