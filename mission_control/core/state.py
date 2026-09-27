"""Global swarm state, telemetry bus and VPS metrics simulation.

Everything lives inside a single process-wide ``SwarmState`` singleton so
that every Gradio tab operates on the same live mission data.  External
systems (Ollama, social APIs, cloud pipelines...) are stubbed with
deterministic simulated data so the app always runs natively.
"""

from __future__ import annotations

import itertools
import random
import threading
import time
import uuid
from collections import deque
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:  # real host metrics when available, simulated otherwise
    import psutil
    _HAVE_PSUTIL = True
except Exception:  # pragma: no cover
    psutil = None
    _HAVE_PSUTIL = False

# ---------------------------------------------------------------------------
LOG_LEVELS = ("TRACE", "DEBUG", "INFO", "OK", "WARN", "CRIT")
LEVEL_COLORS = {
    "TRACE": "#5d8aa8",
    "DEBUG": "#00e5ff",
    "INFO": "#9adcff",
    "OK": "#00ff9f",
    "WARN": "#ffb300",
    "CRIT": "#ff3b5c",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def uid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


class TelemetryBus:
    """Ring buffer of structured mission logs."""

    def __init__(self, maxlen: int = 2000) -> None:
        self._buf: deque = deque(maxlen=maxlen)
        self._lock = threading.Lock()
        self._seq = itertools.count(1)

    def push(self, level: str, source: str, message: str) -> Dict[str, Any]:
        entry = {
            "seq": next(self._seq),
            "ts": now_iso(),
            "level": level.upper(),
            "source": source,
            "message": message,
        }
        with self._lock:
            self._buf.append(entry)
        return entry

    def tail(self, n: int = 60, level: str = "ALL") -> List[Dict[str, Any]]:
        with self._lock:
            items = list(self._buf)
        if level and level != "ALL":
            items = [e for e in items if e["level"] == level]
        return items[-n:]

    def rows(self, n: int = 120, level: str = "ALL") -> List[List[str]]:
        return [[e["ts"], e["level"], e["source"], e["message"]]
                for e in reversed(self.tail(n, level))]

    def clear(self) -> None:
        with self._lock:
            self._buf.clear()


class SwarmState:
    """Process-wide mission state shared across all tabs."""

    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.bus = TelemetryBus()

        # mission flags -----------------------------------------------------
        self.halted: bool = False
        self.halt_reason: str = ""
        self.boot_ts: float = time.time()

        # swarm --------------------------------------------------------------
        # id -> agent dict (see swarm.make_agent)
        self.agents: Dict[str, Dict[str, Any]] = {}

        # ollama / model engine ----------------------------------------------
        self.ollama_url: str = "http://localhost:11434"
        self.ollama_connected: bool = False
        self.models: List[Dict[str, Any]] = []          # tags from /api/tags
        self.hf_models: List[Dict[str, Any]] = []       # hf.co pulls
        self.local_gguf: List[Dict[str, Any]] = []      # scanned GGUF files

        # browser ------------------------------------------------------------
        self.browser_live: bool = False
        self.browser_fps: float = 1.0
        self.browser_actions: List[Dict[str, Any]] = []

        # content pipeline ----------------------------------------------------
        self.render_tasks: Dict[str, Dict[str, Any]] = {}
        self.content_queue: List[Dict[str, Any]] = []
        self.schedule: List[Dict[str, Any]] = []

        # social ---------------------------------------------------------------
        self.connectors: Dict[str, Dict[str, str]] = {}
        self.profiles: Dict[str, Dict[str, Any]] = {}
        self.daemons: Dict[str, Dict[str, Any]] = {}

        # workflows / integrations ----------------------------------------------
        self.workflows: Dict[str, Dict[str, Any]] = {}
        self.github_cfg: Dict[str, str] = {}
        self.azure_cfg: Dict[str, str] = {}
        self.brand_connectors: Dict[str, Dict[str, str]] = {}
        self.telegram_cfg: Dict[str, Any] = {"token": "", "allowed": "",
                                              "running": False, "bot_name": ""}
        self.pipeline_runs: List[Dict[str, Any]] = []

        # UI configuration ------------------------------------------------------
        self.skin: str = "JARVIS"
        self.ui_flags: Dict[str, bool] = {}

        # hardware ----------------------------------------------------------------
        self.hardware: Dict[str, Dict[str, Any]] = {}
        self.docker_containers: List[Dict[str, Any]] = []

        # ssh -------------------------------------------------------------------------
        self.ssh_mode: Optional[str] = None
        self.ssh_banner: str = "NO ACTIVE SHELL SESSION"

        # simulated activity counters ---------------------------------------------------
        self._rnd = random.Random(2077)
        self.packets = itertools.count(1)

    # ------------------------------------------------------------------ utils
    def log(self, level: str, source: str, message: str) -> Dict[str, Any]:
        return self.bus.push(level, source, message)

    def uptime(self) -> str:
        s = int(time.time() - self.boot_ts)
        h, rem = divmod(s, 3600)
        m, sec = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{sec:02d}"

    # ------------------------------------------------------------- kill switch
    def halt_all(self, reason: str = "OPERATOR KILL SWITCH") -> str:
        with self.lock:
            self.halted = True
            self.halt_reason = reason
            for agent in self.agents.values():
                agent["status"] = "HALTED"
            self.browser_live = False
            for task in self.render_tasks.values():
                task["status"] = "ABORTED"
            for d in self.daemons.values():
                d["status"] = "HALTED"
        self.log("CRIT", "KILL-SWITCH", f"EMERGENCY HALT ENGAGED :: {reason}")
        return (f"⛔ KILL SWITCH ENGAGED — {reason}. All commanders, minions, browser "
                f"tasks, render loops and workflows have been frozen.")

    def resume_all(self) -> str:
        with self.lock:
            self.halted = False
            self.halt_reason = ""
            for agent in self.agents.values():
                agent["status"] = "IDLE"
            for task in self.render_tasks.values():
                if task["status"] == "ABORTED":
                    task["status"] = "QUEUED"
        self.log("OK", "KILL-SWITCH", "Swarm re-armed. All systems nominal.")
        return "✅ SWARM RE-ARMED — agents restored to IDLE, render queue thawed."

    # ------------------------------------------------------------------ metrics
    def metrics(self) -> Dict[str, Any]:
        if _HAVE_PSUTIL:
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory()
            ram_used_gb = mem.used / (1024 ** 3)
            ram_total_gb = mem.total / (1024 ** 3)
            ram_pct = mem.percent
        else:  # simulated fallback
            cpu = 22.0 + 18.0 * abs(self._rnd.random() - 0.5) * 2
            ram_pct = 41.0 + 9.0 * self._rnd.random()
            ram_total_gb, ram_used_gb = 32.0, 32.0 * ram_pct / 100.0

        commanders = [a for a in self.agents.values() if a["tier"] == "commander"]
        minions = [a for a in self.agents.values() if a["tier"] == "minion"]
        active_cmd = sum(1 for a in commanders if a["status"] not in ("HALTED",))
        active_min = sum(1 for a in minions if a["status"] not in ("HALTED",))
        browser_instances = 1 if self.browser_live else 0
        browser_instances += sum(1 for a in self.agents.values()
                                 if a.get("browser_task"))
        render_tasks = sum(1 for t in self.render_tasks.values()
                           if t["status"] in ("RENDERING", "QUEUED"))
        pipelines = (sum(1 for d in self.daemons.values() if d["status"] == "RUNNING")
                     + sum(1 for w in self.workflows.values() if w.get("running"))
                     + len([r for r in self.pipeline_runs if r["status"] == "RUNNING"]))
        return {
            "cpu": cpu,
            "ram_pct": ram_pct,
            "ram_used_gb": ram_used_gb,
            "ram_total_gb": ram_total_gb,
            "commanders": len(commanders),
            "commanders_active": active_cmd,
            "minions": len(minions),
            "minions_active": active_min,
            "browser_instances": browser_instances,
            "render_tasks": render_tasks,
            "pipelines": pipelines,
            "uptime": self.uptime(),
            "halted": self.halted,
        }


STATE = SwarmState()


def seed_static_data() -> None:
    """Populate hardware, docker, personas + preset pipelines once at boot."""
    if STATE.hardware:
        return
    STATE.hardware = {
        "GPU-RIG-01": {"kind": "GPU RIG", "chip": "8x A100 80GB", "status": "ONLINE",
                        "load": 63, "temp": 58, "power_w": 2900},
        "GPU-RIG-02": {"kind": "GPU RIG", "chip": "4x RTX 6000", "status": "ONLINE",
                        "load": 22, "temp": 49, "power_w": 1400},
        "RPI-SWARM": {"kind": "EDGE CLUSTER", "chip": "12x RP5 nodes", "status": "ONLINE",
                       "load": 41, "temp": 44, "power_w": 96},
        "FPGA-FARM": {"kind": "ACCELERATOR", "chip": "6x U250", "status": "STANDBY",
                       "load": 0, "temp": 37, "power_w": 210},
        "NAS-VAULT": {"kind": "STORAGE", "chip": "180TB ZFS", "status": "ONLINE",
                       "load": 12, "temp": 35, "power_w": 320},
        "5G-RELAY": {"kind": "UPLINK", "chip": "mmWave 8Gb/s", "status": "ONLINE",
                      "load": 77, "temp": 41, "power_w": 45},
    }
    STATE.docker_containers = [
        {"name": "omni-ollama", "image": "ollama/ollama:latest", "status": "running", "cpu": "38%", "mem": "21.4G"},
        {"name": "omni-browser-vnc", "image": "browseruse/headful:2.4", "status": "running", "cpu": "12%", "mem": "3.1G"},
        {"name": "omni-render-farm", "image": "omnihack/ffmpeg-farm:1.9", "status": "running", "cpu": "84%", "mem": "9.8G"},
        {"name": "omni-cron-daemon", "image": "omnihack/profile-daemon:2.0", "status": "running", "cpu": "2%", "mem": "412M"},
        {"name": "omni-novnc", "image": "thegeeklab/novnc:latest", "status": "running", "cpu": "1%", "mem": "96M"},
        {"name": "omni-vector-db", "image": "qdrant/qdrant:v1.14", "status": "exited", "cpu": "0%", "mem": "0B"},
    ]
    STATE.log("INFO", "HARDWARE-HUB", "Hardware matrix initialised :: 6 devices, 6 containers registered.")
    _seed_personas()
    _seed_preset_workflows()


def _seed_personas() -> None:
    """Four static social personas (placeholder accounts for 4 users)."""
    personas = {
        "ALEX-TECH": {
            "mode": "STATIC / ALWAYS-ON", "desc": "Tech Guru — AI news, tool reviews.",
            "accounts": {"Twitter (X)": "@alex_tech_daily", "YouTube": "AlexTechLabs",
                          "TikTok": "@alex.tech", "Instagram": "@alex_tech_daily",
                          "GitHub": "alex-tech"},
        },
        "MIA-GAMING": {
            "mode": "STATIC / ALWAYS-ON", "desc": "Gaming — highlights, clips, memes.",
            "accounts": {"YouTube": "MiaPlaysHQ", "TikTok": "@mia.clips",
                          "Instagram": "@mia_plays", "Facebook": "MiaPlaysHQ"},
        },
        "LEON-FINANCE": {
            "mode": "ON-DEMAND", "desc": "Finance — market briefs, data viz.",
            "accounts": {"Twitter (X)": "@leon_macro", "YouTube": "LeonMacro",
                          "LinkedIn": "leon-macro"},
        },
        "SARA-LIFESTYLE": {
            "mode": "ON-DEMAND", "desc": "Lifestyle — vlogs, aesthetic reels.",
            "accounts": {"Instagram": "@sara.vibes", "TikTok": "@sara.vibes",
                          "Spotify": "sara-curates", "Pinterest": "saravibes"},
        },
    }
    for name, cfg in personas.items():
        STATE.profiles.setdefault(name, cfg)
    STATE.log("INFO", "PROFILES", "Seeded 4 static personas :: ALEX / MIA / LEON / SARA.")


def _seed_preset_workflows() -> None:
    """Pre-configured content-automation + integration pipelines."""
    presets = {
        "auto-short-factory": {
            "steps": ["🧠 Run Commander Review :: brief=topic-of-day",
                       "🎬 Render Short Video :: profile=ALEX-TECH 9:16",
                       "📸 Post via Instagram Connector :: persona=ALEX-TECH",
                       "🎥 Post via YouTube Connector :: persona=ALEX-TECH",
                       "🎵 Post via TikTok Connector :: persona=ALEX-TECH",
                       "🗄️ Persist Artifacts to NAS :: path=/render/shorts"],
            "running": False,
        },
        "github-trend-digest": {
            "steps": ["🐙 Fetch GitHub Repo :: repo=trending",
                       "🕷️ Spawn Underclass Scraper :: depth=2",
                       "✉️ Publish via Gmail Connector :: digest=true",
                       "🔀 Relay to n8n :: webhook=trend-digest"],
            "running": False,
        },
        "kaggle-data-drop": {
            "steps": ["📊 Kaggle Dataset Pull :: dataset=daily-metrics",
                       "🧮 Run Skill Lab Capability Check :: domain=Data Science",
                       "🎬 Render Short Video :: chart-visualisation",
                       "📨 Send Slack/Discord Alert :: channel=#data"],
            "running": False,
        },
        "social-crosspost-loop": {
            "steps": ["🌐 Execute Browser-Use Task :: login=stored-cookies",
                       "📸 Post via Instagram Connector :: persona=SARA-LIFESTYLE",
                       "🎵 Post via TikTok Connector :: persona=MIA-GAMING",
                       "🎥 Post via YouTube Connector :: persona=ALEX-TECH",
                       "☁️ Trigger Azure Pipeline :: notify=ops"],
            "running": False,
        },
    }
    for name, cfg in presets.items():
        STATE.workflows.setdefault(name, cfg)
    STATE.log("INFO", "WORKFLOW", f"Pre-configured {len(presets)} pipelines.")
