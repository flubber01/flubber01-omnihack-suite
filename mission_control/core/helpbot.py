"""🤖 OMNI HELP BOT :: step-by-step setup guides inside a floating chat.

Rule-based assistant that walks the operator through every subsystem
(Ollama, HF models, Telegram, agents, browser, content factory, social
personas, SSH, workflows, skills, skins, multi-screen, install, kill
switch).  Type a keyword to open a guide, ``next`` to advance.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from .state import STATE

GUIDES: Dict[str, Dict[str, object]] = {
    "start": {
        "title": "🚀 QUICKSTART",
        "steps": [
            "Welcome, Operator. This console has 3 views: `/` (full), `/ops` "
            "(work screen), `/wall` (monitor wall) — perfect for 2 monitors.",
            "Step 1 — connect the brain: open **🤖 Agent Configurator ▸ ⚡ Ollama + HF "
            "Engine**, enter your Ollama URL (default `http://localhost:11434`) and hit "
            "CONNECT. No daemon? The SIMULATED ENGINE takes over automatically.",
            "Step 2 — talk to the swarm: go to **🛸 Swarm Live Operations**, type a "
            "directive into the chatbox or use the AGENT DIRECT TERMINAL (`/help`).",
            "Step 3 — make content: **🎬 Content Automation** ▸ pick a preset, then "
            "RUN FULL AUTOPILOT (script → render → post).",
            "Step 4 — arm socials: **📡 Social Connectors** ▸ save API keys, bind "
            "accounts to one of the 4 personas (ALEX/MIA/LEON/SARA). Done — you are operational.",
        ],
    },
    "ollama": {
        "title": "🧠 OLLAMA CONNECTION",
        "steps": [
            "Guide: connecting your local Ollama daemon.",
            "1. On your VPS run `ollama serve` (default port 11434).",
            "2. Here open **🤖 Agent Configurator ▸ ⚡ Ollama + HF Engine**.",
            "3. Enter the host (e.g. `http://localhost:11434`) → **CONNECT / SCAN "
            "/api/tags**. Live daemon = real model list, otherwise the simulated "
            "catalogue is served.",
            "4. Pull models: type a tag like `llama3.1:70b` → PULL MODEL.",
            "5. Bind any model to any agent in the **🔥 INSTANT MODEL BIND** panel.",
        ],
    },
    "hf": {
        "title": "🤗 HUGGINGFACE MODELS",
        "steps": [
            "Guide: running HuggingFace GGUF repos through Ollama.",
            "1. Open **⚡ Ollama + HF Engine** in the Agent Configurator.",
            "2. Paste an HF repo id, e.g. `QuantFactory/Mistral-7B-Instruct-v0.3-GGUF` "
            "(optionally a specific file name).",
            "3. Hit **PULL HUGGINGFACE MODEL** — it appears as `hf.co/…` tag.",
            "4. Or scan local weights: set `/home/models` → **SCAN FOR *.GGUF** → "
            "pick a path → **BUILD MODELFILE + REGISTER**.",
            "5. Bind the new model to any agent instantly via **⚡ BIND MODEL TO AGENT**.",
        ],
    },
    "telegram": {
        "title": "📱 TELEGRAM CONTROL",
        "steps": [
            "Guide: controlling the swarm from your phone.",
            "1. Message **@BotFather** on Telegram → `/newbot` → copy the token.",
            "2. Open **⚙️ Settings & Config ▸ 📱 TELEGRAM CONTROL**.",
            "3. Paste the token; optionally whitelist your chat id(s) comma-separated "
            "(blank = open).",
            "4. Hit **🟢 ARM BRIDGE** — the bridge validates via getMe and starts polling.",
            "5. Send the bot `/help` — available: /status /agents /kill /resume "
            "/short <topic> /say <AGENT> <msg> /skin.",
        ],
    },
    "agents": {
        "title": "🤖 AGENTS & SWARM",
        "steps": [
            "Guide: building your hierarchy.",
            "1. **🤖 Agent Configurator ▸ 🧬 AGENT IDENTITY** — select any agent to "
            "edit its SYSTEM PROMPT (identity, boundaries, quirks, rules).",
            "2. Spawn a COMMANDER (strategy layer) or a MINION (task worker under a "
            "commander) via the accordions.",
            "3. Lazy mode: open **🧠 DEFINE AI'S JOB**, describe the mission in plain "
            "language → the compiler spawns commander + minions with prompts & routines.",
            "4. Fuse capabilities in **🔬 Skill Lab** (202 skills).",
            "5. Chat with everyone in **🛸 Swarm Live Operations** — chatbox or terminal.",
        ],
    },
    "browser": {
        "title": "🌐 LIVE BROWSER",
        "steps": [
            "Guide: remote browser streaming.",
            "1. Open **🌐 LIVE BROWSER STREAM** → **START STREAM** (adjust FPS).",
            "2. Click directly on the viewport — coordinates are captured and injected "
            "remotely. Use ADDRESS BAR + GO to navigate.",
            "3. AI control: pick a vision model → **READ DOM + SCREENSHOT** → "
            "**AI AUTOPILOT INJECT** (the model clicks/types for you).",
            "4. Need a real desktop? Switch mode to **noVNC REPLICA**, point the URL at "
            "your VPS (`docker run -p 6080:6080 ghcr.io/browseruse/headful-vnc`).",
        ],
    },
    "content": {
        "title": "🎬 CONTENT FACTORY",
        "steps": [
            "Guide: automated shorts.",
            "1. Open **🎬 Content Automation**.",
            "2. Pick a **PRE-CONFIGURED PIPELINE** preset (Tech/Gaming/Market/…)"
            " — topic, tone, platforms and persona fill in automatically.",
            "3. **RUN FULL AUTOPILOT** = ideation → script → assets → TTS voiceover → "
            "FFmpeg render → cross-platform distribution.",
            "4. Schedule recurring posts in the **VIDEO/SHORT PLANNER** (datetime or cron).",
            "5. Watch the queue + stage of every job in the PRODUCTION QUEUE.",
        ],
    },
    "social": {
        "title": "📡 SOCIAL & PERSONAS",
        "steps": [
            "Guide: connectors + profile matrix.",
            "1. **📡 Social Connectors** ▸ choose platform → paste API key / secret / "
            "OAuth token / webhook → SAVE.",
            "2. 4 personas are pre-seeded: ALEX-TECH, MIA-GAMING, LEON-FINANCE, "
            "SARA-LIFESTYLE.",
            "3. Create your own persona, then BIND accounts per platform to it.",
            "4. Toggle the background DAEMON per persona: STATIC/ALWAYS-ON (cron loop) "
            "or ON-DEMAND.",
        ],
    },
    "ssh": {
        "title": "💻 SSH TERMINAL",
        "steps": [
            "Guide: controlling your VPS.",
            "1. Open **💻 SSH Terminal**.",
            "2. For your real VPS: enter host, port, user, password or paste the PEM "
            "key → CONNECT (paramiko).",
            "3. Leave the host blank to use the built-in LOCAL SANDBOX shell.",
            "4. Quick-op buttons cover uname/df/top/ports/docker. `exit` closes the session.",
        ],
    },
    "workflow": {
        "title": "🗺️ WORKFLOWS & CONNECTORS",
        "steps": [
            "Guide: automation chains.",
            "1. **🗺️ Workflows** ▸ load a pre-configured pipeline "
            "(auto-short-factory, github-trend-digest, kaggle-data-drop, "
            "social-crosspost-loop) or build your own from the NODE PALETTE.",
            "2. Add steps, reorder with ⬆⬇, then **EXECUTE WORKFLOW** (live log).",
            "3. Paste credentials for GitHub / Azure DevOps in their panels.",
            "4. Brand connectors: n8n, Kaggle, Gmail, Slack, Discord, Notion, OpenAI, "
            "Zapier, HuggingFace, Stripe — just paste the key → SAVE → TEST.",
        ],
    },
    "skills": {
        "title": "🔬 SKILL LAB",
        "steps": [
            "Guide: fusing capabilities.",
            "1. Open **🔬 Skill Lab** — 202 skills in 6 domains.",
            "2. Search (e.g. `ffmpeg`, `port`, `seo`) or filter by domain.",
            "3. Tick any number of skills → pick a TARGET AGENT → **FUSE**.",
            "4. FIRE TEST SHOT runs a simulated execution receipt.",
            "5. Strip skills again via the INSTALLED dropdown.",
        ],
    },
    "skin": {
        "title": "🎨 HUD SKINS",
        "steps": [
            "Guide: changing the look.",
            "1. Open **⚙️ Settings & Config ▸ 🎨 HUD SKIN**.",
            "2. Choose **MILITARY OPS** (standard), **JARVIS** or **CYBERPUNK** → "
            "applies instantly, all screens resync.",
            "3. From Telegram: `/skin jarvis` works too.",
        ],
    },
    "screens": {
        "title": "🖥️ MULTI-SCREEN",
        "steps": [
            "Guide: two monitors.",
            "1. This server exposes three views: `/`, `/ops`, `/wall`.",
            "2. Open `/ops` (work: chat + browser + content) in one browser window and "
            "drag it to monitor 2.",
            "3. Keep `/` or `/wall` (telemetry + logs) on monitor 1.",
            "4. Everything shares the same live state — no extra setup needed.",
        ],
    },
    "install": {
        "title": "📦 INSTALL ANYWHERE",
        "steps": [
            "Guide: one-line install on any VPS.",
            "Run this single command:\n\n```\ncurl -fsSL https://raw.githubusercontent.com/"
            "flubber01/flubber01-omnihack-suite/arena/01a0e419-flubber01-omnihack-suite/"
            "install.sh | bash\n```",
            "It clones the repo, creates a venv, installs dependencies and launches the "
            "console on port 7860. Use `OMNI_PORT=8080 curl … | bash` to change ports.",
        ],
    },
    "kill": {
        "title": "⛔ KILL SWITCH",
        "steps": [
            "Guide: emergency stop.",
            "1. Top bar → **⛔ EMERGENCY KILL SWITCH** freezes agents, browser tasks, "
            "renders and workflows instantly.",
            "2. Works from the terminal (`/kill`), Telegram (`/kill`) and `/wall` view.",
            "3. **✅ RE-ARM SWARM** restores everything.",
        ],
    },
}

KEYWORDS = {
    "start": ["start", "quickstart", "begin", "anfang", "los", "setup", "beginnen"],
    "ollama": ["ollama", "llm", "model", "modell", "daemon", "11434"],
    "hf": ["huggingface", "hf", "gguf", "mistral", "quant", "modelfile"],
    "telegram": ["telegram", "botfather", "handy", "phone", "bot token"],
    "agents": ["agent", "swarm", "commander", "minion", "prompt", "hirarchie",
                "hierarchy", "job", "spawn"],
    "browser": ["browser", "vnc", "stream", "viewport", "autopilot", "screenshot"],
    "content": ["content", "video", "short", "render", "autopilot", "tiktok",
                 "youtube", "reel", "pipeline", "preset"],
    "social": ["social", "persona", "profile", "connector", "instagram", "account",
                "daemon", "twitter"],
    "ssh": ["ssh", "terminal", "shell", "vps", "paramiko"],
    "workflow": ["workflow", "n8n", "kaggle", "gmail", "github", "azure",
                  "slack", "discord", "notion", "zapier", "stripe"],
    "skills": ["skill", "fähigkeit", "fuse", "labor", "lab"],
    "skin": ["skin", "style", "theme", "design", "aussehen", "jarvis",
              "cyberpunk", "military", "farbe"],
    "screens": ["screen", "monitor", "dual", "zweit", "second", "wall", "/ops"],
    "install": ["install", "installation", "deploy", "bash", "curl", "einzeiler"],
    "kill": ["kill", "notfall", "emergency", "stop", "halt"],
}

TOPIC_ALIASES = {num: topic for num, topic in enumerate(GUIDES, 1)}

WELCOME = (
    "🤖 **OMNI SETUP ASSISTANT** online.\n\n"
    "Ich führe dich Schritt für Schritt durch die Einrichtung — Ollama, "
    "HuggingFace-Modelle, Telegram, Agenten, Browser, Content-Fabrik, Socials, "
    "Workflows, Skins, Multi-Screen …\n\n"
    "Schreib einfach ein Stichwort (z. B. `telegram`, `ollama`, `video`) oder "
    "`topics` für die Liste. Mit `next` geht's im Guide weiter."
)


class HelpBot:
    def __init__(self) -> None:
        self.topic: Optional[str] = None
        self.step: int = 0

    # ------------------------------------------------------------------ utils
    def _menu(self) -> str:
        lines = ["**Verfügbare Guides:**", ""]
        for i, (topic, g) in enumerate(GUIDES.items(), 1):
            lines.append(f"`{i:02d}` **{topic}** — {g['title']}")
        lines.append("\nSchreib die Nummer oder ein Stichwort, `next` für den "
                     "nächsten Schritt.")
        return "\n".join(lines)

    def _step_text(self) -> str:
        g = GUIDES[self.topic]
        total = len(g["steps"])
        step = g["steps"][self.step]
        nav = ("➡️ Antworte `next` für Schritt "
               f"{self.step + 2}/{total}." if self.step < total - 1
               else "✅ Guide abgeschlossen. Schreib `topics` für weitere Themen.")
        return (f"{g['title']} — Schritt {self.step + 1}/{total}\n\n{step}\n\n{nav}")

    # ------------------------------------------------------------------ reply
    def reply(self, text: str) -> str:
        text = (text or "").strip()
        low = text.lower()

        if low in {"topics", "themen", "menu", "menü", "?", "help", "hilfe"}:
            return self._menu()
        if low in {"next", "weiter", "n", ">"}:
            if self.topic is None:
                return "Kein Guide aktiv. Schreib `topics` und wähle eines."
            if self.step < len(GUIDES[self.topic]["steps"]) - 1:
                self.step += 1
                STATE.log("DEBUG", "HELPBOT", f"guide '{self.topic}' → step {self.step + 1}")
                return self._step_text()
            return "✅ Dieser Guide ist schon fertig. `topics` zeigt alle Themen."
        if low in {"restart", "reset", "neu"}:
            self.topic, self.step = None, 0
            return WELCOME

        # numeric topic pick
        if low.isdigit():
            topic = TOPIC_ALIASES.get(int(low))
            if topic:
                self.topic, self.step = topic, 0
                STATE.log("INFO", "HELPBOT", f"guide opened :: {topic}")
                return self._step_text()

        # keyword match
        for topic, words in KEYWORDS.items():
            if any(w in low for w in words):
                self.topic, self.step = topic, 0
                STATE.log("INFO", "HELPBOT", f"guide opened :: {topic} (keyword match)")
                return self._step_text()

        return ("🤔 Das habe ich nicht zugeordnet. Schreib `topics` für alle Guides — "
                "oder versuche: `start`, `ollama`, `telegram`, `video`, `agents`.")


HELPBOT = HelpBot()


def chat(history: List[dict], text: str) -> List[dict]:
    """Gradio handler: append user msg + bot answer to messages history."""
    history = list(history or [])
    text = (text or "").strip()
    if not text:
        return history
    history.append({"role": "user", "content": text})
    history.append({"role": "assistant", "content": HELPBOT.reply(text),
                    "metadata": {"title": "🤖 OMNI SETUP ASSISTANT"}})
    return history
