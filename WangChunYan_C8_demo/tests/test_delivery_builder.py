# -*- coding: utf-8 -*-
"""delivery_builder 单元测试：静态站点产物完整性。"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from course_pipeline.content_generator import generate_content  # noqa: E402
from course_pipeline.delivery_builder import build_site  # noqa: E402
from course_pipeline.syllabus_parser import parse_syllabus  # noqa: E402
from course_pipeline.models import course_to_dict  # noqa: E402

DEMO_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_MD = DEMO_ROOT / "samples" / "sample_syllabus.md"


class TestDeliveryBuilder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.course = parse_syllabus(SAMPLE_MD)
        cls.framework = generate_content(cls.course)
        cls.tmp = tempfile.TemporaryDirectory()
        cls.result = build_site(course_to_dict(cls.course), cls.framework, cls.tmp.name)
        cls.site_dir = Path(cls.result["site_dir"])

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_page_count(self):
        """页面数 = 1 首页 + 模块页 + 课时页。"""
        expected = 1 + len(self.course.modules) + len(self.course.all_lessons())
        self.assertEqual(self.result["pages"], expected)

    def test_index_contains_course_title(self):
        """首页必须包含课程名称。"""
        index = (self.site_dir / "index.html").read_text(encoding="utf-8")
        self.assertIn(self.course.title, index)

    def test_lesson_pages_exist(self):
        """每个课时都有对应页面，且包含课时标题。"""
        for lesson in self.course.all_lessons():
            page = self.site_dir / "lessons" / f"{lesson.lesson_id}.html"
            self.assertTrue(page.exists(), f"缺少课时页 {page}")
            self.assertIn(lesson.title, page.read_text(encoding="utf-8"))

    def test_css_stylesheet_exists(self):
        """样式表必须生成。"""
        self.assertTrue((self.site_dir / "assets" / "style.css").exists())

    def test_index_links_resolve(self):
        """首页里的模块链接必须指向真实存在的文件。"""
        import re
        index = (self.site_dir / "index.html").read_text(encoding="utf-8")
        for m in re.finditer(r'href="modules/([^"]+)"', index):
            self.assertTrue((self.site_dir / "modules" / m.group(1)).exists(), m.group(1))
        for m in re.finditer(r'href="lessons/([^"]+)"', index):
            self.assertTrue((self.site_dir / "lessons" / m.group(1)).exists(), m.group(1))


if __name__ == "__main__":
    unittest.main()
