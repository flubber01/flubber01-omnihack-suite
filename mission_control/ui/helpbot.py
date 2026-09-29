"""🤖 FLOATING HELP BOT :: site-style setup assistant (bottom-right)."""

from __future__ import annotations

import gradio as gr

from ..core.helpbot import WELCOME, chat
from . import visibility as vis

OPEN_BTN = """
<div id="hb-open"
     style="display:none;position:fixed;right:18px;bottom:18px;z-index:700;
            padding:10px 16px;cursor:pointer;user-select:none;
            border:1px solid var(--nx-accent);color:var(--nx-accent);
            background:rgba(5,10,8,0.92);letter-spacing:2px;font-size:13px;
            box-shadow:0 0 16px var(--nx-glow-a);
            clip-path:polygon(10px 0,100% 0,100% calc(100% - 10px),calc(100% - 10px) 100%,0 100%,0 10px);"
     onclick="var p=document.querySelector('.helpbot-float');
              if(p){p.style.display='';} this.style.display='none';">
  🤖 SETUP HELP
</div>
"""

CLOSE_JS = """
<div style="text-align:right;margin:-6px 0 -2px 0;">
  <span style="color:var(--nx-dim);font-size:10px;letter-spacing:2px;">OMNI SETUP ASSISTANT</span>
  <span style="cursor:pointer;margin-left:10px;color:var(--nx-accent);font-size:13px;"
        onclick="var p=document.querySelector('.helpbot-float');
                 var b=document.getElementById('hb-open');
                 if(p){p.style.display='none';} if(b){b.style.display='';}">✕ HIDE</span>
</div>
"""


def render() -> dict:
    with gr.Column(elem_classes="helpbot-float") as bot_col:
        gr.HTML(CLOSE_JS)
        bot = gr.Chatbot(
            value=[{"role": "assistant", "content": WELCOME,
                    "metadata": {"title": "🤖 OMNI SETUP ASSISTANT"}}],
            height=300, elem_classes="helpbot-chat",
            placeholder="Ask: telegram · ollama · video · agents …")
        box = gr.Textbox(placeholder="Frage zur Einrichtung… (z. B. 'telegram', 'next', 'topics')",
                          show_label=False, max_lines=2)

    gr.HTML(OPEN_BTN)

    def ask(history, text):
        return chat(history, text), ""

    box.submit(ask, inputs=[bot, box], outputs=[bot, box])

    vis.register("helpbot", bot_col, "Help Bot: floating setup assistant")
    return {"bot": bot, "box": box, "col": bot_col}
