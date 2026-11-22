# -*- coding: utf-8 -*-
"""
delivery_builder.py —— 第 4 级：代理 → 交付站点（Agent → Delivery）

把课程内容框架渲染成一个纯静态 HTML 课程站点：
  output/site/
    ├── index.html            课程首页（模块导航）
    ├── modules/M1.html       模块页（课时导航）
    ├── lessons/M1-L1.html    课时页（目标/流程/讲义/练习/作业）
    └── assets/style.css      样式

为什么是静态站点？
  - 零运维：任何静态服务器（甚至 file:// 直接打开）都能访问
  - 可验证：验收人打开 HTML 就能看到交付物（C8 要求"别人能验证、能使用"）
  - 与解耦：站点只消费 ContentFramework，与生成方式（模板/LLM）无关

呈现结构借鉴 Open edX 的导航思路（左侧层级：模块 → 课时），
但刻意做了轻量化：不需要数据库、不需要账号系统。
"""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any, Dict, List


def build_site(course: Dict[str, Any], framework: Dict[str, Any], out_dir: str | Path) -> Dict[str, Any]:
    """渲染静态课程站点。

    参数：
        course    : Course.to_dict()（课程元信息）
        framework : content_generator.generate_content() 的输出
        out_dir   : 输出根目录（会在其下创建 site/）
    返回：
        {"site_dir": ..., "pages": N}
    """
    site_dir = Path(out_dir) / "site"
    assets = site_dir / "assets"
    modules_dir = site_dir / "modules"
    lessons_dir = site_dir / "lessons"
    for d in (assets, modules_dir, lessons_dir):
        d.mkdir(parents=True, exist_ok=True)

    # 按 lesson_id 索引教学设计，供课时页查询
    designs = {d["lesson_id"]: d for d in framework.get("lessons", [])}

    # ---- 样式表 ----
    (assets / "style.css").write_text(_STYLE_CSS, encoding="utf-8")

    # ---- 首页 ----
    (site_dir / "index.html").write_text(_render_index(course), encoding="utf-8")

    # ---- 模块页 + 课时页 ----
    page_count = 1  # 已写 index.html
    for module in course.get("modules", []):
        (modules_dir / f"{module['module_id']}.html").write_text(
            _render_module(course, module), encoding="utf-8"
        )
        page_count += 1
        for lesson in module.get("lessons", []):
            design = designs.get(lesson["lesson_id"], {})
            (lessons_dir / f"{lesson['lesson_id']}.html").write_text(
                _render_lesson(course, module, lesson, design), encoding="utf-8"
            )
            page_count += 1

    return {"site_dir": str(site_dir), "pages": page_count}


# ---------------------------------------------------------------------------
# 页面渲染（全部用标准库字符串模板 + html.escape 防注入）
# ---------------------------------------------------------------------------
def _render_index(course: Dict[str, Any]) -> str:
    """课程首页。"""
    e = html.escape
    cards = []
    for module in course.get("modules", []):
        lesson_links = "".join(
            f'<li><a href="lessons/{e(l["lesson_id"])}.html">{e(l["lesson_id"])} {e(l["title"])}</a></li>'
            for l in module.get("lessons", [])
        )
        cards.append(f"""
        <section class="card">
          <h2><a href="modules/{e(module['module_id'])}.html">{e(module['module_id'])} · {e(module['title'])}</a>
              <span class="tag">{e(module.get('week_range', ''))}</span></h2>
          <ul>{lesson_links}</ul>
        </section>""")
    objectives = "".join(f"<li>{e(o)}</li>" for o in course.get("objectives", []))
    return _html_page(
        title=course.get("title", "课程站点"),
        body=f"""
        <header>
          <h1>{e(course.get('title', ''))}</h1>
          <p class="meta">课程编号：{e(course.get('course_id', ''))} ｜ 讲师：{e(course.get('instructor', ''))}
             ｜ 周数：{e(str(course.get('weeks', '')))} ｜ 标签：{e(', '.join(course.get('tags', [])))}</p>
          <p>{e(course.get('description', ''))}</p>
        </header>
        <section class="card">
          <h2>课程目标</h2>
          <ul>{objectives}</ul>
        </section>
        {''.join(cards)}
        <footer><p>由课程生产流水线（course-pipeline）自动生成 · 交付站点</p></footer>
        """,
        css_href="assets/style.css",
    )


def _render_module(course: Dict[str, Any], module: Dict[str, Any]) -> str:
    """模块页。"""
    e = html.escape
    objectives = "".join(f"<li>{e(o)}</li>" for o in module.get("objectives", []))
    rows = "".join(
        f"""<tr><td>{e(l['lesson_id'])}</td><td><a href="../lessons/{e(l['lesson_id'])}.html">{e(l['title'])}</a></td>
            <td>{e(l.get('summary', ''))}</td></tr>"""
        for l in module.get("lessons", [])
    )
    return _html_page(
        title=f"{module.get('module_id')} · {module.get('title')}",
        body=f"""
        <nav><a href="../index.html">← 返回课程首页</a></nav>
        <header>
          <h1>{e(module.get('module_id'))} · {e(module.get('title'))}</h1>
          <p class="meta">覆盖周次：{e(module.get('week_range', ''))}</p>
        </header>
        <section class="card">
          <h2>模块目标</h2>
          <ul>{objectives or '<li>（见课程大纲）</li>'}</ul>
        </section>
        <section class="card">
          <h2>课时列表</h2>
          <table>
            <tr><th>编号</th><th>课时</th><th>简介</th></tr>
            {rows}
          </table>
        </section>
        """,
        css_href="../assets/style.css",
    )


def _render_lesson(course: Dict[str, Any], module: Dict[str, Any], lesson: Dict[str, Any], design: Dict[str, Any]) -> str:
    """课时页：教学设计的最终呈现。"""
    e = html.escape
    topics = "".join(f"<li>{e(t)}</li>" for t in design.get("topics", lesson.get("topics", [])))
    flow = "".join(
        f"<li><strong>{e(s['stage'])}</strong>（约 {s['minutes']} 分钟）</li>"
        for s in design.get("teaching_flow", [])
    )
    readings = "".join(f"<li>{e(r)}</li>" for r in design.get("readings", []))
    exercises = "".join(
        f"<li><strong>{e(x['title'])}</strong>（{e(x['ex_type'])}，约 {x['minutes']} 分钟）：{e(x.get('description', ''))}</li>"
        for x in design.get("exercises", [])
    )
    assignments = "".join(
        f"<li><strong>{e(a['title'])}</strong>：{e(a.get('description', ''))}</li>"
        for a in design.get("assignments", [])
    )
    rubric = "".join(
        f"<tr><td>{e(r['dimension'])}</td><td>{r['weight']:.0%}</td><td>{e(r['criteria'])}</td></tr>"
        for r in design.get("rubric", [])
    )
    return _html_page(
        title=f"{lesson.get('lesson_id')} {lesson.get('title')}",
        body=f"""
        <nav><a href="../index.html">首页</a> /
             <a href="../modules/{e(module.get('module_id'))}.html">{e(module.get('module_id'))} {e(module.get('title'))}</a></nav>
        <header>
          <h1>{e(lesson.get('lesson_id'))} · {e(lesson.get('title'))}</h1>
          <p class="meta">{e(lesson.get('summary', ''))}</p>
        </header>
        <section class="card"><h2>学习目标</h2><ul>{topics}</ul></section>
        <section class="card"><h2>教学流程</h2><ol>{flow}</ol></section>
        <section class="card"><h2>阅读材料</h2><ul>{readings or '<li>（无）</li>'}</ul></section>
        <section class="card"><h2>课堂练习</h2><ul>{exercises or '<li>（无）</li>'}</ul></section>
        <section class="card"><h2>课后作业</h2><ul>{assignments or '<li>（无）</li>'}</ul></section>
        <section class="card">
          <h2>评分量规</h2>
          <table>
            <tr><th>维度</th><th>权重</th><th>标准</th></tr>
            {rubric}
          </table>
        </section>
        <section class="card">
          <h2>ILT 学习代理</h2>
          <p>本课时已封装为学习代理 <code>ilt-{e(lesson.get('lesson_id', '').lower())}</code>，
             详见交付包 <code>agents/</code> 目录下的 SKILL.md。</p>
        </section>
        """,
        css_href="../assets/style.css",
    )


def _html_page(title: str, body: str, css_href: str = "assets/style.css") -> str:
    """统一的 HTML 页面骨架。

    css_href：样式表的相对路径——
      站点根目录页面(index.html)传 "assets/style.css"；
      modules/ 与 lessons/ 子目录页面传 "../assets/style.css"。
    """
    e = html.escape
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(title)}</title>
  <link rel="stylesheet" href="{e(css_href)}">
</head>
<body>
{body}
</body>
</html>
"""


# ---------------------------------------------------------------------------
# 站点样式（轻量、可读优先）
# ---------------------------------------------------------------------------
_STYLE_CSS = """
* { box-sizing: border-box; }
body {
  font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
  margin: 0 auto; max-width: 920px; padding: 24px;
  color: #222; background: #fafafa; line-height: 1.7;
}
header { border-bottom: 2px solid #2c5f8a; margin-bottom: 20px; padding-bottom: 12px; }
h1 { color: #1d4468; margin-bottom: 4px; }
h2 { color: #2c5f8a; }
.meta { color: #666; font-size: 0.92em; }
.card {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 8px;
  padding: 16px 20px; margin: 16px 0;
}
.tag {
  background: #e8f1f8; color: #2c5f8a; border-radius: 4px;
  font-size: 0.8em; padding: 2px 8px; margin-left: 8px;
}
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #dde3ea; padding: 8px 10px; text-align: left; }
th { background: #eef3f7; }
a { color: #2c5f8a; text-decoration: none; }
a:hover { text-decoration: underline; }
code { background: #eef3f7; padding: 2px 6px; border-radius: 4px; }
footer { margin-top: 32px; color: #999; font-size: 0.85em; text-align: center; }
"""
