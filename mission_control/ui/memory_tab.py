"""🧠 MEMORY & LEARNING :: vault browser, remember loop, self-improvement."""

from __future__ import annotations

import gradio as gr

from ..core import swarm
from ..core.memory import MEMORY, REMEMBER
from ..core.state import STATE


# ------------------------------------------------------------------ views
def stats_md():
    s = MEMORY.stats()
    led = "led-green" if REMEMBER.running else "led-red"
    loop = "RUNNING" if REMEMBER.running else "IDLE"
    return (
        f"**🧠 MEMORY VAULT** (SQLite)\n\n"
        f"- Memories total: **{s['memories']}** · raw queue: {s['raw']}\n"
        f"- Lessons learned: **{s['lessons']}** · avg confidence {s['avg_confidence']}%\n"
        f"- Skill executions logged: {s['skill_runs']} (ok-rate {s['skill_ok_rate']}%)\n"
        f"- Improvement score: **{s['improvement']} / 100**\n\n"
        f"<span class='{led} led'></span> REMEMBER LOOP: **{loop}** "
        f"(every {REMEMBER.interval}s · cycles {REMEMBER.cycles})"
    )


def stream_rows():
    return [[m["ts"][-8:], m["kind"], m["agent"], m["content"][:90],
             str(m["importance"]), m["status"]] for m in MEMORY.recent(14)] \
        or [["—", "—", "—", "vault empty", "—", "—"]]


def lesson_rows():
    return [[l["ts"][-8:], l["source"], l["lesson"][:80],
             f"{l['confidence'] * 100:.0f}%", str(l["applied"])]
            for l in MEMORY.lessons(12)] or [["—", "—", "no lessons yet", "—", "—"]]


def do_recall(query, agent, kind):
    hits = MEMORY.recall(query, agent, kind, limit=12)
    rows = [[h["ts"][-8:], h["kind"], h["agent"], h["content"][:80], str(h["score"])]
            for h in hits]
    return rows or [["—", "—", "—", "nothing recalled", "0"]]


# ---------------------------------------------------------------- actions
def manual_store(agent, kind, content, importance):
    if not (content or "").strip():
        return "❌ Write a memory first.", stream_rows(), stats_md()
    mid = MEMORY.store(agent or "OPERATOR", content, kind, int(importance))
    STATE.log("OK", "MEMORY", f"Memory stored :: {mid} ({kind}, agent={agent or 'OPERATOR'}).")
    return f"💾 Stored as `{mid}`.", stream_rows(), stats_md()


def run_cycle_now():
    note = REMEMBER.run_cycle()
    return f"🔁 {note}", stats_md(), stream_rows(), lesson_rows()


def arm_loop(interval):
    return REMEMBER.start(interval), stats_md()


def disarm_loop():
    return REMEMBER.stop(), stats_md()


def flush_vault():
    msg = MEMORY.flush()
    return msg, stream_rows(), lesson_rows(), stats_md()


def auto_refresh():
    return stats_md(), stream_rows(), lesson_rows()


# ----------------------------------------------------------------- render
def render() -> dict:
    with gr.Row():
        gr.Markdown("## 🧠 MEMORY & LEARNING\n"
                    "<span class='cyber-sub'>SQLITE MEMORY VAULT · REMEMBER LOOP · "
                    "CONTINUOUS SELF-IMPROVEMENT</span>")

    with gr.Row():
        # ------------------------------------------------------------ loop
        with gr.Column(scale=4):
            stats_panel = gr.Markdown(stats_md, elem_classes="cyber-panel")
            gr.Markdown("#### 🔁 REMEMBER LOOP")
            interval = gr.Slider(10, 120, value=REMEMBER.interval, step=5,
                                  label="CYCLE INTERVAL (sec)")
            with gr.Row():
                arm_btn = gr.Button("🔁 ARM LOOP", variant="primary")
                disarm_btn = gr.Button("⏹ DISARM", variant="stop")
            cycle_btn = gr.Button("⚡ RUN CONSOLIDATION CYCLE NOW", variant="secondary")
            loop_msg = gr.Markdown("")
            gr.Markdown(
                "<span class='cyber-sub'>Each cycle: telemetry snapshot → consolidate raw "
                "memories into lessons → update improvement score. Chat, autopilot runs "
                "and skill executions feed the vault automatically.</span>")
        # ------------------------------------------------------------ vault
        with gr.Column(scale=5):
            gr.Markdown("#### 🗃️ MEMORY STREAM (latest first)")
            stream = gr.Dataframe(value=stream_rows, interactive=False,
                                   headers=["TS", "KIND", "AGENT", "CONTENT", "IMP", "STATE"],
                                   max_height=240)
            gr.Markdown("#### ✍️ STORE MEMORY MANUALLY")
            with gr.Row():
                mem_agent = gr.Dropdown(["OPERATOR", "SWARM", "REMEMBER-LOOP"]
                                         + swarm.agent_choices(), value="OPERATOR",
                                         label="AGENT", scale=2)
                mem_kind = gr.Dropdown(["episodic", "procedural", "semantic", "feedback"],
                                        value="episodic", label="KIND", scale=1)
                mem_imp = gr.Slider(1, 10, value=5, step=1, label="IMPORTANCE", scale=1)
            mem_text = gr.Textbox(label="CONTENT",
                                   placeholder="e.g. 'Operator prefers posts between 17-21h'")
            with gr.Row():
                store_btn = gr.Button("💾 STORE", variant="primary")
                flush_btn = gr.Button("🗑️ FLUSH VAULT", variant="stop")
            store_msg = gr.Markdown("")
        # ---------------------------------------------------------- recall
        with gr.Column(scale=3):
            gr.Markdown("#### 🔎 RECALL (semantic search)")
            recall_q = gr.Textbox(label="QUERY", placeholder="e.g. render, telegram, 17h…")
            with gr.Row():
                recall_agent = gr.Dropdown(["ALL"] + swarm.agent_choices(), value="ALL",
                                              label="AGENT", scale=2)
                recall_kind = gr.Dropdown(["ALL", "episodic", "procedural", "semantic",
                                            "feedback"], value="ALL", label="KIND", scale=1)
            recall_btn = gr.Button("🔎 RECALL", variant="primary")
            recall_table = gr.Dataframe(value=[["—", "—", "—", "nothing recalled", "0"]],
                                          interactive=False,
                                          headers=["TS", "KIND", "AGENT", "CONTENT", "SCORE"],
                                          max_height=180)
            gr.Markdown("#### 🎓 LESSONS LEARNED")
            lesson_table = gr.Dataframe(value=lesson_rows, interactive=False,
                                          headers=["TS", "SOURCE", "LESSON", "CONF", "USED"],
                                          max_height=180)

    # ---------------------------------------------------------------- events
    arm_btn.click(arm_loop, inputs=[interval], outputs=[loop_msg, stats_panel])
    disarm_btn.click(disarm_loop, outputs=[loop_msg, stats_panel])
    cycle_btn.click(run_cycle_now, outputs=[loop_msg, stats_panel, stream, lesson_table])
    store_btn.click(manual_store, inputs=[mem_agent, mem_kind, mem_text, mem_imp],
                    outputs=[store_msg, stream, stats_panel])
    flush_btn.click(flush_vault, outputs=[store_msg, stream, lesson_table, stats_panel])
    recall_btn.click(do_recall, inputs=[recall_q, recall_agent, recall_kind],
                     outputs=[recall_table])
    recall_q.submit(do_recall, inputs=[recall_q, recall_agent, recall_kind],
                    outputs=[recall_table])

    timer = gr.Timer(4.0)
    timer.tick(auto_refresh, outputs=[stats_panel, stream, lesson_table])

    return {"mem_agent": mem_agent}
