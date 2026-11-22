# -*- coding: utf-8 -*-
"""portfolio_archiver 单元测试：作品集归档 + xAPI 风格学习记录。"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from course_pipeline.models import course_to_dict  # noqa: E402
from course_pipeline.portfolio_archiver import archive_submissions  # noqa: E402
from course_pipeline.syllabus_parser import parse_syllabus  # noqa: E402

DEMO_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_MD = DEMO_ROOT / "samples" / "sample_syllabus.md"
SAMPLE_SUBMISSIONS = DEMO_ROOT / "samples" / "sample_submissions.json"


class TestPortfolioArchiver(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.course = parse_syllabus(SAMPLE_MD)
        cls.tmp = tempfile.TemporaryDirectory()
        cls.result = archive_submissions(
            SAMPLE_SUBMISSIONS, course_to_dict(cls.course), cls.tmp.name
        )
        cls.portfolio_dir = Path(cls.result["portfolio_dir"])

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_statement_count(self):
        """学习记录条数 = 提交条数。"""
        data = json.loads(SAMPLE_SUBMISSIONS.read_text(encoding="utf-8"))
        self.assertEqual(self.result["statement_count"], len(data["submissions"]))

    def test_records_jsonl_xapi_shape(self):
        """每条记录必须是 actor-verb-object 三元组结构（借鉴 xAPI）。"""
        lines = (self.portfolio_dir / "records.jsonl").read_text(encoding="utf-8").strip().splitlines()
        for line in lines:
            st = json.loads(line)
            self.assertIn("actor", st)
            self.assertIn("verb", st)
            self.assertIn("object", st)
            self.assertIn("timestamp", st)

    def test_student_manifest(self):
        """每个学生目录必须有 manifest.json 与 index.html。"""
        student_dirs = [d for d in (self.portfolio_dir / "students").iterdir() if d.is_dir()]
        self.assertGreaterEqual(len(student_dirs), 2)
        for d in student_dirs:
            self.assertTrue((d / "manifest.json").exists(), f"{d} 缺少 manifest.json")
            self.assertTrue((d / "index.html").exists(), f"{d} 缺少 index.html")

    def test_class_index(self):
        """班级总览页必须生成并包含学生姓名。"""
        index = (self.portfolio_dir / "index.html").read_text(encoding="utf-8")
        self.assertIn("WangChunYan", index)

    def test_invalid_lesson_id_rejected(self):
        """引用不存在的课时必须报错（数据完整性校验）。"""
        bad = {
            "submissions": [
                {"student_id": "S1", "student_name": "X", "lesson_id": "M9-L9",
                 "artifact": "a.md", "artifact_type": "report", "submitted_at": "2026-01-01T00:00:00+08:00"}
            ]
        }
        bad_file = Path(self.tmp.name) / "bad_submissions.json"
        bad_file.write_text(json.dumps(bad, ensure_ascii=False), encoding="utf-8")
        with self.assertRaises(ValueError):
            archive_submissions(bad_file, course_to_dict(self.course), self.tmp.name)


if __name__ == "__main__":
    unittest.main()
