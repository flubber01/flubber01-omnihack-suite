"""📊 SYSTEM LOGS :: live telemetry stream with level filtering."""

from __future__ import annotations

import gradio as gr

from ..core.state import STATE, LOG_LEVELS


def log_rows(level):
    return STATE.bus.rows(140, level or "ALL") or [["—", "—", "—", "log buffer empty"]]


def level_counts():
    counts = {lv: 0 for lv in LOG_LEVELS}
    for e in STATE.bus.tail(2000):
        counts[e["level"]] = counts.get(e["level"], 0) + 1
    return " · ".join(f"**{lv}** {counts.get(lv, 0)}" for lv in LOG_LEVELS)


def clear_logs():
    STATE.bus.clear()
    STATE.log("INFO", "LOGS", "Log buffer flushed by operator.")
    return [["—", "—", "—", "log buffer empty"]], level_counts()


# ------------------------------------------------------------------ render
def render() -> dict:
    with gr.Row():
        gr.Markdown("## 📊 SYSTEM LOGS\n"
                    "<span class='cyber-sub'>RING BUFFER 2000 EVENTS · ALL SUBSYSTEMS · "
                    "AUTO-REFRESH 2s</span>")
    with gr.Row():
        level = gr.Dropdown(["ALL"] + list(LOG_LEVELS), value="ALL", label="LEVEL FILTER",
                             scale=1)
        counts = gr.Markdown(level_counts, scale=4)
        clear_btn = gr.Button("🧹 FLUSH BUFFER", variant="stop", scale=1)
    table = gr.Dataframe(value=lambda: log_rows("ALL"), interactive=False,
                          headers=["TIMESTAMP", "LEVEL", "SOURCE", "MESSAGE"],
                          max_height=480, wrap=True)

    timer = gr.Timer(2.0)
    timer.tick(log_rows, inputs=[level], outputs=[table])
    timer.tick(level_counts, outputs=[counts])
    level.change(log_rows, inputs=[level], outputs=[table])
    clear_btn.click(clear_logs, outputs=[table, counts])

    return {"level": level}
