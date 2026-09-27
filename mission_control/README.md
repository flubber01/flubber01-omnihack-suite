# 🛰️ OMNIHACK // MISSION CONTROL

**Maxed-Out Agentic Swarm Mission Control Center & Automated Social Media Factory
with Live Remote Browser Streaming.**

A production-grade Gradio 6 command deck: cyberpunk/military dark UI, hierarchical
agent swarm, universal Ollama + HuggingFace engine, live remote browser with
click-to-steal coordinate injection, a 202-skill lab, embedded SSH terminal,
workflow builder with GitHub/Azure connectors, hardware hub and a global
emergency kill switch. Every external integration ships with a deterministic
simulated backend so the app runs natively with zero credentials.

## 🚀 Run

```bash
pip install -r requirements.txt
python run_mission_control.py          # → http://0.0.0.0:7860
OMNI_PORT=8080 python run_mission_control.py   # custom port
```

## 🗺️ Tabs

| Tab | Capability |
|-----|-----------|
| 🛸 Swarm Live Operations | Streaming multi-agent chatbox (broadcast or targeted), live ops matrix, halt/resume per agent, ping-all |
| 🤖 Hierarchical Agent Configurator | Commanders ➔ minions tree, fully editable system prompts, model binding, **Define AI's Job** intent compiler |
| ⚡ Ollama + HF Engine | `/api/tags` scanner, native pulls, **`hf.co/Org/Repo-GGUF` pulls**, local `.gguf` scan ➔ Modelfile builder, instant bind-to-agent |
| 🌐 LIVE BROWSER STREAM | Pillow-rendered stealth viewport @ N fps, click-capture overlay → coordinate injection, keyboard/scroll/goto, DOM dump, **Ollama vision/control bridge (inspect + autopilot)**, noVNC iframe fallback |
| 🎬 Content Automation & Planner | Wizard (script ➔ assets ➔ TTS ➔ FFmpeg render ➔ multi-platform distribute), one-click autopilot, cron-style planner |
| 📡 Social Connectors & Profiles | API/OAuth/webhook vaults for X, YouTube, TikTok, Spotify, Instagram, Facebook · multi-persona profile matrix · static/on-demand daemons |
| 🔬 Skill Lab | **202 stubbed skills** across 6 domains, fuzzy search, fuse/strip onto any agent, test-fire receipts |
| 💻 Direct SSH Terminal | paramiko interactive shell (blank host → local sandbox), quick-ops, streaming output |
| 🗺️ Workflow Builder | Node sequencer with live execution log, GitHub + Azure DevOps connectors, **config.json export/import** |
| 🔌 Hardware Hub | GPU rigs / edge cluster / NAS matrix, load & power telemetry, docker fleet control |
| 📊 System Logs | 2000-event ring buffer, level filtering, auto-refresh |

## ⛔ Fail-safes

* **EMERGENCY KILL SWITCH** (top bar) freezes every agent, browser task, render
  loop and workflow instantly; **RE-ARM** restores the swarm.
* SSH sandbox blocks destructive patterns; credentials are never persisted.

## 🧱 Architecture

```
mission_control/
├── app.py                 # Blocks assembly, timers, kill-switch wiring
├── core/                  # engines (state, swarm, ollama, browser, ssh,
│                          #          pipeline, skills, persistence, theme)
├── ui/                    # one module per tab (topbar + 10 tabs)
└── data/                  # runtime vaults: config.json, connectors.json,
                           # profiles.json (git-ignored)
```

All backend seams (`OllamaEngine`, `BrowserInstance`, `SSHBridge`,
`ContentPipeline`, `SKILL_REGISTRY`) are drop-in points: attach a real Ollama
daemon, Playwright/browser-use, or platform APIs and the UI keeps working
unchanged.
