# -*- coding: utf-8 -*-
"""
pipeline.py —— 课程生产流水线的命令行入口（一键跑通五级）

用法示例：
  # 端到端跑完整条流水线（默认读 samples/sample_syllabus.md）
  python pipeline.py

  # 指定自己的教学大纲
  python pipeline.py --syllabus path/to/my_syllabus.md --out output

  # 只跑某一级（调试用）
  python pipeline.py --stage parse
  python pipeline.py --stage content
  python pipeline.py --stage agents
  python pipeline.py --stage delivery
  python pipeline.py --stage portfolio

流水线阶段与 Project C 工作流的对应关系：
  parse      Syllabus → CourseModel         教学大纲解析
  content    CourseModel → ContentFramework 内容框架生成
  agents     ContentFramework → ILT Agents  学习代理封装
  delivery   ContentFramework → Site        交付站点生成
  portfolio  Submissions → Portfolio        作品集归档
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

# 支持"直接 python pipeline.py"运行：把包目录加入模块搜索路径
sys.path.insert(0, str(Path(__file__).resolve().parent))

from course_pipeline import (  # noqa: E402
    archive_submissions,
    build_agents,
    build_site,
    course_to_dict,
    generate_content,
    parse_syllabus,
)

# 默认样例路径（相对本文件）
DEFAULT_SYLLABUS = Path(__file__).resolve().parent / "samples" / "sample_syllabus.md"
DEFAULT_SUBMISSIONS = Path(__file__).resolve().parent / "samples" / "sample_submissions.json"

ALL_STAGES = ["parse", "content", "agents", "delivery", "portfolio"]


def _expand_stages(stages: List[str]) -> List[str]:
    """展开阶段依赖：后面阶段依赖前面阶段的产物，自动补上前置阶段。

    依赖关系：
      content   依赖 parse
      agents    依赖 parse + content
      delivery  依赖 parse + content
      portfolio 依赖 parse（另需提交记录文件）
    """
    s = set(stages)
    if s & {"content", "agents", "delivery", "portfolio"}:
        s.add("parse")
    if s & {"agents", "delivery"}:
        s.add("content")
    # 按流水线固定顺序返回（保证前置产物先生成）
    return [st for st in ALL_STAGES if st in s]


def run_pipeline(
    syllabus_path: Path,
    out_dir: Path,
    submissions_path: Path | None,
    stages: List[str],
) -> Dict[str, Any]:
    """按选定阶段执行流水线（自动展开依赖），返回执行报告。"""
    out_dir.mkdir(parents=True, exist_ok=True)
    ordered = _expand_stages(stages)
    report: Dict[str, Any] = {"stages": [], "executed": ordered}
    course = None
    framework = None

    # ---- 阶段 1：解析教学大纲 ----
    if "parse" in ordered:
        course = parse_syllabus(syllabus_path)
        model_file = out_dir / "course_model.json"
        model_file.write_text(
            json.dumps(course_to_dict(course), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        report["stages"].append({
            "stage": "parse",
            "output": str(model_file),
            "detail": f"课程《{course.title}》：{len(course.modules)} 个模块 / {len(course.all_lessons())} 个课时",
        })

    # ---- 阶段 2：生成内容框架 ----
    if "content" in ordered:
        assert course is not None, "执行 content 阶段前必须先解析大纲"
        framework = generate_content(course)
        fw_file = out_dir / "content_framework.json"
        fw_file.write_text(
            json.dumps(framework, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        report["stages"].append({
            "stage": "content",
            "output": str(fw_file),
            "detail": f"生成 {len(framework['lessons'])} 份教学设计 + {len(framework['faq_seed'])} 条种子 FAQ",
        })

    # ---- 阶段 3：封装 ILT 学习代理 ----
    if "agents" in ordered:
        assert course is not None and framework is not None, "agents 阶段依赖 parse + content"
        result = build_agents(course.course_id, framework, out_dir)
        report["stages"].append({
            "stage": "agents",
            "output": result["agents_dir"],
            "detail": f"封装 {result['count']} 个 ILT 学习代理（含 SKILL.md）",
        })

    # ---- 阶段 4：生成交付站点 ----
    if "delivery" in ordered:
        assert course is not None and framework is not None, "delivery 阶段依赖 parse + content"
        result = build_site(course_to_dict(course), framework, out_dir)
        report["stages"].append({
            "stage": "delivery",
            "output": result["site_dir"],
            "detail": f"生成 {result['pages']} 个静态页面",
        })

    # ---- 阶段 5：作品集归档 ----
    if "portfolio" in ordered:
        assert course is not None, "portfolio 阶段依赖 parse"
        sub_path = submissions_path or DEFAULT_SUBMISSIONS
        if not sub_path.exists():
            report["stages"].append({
                "stage": "portfolio",
                "output": "",
                "detail": f"跳过：找不到提交记录 {sub_path}",
            })
        else:
            result = archive_submissions(sub_path, course_to_dict(course), out_dir)
            report["stages"].append({
                "stage": "portfolio",
                "output": result["portfolio_dir"],
                "detail": f"归档 {result['statement_count']} 条学习记录 / {result['student_count']} 名学生",
            })

    return report


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="课程生产流水线：Syllabus → Content → Agent → Delivery → Portfolio",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例：python pipeline.py --syllabus samples/sample_syllabus.md --out output",
    )
    parser.add_argument("--syllabus", type=Path, default=DEFAULT_SYLLABUS,
                        help="教学大纲文件路径（.md 或 .json），默认 samples/sample_syllabus.md")
    parser.add_argument("--out", type=Path, default=Path("output"),
                        help="输出目录，默认 ./output")
    parser.add_argument("--submissions", type=Path, default=DEFAULT_SUBMISSIONS,
                        help="学生提交记录 JSON，默认 samples/sample_submissions.json")
    parser.add_argument("--stage", choices=ALL_STAGES + ["all"], default="all",
                        help="只执行指定阶段，默认 all（全流程）")
    args = parser.parse_args(argv)

    stages = ALL_STAGES if args.stage == "all" else [args.stage]

    print("=" * 60)
    print("课程生产流水线 Course Production Pipeline")
    print("=" * 60)
    print(f"大纲文件 : {args.syllabus}")
    print(f"输出目录 : {args.out}")
    print(f"执行阶段 : {' → '.join(stages)}")
    print("-" * 60)

    try:
        report = run_pipeline(args.syllabus, args.out, args.submissions, stages)
    except (ValueError, FileNotFoundError) as exc:
        print(f"[失败] {exc}", file=sys.stderr)
        return 1

    for item in report["stages"]:
        print(f"[OK] {item['stage']:<10} {item['detail']}")
        if item["output"]:
            print(f"     └─ 输出：{item['output']}")
    print("-" * 60)
    print("流水线执行完成。产物可直接打开查看（site/index.html、portfolio/index.html）。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
