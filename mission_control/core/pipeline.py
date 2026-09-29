"""CONTENT AUTOMATION PIPELINE :: script → assets → voiceover → render → post.

Every stage returns a plausible simulated artifact so the planner is fully
navigable without external services.  The FFmpeg stage is a real wrapper
call-site (stubbed execution) so swapping in a render farm is trivial.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List

from .state import STATE, now_iso, uid

_RND = random.Random(99)

VOICES = ["ARIA-9 (fem, warm)", "VOLT-3 (masc, punchy)", "NOVA-5 (fem, narration)",
          "REX-1 (masc, hype)", "ECHO-7 (neutral, docu)"]
TONES = ["Hype / Viral", "Educational", "Dark / Cinematic", "Tech Review", "Motivational"]
PLATFORMS = ["YouTube Shorts", "TikTok", "Instagram Reels", "Facebook", "X (Twitter)"]

HOOKS = [
    "Nobody is talking about this yet…",
    "I tested it for 30 days straight. Here's the truth.",
    "This changes everything you knew about {topic}.",
    "Stop scrolling — the {topic} secret is finally out.",
    "POV: you discover {topic} before everyone else.",
]
BEATS = [
    "Reveal the core claim with on-screen proof.",
    "Cut to b-roll while the voiceover drops the key stat.",
    "Quick myth-bust: what everyone gets wrong.",
    "Show the exact steps in three fast cuts.",
    "Insert pattern-interrupt zoom + sound sting.",
]
CTAS = [
    "Follow for part 2 — tomorrow we go deeper.",
    "Save this before it gets buried.",
    "Comment '{topic}' and I'll send the full breakdown.",
    "Share this with someone who needs it today.",
]


class ContentPipeline:
    def __init__(self) -> None:
        self.jobs: Dict[str, Dict[str, Any]] = {}

    # ------------------------------------------------------------------ jobs
    def new_job(self, topic: str, tone: str, length: int,
                platforms: List[str], profile: str) -> Dict[str, Any]:
        job = {
            "id": uid("vid"),
            "topic": (topic or "untitled brief").strip(),
            "tone": tone,
            "length_s": int(length),
            "platforms": list(platforms or []),
            "profile": profile,
            "stage": "IDEATION",
            "progress": 0.0,
            "script": "",
            "assets": [],
            "voiceover": {},
            "render": {},
            "posts": [],
            "created_at": now_iso(),
        }
        self.jobs[job["id"]] = job
        STATE.content_queue.append(job)
        STATE.log("INFO", "PIPELINE", f"New content job {job['id']} :: {job['topic']}")
        return job

    # ---------------------------------------------------------------- stages
    def write_script(self, job_id: str) -> Dict[str, Any]:
        job = self.jobs.get(job_id)
        if not job:
            return {"ok": False, "error": "unknown job"}
        rnd = random.Random(job_id)
        topic = job["topic"]
        hook = rnd.choice(HOOKS).format(topic=topic)
        lines = [f"🎬 SCRIPT :: '{topic}'  [{job['tone']} · {job['length_s']}s]",
                 "", f"[0:00 HOOK] {hook}"]
        beats = rnd.sample(BEATS, k=3)
        t = 3
        seg = max(4, (job["length_s"] - 12) // 3)
        for i, b in enumerate(beats, 1):
            lines.append(f"[0:{t:02d} BEAT {i}] {b}  (VO: '{topic}' context #{i})")
            t += seg
        lines.append(f"[0:{min(t, 59):02d} CTA] {rnd.choice(CTAS).format(topic=topic)}")
        lines += ["", "#shorts #viral #" + topic.replace(" ", "")[:24]]
        job["script"] = "\n".join(lines)
        job["stage"] = "SCRIPTED"
        STATE.log("OK", "PIPELINE", f"Script written for {job_id}.")
        return {"ok": True, "script": job["script"]}

    def fetch_assets(self, job_id: str) -> Dict[str, Any]:
        job = self.jobs.get(job_id)
        if not job:
            return {"ok": False, "error": "unknown job"}
        rnd = random.Random(job_id + "assets")
        assets = []
        for i in range(rnd.randint(4, 6)):
            assets.append({
                "id": uid("ast"),
                "kind": rnd.choice(["stock-video", "image", "b-roll", "meme", "chart"]),
                "source": rnd.choice(["Pexels", "Pixabay", "Storyblocks", "LocalVault"]),
                "duration_s": rnd.randint(2, 9),
                "tags": [job["topic"].split()[0].lower(), "vertical", "4k"],
            })
        job["assets"] = assets
        job["stage"] = "ASSETS_READY"
        STATE.log("OK", "PIPELINE", f"Fetched {len(assets)} assets for {job_id}.")
        return {"ok": True, "assets": assets}

    def generate_voiceover(self, job_id: str, voice: str) -> Dict[str, Any]:
        job = self.jobs.get(job_id)
        if not job:
            return {"ok": False, "error": "unknown job"}
        words = max(20, len(job.get("script", "").split()) or job["length_s"] * 2)
        vo = {
            "engine": "omniTTS-neural (stub)",
            "voice": voice,
            "words": words,
            "est_duration_s": round(words / 2.6, 1),
            "file": f"/render/{job['id']}/voiceover.wav",
            "loudness_lufs": -16.0,
        }
        job["voiceover"] = vo
        job["stage"] = "VOICEOVER_READY"
        STATE.log("OK", "PIPELINE", f"Voiceover synthesized for {job_id} ({voice}).")
        return {"ok": True, "voiceover": vo}

    def render(self, job_id: str) -> Dict[str, Any]:
        """Simulated FFmpeg concatenation wrapper."""
        job = self.jobs.get(job_id)
        if not job:
            return {"ok": False, "error": "unknown job"}
        task = {"id": uid("rnd"), "job": job_id, "status": "RENDERING", "progress": 0}
        STATE.render_tasks[task["id"]] = task
        cmd = ("ffmpeg -y -f concat -safe 0 -i clips.txt "
               f"-i {job['voiceover'].get('file', 'vo.wav')} "
               "-vf scale=1080:1920 -c:v libx264 -preset veryfast -c:a aac "
               f"-t {job['length_s']} {job['id']}.mp4")
        STATE.log("INFO", "FFMPEG", f"Render task {task['id']} dispatched :: {job['id']}.mp4")
        render = {
            "task_id": task["id"],
            "ffmpeg_cmd": cmd,
            "resolution": "1080x1920 (9:16)",
            "codec": "H.264 / AAC",
            "output": f"/render/{job['id']}/{job['id']}.mp4",
            "simulated_frames": job["length_s"] * 30,
        }
        job["render"] = render
        job["stage"] = "RENDERED"
        task["status"] = "DONE"
        STATE.log("OK", "FFMPEG", f"Render complete :: {job['id']}.mp4 "
                                  f"({job['length_s']}s @ 1080x1920).")
        return {"ok": True, "render": render, "ffmpeg_cmd": cmd}

    def distribute(self, job_id: str) -> Dict[str, Any]:
        job = self.jobs.get(job_id)
        if not job:
            return {"ok": False, "error": "unknown job"}
        posts = []
        for platform in job["platforms"]:
            posts.append({
                "platform": platform,
                "profile": job["profile"],
                "status": "UPLOADED (simulated)",
                "url": f"https://{platform.split()[0].lower()}.example/{job['id']}",
                "cookies": "stored-profile-cookies",
                "uploaded_at": now_iso(),
            })
        job["posts"] = posts
        job["stage"] = "DISTRIBUTED"
        STATE.pipeline_runs.append({"id": job_id, "status": "COMPLETE",
                                    "targets": len(posts)})
        STATE.log("OK", "DISTRIBUTE", f"{job_id} pushed to {len(posts)} platform(s).")
        return {"ok": True, "posts": posts}

    # ----------------------------------------------------------------- table
    def queue_rows(self) -> List[List[str]]:
        rows = []
        for job in reversed(STATE.content_queue):
            rows.append([
                job["id"], job["topic"][:32], job["tone"],
                str(job["length_s"]) + "s", ",".join(p.split()[0] for p in job["platforms"]),
                job["profile"], job["stage"],
            ])
        return rows

    def run_autopilot(self, topic: str, tone: str, length: int,
                      platforms: List[str], profile: str, voice: str) -> Dict[str, Any]:
        """Full one-click flow: ideation ➔ scripting ➔ rendering ➔ distribution."""
        job = self.new_job(topic, tone, length, platforms, profile)
        self.write_script(job["id"])
        self.fetch_assets(job["id"])
        self.generate_voiceover(job["id"], voice)
        self.render(job["id"])
        post = self.distribute(job["id"])
        # 🧠 procedural memory: how the factory executed this run
        try:
            from .memory import MEMORY
            MEMORY.store(profile or "FACTORY",
                         f"autopilot render '{topic}' ({length}s, {tone}) → posted to "
                         f"{', '.join(p['platform'] for p in post.get('posts', []))}",
                         kind="procedural", importance=8)
        except Exception:
            pass
        return {"ok": True, "job": job, "posts": post.get("posts", [])}


PIPELINE = ContentPipeline()
