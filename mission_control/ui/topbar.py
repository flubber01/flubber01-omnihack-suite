"""TOP STATUS BAR :: live VPS telemetry strip + emergency kill switch."""

from __future__ import annotations

import gradio as gr

from ..core.state import STATE


def metrics_html() -> str:
    m = STATE.metrics()
    halt_cls = "red" if m["halted"] else "green"
    halt_txt = "⛔ HALTED" if m["halted"] else "● NOMINAL"
    def cell(k: str, v: str, cls: str = "", bar: float | None = None) -> str:
        bar_html = (f'<div class="bar-track"><div class="bar-fill" '
                    f'style="width:{min(100, max(0, bar)):.0f}%"></div></div>'
                    if bar is not None else "")
        return (f'<div class="metric-cell"><span class="k">{k}</span>'
                f'<span class="v {cls}">{v}</span>{bar_html}</div>')
    parts = [
        cell("VPS CPU", f"{m['cpu']:.0f}%", "amber" if m["cpu"] > 80 else "", m["cpu"]),
        cell("VPS RAM", f"{m['ram_used_gb']:.1f}/{m['ram_total_gb']:.0f} GB",
             "amber" if m["ram_pct"] > 85 else "", m["ram_pct"]),
        cell("MAIN AGENTS", f"{m['commanders_active']}/{m['commanders']}", "green"),
        cell("UNDERCLASS", f"{m['minions_active']}/{m['minions']}", "green"),
        cell("BROWSERS", str(m["browser_instances"])),
        cell("RENDER TASKS", str(m["render_tasks"]), "amber" if m["render_tasks"] else ""),
        cell("PIPELINES", str(m["pipelines"])),
        cell("UPTIME", m["uptime"]),
        cell("SWARM STATE", halt_txt, halt_cls),
    ]
    return '<div class="omni-topbar">' + "".join(parts) + "</div>"


HEADER_HTML = """
<div class="omni-header">
  <h1>◤ OMNIHACK // MISSION CONTROL ◢</h1>
  <div class="sub">MAXED-OUT AGENTIC SWARM · AUTOMATED SOCIAL FACTORY · LIVE REMOTE BROWSER
  &nbsp;·&nbsp; VPS NODE: EU-CENTRAL-01 &nbsp;·&nbsp; CLEARANCE: OMEGA</div>
</div>
"""


def kill_switch() -> tuple[str, str]:
    return STATE.halt_all(), metrics_html()


def resume_switch() -> tuple[str, str]:
    return STATE.resume_all(), metrics_html()


def render() -> dict:
    """Build the header + telemetry strip. Returns components for wiring."""
    gr.HTML(HEADER_HTML)
    with gr.Row():
        topbar_html = gr.HTML(metrics_html, elem_classes="topbar-live")
        with gr.Column(scale=0, min_width=300):
            kill_btn = gr.Button("⛔ EMERGENCY KILL SWITCH", variant="stop",
                                  elem_id="btn-kill", size="lg")
            resume_btn = gr.Button("✅ RE-ARM SWARM", variant="primary",
                                    elem_id="btn-resume", size="lg")
    banner = gr.Markdown(visible=False, elem_classes="cyber-panel")
    return {"topbar_html": topbar_html, "kill_btn": kill_btn,
            "resume_btn": resume_btn, "banner": banner}
