"""Cyberpunk / military-grade Mission Control theme for Gradio.

Provides a custom ``gr.Theme`` plus a large CSS payload that injects:

* a dark matrix-grid backdrop with animated scanlines,
* neon corner-bracket panels,
* glowing tab navigation,
* LED status pulses, monospace terminal typography,
* styled buttons / tables / scrollbars.
"""

from __future__ import annotations

import gradio as gr

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------
NEON_GREEN = "#00ff9f"
NEON_CYAN = "#00e5ff"
NEON_MAGENTA = "#ff2bd6"
NEON_AMBER = "#ffb300"
NEON_RED = "#ff3b5c"
BG_DEEP = "#03060b"
BG_PANEL = "#080f18"
BG_PANEL_2 = "#0c1622"
GRID_LINE = "#0e2233"
TXT_MAIN = "#c9ffe9"
TXT_DIM = "#5d8aa8"

LED_CSS = {
    "green": "led-green",
    "cyan": "led-cyan",
    "amber": "led-amber",
    "red": "led-red",
    "magenta": "led-magenta",
}


def build_theme() -> gr.Theme:
    """Construct the neon-on-black Gradio theme object."""
    theme = gr.themes.Base(
        primary_hue=gr.themes.colors.emerald,
        secondary_hue=gr.themes.colors.cyan,
        neutral_hue=gr.themes.colors.slate,
        font=gr.themes.GoogleFont("JetBrains Mono"),
        font_mono=gr.themes.GoogleFont("JetBrains Mono"),
    )
    variables = dict(
        body_background_fill=BG_DEEP,
        body_text_color=TXT_MAIN,
        block_background_fill=BG_PANEL,
        block_border_color=GRID_LINE,
        block_border_width="1px",
        block_label_background_fill="linear-gradient(90deg, #071018 0%, #0b1a26 100%)",
        block_label_text_color=NEON_CYAN,
        block_title_text_color=NEON_CYAN,
        block_shadow="0 0 18px rgba(0, 229, 255, 0.06)",
        button_primary_background_fill="linear-gradient(135deg, #00c97b 0%, #00ff9f 100%)",
        button_primary_background_fill_hover="linear-gradient(135deg, #00ff9f 0%, #7dffd0 100%)",
        button_primary_text_color="#02120a",
        button_secondary_background_fill="linear-gradient(135deg, #073a4d 0%, #0a5a75 100%)",
        button_secondary_background_fill_hover="linear-gradient(135deg, #0a5a75 0%, #0e7ea6 100%)",
        button_secondary_text_color="#bdf3ff",
        button_cancel_background_fill="linear-gradient(135deg, #7a0f26 0%, #c11b3d 100%)",
        button_cancel_text_color="#ffe3ea",
        input_background_fill="#050c14",
        input_border_color=GRID_LINE,
        input_border_color_focus=NEON_CYAN,
        border_color_primary=GRID_LINE,
        background_fill_primary=BG_DEEP,
        background_fill_secondary=BG_PANEL,
        table_border_color=GRID_LINE,
        table_even_background_fill="#07111c",
        table_odd_background_fill="#0a1622",
        checkbox_background_color="#050c14",
        checkbox_background_color_selected="#00c97b",
        shadow_drop="0 0 22px rgba(0,229,255,0.10)",
    )
    # Apply defensively: variable names differ slightly between Gradio majors.
    for key, value in variables.items():
        try:
            theme.set(**{key: value})
        except (TypeError, KeyError):
            continue
    return theme


# ---------------------------------------------------------------------------
# Raw CSS payload
# ---------------------------------------------------------------------------
CSS = f"""
/* ===================== OMNIHACK MISSION CONTROL SKIN ===================== */
@keyframes omni-scan {{
  0%   {{ transform: translateY(-100%); }}
  100% {{ transform: translateY(100vh); }}
}}
@keyframes omni-pulse {{
  0%, 100% {{ opacity: 1; }}
  50%      {{ opacity: 0.35; }}
}}
@keyframes omni-grid-shift {{
  0%   {{ background-position: 0px 0px, 0px 0px; }}
  100% {{ background-position: 56px 56px, 56px 56px; }}
}}
@keyframes omni-flicker {{
  0%, 97%, 100% {{ opacity: 1; }}
  98%           {{ opacity: 0.72; }}
}}

.gradio-container {{
  max-width: 1680px !important;
  font-family: "JetBrains Mono", "Fira Code", monospace !important;
  background:
    radial-gradient(ellipse at 20% -10%, rgba(0, 229, 255, 0.08) 0%, transparent 55%),
    radial-gradient(ellipse at 85% 110%, rgba(255, 43, 214, 0.07) 0%, transparent 55%),
    linear-gradient(rgba(14, 34, 51, 0.55) 1px, transparent 1px),
    linear-gradient(90deg, rgba(14, 34, 51, 0.55) 1px, transparent 1px),
    {BG_DEEP} !important;
  background-size: auto, auto, 56px 56px, 56px 56px, auto !important;
  animation: omni-grid-shift 24s linear infinite;
}}
.gradio-container::before {{
  content: "";
  position: fixed; top: 0; left: 0; right: 0;
  height: 3px;
  background: linear-gradient(90deg, transparent, {NEON_CYAN}, transparent);
  opacity: 0.25;
  animation: omni-scan 7s linear infinite;
  pointer-events: none;
  z-index: 999;
}}

/* ---------- header ---------- */
.omni-header {{
  border: 1px solid {GRID_LINE};
  background: linear-gradient(180deg, #08111c 0%, #060c14 100%);
  box-shadow: inset 0 0 42px rgba(0, 229, 255, 0.05), 0 0 24px rgba(0, 229, 255, 0.08);
  padding: 14px 20px 10px 20px;
  clip-path: polygon(0 0, calc(100% - 26px) 0, 100% 26px, 100% 100%, 26px 100%, 0 calc(100% - 26px));
}}
.omni-header h1 {{
  font-size: 26px; letter-spacing: 6px; margin: 0;
  color: {NEON_GREEN};
  text-shadow: 0 0 8px rgba(0, 255, 159, 0.75), 0 0 34px rgba(0, 255, 159, 0.35);
  animation: omni-flicker 6s infinite;
}}
.omni-header .sub {{
  color: {TXT_DIM}; font-size: 11px; letter-spacing: 3px; margin-top: 4px;
}}

/* ---------- top status bar ---------- */
.omni-topbar {{
  border: 1px solid {GRID_LINE};
  background: linear-gradient(90deg, #071019 0%, #0a1826 55%, #071019 100%);
  padding: 10px 14px;
  display: flex; flex-wrap: wrap; gap: 10px; align-items: center;
  clip-path: polygon(14px 0, 100% 0, 100% calc(100% - 14px), calc(100% - 14px) 100%, 0 100%, 0 14px);
}}
.metric-cell {{
  border: 1px solid {GRID_LINE};
  background: rgba(5, 12, 20, 0.85);
  padding: 6px 12px;
  min-width: 128px;
  display: flex; flex-direction: column; gap: 2px;
}}
.metric-cell .k {{ font-size: 9px; letter-spacing: 2px; color: {TXT_DIM}; }}
.metric-cell .v {{ font-size: 15px; font-weight: 700; color: {NEON_CYAN};
  text-shadow: 0 0 8px rgba(0, 229, 255, 0.55); }}
.metric-cell .v.green {{ color: {NEON_GREEN}; text-shadow: 0 0 8px rgba(0,255,159,.55); }}
.metric-cell .v.amber {{ color: {NEON_AMBER}; text-shadow: 0 0 8px rgba(255,179,0,.55); }}
.metric-cell .v.red   {{ color: {NEON_RED};   text-shadow: 0 0 8px rgba(255,59,92,.55); }}
.bar-track {{ height: 4px; background: #0a1a28; margin-top: 3px; }}
.bar-fill  {{ height: 100%; background: linear-gradient(90deg, {NEON_CYAN}, {NEON_GREEN});
  box-shadow: 0 0 8px rgba(0,255,159,.7); }}

.led {{ display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:6px; }}
.led-green   {{ background:{NEON_GREEN}; box-shadow:0 0 8px {NEON_GREEN}; animation: omni-pulse 1.6s infinite; }}
.led-cyan    {{ background:{NEON_CYAN};  box-shadow:0 0 8px {NEON_CYAN};  animation: omni-pulse 2.1s infinite; }}
.led-amber   {{ background:{NEON_AMBER}; box-shadow:0 0 8px {NEON_AMBER}; animation: omni-pulse 1.2s infinite; }}
.led-red     {{ background:{NEON_RED};   box-shadow:0 0 8px {NEON_RED};   animation: omni-pulse 0.7s infinite; }}
.led-magenta {{ background:{NEON_MAGENTA}; box-shadow:0 0 8px {NEON_MAGENTA}; animation: omni-pulse 1.9s infinite; }}

/* ---------- tabs ---------- */
.omni-tabs > .tab-nav, .omni-tabs .tab-nav {{
  background: linear-gradient(180deg, #060d16 0%, #04090f 100%) !important;
  border: 1px solid {GRID_LINE};
  border-bottom: 2px solid {NEON_CYAN};
  padding: 6px 8px;
  gap: 6px;
  flex-wrap: wrap;
}}
.omni-tabs button {{
  border: 1px solid {GRID_LINE} !important;
  background: rgba(7, 17, 28, 0.9) !important;
  color: {TXT_DIM} !important;
  letter-spacing: 1px;
  font-size: 12px !important;
  clip-path: polygon(8px 0, 100% 0, 100% calc(100% - 8px), calc(100% - 8px) 100%, 0 100%, 0 8px);
}}
.omni-tabs button.selected {{
  color: {NEON_GREEN} !important;
  border-color: {NEON_GREEN} !important;
  background: rgba(0, 255, 159, 0.07) !important;
  box-shadow: 0 0 14px rgba(0, 255, 159, 0.25), inset 0 0 12px rgba(0, 255, 159, 0.08);
  text-shadow: 0 0 6px rgba(0, 255, 159, 0.8);
}}

/* ---------- panels ---------- */
.cyber-panel {{ position: relative; }}
.cyber-panel > .block, .cyber-panel.block {{
  border: 1px solid {GRID_LINE};
  background:
    linear-gradient(rgba(8, 15, 24, 0.94), rgba(8, 15, 24, 0.94)),
    linear-gradient(rgba(14,34,51,.4) 1px, transparent 1px),
    linear-gradient(90deg, rgba(14,34,51,.4) 1px, transparent 1px);
  background-size: auto, 28px 28px, 28px 28px;
}}
.cyber-heading {{
  color: {NEON_CYAN};
  letter-spacing: 4px;
  font-size: 13px;
  text-shadow: 0 0 10px rgba(0, 229, 255, 0.6);
  border-left: 3px solid {NEON_MAGENTA};
  padding-left: 10px;
  margin: 6px 0 2px 0;
}}
.cyber-sub {{
  color: {TXT_DIM}; font-size: 11px; letter-spacing: 1.5px;
}}

/* ---------- kill switch ---------- */
#btn-kill button {{
  background: linear-gradient(135deg, #5c0618 0%, #ff3b5c 130%) !important;
  color: #fff !important;
  border: 1px solid {NEON_RED} !important;
  box-shadow: 0 0 18px rgba(255, 59, 92, 0.45), inset 0 0 14px rgba(255, 59, 92, 0.25);
  letter-spacing: 3px;
  font-weight: 800;
  animation: omni-pulse 2.4s infinite;
}}
#btn-resume button {{
  background: linear-gradient(135deg, #05341f 0%, #00c97b 130%) !important;
  color: #eafff5 !important;
  border: 1px solid {NEON_GREEN} !important;
  box-shadow: 0 0 18px rgba(0, 255, 159, 0.35);
  letter-spacing: 3px;
  font-weight: 800;
}}

/* ---------- terminal ---------- */
.term-screen textarea, .term-screen pre, .term-screen code {{
  background: #020608 !important;
  color: #7dffb9 !important;
  font-family: "JetBrains Mono", monospace !important;
  font-size: 12px !important;
  border: 1px solid #10352a !important;
  text-shadow: 0 0 4px rgba(0, 255, 159, 0.4);
}}
.term-input textarea {{
  background: #03090d !important;
  color: {NEON_GREEN} !important;
  border: 1px solid {NEON_GREEN} !important;
  box-shadow: inset 0 0 16px rgba(0, 255, 159, 0.08);
}}

/* ---------- browser viewport ---------- */
.bv-wrap {{ position: relative; }}
.bv-wrap > .bc-overlay-block {{
  position: absolute; inset: 0; z-index: 40; padding: 0 !important; margin: 0 !important;
  border: none !important; background: transparent !important; box-shadow: none !important;
}}
#browser-shot img {{ image-rendering: auto; border: 1px solid {GRID_LINE}; }}
.stream-badge {{
  position: absolute; top: 10px; right: 14px; z-index: 41; pointer-events: none;
  color: {NEON_RED}; font-size: 11px; letter-spacing: 3px;
  text-shadow: 0 0 8px rgba(255, 59, 92, 0.9);
  animation: omni-pulse 1.1s infinite;
}}

/* ---------- misc widgets ---------- */
.swarm-chatbot {{ height: 560px; }}
.swarm-chatbot .message {{ border: 1px solid {GRID_LINE}; }}
.agent-tree pre, .agent-tree code {{
  color: {NEON_GREEN} !important; background: #020608 !important;
  text-shadow: 0 0 4px rgba(0, 255, 159, 0.35);
}}
.gradio-container table {{ font-size: 12px; }}
.gradio-container ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
.gradio-container ::-webkit-scrollbar-track {{ background: #050b12; }}
.gradio-container ::-webkit-scrollbar-thumb {{
  background: linear-gradient(180deg, {NEON_CYAN}, {NEON_GREEN});
  border-radius: 0;
}}
.footer-strip {{
  color: {TXT_DIM}; font-size: 10px; letter-spacing: 2px; text-align: center;
  border-top: 1px solid {GRID_LINE}; padding-top: 8px; margin-top: 10px;
}}
"""
