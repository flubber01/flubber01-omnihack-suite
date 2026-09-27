"""OMNIHACK MISSION CONTROL — application assembly.

Builds the full Gradio Blocks app: header, live telemetry top bar,
10 mission tabs, global timers and the emergency kill switch.
"""

from __future__ import annotations

import os

import gradio as gr

from .core import swarm
from .core.persistence import load_persisted
from .core.state import STATE, seed_static_data
from .core.theme import CSS, build_theme
from .ui import (agents_tab, browser_tab, content_tab, hardware_tab,
                  logs_tab, skill_lab_tab, social_tab, ssh_tab, swarm_ops,
                  topbar, workflow_tab)

# Boot-time seeding so every dropdown is populated from the first frame.
swarm.seed_swarm()
seed_static_data()
load_persisted()


# ---------------------------------------------------------------------------
def kill_handler():
    msg = STATE.halt_all()
    return (gr.Markdown(f"### {msg}", visible=True),
            topbar.metrics_html(), swarm.ops_table_rows())


def resume_handler():
    msg = STATE.resume_all()
    return (gr.Markdown(f"### {msg}", visible=True),
            topbar.metrics_html(), swarm.ops_table_rows())


def boot_notice():
    STATE.log("INFO", "BOOT", "Mission Control online :: all subsystems initialised.")
    return gr.Markdown(
        "🛰️ **MISSION CONTROL ONLINE** — telemetry locked, swarm genesis loaded, "
        "202 skills registered.", visible=True)


# ---------------------------------------------------------------------------
def build_demo() -> gr.Blocks:
    with gr.Blocks(title="OMNIHACK // MISSION CONTROL") as demo:
        # ------------------------------------------------------------ header
        top = topbar.render()

        with gr.Tabs(elem_classes="omni-tabs", selected="ops"):
            with gr.Tab("🛸 Swarm Live Operations", id="ops"):
                ops = swarm_ops.render()
            with gr.Tab("🤖 Hierarchical Agent Configurator", id="agents"):
                agents = agents_tab.render(ops["ops_table"])
            with gr.Tab("🌐 LIVE BROWSER STREAM", id="browser"):
                browser_tab.render()
            with gr.Tab("🎬 Content Automation & Planner", id="content"):
                content_tab.render()
            with gr.Tab("📡 Social Connectors & Profiles", id="social"):
                social_tab.render()
            with gr.Tab("🔬 Skill Lab", id="skills"):
                skill_lab_tab.render(ops["ops_table"])
            with gr.Tab("💻 Direct SSH Terminal", id="ssh"):
                ssh_tab.render()
            with gr.Tab("🗺️ Workflow Builder", id="workflow"):
                workflow_tab.render()
            with gr.Tab("🔌 Hardware Hub", id="hardware"):
                hardware_tab.render()
            with gr.Tab("📊 System Logs", id="logs"):
                logs_tab.render()

        gr.HTML('<div class="footer-strip">OMNIHACK SUITE v1.0 · AGENTIC SWARM MISSION '
                'CONTROL · ALL EXTERNAL CALLS STUBBED FOR SAFE OPERATION · '
                'CLEARANCE OMEGA · flubber01</div>')

        # ------------------------------------------------- global wiring
        top["kill_btn"].click(kill_handler,
                               outputs=[top["banner"], top["topbar_html"], ops["ops_table"]])
        top["resume_btn"].click(resume_handler,
                                 outputs=[top["banner"], top["topbar_html"], ops["ops_table"]])

        heartbeat = gr.Timer(2.0)
        heartbeat.tick(topbar.metrics_html, outputs=[top["topbar_html"]])

        demo.load(boot_notice, outputs=[top["banner"]])

    return demo


def main() -> None:
    demo = build_demo()
    demo.queue()
    demo.launch(
        server_name=os.environ.get("OMNI_HOST", "0.0.0.0"),
        server_port=int(os.environ.get("OMNI_PORT", "7860")),
        theme=build_theme(),
        css=CSS,
        share=False,
    )


if __name__ == "__main__":
    main()
