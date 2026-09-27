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


# ----------------------------------------------------- agent direct terminal
TERM_BANNER = (
    "╔══════════════════════════════════════════════════════════════╗\n"
    "║  OMNI-DIRECT :: AGENT UPLINK TERMINAL   type /help            ║\n"
    "╚══════════════════════════════════════════════════════════════╝\n"
)
TERM_HELP = (
    "/help                     this list\n"
    "/clear                    flush terminal\n"
    "/status                   swarm telemetry\n"
    "/agents                   roster\n"
    "/tree                     hierarchy map\n"
    "/kill  |  /resume         emergency halt / re-arm\n"
    "/say <AGENT> <msg>        direct-talk any agent\n"
    "/broadcast <msg>          all commanders respond\n"
    "/model <AGENT> <model>    hot-rebind a brain\n"
    "/skills <AGENT>           list installed skills\n"
    "@AGENT <msg>              shorthand for /say\n"
    "<text>                    talks to the selected target agent"
)


def _term_stream(screen: str, speaker: str, text: str):
    """Yield progressively longer screens while an agent 'types'."""
    head = f"{screen}\n{speaker} ▸ "
    step = max(6, len(text) // 14)
    for i in range(0, len(text), step):
        if STATE.halted and speaker != "SYSTEM":
            yield head + text[:i] + " ⛔[HALTED]"
            return
        yield head + text[:i + step]
        time.sleep(0.012)
    yield head + text


def term_exec(screen, line, target):
    line = (line or "").strip()
    if not line:
        yield gr.skip(), ""
        return
    screen = screen or TERM_BANNER
    echo = f"{screen}\nOPERATOR ▸ {line}"
    yield echo, ""

    parts = line.split(maxsplit=2)
    cmd = parts[0].lower()

    if cmd == "/help":
        yield echo + "\n\nSYSTEM ▸\n" + TERM_HELP, ""
    elif cmd == "/clear":
        yield TERM_BANNER, ""
    elif cmd == "/status":
        m = STATE.metrics()
        yield (echo + (f"\nSYSTEM ▸ CPU {m['cpu']:.0f}% · RAM {m['ram_pct']:.0f}% · "
                        f"CMDR {m['commanders_active']}/{m['commanders']} · "
                        f"MINIONS {m['minions_active']}/{m['minions']} · "
                        f"BROWSERS {m['browser_instances']} · RENDERS {m['render_tasks']} · "
                        f"{'⛔ HALTED' if m['halted'] else '🟢 NOMINAL'}"), "")
    elif cmd == "/agents":
        rows = [f"{'👑' if a['tier'] == 'commander' else '▸'} {a['name']} "
                f"[{a['status']}] {a['model']}" for a in STATE.agents.values()]
        yield (echo + "\nSYSTEM ▸\n" + "\n".join(rows)), ""
    elif cmd == "/tree":
        yield (echo + "\nSYSTEM ▸\n" + swarm.agent_tree_text()), ""
    elif cmd == "/kill":
        yield (echo + f"\nSYSTEM ▸ {STATE.halt_all('TERMINAL KILL')}"), ""
    elif cmd == "/resume":
        yield (echo + f"\nSYSTEM ▸ {STATE.resume_all()}"), ""
    elif cmd in ("/say", "@") and len(parts) >= 3:
        agent = next((a for a in STATE.agents.values()
                      if a["name"] == parts[1].upper()), None)
        if not agent:
            yield (echo + f"\nSYSTEM ▸ ❌ no agent named {parts[1].upper()}"), ""
        else:
            for s in _term_stream(echo, agent["name"],
                                   swarm._agent_reply(agent, parts[2])):
                yield s, ""
    elif cmd == "/broadcast" and len(parts) >= 2:
        msg = line.split(maxsplit=1)[1]
        out = echo
        for a in [x for x in STATE.agents.values() if x["tier"] == "commander"]:
            for s in _term_stream(out, a["name"], swarm._agent_reply(a, msg)):
                out = s
                yield s, ""
    elif cmd == "/model" and len(parts) >= 3:
        from ..core.ollama import bind_model_to_agent
        agent = next((a for a in STATE.agents.values()
                      if a["name"] == parts[1].upper()), None)
        if not agent:
            yield (echo + f"\nSYSTEM ▸ ❌ no agent named {parts[1].upper()}"), ""
        else:
            yield (echo + "\nSYSTEM ▸ " + bind_model_to_agent(agent["id"], parts[2])), ""
    elif cmd == "/skills" and len(parts) >= 2:
        agent = next((a for a in STATE.agents.values()
                      if a["name"] == parts[1].upper()), None)
        if not agent:
            yield (echo + f"\nSYSTEM ▸ ❌ no agent named {parts[1].upper()}"), ""
        else:
            lst = ", ".join(agent["skills"]) or "(none installed)"
            yield (echo + f"\nSYSTEM ▸ {agent['name']} skills :: {lst}"), ""
    else:
        # plain text → selected target agent
        text = line[1:].strip() if line.startswith("@") else line
        agent = next((a for a in STATE.agents.values()
                      if a["name"] == target), None)
        if not agent:
            yield (echo + "\nSYSTEM ▸ ❌ select a target agent first."), ""
        else:
            for s in _term_stream(echo, agent["name"],
                                   swarm._agent_reply(agent, text)):
                yield s, ""


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

    # ------------------------------------------------- agent direct terminal
    with gr.Row():
        with gr.Column(scale=9):
            gr.Markdown("### 💬 AGENT DIRECT TERMINAL\n"
                        "<span class='cyber-sub'>TYPE /help — talk to any agent directly, "
                        "streaming replies in the console</span>")
            term_screen = gr.Code(language="shell", lines=10, value=TERM_BANNER,
                                   label="OMNI-DIRECT UPLINK", elem_classes="term-screen")
            with gr.Row():
                term_target = gr.Dropdown(swarm.agent_choices(),
                                           value=(swarm.agent_choices()[0]
                                                  if swarm.agent_choices() else None),
                                           label="DEFAULT TARGET", scale=2)
                term_line = gr.Textbox(label="UPLINK", scale=6,
                                        placeholder="/say OMNI-PRIME status report  ·  /help")
                term_btn = gr.Button("⏎ TRANSMIT", variant="primary", scale=1)
        with gr.Column(scale=3):
            gr.Markdown("#### QUICK CMDS")
            for lbl, c in [("status", "/status"), ("agents", "/agents"),
                            ("tree", "/tree"), ("⛔ kill", "/kill"),
                            ("✅ resume", "/resume"), ("help", "/help")]:
                gr.Button(lbl, size="sm", variant="secondary").click(
                    lambda s, cc=c: term_exec(s, cc, None),
                    inputs=[term_screen], outputs=[term_screen, term_line])

    send_btn.click(send_to_swarm, inputs=[chatbot, msg, target], outputs=[chatbot, feed])
    msg.submit(send_to_swarm, inputs=[chatbot, msg, target], outputs=[chatbot, feed])
    clear_btn.click(clear_chat, outputs=[chatbot, notice])
    ping_btn.click(ping_all, outputs=[ops_table, notice])
    halt_btn.click(halt_agent, inputs=[agent_pick], outputs=[ops_table, notice])
    unhalt_btn.click(resume_agent, inputs=[agent_pick], outputs=[ops_table, notice])
    term_btn.click(term_exec, inputs=[term_screen, term_line, term_target],
                   outputs=[term_screen, term_line])
    term_line.submit(term_exec, inputs=[term_screen, term_line, term_target],
                     outputs=[term_screen, term_line])

    timer = gr.Timer(3.0)
    timer.tick(ops_rows, outputs=[ops_table])
    timer.tick(activity_feed, outputs=[feed])

    return {"chatbot": chatbot, "target": target, "agent_pick": agent_pick,
            "timer": timer, "chat_targets": chat_targets, "ops_table": ops_table,
            "term_screen": term_screen}
