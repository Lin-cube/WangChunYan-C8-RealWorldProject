# -*- coding: utf-8 -*-
"""
course_pipeline —— 课程生产流水线（Course Production Pipeline）核心包

流水线五级（对应 Project C 的五条工作流）：
  1. Syllabus  → Content    ：教学大纲 → 课程内容框架   （syllabus_parser + content_generator）
  2. Content   → Agent      ：课程内容 → ILT 学习代理   （ilt_agent_builder）
  3. Agent     → Delivery   ：学习代理 → 交付站点       （delivery_builder）
  4. Delivery  → Portfolio   ：学生产出 → 作品集归档     （portfolio_archiver）
  5. 自动化 + 复用           ：整条流水线一条命令跑通     （pipeline.py）

设计原则（详见 proposal Part 2 拿来主义分析）：
  - Schema-first：每一级之间只通过 models.py 定义的结构化数据交换，
    任何一级都可以被独立替换（例如把模板生成替换成 LLM 生成）而不动其他级。
  - 零第三方依赖：全部使用 Python 标准库，保证任何机器上可直接运行。
  - 可测试：每个阶段都有独立的单元测试，端到端也有集成测试。
"""

from .models import Course, Module, Lesson, Exercise, course_from_dict, course_to_dict
from .syllabus_parser import parse_syllabus, parse_markdown_syllabus, parse_json_syllabus
from .content_generator import generate_content
from .ilt_agent_builder import build_agents
from .delivery_builder import build_site
from .portfolio_archiver import archive_submissions

__all__ = [
    "Course", "Module", "Lesson", "Exercise",
    "course_from_dict", "course_to_dict",
    "parse_syllabus", "parse_markdown_syllabus", "parse_json_syllabus",
    "generate_content",
    "build_agents",
    "build_site",
    "archive_submissions",
]
