"""Theme system :: neutral Gradio theme + CSS-variable driven skins.

Three switchable skins are layered on top of the structural CSS by
redefining the ``--nx-*`` custom properties at runtime (live, no reload):

* ``JARVIS``        — holographic Stark-HUD cyan/gold (default)
* ``CYBERPUNK``     — matrix green/magenta
* ``MILITARY OPS``  — olive/amber stencil console
"""

from __future__ import annotations

import gradio as gr

# ---------------------------------------------------------------------------
# Skin palettes (CSS custom properties)
# ---------------------------------------------------------------------------
SKINS: dict[str, dict[str, str]] = {
    "MILITARY OPS": {
        "--nx-bg": "#07080a",
        "--nx-bg2": "#0c0e08",
        "--nx-panel": "#0d1109",
        "--nx-panel2": "#131a0e",
        "--nx-grid": "#26301c",
        "--nx-accent": "#ffb300",
        "--nx-accent2": "#9acd32",
        "--nx-good": "#9acd32",
        "--nx-warn": "#ffb300",
        "--nx-danger": "#ff5533",
        "--nx-text": "#e8e6cf",
        "--nx-dim": "#7d7f66",
        "--nx-glow-a": "rgba(255, 179, 0, 0.5)",
        "--nx-glow-b": "rgba(154, 205, 50, 0.4)",
        "--nx-font": "'Share Tech Mono', 'JetBrains Mono', monospace",
    },
    "JARVIS": {
        "--nx-bg": "#020a12",
        "--nx-bg2": "#041220",
        "--nx-panel": "#061524",
        "--nx-panel2": "#0a1f33",
        "--nx-grid": "#0b2a3d",
        "--nx-accent": "#35d6ff",
        "--nx-accent2": "#ffd166",
        "--nx-good": "#4dffa6",
        "--nx-warn": "#ffb300",
        "--nx-danger": "#ff4d6d",
        "--nx-text": "#cdeeff",
        "--nx-dim": "#4f7d99",
        "--nx-glow-a": "rgba(53, 214, 255, 0.55)",
        "--nx-glow-b": "rgba(255, 209, 102, 0.45)",
        "--nx-font": "'Rajdhani', 'JetBrains Mono', monospace",
    },
    "CYBERPUNK": {
        "--nx-bg": "#03060b",
        "--nx-bg2": "#060d15",
        "--nx-panel": "#080f18",
        "--nx-panel2": "#0c1622",
        "--nx-grid": "#0e2233",
        "--nx-accent": "#00ff9f",
        "--nx-accent2": "#ff2bd6",
        "--nx-good": "#00ff9f",
        "--nx-warn": "#ffb300",
        "--nx-danger": "#ff3b5c",
        "--nx-text": "#c9ffe9",
        "--nx-dim": "#5d8aa8",
        "--nx-glow-a": "rgba(0, 255, 159, 0.55)",
        "--nx-glow-b": "rgba(255, 43, 214, 0.45)",
        "--nx-font": "'JetBrains Mono', monospace",
    },
}
SKIN_NAMES = list(SKINS.keys())
DEFAULT_SKIN = "MILITARY OPS"


def skin_vars(name: str) -> str:
    palette = SKINS.get(name, SKINS[DEFAULT_SKIN])
    return ":root { " + " ".join(f"{k}: {v};" for k, v in palette.items()) + " }"


def skin_style_block(name: str) -> str:
    """Full <style> payload swapped into the live skin holder."""
    return f"<style id='nx-skin'>{skin_vars(name)}</style>"


def build_theme() -> gr.Theme:
    """Neutral dark theme tuned for the MILITARY OPS default skin —
    skins layer the real personality on top via CSS variables."""
    theme = gr.themes.Base(
        primary_hue=gr.themes.colors.amber,
        secondary_hue=gr.themes.colors.lime,
        neutral_hue=gr.themes.colors.stone,
        font=gr.themes.GoogleFont("Share Tech Mono"),
        font_mono=gr.themes.GoogleFont("JetBrains Mono"),
    )
    variables = dict(
        body_background_fill="#07080a",
        body_text_color="#e8e6cf",
        block_background_fill="#0d1109",
        block_border_color="#26301c",
        block_border_width="1px",
        block_label_background_fill="linear-gradient(90deg, #0d1109 0%, #131a0e 100%)",
        block_label_text_color="#ffb300",
        block_title_text_color="#ffb300",
        block_shadow="0 0 18px rgba(255, 179, 0, 0.06)",
        button_primary_background_fill="linear-gradient(135deg, #7a5600 0%, #ffb300 140%)",
        button_primary_background_fill_hover="linear-gradient(135deg, #ffb300 0%, #ffd66b 120%)",
        button_primary_text_color="#1c1402",
        button_secondary_background_fill="linear-gradient(135deg, #131a0e 0%, #23301a 100%)",
        button_secondary_background_fill_hover="linear-gradient(135deg, #23301a 0%, #33452a 100%)",
        button_secondary_text_color="#d6e6b8",
        button_cancel_background_fill="linear-gradient(135deg, #5c1a06 0%, #ff5533 120%)",
        button_cancel_text_color="#ffe8e3",
        input_background_fill="#0c0e08",
        input_border_color="#26301c",
        input_border_color_focus="#ffb300",
        border_color_primary="#26301c",
        background_fill_primary="#07080a",
        background_fill_secondary="#0d1109",
        table_border_color="#26301c",
        table_even_background_fill="#0b0d08",
        table_odd_background_fill="#10140b",
        checkbox_background_color="#0c0e08",
        checkbox_background_color_selected="#7a5600",
        shadow_drop="0 0 22px rgba(255,179,0,0.10)",
    )
    for key, value in variables.items():
        try:
            theme.set(**{key: value})
        except (TypeError, KeyError):
            continue
    return theme


# ---------------------------------------------------------------------------
# Structural CSS — colors resolve from --nx-* variables (skin-swappable)
# ---------------------------------------------------------------------------
CSS = """
/* ====================== OMNIHACK STRUCTURAL SKIN ========================= */
@keyframes omni-scan { 0% { transform: translateY(-100%); } 100% { transform: translateY(100vh); } }
@keyframes omni-pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.35; } }
@keyframes omni-grid-shift { 0% { background-position: 0 0, 0 0; } 100% { background-position: 48px 48px, 48px 48px; } }
@keyframes omni-spin { 0% { transform: rotate(0deg);} 100% { transform: rotate(360deg);} }
@keyframes omni-flicker { 0%,97%,100% { opacity: 1; } 98% { opacity: 0.75; } }

.gradio-container {
  max-width: 1680px !important;
  font-family: var(--nx-font) !important;
  background:
    radial-gradient(ellipse at 18% -10%, var(--nx-glow-a) 0%, transparent 42%),
    radial-gradient(ellipse at 85% 112%, var(--nx-glow-b) 0%, transparent 45%),
    linear-gradient(var(--nx-grid) 1px, transparent 1px),
    linear-gradient(90deg, var(--nx-grid) 1px, transparent 1px),
    var(--nx-bg) !important;
  background-size: auto, auto, 48px 48px, 48px 48px, auto !important;
  animation: omni-grid-shift 26s linear infinite;
}
.gradio-container::before {
  content: ""; position: fixed; top: 0; left: 0; right: 0; height: 3px;
  background: linear-gradient(90deg, transparent, var(--nx-accent), transparent);
  opacity: 0.25; animation: omni-scan 7s linear infinite; pointer-events: none; z-index: 999;
}

/* ---------- header ---------- */
.omni-header {
  border: 1px solid var(--nx-grid);
  background: linear-gradient(180deg, var(--nx-panel) 0%, var(--nx-bg2) 100%);
  box-shadow: inset 0 0 42px var(--nx-glow-a), 0 0 24px var(--nx-glow-a);
  padding: 10px 18px 8px 18px;
  clip-path: polygon(0 0, calc(100% - 24px) 0, 100% 24px, 100% 100%, 24px 100%, 0 calc(100% - 24px));
  display: flex; align-items: center; gap: 16px;
}
.omni-header .core {
  width: 34px; height: 34px; border-radius: 50%;
  border: 2px solid var(--nx-accent);
  box-shadow: 0 0 14px var(--nx-glow-a), inset 0 0 10px var(--nx-glow-a);
  position: relative; flex: 0 0 auto;
}
.omni-header .core::after {
  content: ""; position: absolute; inset: 5px; border-radius: 50%;
  border: 1px dashed var(--nx-accent2); animation: omni-spin 9s linear infinite;
}
.omni-header h1 {
  font-size: 22px; letter-spacing: 5px; margin: 0; color: var(--nx-accent);
  text-shadow: 0 0 8px var(--nx-glow-a), 0 0 30px var(--nx-glow-a);
  animation: omni-flicker 6s infinite; flex: 1 1 auto;
}
.omni-header .sub { color: var(--nx-dim); font-size: 10px; letter-spacing: 2.5px; }

/* ---------- top status bar ---------- */
.omni-topbar {
  border: 1px solid var(--nx-grid);
  background: linear-gradient(90deg, var(--nx-panel) 0%, var(--nx-panel2) 55%, var(--nx-panel) 100%);
  padding: 6px 10px; display: flex; flex-wrap: wrap; gap: 6px; align-items: center;
  clip-path: polygon(12px 0, 100% 0, 100% calc(100% - 12px), calc(100% - 12px) 100%, 0 100%, 0 12px);
}
.metric-cell {
  border: 1px solid var(--nx-grid); background: rgba(4, 10, 16, 0.85);
  padding: 3px 10px; min-width: 104px; display: flex; flex-direction: column; gap: 1px;
}
.metric-cell .k { font-size: 8.5px; letter-spacing: 2px; color: var(--nx-dim); }
.metric-cell .v { font-size: 14px; font-weight: 700; color: var(--nx-accent);
  text-shadow: 0 0 8px var(--nx-glow-a); }
.metric-cell .v.green { color: var(--nx-good); text-shadow: 0 0 8px var(--nx-glow-a); }
.metric-cell .v.amber { color: var(--nx-warn); text-shadow: 0 0 8px var(--nx-glow-b); }
.metric-cell .v.red   { color: var(--nx-danger); text-shadow: 0 0 8px var(--nx-glow-b); }
.bar-track { height: 3px; background: var(--nx-bg2); margin-top: 2px; }
.bar-fill  { height: 100%; background: linear-gradient(90deg, var(--nx-accent), var(--nx-good));
  box-shadow: 0 0 6px var(--nx-glow-a); }

.led { display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:6px; }
.led-green   { background: var(--nx-good);   box-shadow: 0 0 8px var(--nx-good);   animation: omni-pulse 1.6s infinite; }
.led-cyan    { background: var(--nx-accent); box-shadow: 0 0 8px var(--nx-accent); animation: omni-pulse 2.1s infinite; }
.led-amber   { background: var(--nx-warn);   box-shadow: 0 0 8px var(--nx-warn);   animation: omni-pulse 1.2s infinite; }
.led-red     { background: var(--nx-danger); box-shadow: 0 0 8px var(--nx-danger); animation: omni-pulse 0.7s infinite; }

/* ---------- tabs ---------- */
.omni-tabs > .tab-nav, .omni-tabs .tab-nav {
  background: linear-gradient(180deg, var(--nx-bg2) 0%, var(--nx-bg) 100%) !important;
  border: 1px solid var(--nx-grid); border-bottom: 2px solid var(--nx-accent);
  padding: 4px 6px; gap: 4px; flex-wrap: wrap;
}
.omni-tabs button {
  border: 1px solid var(--nx-grid) !important;
  background: var(--nx-panel) !important; color: var(--nx-dim) !important;
  letter-spacing: 1px; font-size: 12px !important;
  clip-path: polygon(8px 0, 100% 0, 100% calc(100% - 8px), calc(100% - 8px) 100%, 0 100%, 0 8px);
}
.omni-tabs button.selected {
  color: var(--nx-accent) !important; border-color: var(--nx-accent) !important;
  box-shadow: 0 0 14px var(--nx-glow-a), inset 0 0 12px var(--nx-glow-a);
  text-shadow: 0 0 6px var(--nx-glow-a);
}

/* ---------- panels ---------- */
.cyber-panel > .block, .cyber-panel.block {
  border: 1px solid var(--nx-grid);
  background:
    linear-gradient(var(--nx-panel), var(--nx-panel)),
    linear-gradient(var(--nx-grid) 1px, transparent 1px),
    linear-gradient(90deg, var(--nx-grid) 1px, transparent 1px);
  background-size: auto, 26px 26px, 26px 26px;
}
.cyber-heading {
  color: var(--nx-accent); letter-spacing: 3px; font-size: 13px;
  text-shadow: 0 0 10px var(--nx-glow-a);
  border-left: 3px solid var(--nx-accent2); padding-left: 10px; margin: 4px 0 2px 0;
}
.cyber-sub { color: var(--nx-dim); font-size: 10.5px; letter-spacing: 1.5px; }

/* ---------- kill switch ---------- */
#btn-kill button {
  background: linear-gradient(135deg, #5c0618 0%, var(--nx-danger) 130%) !important;
  color: #fff !important; border: 1px solid var(--nx-danger) !important;
  box-shadow: 0 0 18px var(--nx-glow-b), inset 0 0 14px var(--nx-glow-b);
  letter-spacing: 3px; font-weight: 800; animation: omni-pulse 2.4s infinite;
}
#btn-resume button {
  background: linear-gradient(135deg, #05341f 0%, var(--nx-good) 130%) !important;
  color: #03130b !important; border: 1px solid var(--nx-good) !important;
  box-shadow: 0 0 18px var(--nx-glow-a); letter-spacing: 3px; font-weight: 800;
}

/* ---------- terminal ---------- */
.term-screen textarea, .term-screen pre, .term-screen code {
  background: #020608 !important; color: #7dffb9 !important;
  font-family: "JetBrains Mono", monospace !important; font-size: 12px !important;
  border: 1px solid #10352a !important; text-shadow: 0 0 4px rgba(0, 255, 159, 0.4);
}
.term-input textarea {
  background: #03090d !important; color: var(--nx-good) !important;
  border: 1px solid var(--nx-good) !important;
  box-shadow: inset 0 0 16px rgba(0, 255, 159, 0.08);
}

/* ---------- browser viewport ---------- */
.bv-wrap { position: relative; }
.bv-wrap > .bc-overlay-block {
  position: absolute; inset: 0; z-index: 40; padding: 0 !important; margin: 0 !important;
  border: none !important; background: transparent !important; box-shadow: none !important;
}
#browser-shot img { border: 1px solid var(--nx-grid); }
.stream-badge {
  position: absolute; top: 10px; right: 14px; z-index: 41; pointer-events: none;
  color: var(--nx-danger); font-size: 11px; letter-spacing: 3px;
  text-shadow: 0 0 8px var(--nx-glow-b); animation: omni-pulse 1.1s infinite;
}

/* ---------- misc ---------- */
.swarm-chatbot { height: 520px; }
.swarm-chatbot .message { border: 1px solid var(--nx-grid); }
.agent-tree pre, .agent-tree code {
  color: var(--nx-good) !important; background: #020608 !important;
  text-shadow: 0 0 4px rgba(0, 255, 159, 0.35);
}
.gradio-container table { font-size: 12px; }
.gradio-container ::-webkit-scrollbar { width: 8px; height: 8px; }
.gradio-container ::-webkit-scrollbar-track { background: var(--nx-bg2); }
.gradio-container ::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, var(--nx-accent), var(--nx-good)); border-radius: 0;
}
.footer-strip {
  color: var(--nx-dim); font-size: 10px; letter-spacing: 2px; text-align: center;
  border-top: 1px solid var(--nx-grid); padding-top: 6px; margin-top: 8px;
}
.gradio-container .block { border-radius: 2px; }
"""


def launch_css() -> str:
    """Structural CSS + default skin variables for launch()."""
    return skin_vars(DEFAULT_SKIN) + CSS
