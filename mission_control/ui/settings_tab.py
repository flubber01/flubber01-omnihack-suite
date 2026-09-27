"""⚙️ SETTINGS & CONFIG :: skins, UI cleanup toggles, Telegram bridge, IO."""

from __future__ import annotations

import gradio as gr

from ..core.persistence import export_config, import_config
from ..core.state import STATE
from ..core.telegram_bridge import BRIDGE
from ..core.theme import SKIN_NAMES, skin_style_block
from . import visibility as vis


# ----------------------------------------------------------------- skins
def apply_skin(name):
    STATE.skin = name
    STATE.log("OK", "SKIN", f"HUD skin switched → {name}.")
    return skin_style_block(name), f"🎨 Skin **{name}** active."


def skin_payload():
    """Timer-driven: keeps every mounted screen in sync with STATE.skin."""
    return skin_style_block(STATE.skin)


# ------------------------------------------------------------ ui cleanup
def cleanup_choices():
    return [(vis.label_of(n), True) for n in vis.names()]


# -------------------------------------------------------------- telegram
def tg_status():
    cfg = STATE.telegram_cfg
    if cfg.get("running"):
        return f"🟢 BRIDGE ARMED :: @{cfg.get('bot_name', '?')} · polling loop active."
    return "⚫ Bridge idle — paste BotFather token and ARM."


def tg_arm(token, allowed):
    return BRIDGE.start(token, allowed), tg_status()


def tg_disarm():
    return BRIDGE.stop(), tg_status()


def tg_test_log():
    entries = [e for e in STATE.bus.tail(400) if e["source"] == "TELEGRAM"][-8:]
    if not entries:
        return "_no telegram events yet_"
    return "\n\n".join(f"`{e['ts'][-8:]}` {e['level']} :: {e['message']}" for e in entries)


# ------------------------------------------------------------- config io
def do_export():
    path, summary = export_config()
    return path, summary


def do_import(file):
    if file is None:
        return "❌ No file uploaded."
    path = file.name if hasattr(file, "name") else str(file)
    return import_config(path)


# ---------------------------------------------------------------- render
def render(skin_holder: gr.HTML) -> dict:
    with gr.Row():
        gr.Markdown("## ⚙️ USER SETTINGS & CONFIG\n"
                    "<span class='cyber-sub'>HUD SKINS · UI CLEANUP · TELEGRAM BRIDGE · "
                    "STATE EXPORT/IMPORT</span>")

    with gr.Row():
        # ------------------------------------------------------------ skins
        with gr.Column(scale=4):
            gr.Markdown("#### 🎨 HUD SKIN (3 styles, live)")
            skin_dd = gr.Radio(SKIN_NAMES, value=STATE.skin, label="SKIN")
            skin_btn = gr.Button("🎨 APPLY SKIN", variant="primary")
            skin_msg = gr.Markdown(f"Current: **{STATE.skin}**")
            gr.Markdown(
                "<span class='cyber-sub'>JARVIS = holographic Stark HUD · "
                "CYBERPUNK = matrix green/magenta · MILITARY OPS = olive/amber. "
                "All screens resync automatically.</span>")

            gr.Markdown("#### 🖥️ MULTI-SCREEN MODE")
            gr.Markdown(
                "Run this console on **two monitors** by opening the dedicated views:\n"
                "- **`/`** — full mission control (this screen)\n"
                "- **`/ops`** — OPERATOR CONSOLE: chat + browser + content "
                "(second monitor, work view)\n"
                "- **`/wall`** — MONITOR WALL: telemetry + logs + hardware "
                "(second monitor, status view)\n\n"
                "<span class='cyber-sub'>Same host & port — just open both URLs "
                "and drag one to your second display.</span>")

        # ------------------------------------------------------- ui cleanup
        with gr.Column(scale=4):
            gr.Markdown("#### 🧹 UI CLEANUP — hide controls you don't need")
            cb_container = gr.CheckboxGroup(
                value=[vis.label_of(n) for n in vis.names()],
                choices=[vis.label_of(n) for n in vis.names()],
                label="VISIBLE CONTROL GROUPS (untick to hide)")
            gr.Markdown(
                "<span class='cyber-sub'>Unchecked groups disappear everywhere in "
                "this console — keeps the working view lean. Re-tick to restore.</span>")

        # --------------------------------------------------------- telegram
        with gr.Column(scale=4):
            gr.Markdown("#### 📱 TELEGRAM CONTROL (BotFather token)")
            tg_token = gr.Textbox(label="BOT TOKEN (from @BotFather)", type="password",
                                   placeholder="123456789:AAH…xyz")
            tg_allowed = gr.Textbox(label="ALLOWED CHAT IDS (comma-sep, blank = open)",
                                     placeholder="e.g. 123456789, 987654321")
            with gr.Row():
                arm_btn = gr.Button("🟢 ARM BRIDGE", variant="primary")
                disarm_btn = gr.Button("⏹ DISARM", variant="stop")
            tg_msg = gr.Markdown(tg_status)
            tg_log = gr.Markdown(tg_test_log, elem_classes="cyber-panel")

    with gr.Row():
        with gr.Column(scale=6):
            gr.Markdown("#### 💾 MISSION STATE EXPORT / IMPORT")
            with gr.Row():
                exp_btn = gr.DownloadButton("⬇️ EXPORT config.json", variant="primary")
                exp_msg = gr.Markdown("")
            imp_file = gr.File(label="IMPORT config.json", file_types=[".json"])
            imp_msg = gr.Markdown("")
        with gr.Column(scale=6):
            gr.Markdown("#### 🗺️ WHERE THINGS LIVE")
            gr.Markdown(
                "- **Kill switch / re-arm** → top status bar (always visible)\n"
                "- **Brand connectors (n8n, Kaggle, Gmail …)** → Workflow Builder tab\n"
                "- **Pre-configured pipelines** → Workflow Builder ▸ SAVED WORKFLOWS\n"
                "- **4 personas** → Social Connectors ▸ profile matrix\n"
                "- **Agent direct-terminal** → Swarm Live Operations ▸ bottom console")

    # ---------------------------------------------------------------- events
    skin_btn.click(apply_skin, inputs=[skin_dd], outputs=[skin_holder, skin_msg])
    skin_dd.change(apply_skin, inputs=[skin_dd], outputs=[skin_holder, skin_msg])
    arm_btn.click(tg_arm, inputs=[tg_token, tg_allowed], outputs=[tg_msg, tg_msg])
    disarm_btn.click(tg_disarm, outputs=[tg_msg, tg_msg])
    exp_btn.click(do_export, outputs=[exp_btn, exp_msg])
    imp_file.upload(do_import, inputs=[imp_file], outputs=[imp_msg])

    timer = gr.Timer(6.0)
    timer.tick(skin_payload, outputs=[skin_holder])
    timer.tick(tg_status, outputs=[tg_msg])
    timer.tick(tg_test_log, outputs=[tg_log])

    return {"cb_container": cb_container, "skin_holder": skin_holder}
