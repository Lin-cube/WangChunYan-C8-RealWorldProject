# -*- coding: utf-8 -*-
"""
ilt_agent_builder.py —— 第 3 级：课程内容 → ILT 学习代理（Content → Agent）

ILT = Interactive Learning Task（交互式学习任务）。
每个课时被封装成一个"学习代理包"，可被 Claude Code / OpenClaw / 任何支持
SKILL.md 规范的 Agent 运行时识别并调用。

每个代理包目录结构（借鉴 Anthropic Agent Skills 的渐进式披露设计）：
  agents/ilt-m1-l1/
    ├── SKILL.md           技能说明（YAML frontmatter：name + description）
    ├── agent_config.json  结构化配置（输入/输出 schema、KSTAR 认知循环、工作流）
    └── rubric.json        评分量规（来自上一级 content_generator）

命名规范（直接对齐 Agent Skills 规范，这是"拿来"的部分）：
  - name：小写字母、数字、连字符，≤64 字符 → 我们用 ilt-<lesson_id 小写>
  - description：非空，≤1024 字符，必须同时说明"做什么"和"何时使用"
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

# Agent Skills 规范约束（构建时自检，保证产物真的能被 Agent 运行时消费）
_NAME_RE = re.compile(r"^[a-z0-9-]+$")
_NAME_MAX = 64
_DESC_MAX = 1024


def build_agents(course_id: str, framework: Dict[str, Any], out_dir: str | Path) -> Dict[str, Any]:
    """根据内容框架为每个课时生成 ILT 学习代理包。

    参数：
        course_id : 课程编号（写入注册表）
        framework : content_generator.generate_content() 的输出
        out_dir   : 输出根目录（会在其下创建 agents/）
    返回：
        {"agents_dir": ..., "count": N, "index": [...]}
    """
    agents_dir = Path(out_dir) / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)

    index: List[Dict[str, Any]] = []
    for design in framework.get("lessons", []):
        lesson_id = design["lesson_id"]
        agent_name = f"ilt-{lesson_id.lower()}"  # 例：M1-L1 → ilt-m1-l1
        agent_dir = agents_dir / agent_name
        agent_dir.mkdir(parents=True, exist_ok=True)

        # 1) SKILL.md（Agent 运行时读的第一层：元数据 + 指令）
        skill_md = _render_skill_md(design, agent_name)
        (agent_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")

        # 2) agent_config.json（第二层：结构化配置）
        config = _build_agent_config(design, agent_name)
        (agent_dir / "agent_config.json").write_text(
            json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        # 3) rubric.json（评分量规模块化导出，可被 Agent 的反馈环节复用）
        (agent_dir / "rubric.json").write_text(
            json.dumps(design.get("rubric", []), ensure_ascii=False, indent=2), encoding="utf-8"
        )

        index.append({
            "agent_name": agent_name,
            "lesson_id": lesson_id,
            "title": design["title"],
            "path": str(agent_dir.as_posix()),
        })

    # 4) 注册表：Agent 运行时 / 教师端可以一次发现全部代理
    registry = {
        "course_id": course_id,
        "agent_count": len(index),
        "agents": index,
    }
    (agents_dir / "index.json").write_text(
        json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return {"agents_dir": str(agents_dir), "count": len(index), "index": index}


# ---------------------------------------------------------------------------
# SKILL.md 渲染（YAML frontmatter + Markdown 正文）
# ---------------------------------------------------------------------------
def _render_skill_md(design: Dict[str, Any], agent_name: str) -> str:
    """生成符合 Agent Skills 规范的 SKILL.md 文本。"""
    title = design["title"]
    summary = design.get("summary") or f"围绕课时 {design['lesson_id']} 的交互式学习任务"
    topics = design.get("topics", [])

    # description 必须"功能 + 触发时机"双要素，且 ≤1024 字符
    description = (
        f"交互式学习任务（ILT）代理：带领学生学习《{title}》。"
        f"内容涵盖：{'、'.join(topics) if topics else '见课时大纲'}。"
        f"当学生进入课时 {design['lesson_id']} 学习、提问、做练习或需要学习反馈时使用本代理。"
    )
    _check_skill_name(agent_name)
    _check_skill_description(description)

    # 注意：frontmatter 的 name/description 是 Agent 判断"何时调用"的唯一依据
    lines = [
        "---",
        f"name: {agent_name}",
        f"description: {description}",
        "---",
        "",
        f"# ILT 学习代理：{title}",
        "",
        f"> 课时编号：{design['lesson_id']} ｜ 模块：{design.get('module_id', '')}",
        "",
        "## Instructions（代理执行指令）",
        "",
        "按以下五个步骤带领学生完成本课时（对应教学流程）：",
        "",
    ]
    for i, step in enumerate(design.get("teaching_flow", []), start=1):
        lines.append(f"{i}. **{step['stage']}**（约 {step['minutes']} 分钟）")
    lines += [
        "",
        "### 讲解要点",
        "",
    ]
    lines += [f"- {t}" for t in topics] or ["- （见大纲）"]
    lines += [
        "",
        "### 练习与反馈",
        "",
    ]
    for ex in design.get("exercises", []):
        lines.append(f"- **{ex['title']}**（{ex['ex_type']}，约 {ex['minutes']} 分钟）：{ex.get('description', '按课堂要求完成')}")
    if not design.get("exercises"):
        lines.append("- （本课时暂无课堂练习，聚焦讲解与问答）")
    lines += [
        "",
        "### 评分量规（反馈时对照）",
        "",
    ]
    for r in design.get("rubric", []):
        lines.append(f"- **{r['dimension']}**（权重 {r['weight']:.0%}）：{r['criteria']}")
    lines += [
        "",
        "## Examples（调用示例）",
        "",
        f"- 学生：\"我想学 {design['lesson_id']}，帮我讲一下\" → 按教学流程逐步讲解并布置练习。",
        f"- 学生：\"{topics[0] if topics else '这个知识点'}到底怎么理解？\" → 用类比+示例讲解，然后给 1 道检查题。",
        f"- 学生：\"帮我看看这个练习做得怎么样\" → 对照 rubric.json 的四维度给反馈。",
        "",
    ]
    return "\n".join(lines)


def _build_agent_config(design: Dict[str, Any], agent_name: str) -> Dict[str, Any]:
    """生成结构化代理配置：输入/输出 schema + KSTAR 认知循环 + 工作流。"""
    topics = design.get("topics", [])
    return {
        "agent_name": agent_name,
        "lesson_id": design["lesson_id"],
        "title": design["title"],
        # 输入输出契约：任何 Agent 运行时按此契约调用
        "input_schema": {
            "type": "object",
            "properties": {
                "student_question": {"type": "string", "description": "学生的提问或任务描述"},
                "context": {"type": "string", "description": "已有学习上下文（可选）"},
            },
            "required": ["student_question"],
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "explanation": {"type": "string", "description": "针对性讲解"},
                "practice": {"type": "string", "description": "给出的练习题"},
                "feedback": {"type": "string", "description": "对照量规的反馈"},
            },
        },
        # KSTAR 认知循环编码（课程方法论：Knowledge→Situation→Task→Action→Result）
        "kstar_loop": {
            "K": f"课程上下文：{design.get('summary', '')}；知识点：{'、'.join(topics)}",
            "S": "学生在本课时学习中提出的实时情境（提问/练习/困惑）",
            "T": "诊断学习状态 → 讲解知识点 → 布置练习 → 对照量规反馈",
            "A": "代理按 teaching_flow 逐步执行讲解/演示/练习/反馈",
            "R": "输出讲解与反馈，更新学生对本课时的掌握度记录",
        },
        "workflow": [step["stage"] for step in design.get("teaching_flow", [])],
        "rubric_ref": "rubric.json",
    }


# ---------------------------------------------------------------------------
# 规范自检（保证产物真正符合 Agent Skills 命名规范）
# ---------------------------------------------------------------------------
def _check_skill_name(name: str) -> None:
    if len(name) > _NAME_MAX:
        raise ValueError(f"SKILL name 超长（{_NAME_MAX} 字符限制）：{name}")
    if not _NAME_RE.match(name):
        raise ValueError(f"SKILL name 只能包含小写字母/数字/连字符：{name}")


def _check_skill_description(description: str) -> None:
    if not description.strip():
        raise ValueError("SKILL description 不能为空")
    if len(description) > _DESC_MAX:
        raise ValueError(f"SKILL description 超长（{_DESC_MAX} 字符限制）：{len(description)} 字符")
