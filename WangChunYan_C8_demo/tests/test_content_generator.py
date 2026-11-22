# -*- coding: utf-8 -*-
"""content_generator 单元测试：教学设计产物的完整性与一致性。"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from course_pipeline.content_generator import generate_content  # noqa: E402
from course_pipeline.syllabus_parser import parse_syllabus  # noqa: E402

DEMO_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_MD = DEMO_ROOT / "samples" / "sample_syllabus.md"


class TestContentGenerator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """整个测试类只解析、生成一次（省时间）。"""
        cls.course = parse_syllabus(SAMPLE_MD)
        cls.framework = generate_content(cls.course)

    def test_every_lesson_has_design(self):
        """每个课时都必须有一份教学设计。"""
        design_ids = {d["lesson_id"] for d in self.framework["lessons"]}
        expected = {l.lesson_id for l in self.course.all_lessons()}
        self.assertEqual(design_ids, expected)

    def test_design_contains_required_sections(self):
        """教学设计必须包含：流程/幻灯片/讲义/量规。"""
        for design in self.framework["lessons"]:
            self.assertIn("teaching_flow", design)
            self.assertIn("slide_outline", design)
            self.assertIn("content_md", design)
            self.assertIn("rubric", design)
            self.assertTrue(design["content_md"].strip())
            self.assertGreaterEqual(len(design["slide_outline"]), 3)

    def test_practice_stage_matches_exercise_minutes(self):
        """教学流程中'练习'环节时长 = 习题时长之和（不足 10 分钟补到 10 分钟）。"""
        for design in self.framework["lessons"]:
            flow = {s["stage"]: s["minutes"] for s in design["teaching_flow"]}
            expected = max(sum(e["minutes"] for e in design["exercises"]), 10)
            self.assertEqual(flow["练习"], expected)

    def test_rubric_weights_sum_to_one(self):
        """评分量规四个维度权重之和必须为 1.0。"""
        for design in self.framework["lessons"]:
            total = sum(r["weight"] for r in design["rubric"])
            self.assertAlmostEqual(total, 1.0, places=6)

    def test_faq_seed_covers_all_modules(self):
        """每个模块至少生成 3 条种子 FAQ。"""
        module_ids = {m.module_id for m in self.course.modules}
        faq_modules = {}
        for faq in self.framework["faq_seed"]:
            faq_modules.setdefault(faq["module_id"], 0)
            faq_modules[faq["module_id"]] += 1
        self.assertEqual(set(faq_modules), module_ids)
        for mid, count in faq_modules.items():
            self.assertGreaterEqual(count, 3, f"模块 {mid} 的 FAQ 少于 3 条")


if __name__ == "__main__":
    unittest.main()
