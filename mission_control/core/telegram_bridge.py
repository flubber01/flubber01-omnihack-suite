"""📱 TELEGRAM CONTROL BRIDGE :: operate the swarm from your phone.

Paste a BotFather token, hit ARM — the bridge validates the bot via
``getMe`` and starts a background long-polling loop.  Supported commands:

    /status                telemetry snapshot
    /agents                commander + minion roster
    /kill                  EMERGENCY KILL SWITCH
    /resume                re-arm the swarm
    /ping                  broadcast heartbeat
    /short <topic>         run the full content autopilot
    /say <AGENT> <msg>     direct-talk any agent
    /skin <JARVIS|CYBERPUNK|MILITARY OPS>   swap the HUD style
    /help                  command list

Works against the real Telegram Bot API when the VPS has egress; otherwise
it fails gracefully with a CRIT log line.
"""

from __future__ import annotations

import threading
from typing import Any, Dict, List, Optional

import requests

from . import swarm
from .pipeline import PIPELINE, PLATFORMS, TONES, VOICES
from .state import STATE

API = "https://api.telegram.org/bot{token}/{method}"
HELP_TEXT = (
    "🛰️ OMNIHACK TELEGRAM BRIDGE\n"
    "/status — telemetry\n/agents — roster\n/kill — kill switch\n"
    "/resume — re-arm\n/ping — heartbeat\n/short <topic> — content autopilot\n"
    "/say <AGENT> <msg> — talk to an agent\n/skin <name> — HUD style\n/help — this list"
)


class TelegramBridge:
    def __init__(self) -> None:
        self.token: str = ""
        self.allowed: List[str] = []
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self.offset: int = 0

    # ------------------------------------------------------------------ api
    def _call(self, method: str, **params: Any) -> Dict[str, Any]:
        url = API.format(token=self.token, method=method)
        r = requests.get(url, params=params, timeout=35)
        data = r.json()
        if not data.get("ok"):
            raise RuntimeError(data.get("description", method + " failed"))
        return data["result"]

    def _send(self, chat_id: int, text: str) -> None:
        try:
            self._call("sendMessage", chat_id=chat_id, text=text[:4000])
        except Exception as exc:
            STATE.log("WARN", "TELEGRAM", f"sendMessage failed :: {exc}")

    # ------------------------------------------------------------- lifecycle
    def start(self, token: str, allowed: str) -> str:
        token = (token or "").strip()
        if not token:
            return "❌ Paste your BotFather token first."
        self.token = token
        self.allowed = [c.strip() for c in (allowed or "").replace(";", ",").split(",") if c.strip()]
        try:
            me = self._call("getMe")
        except Exception as exc:
            STATE.telegram_cfg.update(running=False)
            STATE.log("CRIT", "TELEGRAM", f"getMe failed :: {exc}")
            return f"❌ Bot unreachable :: {exc}"
        STATE.telegram_cfg.update(token=token, allowed=allowed or "",
                                   running=True, bot_name=me.get("username", "?"))
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True,
                                         name="omni-telegram")
        self._thread.start()
        STATE.log("OK", "TELEGRAM", f"Bridge armed :: @{me.get('username')} "
                                     f"(allowed: {len(self.allowed) or 'everyone'}).")
        return (f"🟢 Bridge armed :: @{me.get('username')} · "
                f"chat whitelist: {', '.join(self.allowed) or 'OPEN'} · send /help to the bot.")

    def stop(self) -> str:
        self._stop.set()
        STATE.telegram_cfg["running"] = False
        STATE.log("INFO", "TELEGRAM", "Bridge disarmed.")
        return "⏹ Telegram bridge disarmed."

    @property
    def running(self) -> bool:
        return STATE.telegram_cfg.get("running", False) and not self._stop.is_set()

    # ------------------------------------------------------------------ loop
    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                updates = self._call("getUpdates", offset=self.offset + 1,
                                      timeout=25, allowed_updates='["message"]')
            except Exception:
                if self._stop.wait(5):
                    return
                continue
            for upd in updates:
                self.offset = max(self.offset, upd.get("update_id", 0))
                msg = upd.get("message") or {}
                text = (msg.get("text") or "").strip()
                chat = msg.get("chat", {})
                chat_id = chat.get("id")
                if not text or chat_id is None:
                    continue
                if self.allowed and str(chat_id) not in self.allowed \
                        and str(chat.get("username", "")) not in self.allowed:
                    self._send(chat_id, "⛔ Unauthorized — your chat id is not whitelisted.")
                    STATE.log("WARN", "TELEGRAM", f"Rejected chat {chat_id}.")
                    continue
                STATE.log("INFO", "TELEGRAM", f"cmd from {chat.get('username', chat_id)} :: {text[:60]}")
                try:
                    self._send(chat_id, self.handle(text))
                except Exception as exc:
                    self._send(chat_id, f"❌ Handler error :: {exc}")

    # --------------------------------------------------------------- handlers
    def handle(self, text: str) -> str:
        parts = text.split(maxsplit=2)
        cmd = parts[0].lower().split("@")[0]

        if cmd == "/help":
            return HELP_TEXT
        if cmd == "/status":
            m = STATE.metrics()
            return (f"📊 SWARM STATUS\nCPU {m['cpu']:.0f}% · RAM {m['ram_pct']:.0f}%\n"
                    f"Commanders {m['commanders_active']}/{m['commanders']} · "
                    f"Minions {m['minions_active']}/{m['minions']}\n"
                    f"Browsers {m['browser_instances']} · Renders {m['render_tasks']} · "
                    f"Pipelines {m['pipelines']}\n"
                    f"State: {'⛔ HALTED' if m['halted'] else '🟢 NOMINAL'} · up {m['uptime']}")
        if cmd == "/agents":
            lines = []
            for a in STATE.agents.values():
                mark = "👑" if a["tier"] == "commander" else "▸"
                lines.append(f"{mark} {a['name']} [{a['status']}] model={a['model']}")
            return "🤖 ROSTER\n" + "\n".join(lines) if lines else "Swarm empty."
        if cmd == "/kill":
            return STATE.halt_all("TELEGRAM KILL SWITCH")
        if cmd == "/resume":
            return STATE.resume_all()
        if cmd == "/ping":
            n = sum(1 for a in STATE.agents.values() if a["status"] != "HALTED")
            return f"📡 PING → {n} agents acknowledged."
        if cmd == "/skin":
            from .theme import SKIN_NAMES
            want = (parts[1].upper() if len(parts) > 1 else "")
            match = next((s for s in SKIN_NAMES if s.upper().startswith(want)), None)
            if not match:
                return f"Unknown skin. Options: {', '.join(SKIN_NAMES)}"
            STATE.skin = match
            return f"🎨 HUD skin switched → {match} (applies on next tab refresh)."
        if cmd == "/short":
            topic = text[len("/short"):].strip() or "untitled brief"
            res = PIPELINE.run_autopilot(topic, TONES[0], 45, PLATFORMS[:3],
                                          "ALEX-TECH", VOICES[0])
            posts = ", ".join(p["platform"] for p in res["posts"])
            return f"🎬 Autopilot done :: {res['job']['id']}\n→ {posts}"
        if cmd == "/say" and len(parts) >= 3:
            agent_name, message = parts[1].upper(), parts[2]
            agent = next((a for a in STATE.agents.values()
                          if a["name"] == agent_name), None)
            if not agent:
                return f"No agent named {agent_name}."
            return f"{agent['name']} ▸ " + swarm._agent_reply(agent, message)
        return HELP_TEXT


BRIDGE = TelegramBridge()
