# 🛰️ OMNIHACK // MISSION CONTROL v2.0

**Maxed-Out Agentic Swarm Mission Control Center & Automated Social Media Factory
with Live Remote Browser Streaming.**

Cyberpunk command deck on Gradio 6: hierarchical agent swarm, universal
Ollama + HuggingFace engine, live remote browser, 202-skill lab, embedded SSH
terminal, workflow builder with 10+ brand connectors, hardware hub, Telegram
remote control, 3 switchable HUD skins and a global emergency kill switch.
Every external integration ships with a deterministic simulated backend — the
app runs natively with zero credentials.

## 🚀 One-shot install (single bash command)

```bash
# inside a clone:
bash install.sh

# fully remote (clones the repo for you):
bash <(curl -fsSL https://raw.githubusercontent.com/flubber01/flubber01-omnihack-suite/arena/01a0e419-flubber01-omnihack-suite/install.sh)
```

Manual: `pip install -r requirements.txt && python run_mission_control.py`

## 🖥️ Multi-Screen Mode (2 monitors)

One server, three views — open two of them and drag one to your second display:

| URL | Screen | Content |
|-----|--------|---------|
| `/` | Full console | all tabs + settings |
| `/ops` | **Operator console** | swarm chat + agent terminal, live browser, content factory |
| `/wall` | **Monitor wall** | telemetry, ops matrix, log stream, hardware, browser peek (read-only) |

## 🗺️ Tabs (main console)

| Tab | Capability |
|-----|-----------|
| 🛸 Swarm Live Operations | streaming multi-agent chatbox, live ops matrix, **AGENT DIRECT TERMINAL** (`/help`, `/say`, `/status`, `/kill` …) |
| 🤖 Agent Configurator | commander➔minion tree, editable system prompts, model binding, **Define AI's Job** intent compiler |
| ⚡ Ollama + HF Engine | `/api/tags` scanner, **hf.co/Org/Repo-GGUF** pulls, local GGUF ➔ Modelfile, instant bind |
| 🌐 Live Browser Stream | stealth viewport, click-capture ➔ coordinate injection, DOM dump, **Ollama autopilot**, noVNC fallback |
| 🎬 Content Automation | wizard + **5 pre-configured pipeline presets**, one-click autopilot, planner |
| 📡 Social Connectors | X/YouTube/TikTok/Spotify/Instagram/Facebook vaults · **4 seeded personas** (ALEX/MIA/LEON/SARA) · daemons |
| 🔬 Skill Lab | 202 stubbed skills, fuzzy search, fuse/strip onto agents |
| 💻 SSH Terminal | paramiko shell (blank host → sandbox), quick-ops |
| 🗺️ Workflows & Connectors | node sequencer, GitHub + Azure, **n8n · Kaggle · Gmail · Slack · Discord · Notion · OpenAI · Zapier · HuggingFace · Stripe**, 4 shipped blueprint pipelines |
| 🔌 Hardware Hub | GPU/edge/NAS matrix, docker fleet, power telemetry |
| 📊 System Logs | 2000-event ring buffer, level filter |
| ⚙️ Settings & Config | **3 HUD skins**, **UI cleanup toggles** (hide unused controls), **Telegram bridge**, config.json export/import |

## 🎨 HUD skins (live-switchable)

* **MILITARY OPS** — olive/amber stencil console (default)
* **JARVIS** — holographic Stark HUD, cyan/gold
* **CYBERPUNK** — matrix green/magenta

## 📱 Telegram control

Settings ▸ Telegram: paste your **@BotFather** token, optionally whitelist
chat ids, hit ARM. Then from your phone:

```
/status  /agents  /kill  /resume  /ping
/short <topic>           → full content autopilot
/say <AGENT> <msg>       → direct-talk any agent
/skin <name>             → swap HUD style
```

## ⛔ Fail-safes

* **EMERGENCY KILL SWITCH** (top bar + `/kill` + Telegram `/kill`) freezes
  every agent, browser task, render loop and workflow instantly.
* SSH sandbox blocks destructive patterns; credentials are never persisted.

## 🧱 Architecture

```
mission_control/
├── app.py                  # FastAPI host: / + /ops + /wall (uvicorn)
├── core/                   # state, swarm, ollama, browser, ssh, pipeline,
│                           # skills, persistence, telegram_bridge, theme
├── ui/                     # topbar + 11 tabs + screens.py (multi-monitor)
└── data/                   # runtime vaults (git-ignored)
```
