# -*- coding: utf-8 -*-
"""
portfolio_archiver.py —— 第 5 级：交付 → 作品集（Delivery → Portfolio）

收集学生在各课时的产出物（笔记、代码、报告……），自动归档为个人作品集 + 班级总览。

产物结构：
  output/portfolio/
    ├── index.html                  班级作品集总览（谁交了什么、交了多少）
    ├── records.jsonl               学习记录流（借鉴 xAPI 的 actor-verb-object 语句结构）
    └── students/
        └── <student_id>/
            ├── manifest.json       该学生的产出清单（机器可读）
            └── index.html          该学生的个人作品集页（人可读）

关于 xAPI 借鉴（详见《拿来说明》）：
  xAPI（IEEE 9274.1.1-2023）用 "actor-verb-object" 三元组记录学习行为，
  例如 "王春燕 completed M1-L1 练习"。我们把每次提交记录为一条 statement，
  写入 records.jsonl——这样作品集不只是"文件堆"，而是可查询的学习证据链。
"""

from __future__ import annotations

import html
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List


def archive_submissions(
    submissions_path: str | Path,
    course: Dict[str, Any],
    out_dir: str | Path,
) -> Dict[str, Any]:
    """把学生提交记录归档为作品集。

    参数：
        submissions_path : 提交记录 JSON 文件（{"submissions": [...]}）
        course           : Course.to_dict()，用于校验 lesson_id 合法性
        out_dir          : 输出根目录（会在其下创建 portfolio/）
    返回：
        {"portfolio_dir": ..., "statement_count": N, "student_count": M}
    """
    data = json.loads(Path(submissions_path).read_text(encoding="utf-8"))
    submissions = data.get("submissions", [])
    if not submissions:
        raise ValueError("提交记录为空：submissions 数组至少要有一条记录")

    # 建立课时索引，用于校验每条提交引用的 lesson_id 是否存在
    valid_lessons = set()
    for module in course.get("modules", []):
        for lesson in module.get("lessons", []):
            valid_lessons.add(lesson["lesson_id"])

    portfolio_dir = Path(out_dir) / "portfolio"
    students_dir = portfolio_dir / "students"
    students_dir.mkdir(parents=True, exist_ok=True)

    statements: List[Dict[str, Any]] = []
    by_student: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for i, sub in enumerate(submissions):
        sid = str(sub.get("student_id", "")).strip()
        lesson_id = str(sub.get("lesson_id", "")).strip()
        if not sid:
            raise ValueError(f"第 {i + 1} 条提交缺少 student_id")
        if lesson_id not in valid_lessons:
            raise ValueError(f"第 {i + 1} 条提交引用了不存在的课时：{lesson_id}")

        record = {
            "student_id": sid,
            "student_name": sub.get("student_name", sid),
            "lesson_id": lesson_id,
            "artifact": sub.get("artifact", ""),
            "artifact_type": sub.get("artifact_type", "document"),
            "submitted_at": sub.get("submitted_at", ""),
            "note": sub.get("note", ""),
        }
        by_student[sid].append(record)

        # xAPI 风格学习语句：actor + verb + object + result + context
        statements.append({
            "actor": {"id": sid, "name": record["student_name"]},
            "verb": {"id": "http://adlnet.gov/expapi/verbs/submitted", "display": "submitted"},
            "object": {"id": lesson_id, "definition": {"type": "lesson"}},
            "timestamp": record["submitted_at"],
            "result": {
                "artifact": record["artifact"],
                "artifact_type": record["artifact_type"],
                "note": record["note"],
            },
            "context": {"course": course.get("course_id", "")},
        })

    # ---- 1) 学习记录流 records.jsonl（每行一条 statement） ----
    records_file = portfolio_dir / "records.jsonl"
    with records_file.open("w", encoding="utf-8") as f:
        for st in statements:
            f.write(json.dumps(st, ensure_ascii=False) + "\n")

    # ---- 2) 每个学生的作品集 ----
    for sid, items in by_student.items():
        sdir = students_dir / sid
        sdir.mkdir(parents=True, exist_ok=True)
        manifest = {
            "student_id": sid,
            "student_name": items[0]["student_name"],
            "course_id": course.get("course_id", ""),
            "submission_count": len(items),
            "items": items,
        }
        (sdir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (sdir / "index.html").write_text(_render_student_page(course, manifest), encoding="utf-8")

    # ---- 3) 班级总览 ----
    (portfolio_dir / "index.html").write_text(
        _render_class_page(course, by_student), encoding="utf-8"
    )

    return {
        "portfolio_dir": str(portfolio_dir),
        "statement_count": len(statements),
        "student_count": len(by_student),
    }


# ---------------------------------------------------------------------------
# HTML 渲染
# ---------------------------------------------------------------------------
# 作品集页面自带样式（自包含：单独拷走 portfolio/ 目录也能正常打开）
_PORTFOLIO_CSS = """
* { box-sizing: border-box; }
body { font-family: "Segoe UI", "Microsoft YaHei", sans-serif; margin: 0 auto;
       max-width: 920px; padding: 24px; color: #222; background: #fafafa; line-height: 1.7; }
header { border-bottom: 2px solid #2c5f8a; margin-bottom: 20px; padding-bottom: 12px; }
h1 { color: #1d4468; } h2 { color: #2c5f8a; }
.meta { color: #666; font-size: 0.92em; }
.card { background: #fff; border: 1px solid #e2e8f0; border-radius: 8px;
        padding: 16px 20px; margin: 16px 0; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #dde3ea; padding: 8px 10px; text-align: left; }
th { background: #eef3f7; }
a { color: #2c5f8a; text-decoration: none; }
a:hover { text-decoration: underline; }
"""


def _render_student_page(course: Dict[str, Any], manifest: Dict[str, Any]) -> str:
    """个人作品集页面。"""
    e = html.escape
    rows = "".join(
        f"""<tr>
              <td>{e(it['lesson_id'])}</td>
              <td>{e(it['artifact'])}</td>
              <td>{e(it['artifact_type'])}</td>
              <td>{e(it['submitted_at'])}</td>
              <td>{e(it.get('note', ''))}</td>
            </tr>"""
        for it in manifest.get("items", [])
    )
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>作品集 · {e(manifest.get('student_name', ''))}</title>
  <style>{_PORTFOLIO_CSS}</style>
</head>
<body>
  <nav><a href="../index.html">← 返回班级作品集</a></nav>
  <header>
    <h1>{e(manifest.get('student_name', ''))} 的作品集</h1>
    <p class="meta">学号：{e(manifest.get('student_id', ''))} ｜ 课程：{e(course.get('title', ''))}
       ｜ 提交数：{manifest.get('submission_count', 0)}</p>
  </header>
  <section class="card">
    <h2>产出清单</h2>
    <table>
      <tr><th>课时</th><th>产出物</th><th>类型</th><th>提交时间</th><th>备注</th></tr>
      {rows}
    </table>
  </section>
</body>
</html>
"""


def _render_class_page(course: Dict[str, Any], by_student: Dict[str, List[Dict[str, Any]]]) -> str:
    """班级作品集总览页。"""
    e = html.escape
    rows = ""
    for sid, items in sorted(by_student.items()):
        name = items[0]["student_name"]
        lesson_ids = "、".join(sorted({it["lesson_id"] for it in items}))
        rows += f"""<tr>
            <td><a href="students/{e(sid)}/index.html">{e(name)}</a></td>
            <td>{e(sid)}</td>
            <td>{len(items)}</td>
            <td>{e(lesson_ids)}</td>
          </tr>"""
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>班级作品集 · {e(course.get('title', ''))}</title>
  <style>{_PORTFOLIO_CSS}</style>
</head>
<body>
  <header>
    <h1>{e(course.get('title', ''))} · 班级作品集</h1>
    <p class="meta">共 {len(by_student)} 名学生提交产出物（学习记录见 records.jsonl）</p>
  </header>
  <section class="card">
    <h2>学生总览</h2>
    <table>
      <tr><th>姓名</th><th>学号</th><th>提交数</th><th>覆盖课时</th></tr>
      {rows}
    </table>
  </section>
</body>
</html>
"""
