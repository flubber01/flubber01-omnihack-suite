"""🛸 SWARM LIVE OPERATIONS :: chatbox widget + live agent ops table."""

from __future__ import annotations

import time

import gradio as gr

from ..core import swarm
from ..core.state import STATE


# ------------------------------------------------------------------ handlers
def send_to_swarm(history, text, target):
    text = (text or "").strip()
    if not text:
        yield history, gr.skip()
        return
    for h in swarm.swarm_chat_stream(history, text, target):
        yield h, gr.skip()
    yield history, activity_feed()


def clear_chat():
    return [], "🧹 Chat buffer flushed."


def ping_all():
    n = 0
    for a in STATE.agents.values():
        if a["status"] != "HALTED":
            a["status"] = "ACTIVE"
            n += 1
    STATE.log("INFO", "SWARM-OPS", f"Broadcast PING → {n} agents acknowledged heartbeat.")
    time.sleep(0.05)
    for a in STATE.agents.values():
        if a["status"] == "ACTIVE":
            a["status"] = "IDLE"
    return ops_rows(), f"📡 PING broadcast → **{n}** agents acknowledged."


def halt_agent(name):
    aid = swarm.agent_id_by_name(name)
    if not aid:
        return ops_rows(), "❌ Select an agent first."
    STATE.agents[aid]["status"] = "HALTED"
    STATE.log("WARN", "SWARM-OPS", f"Agent '{name}' manually frozen.")
    return ops_rows(), f"🧊 '{name}' frozen."


def resume_agent(name):
    aid = swarm.agent_id_by_name(name)
    if not aid:
        return ops_rows(), "❌ Select an agent first."
    STATE.agents[aid]["status"] = "IDLE"
    STATE.log("OK", "SWARM-OPS", f"Agent '{name}' restored to IDLE.")
    return ops_rows(), f"▶️ '{name}' restored."


def ops_rows():
    return swarm.ops_table_rows() or [["—"] * 7]


def activity_feed() -> str:
    entries = STATE.bus.tail(9)
    if not entries:
        return "_no activity yet_"
    lines = [f"`{e['ts'][-8:]}` **{e['source']}** :: {e['message']}" for e in entries]
    return "\n\n".join(lines)


def chat_targets():
    return gr.Dropdown(choices=["⚡ SWARM BROADCAST"] + swarm.agent_choices(),
                       value="⚡ SWARM BROADCAST")


# -------------------------------------------------------------------- render
def render() -> dict:
    with gr.Row():
        gr.Markdown("## 🛸 SWARM LIVE OPERATIONS\n"
                    "<span class='cyber-sub'>MULTI-AGENT COMMAND NET · STREAMING DECISION LOGS</span>")
    with gr.Row():
        with gr.Column(scale=7):
            chatbot = gr.Chatbot(
                value=[], height=540,
                elem_classes="swarm-chatbot",
                placeholder="⚡ Transmit a directive to the swarm…",
            )
            with gr.Row():
                target = gr.Dropdown(["⚡ SWARM BROADCAST"] + swarm.agent_choices(),
                                      value="⚡ SWARM BROADCAST", label="🎯 TARGET",
                                      scale=2, allow_custom_value=False)
                msg = gr.Textbox(label="OPERATOR UPLINK", placeholder="e.g. Scrape HN and schedule 3 shorts…",
                                  scale=5, max_lines=2)
            with gr.Row():
                send_btn = gr.Button("📡 TRANSMIT", variant="primary")
                clear_btn = gr.Button("🧹 FLUSH BUFFER", variant="secondary")
        with gr.Column(scale=5):
            gr.Markdown("### LIVE AGENT OPS MATRIX")
            ops_table = gr.Dataframe(
                value=ops_rows, interactive=False, wrap=True, max_height=330,
                headers=["AGENT", "TIER", "PARENT", "MODEL", "STATUS", "SKILLS", "ROUTINES"],
            )
            with gr.Row():
                agent_pick = gr.Dropdown(swarm.agent_choices(), label="SELECT AGENT",
                                          allow_custom_value=False)
                halt_btn = gr.Button("🧊 HALT", variant="stop")
                unhalt_btn = gr.Button("▶ RESUME", variant="secondary")
                ping_btn = gr.Button("📡 PING ALL", variant="primary")
            gr.Markdown("### ACTIVITY FEED")
            feed = gr.Markdown(activity_feed, elem_classes="cyber-panel")
            notice = gr.Markdown("")

    send_btn.click(send_to_swarm, inputs=[chatbot, msg, target], outputs=[chatbot, feed])
    msg.submit(send_to_swarm, inputs=[chatbot, msg, target], outputs=[chatbot, feed])
    clear_btn.click(clear_chat, outputs=[chatbot, notice])
    ping_btn.click(ping_all, outputs=[ops_table, notice])
    halt_btn.click(halt_agent, inputs=[agent_pick], outputs=[ops_table, notice])
    unhalt_btn.click(resume_agent, inputs=[agent_pick], outputs=[ops_table, notice])

    timer = gr.Timer(3.0)
    timer.tick(ops_rows, outputs=[ops_table])
    timer.tick(activity_feed, outputs=[feed])

    return {"chatbot": chatbot, "target": target, "agent_pick": agent_pick,
            "timer": timer, "chat_targets": chat_targets, "ops_table": ops_table}
