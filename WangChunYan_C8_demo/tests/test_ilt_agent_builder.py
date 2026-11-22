# -*- coding: utf-8 -*-
"""ilt_agent_builder 单元测试：SKILL.md 规范符合性。"""
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from course_pipeline.content_generator import generate_content  # noqa: E402
from course_pipeline.ilt_agent_builder import build_agents  # noqa: E402
from course_pipeline.syllabus_parser import parse_syllabus  # noqa: E402

DEMO_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_MD = DEMO_ROOT / "samples" / "sample_syllabus.md"


class TestIltAgentBuilder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.course = parse_syllabus(SAMPLE_MD)
        cls.framework = generate_content(cls.course)
        cls.tmp = tempfile.TemporaryDirectory()
        cls.result = build_agents(cls.course.course_id, cls.framework, cls.tmp.name)
        cls.agents_dir = Path(cls.result["agents_dir"])

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_agent_count_matches_lessons(self):
        """每个课时一个代理包。"""
        self.assertEqual(self.result["count"], len(self.course.all_lessons()))

    def test_skill_md_frontmatter(self):
        """每个 SKILL.md 必须有合法的 YAML frontmatter（name + description）。"""
        for agent in self.result["index"]:
            skill_path = Path(agent["path"]) / "SKILL.md"
            text = skill_path.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\n"), f"{skill_path} 缺少 frontmatter")
            # 提取 frontmatter 块
            parts = text.split("---")
            frontmatter = parts[1] if len(parts) > 2 else ""
            name_m = re.search(r"^name:\s*(.+)$", frontmatter, re.MULTILINE)
            desc_m = re.search(r"^description:\s*(.+)$", frontmatter, re.MULTILINE)
            self.assertIsNotNone(name_m, f"{skill_path} 缺少 name")
            self.assertIsNotNone(desc_m, f"{skill_path} 缺少 description")

            name = name_m.group(1).strip()
            desc = desc_m.group(1).strip()
            # Agent Skills 命名规范：小写字母/数字/连字符，≤64 字符
            self.assertRegex(name, r"^[a-z0-9-]+$")
            self.assertLessEqual(len(name), 64)
            self.assertLessEqual(len(desc), 1024)

    def test_agent_config_contract(self):
        """代理配置必须包含输入/输出 schema 与 KSTAR 循环。"""
        for agent in self.result["index"]:
            cfg = json.loads((Path(agent["path"]) / "agent_config.json").read_text(encoding="utf-8"))
            self.assertIn("input_schema", cfg)
            self.assertIn("output_schema", cfg)
            self.assertIn("kstar_loop", cfg)
            for key in ("K", "S", "T", "A", "R"):
                self.assertIn(key, cfg["kstar_loop"])

    def test_registry_index(self):
        """注册表 index.json 必须登记全部代理。"""
        registry = json.loads((self.agents_dir / "index.json").read_text(encoding="utf-8"))
        self.assertEqual(registry["agent_count"], self.result["count"])
        self.assertEqual(len(registry["agents"]), self.result["count"])


if __name__ == "__main__":
    unittest.main()
