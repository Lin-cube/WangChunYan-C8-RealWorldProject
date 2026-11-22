# -*- coding: utf-8 -*-
"""端到端集成测试：一条命令跑通五级流水线，检查全部产物。"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline import main as pipeline_main  # noqa: E402

DEMO_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_MD = DEMO_ROOT / "samples" / "sample_syllabus.md"
SAMPLE_SUBMISSIONS = DEMO_ROOT / "samples" / "sample_submissions.json"


class TestPipelineEndToEnd(unittest.TestCase):
    def test_full_pipeline_run(self):
        """完整流水线：退出码 0，五级产物齐全。"""
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "output"
            code = pipeline_main([
                "--syllabus", str(SAMPLE_MD),
                "--out", str(out),
                "--submissions", str(SAMPLE_SUBMISSIONS),
            ])
            self.assertEqual(code, 0)

            # 1) 解析产物
            self.assertTrue((out / "course_model.json").exists())
            # 2) 内容框架
            self.assertTrue((out / "content_framework.json").exists())
            # 3) 学习代理
            self.assertTrue((out / "agents" / "index.json").exists())
            self.assertTrue((out / "agents" / "ilt-m1-l1" / "SKILL.md").exists())
            # 4) 交付站点
            self.assertTrue((out / "site" / "index.html").exists())
            # 5) 作品集
            self.assertTrue((out / "portfolio" / "index.html").exists())
            self.assertTrue((out / "portfolio" / "records.jsonl").exists())

    def test_single_stage_parse(self):
        """单阶段模式：只跑 parse 时不应生成 content_framework。"""
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "output"
            code = pipeline_main([
                "--syllabus", str(SAMPLE_MD),
                "--out", str(out),
                "--stage", "parse",
            ])
            self.assertEqual(code, 0)
            self.assertTrue((out / "course_model.json").exists())
            self.assertFalse((out / "content_framework.json").exists())

    def test_stage_content_pulls_parse_dependency(self):
        """单阶段模式：跑 content 时自动补上 parse 依赖。"""
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "output"
            code = pipeline_main([
                "--syllabus", str(SAMPLE_MD),
                "--out", str(out),
                "--stage", "content",
            ])
            self.assertEqual(code, 0)
            self.assertTrue((out / "course_model.json").exists())
            self.assertTrue((out / "content_framework.json").exists())

    def test_bad_syllabus_returns_error_code(self):
        """坏大纲必须返回非 0 退出码（而不是崩溃）。"""
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.md"
            bad.write_text("这不是合法大纲", encoding="utf-8")
            code = pipeline_main(["--syllabus", str(bad), "--out", str(Path(tmp) / "o")])
            self.assertEqual(code, 1)

    def test_course_model_json_is_valid(self):
        """course_model.json 可被再次读入并解析为合法结构。"""
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "output"
            pipeline_main(["--syllabus", str(SAMPLE_MD), "--out", str(out), "--stage", "parse"])
            data = json.loads((out / "course_model.json").read_text(encoding="utf-8"))
            self.assertEqual(data["course_id"], "CS-AI201")


if __name__ == "__main__":
    unittest.main()
