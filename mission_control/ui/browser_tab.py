"""🌐 LIVE BROWSER STREAM :: screenshot stream + noVNC replica + AI bridge."""

from __future__ import annotations

import gradio as gr

from ..core import browser as br
from ..core.ollama import ENGINE
from ..core.state import STATE

CLICK_JS = """
<div id="bc-capture"
     style="position:absolute;inset:0;z-index:41;cursor:crosshair;"
     title="Click to inject remote pointer event"
     onclick="(function(ev){
        var r=ev.currentTarget.getBoundingClientRect();
        var x=Math.round((ev.clientX-r.left)/r.width*1024);
        var y=Math.round((ev.clientY-r.top)/r.height*640);
        function set(sel,val){var el=document.querySelector(sel);
          if(el){el.value=val; el.dispatchEvent(new Event('input',{bubbles:true}));}}
        set('#bc-x input', x); set('#bc-y input', y);
        var t=document.querySelector('#bc-clickinfo textarea');
        if(t){t.value='🎯 REMOTE CLICK CAPTURED ▸ x='+x+'  y='+y+'  (press INJECT)';
              t.dispatchEvent(new Event('input',{bubbles:true}));}
     })(event)"></div>
"""


# ----------------------------------------------------------------- streaming
def grab_frame():
    """Timer tick: refresh the stream while live, else skip."""
    if not STATE.browser_live or STATE.halted:
        return gr.skip()
    return br.screenshot()


def start_stream(fps):
    STATE.browser_live = True
    STATE.browser_fps = float(fps or 1.0)
    STATE.log("OK", "BROWSER", f"Screenshot stream ONLINE @ {STATE.browser_fps} fps.")
    return br.screenshot(), "🔴 STREAM LIVE — frames refreshing. Click the viewport to steer."


def stop_stream():
    STATE.browser_live = False
    STATE.log("INFO", "BROWSER", "Screenshot stream paused.")
    return br.screenshot(), "⏸️ Stream paused."


def go_url(url):
    msg = br.BROWSER.navigate(url)
    return br.screenshot(), msg, action_rows()


def inject_click(x, y):
    msg = br.BROWSER.click(x, y)
    return br.screenshot(), msg, action_rows(), ""


def send_keys(text):
    msg = br.BROWSER.type_text(text)
    return br.screenshot(), msg, action_rows()


def scroll_page(dy):
    msg = br.BROWSER.scroll_by(dy)
    return br.screenshot(), msg, action_rows()


def snapshot_now():
    return br.screenshot(), "📸 Manual frame captured."


# ----------------------------------------------------------------- AI bridge
def ai_inspect(model):
    return br.BROWSER.ai_inspect(model or "llava:13b-v1.6")


def ai_autopilot(model):
    results = br.BROWSER.ai_autopilot(model or "llava:13b-v1.6")
    return ("\n".join(results), br.screenshot(), action_rows(),
            br.BROWSER.dom_summary())


def dump_dom():
    return br.BROWSER.dom_summary()


def action_rows():
    return [[a["ts"], a["kind"].upper(), a["detail"]]
            for a in reversed(br.BROWSER.actions[-14:])] or [["—", "—", "no actions yet"]]


# ------------------------------------------------------------------- VNC mode
def load_vnc(url):
    url = (url or "http://localhost:6080/vnc.html?autoconnect=true").strip()
    STATE.log("INFO", "VNC", f"noVNC replica iframe targeted at {url}")
    return (f'<iframe src="{url}" style="width:100%;height:620px;border:1px solid #0e2233;'
            f'background:#05080d" title="noVNC replica"></iframe>'
            f'<div class="cyber-sub" style="margin-top:6px">If the frame is blank, start the '
            f'headful browser container on your VPS:<br>'
            f'<code>docker run -d -p 6080:6080 -p 5900:5900 ghcr.io/browseruse/headful-vnc</code>'
            f'</div>')


# -------------------------------------------------------------------- render
def render() -> dict:
    with gr.Row():
        gr.Markdown("## 🌐 LIVE BROWSER STREAM & REPLICA WINDOW\n"
                    "<span class='cyber-sub'>CONTROL A REMOTE BROWSER FROM ANYWHERE · "
                    "SCREENSHOT STREAM ⇄ noVNC FALLBACK · OLLAMA CONTROL BRIDGE</span>")

    mode = gr.Radio(["📷 SCREENSHOT STREAM (Playwright/browser-use)",
                     "🖥️ EMBEDDED noVNC REPLICA (Docker/Xvfb)"],
                     value="📷 SCREENSHOT STREAM (Playwright/browser-use)",
                     label="STREAM MODE")

    with gr.Row():
        # ---------------------------------------------------------- viewport
        with gr.Column(scale=7):
            with gr.Column(elem_classes="bv-wrap"):
                shot = gr.Image(value=br.screenshot(), type="pil", label="REMOTE VIEWPORT",
                                 height=470,
                                 elem_id="browser-shot", interactive=False)
                gr.HTML(CLICK_JS, elem_classes="bc-overlay-block")
                gr.HTML('<div class="stream-badge">● REC</div>')
            click_info = gr.Textbox(elem_id="bc-clickinfo", interactive=False,
                                     value="🎯 Click anywhere on the viewport to capture coords.",
                                     label="COORD CAPTURE")
            with gr.Row():
                click_x = gr.Number(value=512, label="X", precision=0, elem_id="bc-x", scale=1)
                click_y = gr.Number(value=320, label="Y", precision=0, elem_id="bc-y", scale=1)
                click_btn = gr.Button("🖱️ INJECT CLICK", variant="primary", scale=2)
                keys_txt = gr.Textbox(label="KEYBOARD INJECT", placeholder="type into focused field…",
                                       scale=3)
                keys_btn = gr.Button("⌨️ SEND", variant="secondary", scale=1)
            with gr.Row():
                url_box = gr.Textbox(value=br.BROWSER.url, label="ADDRESS BAR", scale=5)
                go_btn = gr.Button("🌐 GO", variant="primary", scale=1)
                snap_btn = gr.Button("📸 FRAME", variant="secondary", scale=1)
            with gr.Row():
                scroll_dd = gr.Slider(-600, 600, value=240, step=20, label="SCROLL Δy (px)")
                scroll_btn = gr.Button("📜 SCROLL", variant="secondary")
                fps = gr.Slider(0.2, 5.0, value=1.0, step=0.2, label="STREAM FPS")
                start_btn = gr.Button("🔴 START STREAM", variant="primary")
                stop_btn = gr.Button("⏸ PAUSE", variant="stop")
            stream_msg = gr.Markdown("🟢 Remote browser attached :: stealth profile ACTIVE.")
            # VNC fallback pane (hidden until mode switched)
            vnc_url = gr.Textbox(value="http://localhost:6080/vnc.html?autoconnect=true",
                                  label="noVNC / VNC WEB URL", visible=True)
            vnc_btn = gr.Button("🖥️ LOAD noVNC REPLICA", variant="secondary")
            vnc_html = gr.HTML("")

        # ---------------------------------------------------------- AI bridge
        with gr.Column(scale=5):
            gr.Markdown("#### 🧿 OLLAMA BROWSER CONTROL BRIDGE")
            ai_model = gr.Dropdown(ENGINE.all_model_names(),
                                    value=("llava:13b-v1.6"
                                           if "llava:13b-v1.6" in ENGINE.all_model_names()
                                           else ENGINE.all_model_names()[0]),
                                    label="Vision/Control Model", allow_custom_value=True)
            with gr.Row():
                inspect_btn = gr.Button("👁️ READ DOM + SCREENSHOT", variant="secondary")
                autopilot_btn = gr.Button("🤖 AI AUTOPILOT INJECT", variant="primary")
            ai_plan = gr.Markdown("", elem_classes="cyber-panel")
            gr.Markdown("#### 🧾 LIVE DOM SNAPSHOT")
            dom_btn = gr.Button("🌳 DUMP DOM", variant="secondary")
            dom_box = gr.Code(value=br.BROWSER.dom_summary, language=None,
                               lines=14, label="DOM TREE", elem_classes="term-screen")
            gr.Markdown("#### 🕹️ ACTION LOG")
            action_table = gr.Dataframe(value=action_rows, headers=["TS", "EVENT", "DETAIL"],
                                          interactive=False, max_height=170)

    # --------------------------------------------------------------- wiring
    timer = gr.Timer(1.0)
    timer.tick(grab_frame, outputs=[shot])

    mode.change(lambda m: (gr.update(visible=("noVNC" in m)),
                            gr.update(visible=("noVNC" not in m)),
                            gr.update(visible=("noVNC" not in m))),
                inputs=[mode], outputs=[vnc_html, shot, click_info])
    start_btn.click(start_stream, inputs=[fps], outputs=[shot, stream_msg])
    stop_btn.click(stop_stream, outputs=[shot, stream_msg])
    go_btn.click(go_url, inputs=[url_box], outputs=[shot, stream_msg, action_table])
    url_box.submit(go_url, inputs=[url_box], outputs=[shot, stream_msg, action_table])
    click_btn.click(inject_click, inputs=[click_x, click_y],
                    outputs=[shot, stream_msg, action_table, click_info])
    keys_btn.click(send_keys, inputs=[keys_txt], outputs=[shot, stream_msg, action_table])
    keys_txt.submit(send_keys, inputs=[keys_txt], outputs=[shot, stream_msg, action_table])
    scroll_btn.click(scroll_page, inputs=[scroll_dd], outputs=[shot, stream_msg, action_table])
    snap_btn.click(snapshot_now, outputs=[shot, stream_msg])
    vnc_btn.click(load_vnc, inputs=[vnc_url], outputs=[vnc_html])
    inspect_btn.click(ai_inspect, inputs=[ai_model], outputs=[ai_plan])
    autopilot_btn.click(ai_autopilot, inputs=[ai_model],
                        outputs=[ai_plan, shot, action_table, dom_box])
    dom_btn.click(dump_dom, outputs=[dom_box])

    return {"shot": shot, "timer": timer}
