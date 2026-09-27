"""🔬 SKILL LAB :: 202-skill registry with searchable assignment UI."""

from __future__ import annotations

import gradio as gr

from ..core import swarm
from ..core.skills import (SKILL_REGISTRY, domain_counts, execute_skill,
                            search_skills, skill_label)
from ..core.state import STATE
from . import visibility as vis

DOMAINS = ["ALL"] + sorted({s["domain"] for s in SKILL_REGISTRY.values()})


# ----------------------------------------------------------------- handlers
def filter_skills(query, domain):
    ids = search_skills(query, domain)
    return gr.CheckboxGroup(choices=[skill_label(s) for s in ids], value=[])


def skill_detail(labels):
    if not labels:
        return "_select a skill to inspect_"
    sid = labels[-1].split("]")[0].lstrip("[")
    s = SKILL_REGISTRY.get(sid)
    if not s:
        return "_unknown skill_"
    return (f"**{s['name']}**  ·  `{s['id']}`  ·  domain `{s['domain']}`\n\n"
            f"{s['desc']}\n\n```python\n# stubbed executor signature\n"
            f"{s['id'].replace('.', '_')}(**params) -> receipt\n```")


def test_skill(labels):
    if not labels:
        return "❌ Select a skill to fire."
    sid = labels[-1].split("]")[0].lstrip("[")
    receipt = execute_skill(sid, demo=True)
    return f"🧪 `{receipt['status']}` :: {receipt['output']} (runtime {receipt['runtime_ms']}ms)"


def assign_skills(agent_name, labels, tier_note):
    aid = swarm.agent_id_by_name(agent_name)
    if not aid:
        return "❌ Select a target agent.", gr.skip()
    if not labels:
        return "❌ Tick at least one skill.", gr.skip()
    agent = STATE.agents[aid]
    added = []
    for lbl in labels:
        sid = lbl.split("]")[0].lstrip("[")
        if sid in SKILL_REGISTRY and sid not in agent["skills"]:
            agent["skills"].append(sid)
            added.append(sid)
    STATE.log("OK", "SKILL-LAB", f"{len(added)} skill(s) fused into {agent['name']}.")
    return (f"⚡ Fused **{len(added)}** skill(s) into `{agent['name']}` "
            f"(total {len(agent['skills'])}).", swarm.ops_table_rows())


def unassign_skill(agent_name, sid_label):
    aid = swarm.agent_id_by_name(agent_name)
    if not aid:
        return "❌ Select a target agent.", gr.skip()
    agent = STATE.agents[aid]
    sid = (sid_label or "").split("]")[0].lstrip("[")
    if sid in agent["skills"]:
        agent["skills"].remove(sid)
        STATE.log("INFO", "SKILL-LAB", f"Skill {sid} stripped from {agent['name']}.")
    return f"🧹 Removed `{sid}` from {agent['name']}.", swarm.ops_table_rows()


def assigned_list(agent_name):
    aid = swarm.agent_id_by_name(agent_name)
    if not aid:
        return gr.Dropdown(choices=[], value=None)
    agent = STATE.agents[aid]
    choices = [skill_label(s) for s in agent["skills"]]
    return gr.Dropdown(choices=choices, value=choices[0] if choices else None)


def registry_stats():
    counts = domain_counts()
    lines = [f"**TOTAL SKILLS :: {len(SKILL_REGISTRY)}**", ""]
    for dom, n in sorted(counts.items()):
        lines.append(f"- {dom}: **{n}**")
    return "\n".join(lines)


# ------------------------------------------------------------------ render
def render(ops_table) -> dict:
    with gr.Row():
        gr.Markdown("## 🔬 SKILL LAB\n"
                    "<span class='cyber-sub'>202 STUBBED CAPABILITIES · FUSE INTO ANY "
                    "COMMANDER OR MINION</span>")
    with gr.Row():
        with gr.Column(scale=3):
            gr.Markdown(registry_stats, elem_classes="cyber-panel")
            search = gr.Textbox(label="🔍 SEARCH SKILLS", placeholder="e.g. ffmpeg, port, seo…")
            domain = gr.Dropdown(DOMAINS, value="ALL", label="DOMAIN FILTER")
            detail = gr.Markdown("_select a skill to inspect_", elem_classes="cyber-panel")
            with gr.Row() as test_row:
                test_btn = gr.Button("🧪 FIRE TEST SHOT", variant="secondary")
                test_out = gr.Markdown("")
            vis.register("skilllab.testfire", test_row, "Skill Lab: test-shot row")
        with gr.Column(scale=5):
            gr.Markdown("#### SKILL RACK — tick any number of skills")
            first_ids = search_skills("", "ALL")[:24]
            rack = gr.CheckboxGroup(
                choices=[skill_label(s) for s in first_ids], value=[],
                label=f"REGISTRY ({len(SKILL_REGISTRY)} total — filter to browse)")
        with gr.Column(scale=4):
            gr.Markdown("#### 🎯 AGENT FUSION CHAMBER")
            agent_dd = gr.Dropdown(swarm.agent_choices(), label="TARGET AGENT",
                                    allow_custom_value=False)
            assign_btn = gr.Button("⚡ FUSE SELECTED SKILLS → AGENT", variant="primary")
            assign_msg = gr.Markdown("")
            gr.Markdown("#### CURRENTLY INSTALLED")
            installed = gr.Dropdown([], label="INSTALLED ON SELECTED AGENT")
            strip_btn = gr.Button("🧹 STRIP SELECTED SKILL", variant="stop")
            strip_msg = gr.Markdown("")

    # ---------------------------------------------------------------- events
    search.change(filter_skills, inputs=[search, domain], outputs=[rack])
    domain.change(filter_skills, inputs=[search, domain], outputs=[rack])
    rack.change(skill_detail, inputs=[rack], outputs=[detail])
    test_btn.click(test_skill, inputs=[rack], outputs=[test_out])
    assign_btn.click(assign_skills, inputs=[agent_dd, rack, search],
                     outputs=[assign_msg, ops_table])
    agent_dd.change(assigned_list, inputs=[agent_dd], outputs=[installed])
    strip_btn.click(unassign_skill, inputs=[agent_dd, installed],
                    outputs=[strip_msg, ops_table])

    return {"agent_dd": agent_dd, "rack": rack}
