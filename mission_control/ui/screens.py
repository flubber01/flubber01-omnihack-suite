"""MULTI-SCREEN MODE :: slim Gradio apps for a second monitor.

* ``/ops``  — OPERATOR CONSOLE: swarm chat + agent terminal, live browser,
              content factory (the *work* screen).
* ``/wall`` — MONITOR WALL: telemetry strip, ops matrix, log stream,
              hardware matrix, browser peek (the *status* screen).

Both share the same STATE singleton, so they always mirror the main console.
"""

from __future__ import annotations

import gradio as gr

from ..core import browser as br
from ..core import swarm
from ..core.pipeline import PIPELINE
from ..core.state import STATE
from ..core.theme import skin_style_block
from . import browser_tab, content_tab, hardware_tab, swarm_ops, topbar

MINI_HEADER = """
<div class="omni-header">
  <div class="core"></div>
  <div style="flex:1">
    <h1 style="font-size:17px;letter-spacing:4px">{title}</h1>
    <div class="sub">{sub}</div>
  </div>
</div>
"""


def _skin_sync(skin_holder: gr.HTML) -> gr.Timer:
    t = gr.Timer(6.0)
    t.tick(lambda: skin_style_block(STATE.skin), outputs=[skin_holder])
    return t


# --------------------------------------------------------------------- /ops
def build_ops_screen() -> gr.Blocks:
    with gr.Blocks(title="OMNIHACK // OPERATOR CONSOLE") as demo:
        skin_holder = gr.HTML(skin_style_block(STATE.skin))
        gr.HTML(MINI_HEADER.format(title="◤ OPERATOR CONSOLE ◢",
                                    sub="SCREEN A · CHAT + BROWSER + CONTENT FACTORY"))
        top = topbar.render()
        with gr.Tabs(elem_classes="omni-tabs", selected="chat"):
            with gr.Tab("💬 SWARM CHAT + TERMINAL", id="chat"):
                swarm_ops.render()
            with gr.Tab("🌐 LIVE BROWSER", id="browser"):
                browser_tab.render()
            with gr.Tab("🎬 CONTENT FACTORY", id="content"):
                content_tab.render()

        def _ops_kill():
            return (gr.Markdown(f"### {STATE.halt_all()}", visible=True),
                    topbar.metrics_html())

        def _ops_resume():
            return (gr.Markdown(f"### {STATE.resume_all()}", visible=True),
                    topbar.metrics_html())

        top["kill_btn"].click(_ops_kill, outputs=[top["banner"], top["topbar_html"]])
        top["resume_btn"].click(_ops_resume, outputs=[top["banner"], top["topbar_html"]])

        hb = gr.Timer(2.0)
        hb.tick(topbar.metrics_html, outputs=[top["topbar_html"]])
        _skin_sync(skin_holder)
    return demo


# -------------------------------------------------------------------- /wall
def wall_log_rows():
    return STATE.bus.rows(120, "ALL") or [["—", "—", "—", "empty"]]


def wall_queue_rows():
    return PIPELINE.queue_rows()[:12] or [["—"] * 7]


def wall_browser_frame():
    return br.screenshot()


def build_wall_screen() -> gr.Blocks:
    with gr.Blocks(title="OMNIHACK // MONITOR WALL") as demo:
        skin_holder = gr.HTML(skin_style_block(STATE.skin))
        gr.HTML(MINI_HEADER.format(title="◤ MONITOR WALL ◢",
                                    sub="SCREEN B · TELEMETRY + LOGS + HARDWARE"))
        top_html = gr.HTML(topbar.metrics_html)

        with gr.Row():
            with gr.Column(scale=5):
                gr.Markdown("#### 🤖 LIVE AGENT OPS MATRIX")
                ops_table = gr.Dataframe(value=swarm.ops_table_rows, interactive=False,
                                          headers=["AGENT", "TIER", "PARENT", "MODEL",
                                                   "STATUS", "SKILLS", "ROUTINES"],
                                          max_height=300)
            with gr.Column(scale=4):
                gr.Markdown("#### 📊 SYSTEM LOG STREAM")
                log_table = gr.Dataframe(value=wall_log_rows, interactive=False,
                                          headers=["TS", "LEVEL", "SOURCE", "MESSAGE"],
                                          max_height=300)
            with gr.Column(scale=3):
                gr.Markdown("#### 🌐 BROWSER PEEK")
                shot = gr.Image(value=br.screenshot(), type="pil", interactive=False,
                                 height=280)

        with gr.Row():
            with gr.Column(scale=6):
                gr.Markdown("#### 🔌 HARDWARE MATRIX")
                hw_table = gr.Dataframe(value=hardware_tab.device_rows, interactive=False,
                                         headers=["DEVICE", "KIND", "CHIP", "STATUS",
                                                  "LOAD", "TEMP", "POWER"],
                                         max_height=230)
            with gr.Column(scale=6):
                gr.Markdown("#### 🎬 CONTENT PRODUCTION QUEUE")
                q_table = gr.Dataframe(value=wall_queue_rows, interactive=False,
                                        headers=["ID", "TOPIC", "TONE", "LEN", "PLATFORMS",
                                                 "PROFILE", "STAGE"], max_height=230)

        gr.HTML('<div class="footer-strip">MONITOR WALL · read-only mirror of the '
                'mission state · use the main console at / to operate</div>')

        t = gr.Timer(2.5)
        t.tick(topbar.metrics_html, outputs=[top_html])
        t.tick(swarm.ops_table_rows, outputs=[ops_table])
        t.tick(wall_log_rows, outputs=[log_table])
        t.tick(wall_browser_frame, outputs=[shot])
        t.tick(hardware_tab.device_rows, outputs=[hw_table])
        t.tick(wall_queue_rows, outputs=[q_table])
        _skin_sync(skin_holder)
    return demo
