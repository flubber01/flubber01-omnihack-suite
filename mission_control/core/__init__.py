"""Core engines for the OmniHack Mission Control suite.

Modules
-------
theme        Cyberpunk / military-grade Gradio theme + injected CSS.
state        Global SwarmState singleton, telemetry bus, metrics simulator.
skills       The 200+ skill registry (mock/stubbed executors).
ollama       Universal Ollama engine + native HuggingFace GGUF bridge.
browser      Remote browser simulator (screenshot stream, DOM, AI bridge).
ssh_terminal Paramiko SSH bridge with local-shell fallback.
pipeline     Content automation pipeline (script/assets/TTS/render/post).
swarm        Hierarchical agent swarm, role generation, multi-agent chat.
persistence  config.json export / import of the entire swarm state.
"""

__version__ = "1.0.0"
