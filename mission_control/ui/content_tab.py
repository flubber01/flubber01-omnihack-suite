"""🎬 CONTENT AUTOMATION & PLANNER :: script ➔ assets ➔ TTS ➔ render ➔ post."""

from __future__ import annotations

import time

import gradio as gr

from ..core import swarm
from ..core.pipeline import PIPELINE, PLATFORMS, TONES, VOICES
from ..core.state import STATE
from . import visibility as vis


def _profile_names():
    return list(STATE.profiles.keys()) or ["DEFAULT-FACTORY"]


# ---------------------------------------------------------- preset pipelines
CONTENT_PRESETS = {
    "📰 Daily Tech Short": {
        "topic": "Top 3 AI tools nobody is talking about yet",
        "tone": "Tech Review", "length": 45,
        "platforms": ["YouTube Shorts", "TikTok", "Instagram Reels"],
        "profile": "ALEX-TECH"},
    "🎮 Gaming Highlight": {
        "topic": "Insane clutch play breakdown — frame by frame",
        "tone": "Hype / Viral", "length": 30,
        "platforms": ["TikTok", "YouTube Shorts"],
        "profile": "MIA-GAMING"},
    "📈 Market Brief": {
        "topic": "60-second macro brief: what moved the market today",
        "tone": "Educational", "length": 60,
        "platforms": ["YouTube Shorts", "X (Twitter)"],
        "profile": "LEON-FINANCE"},
    "🌸 Aesthetic Reel": {
        "topic": "Slow-morning routine — cinematic b-roll edit",
        "tone": "Dark / Cinematic", "length": 25,
        "platforms": ["Instagram Reels", "TikTok"],
        "profile": "SARA-LIFESTYLE"},
    "🧠 Tutorial Snippet": {
        "topic": "Automate your VPS in 3 commands — full walkthrough",
        "tone": "Educational", "length": 90,
        "platforms": ["YouTube Shorts", "TikTok", "Instagram Reels"],
        "profile": "ALEX-TECH"},
}


def apply_preset(name):
    p = CONTENT_PRESETS.get(name)
    if not p:
        return (gr.skip(),) * 5
    return p["topic"], p["tone"], p["length"], p["platforms"], p["profile"]


# ------------------------------------------------------------------ wizard
def create_job(topic, tone, length, platforms, profile):
    if not platforms:
        return "❌ Pick at least one distribution platform.", gr.skip(), gr.skip()
    job = PIPELINE.new_job(topic, tone, length, platforms, profile)
    return (f"🆕 Job `{job['id']}` created for '{job['topic']}' → stage IDEATION.",
            job["id"], queue_rows())


def write_script(job_id):
    res = PIPELINE.write_script(job_id)
    if not res.get("ok"):
        return f"❌ {res['error']}", gr.skip(), gr.skip()
    return "✍️ Script locked.", res["script"], queue_rows()


def fetch_assets(job_id):
    res = PIPELINE.fetch_assets(job_id)
    if not res.get("ok"):
        return "❌ create the job first.", []
    rows = [[a["id"], a["kind"], a["source"], f"{a['duration_s']}s",
             ", ".join(a["tags"])] for a in res["assets"]]
    return f"📦 {len(rows)} assets staged from stock vaults.", rows


def gen_voiceover(job_id, voice):
    res = PIPELINE.generate_voiceover(job_id, voice)
    if not res.get("ok"):
        return "❌ create the job first."
    vo = res["voiceover"]
    return (f"🎙️ Voiceover synthesized :: **{vo['voice']}** · {vo['words']} words · "
            f"~{vo['est_duration_s']}s · {vo['loudness_lufs']} LUFS → `{vo['file']}`")


def render_job(job_id):
    """Generator: streams simulated FFmpeg render progress."""
    job = PIPELINE.jobs.get(job_id)
    if not job:
        yield "❌ create the job first.", gr.skip(), gr.skip()
        return
    res = PIPELINE.render(job_id)
    cmd = res["ffmpeg_cmd"]
    for pct in range(0, 101, 5):
        if STATE.halted:
            yield f"⛔ Render aborted at {pct}% by KILL SWITCH.", gr.skip(), gr.skip()
            return
        yield (f"🎬 RENDERING `{job_id}.mp4` … {pct}%\n\n```bash\n{cmd}\n```",
               gr.skip(), gr.skip())
        time.sleep(0.06)
    r = res["render"]
    yield (f"✅ RENDER COMPLETE :: `{r['output']}` · {r['resolution']} · "
           f"{r['codec']} · {r['simulated_frames']} frames",
           queue_rows(), gr.skip())


def distribute_job(job_id):
    res = PIPELINE.distribute(job_id)
    if not res.get("ok"):
        return "❌ render first.", [], gr.skip()
    rows = [[p["platform"], p["profile"], p["status"], p["url"], p["uploaded_at"]]
            for p in res["posts"]]
    return (f"🚀 Distributed to {len(rows)} platform(s) via stored profile cookies.",
            rows, queue_rows())


def autopilot(topic, tone, length, platforms, profile, voice):
    """One-click full pipeline: ideation ➔ scripting ➔ rendering ➔ distribution."""
    if not (topic or "").strip():
        return "❌ Give the factory a topic.", gr.skip(), gr.skip(), gr.skip()
    result = PIPELINE.run_autopilot(topic, tone, length, platforms or PLATFORMS[:3],
                                     profile, voice)
    job = result["job"]
    report = [f"### 🤖 AUTOPILOT COMPLETE — `{job['id']}`",
              f"**Topic:** {job['topic']} · **Tone:** {job['tone']} · {job['length_s']}s",
              "", "**Stages executed:**",
              "1. ✅ Ideation + beat-sheet script",
              f"2. ✅ Assets fetched ({len(job['assets'])} items)",
              f"3. ✅ Voiceover :: {voice}",
              "4. ✅ FFmpeg render (1080×1920, 30fps)",
              f"5. ✅ Distributed → {', '.join(p['platform'] for p in result['posts'])}"]
    return ("\n".join(report), job["id"], job["script"], queue_rows())


# ----------------------------------------------------------------- planner
def add_schedule(job_id, when, cadence, platforms):
    if not (when or "").strip():
        return "❌ Set a date/time or cron expression.", schedule_rows()
    entry = {"id": job_id or "pending", "when": when,
             "cadence": cadence or "once",
             "platforms": ", ".join(platforms or []),
             "status": "ARMED"}
    STATE.schedule.append(entry)
    STATE.log("OK", "PLANNER", f"Scheduled {job_id or 'next-render'} :: {when} ({cadence}).")
    return f"⏰ Armed :: {when} ({cadence})", schedule_rows()


def schedule_rows():
    return [[s["id"], s["when"], s["cadence"], s["platforms"], s["status"]]
            for s in reversed(STATE.schedule)] or [["—", "—", "—", "—", "empty"]]


def queue_rows():
    return PIPELINE.queue_rows() or [["—"] * 7]


# ------------------------------------------------------------------ render
def render() -> dict:
    with gr.Row():
        gr.Markdown("## 🎬 CONTENT AUTOMATION & SHORT/VIDEO PLANNER\n"
                    "<span class='cyber-sub'>IDEATION ➔ SCRIPTING ➔ RENDERING ➔ "
                    "CROSS-PLATFORM DISTRIBUTION</span>")

    with gr.Row():
        with gr.Column(scale=5):
            gr.Markdown("#### 🏭 SHORT FACTORY WIZARD")
            preset = gr.Dropdown(list(CONTENT_PRESETS.keys()),
                                  label="⚡ PRE-CONFIGURED PIPELINE (fills everything)")
            topic = gr.Textbox(label="TOPIC / BRIEF",
                                placeholder="e.g. '5 Ollama tricks nobody knows'")
            with gr.Row():
                tone = gr.Dropdown(TONES, value=TONES[0], label="TONE")
                length = gr.Slider(15, 180, value=45, step=5, label="LENGTH (sec)")
            platforms = gr.CheckboxGroup(PLATFORMS, value=PLATFORMS[:3],
                                          label="🎯 DISTRIBUTION TARGETS")
            with gr.Row():
                profile = gr.Dropdown(_profile_names(), value=_profile_names()[0],
                                       label="POSTING PROFILE (cookies)",
                                       allow_custom_value=True)
                voice = gr.Dropdown(VOICES, value=VOICES[0], label="🎙️ TTS VOICE")
            with gr.Row():
                create_btn = gr.Button("🆕 CREATE JOB", variant="secondary")
                auto_btn = gr.Button("🤖 RUN FULL AUTOPILOT", variant="primary")
            job_id = gr.Textbox(label="ACTIVE JOB ID", value="—")
            wizard_status = gr.Markdown("_factory idle_")

            gr.Markdown("#### ⚙️ STAGE CONTROLS")
            with gr.Row() as stage_row:
                s1 = gr.Button("✍️ 1. SCRIPT", variant="secondary")
                s2 = gr.Button("📦 2. ASSETS", variant="secondary")
                s3 = gr.Button("🎙️ 3. VOICEOVER", variant="secondary")
                s4 = gr.Button("🎬 4. RENDER", variant="secondary")
                s5 = gr.Button("🚀 5. POST", variant="primary")
            vis.register("content.stages", stage_row, "Content: manual stage buttons")
            script_box = gr.Code(language=None, lines=10, label="SCRIPT OUTPUT",
                                  elem_classes="term-screen")
        with gr.Column(scale=5):
            autopilot_report = gr.Markdown("", elem_classes="cyber-panel")
            asset_table = gr.Dataframe(headers=["ID", "KIND", "SOURCE", "DUR", "TAGS"],
                                         interactive=False, max_height=150, label="ASSETS")
            vo_info = gr.Markdown("")
            post_table = gr.Dataframe(
                headers=["PLATFORM", "PROFILE", "STATUS", "URL", "UPLOADED"],
                interactive=False, max_height=150, label="DISTRIBUTION RECEIPTS")

    with gr.Row():
        with gr.Column(scale=6):
            gr.Markdown("#### 🗓️ VIDEO/SHORT PLANNER")
            with gr.Row():
                when = gr.Textbox(label="WHEN (datetime or cron)",
                                   placeholder="2026-09-28 18:00 or 0 9 * * *")
                cadence = gr.Dropdown(["once", "hourly", "daily", "weekly"],
                                         value="daily", label="CADENCE")
            sched_plats = gr.CheckboxGroup(PLATFORMS, value=PLATFORMS[:2],
                                            label="PLATFORMS")
            sched_btn = gr.Button("⏰ ARM SCHEDULE", variant="primary")
            sched_msg = gr.Markdown("")
            sched_table = gr.Dataframe(value=schedule_rows, interactive=False,
                                         headers=["JOB", "WHEN", "CADENCE", "PLATFORMS", "STATUS"])
        with gr.Column(scale=6):
            gr.Markdown("#### 📥 PRODUCTION QUEUE")
            queue_table = gr.Dataframe(value=queue_rows, interactive=False, max_height=250,
                                         headers=["ID", "TOPIC", "TONE", "LEN", "PLATFORMS",
                                                  "PROFILE", "STAGE"])

    # ---------------------------------------------------------------- events
    preset.change(apply_preset, inputs=[preset],
                  outputs=[topic, tone, length, platforms, profile])
    create_btn.click(create_job, inputs=[topic, tone, length, platforms, profile],
                     outputs=[wizard_status, job_id, queue_table])
    auto_btn.click(autopilot, inputs=[topic, tone, length, platforms, profile, voice],
                   outputs=[autopilot_report, job_id, script_box, queue_table])
    s1.click(write_script, inputs=[job_id], outputs=[wizard_status, script_box, queue_table])
    s2.click(fetch_assets, inputs=[job_id], outputs=[wizard_status, asset_table])
    s3.click(gen_voiceover, inputs=[job_id, voice], outputs=[vo_info])
    s4.click(render_job, inputs=[job_id], outputs=[wizard_status, queue_table, autopilot_report])
    s5.click(distribute_job, inputs=[job_id], outputs=[wizard_status, post_table, queue_table])
    sched_btn.click(add_schedule, inputs=[job_id, when, cadence, sched_plats],
                    outputs=[sched_msg, sched_table])

    def _profile_dd():
        names = _profile_names()
        return gr.Dropdown(choices=names, value=names[0] if names else None,
                           allow_custom_value=True)

    timer = gr.Timer(4.0)
    timer.tick(queue_rows, outputs=[queue_table])
    timer.tick(_profile_dd, outputs=[profile])

    return {"job_id": job_id, "profile": profile}
