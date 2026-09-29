"""OMNIHACK MISSION CONTROL — application assembly.

Mounts three Gradio apps on one server (multi-screen mode):

* ``/``     full mission control (10 tabs + settings)
* ``/ops``  operator console for a second monitor (chat + browser + content)
* ``/wall`` read-only monitor wall for a second monitor
"""

from __future__ import annotations

import os

import gradio as gr

from .core import swarm
from .core.persistence import load_persisted
from .core.state import STATE, seed_static_data
from .core.theme import build_theme, launch_css, skin_style_block
from .ui import (agents_tab, browser_tab, content_tab, hardware_tab,
                  helpbot, logs_tab, memory_tab, screens, settings_tab,
                  skill_lab_tab, social_tab, ssh_tab, swarm_ops, topbar,
                  visibility as vis, workflow_tab)

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
        "🛰️ **MISSION CONTROL ONLINE** — swarm genesis loaded, 202 skills registered, "
        "4 personas armed. Second-monitor views: **`/ops`** (work) & **`/wall`** (status).",
        visible=True)


# ---------------------------------------------------------------------------
def build_main() -> gr.Blocks:
    with gr.Blocks(title="OMNIHACK // MISSION CONTROL") as demo:
        skin_holder = gr.HTML(skin_style_block(STATE.skin))

        # ------------------------------------------------------------ header
        top = topbar.render()

        # 🤖 floating setup assistant — rendered early so Settings' UI-cleanup
        #    list can see it; it is position:fixed so layout order is cosmetic.
        helpbot.render()

        with gr.Tabs(elem_classes="omni-tabs", selected="ops"):
            with gr.Tab("🛸 Swarm Live Operations", id="ops"):
                ops = swarm_ops.render()
            with gr.Tab("🤖 Agent Configurator", id="agents"):
                agents_tab.render(ops["ops_table"])
            with gr.Tab("🌐 LIVE BROWSER STREAM", id="browser"):
                browser_tab.render()
            with gr.Tab("🎬 Content Automation", id="content"):
                content_tab.render()
            with gr.Tab("📡 Social Connectors", id="social"):
                social_tab.render()
            with gr.Tab("🔬 Skill Lab", id="skills"):
                skill_lab_tab.render(ops["ops_table"])
            with gr.Tab("🧠 Memory & Learning", id="memory"):
                memory_tab.render()
            with gr.Tab("💻 SSH Terminal", id="ssh"):
                ssh_tab.render()
            with gr.Tab("🗺️ Workflows & Connectors", id="workflow"):
                workflow_tab.render()
            with gr.Tab("🔌 Hardware Hub", id="hardware"):
                hardware_tab.render()
            with gr.Tab("📊 System Logs", id="logs"):
                logs_tab.render()
            with gr.Tab("⚙️ Settings & Config", id="settings"):
                settings = settings_tab.render(skin_holder)

        gr.HTML('<div class="footer-strip">OMNIHACK SUITE v2.1 · AGENTIC SWARM MISSION '
                'CONTROL · MULTI-SCREEN: /ops + /wall · TELEGRAM BRIDGE IN SETTINGS · '
                'CLEARANCE OMEGA · flubber01</div>')

        # ------------------------------------------------- global wiring
        top["kill_btn"].click(kill_handler,
                               outputs=[top["banner"], top["topbar_html"], ops["ops_table"]])
        top["resume_btn"].click(resume_handler,
                                 outputs=[top["banner"], top["topbar_html"], ops["ops_table"]])

        heartbeat = gr.Timer(2.0)
        heartbeat.tick(topbar.metrics_html, outputs=[top["topbar_html"]])

        # UI-cleanup toggles: hide/show registered optional control groups.
        names = vis.names()
        components = [vis.GROUPS[n][0] for n in names]
        labels = [vis.label_of(n) for n in names]

        def apply_cleanup(visible_labels, _names=tuple(names), _labels=tuple(labels)):
            out = []
            for n, lbl in zip(_names, _labels):
                out.append(gr.update(visible=(lbl in (visible_labels or []))))
            return out

        settings["cb_container"].change(apply_cleanup,
                                         inputs=[settings["cb_container"]],
                                         outputs=components)

        demo.load(boot_notice, outputs=[top["banner"]])

    return demo


# ---------------------------------------------------------------------------
def build_server():
    """FastAPI host carrying all three screens."""
    from fastapi import FastAPI

    from fastapi.responses import RedirectResponse

    app = FastAPI(title="OMNIHACK Mission Control")
    theme = build_theme()

    # Bare /ops and /wall (no trailing slash) → redirect into the sub-app.
    # These must be registered BEFORE the mounts so the exact-path route
    # wins over the prefix Mount for the slash-less request.
    @app.get("/ops", include_in_schema=False)
    def _ops_redirect():
        return RedirectResponse(url="/ops/")

    @app.get("/wall", include_in_schema=False)
    def _wall_redirect():
        return RedirectResponse(url="/wall/")

    # Sub-screens next; the catch-all "/" console is mounted LAST because
    # Starlette matches mounts by prefix in registration order.
    app = gr.mount_gradio_app(app, screens.build_ops_screen(), path="/ops",
                               theme=theme, css=launch_css())
    app = gr.mount_gradio_app(app, screens.build_wall_screen(), path="/wall",
                               theme=theme, css=launch_css())
    app = gr.mount_gradio_app(app, build_main(), path="/", theme=theme, css=launch_css())
    return app


def main() -> None:
    import uvicorn

    app = build_server()
    host = os.environ.get("OMNI_HOST", "0.0.0.0")
    port = int(os.environ.get("OMNI_PORT", "7860"))
    print(f"\n  ◤ OMNIHACK MISSION CONTROL ◢\n"
          f"  main console   → http://{host}:{port}/\n"
          f"  operator view  → http://{host}:{port}/ops\n"
          f"  monitor wall   → http://{host}:{port}/wall\n")
    uvicorn.run(app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    main()
