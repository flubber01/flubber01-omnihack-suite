"""💻 DIRECT SSH TERMINAL :: embedded PuTTY-style shell over paramiko."""

from __future__ import annotations

import gradio as gr

from ..core.ssh_terminal import SSH
from ..core.state import STATE


def connect(host, port, user, password, key):
    ok, banner = SSH.connect(host, int(port or 22), user, password, key)
    status = "🟢 CONNECTED" if ok else "🔴 FAILED"
    return banner, f"{status} :: {STATE.ssh_banner}"


def disconnect():
    SSH.close()
    return "\n[session closed]\n$ ", "⚫ DISCONNECTED :: NO ACTIVE SHELL SESSION"


def submit_command(screen, cmd):
    if not (cmd or "").strip():
        return gr.skip(), ""
    if not SSH.mode:
        return ((screen or "") +
                "\n[!] No shell session — CONNECT first (blank host = local sandbox).\n$ "), ""
    result = SSH.execute(cmd)
    fragment = result.rstrip()
    if not fragment.endswith("$"):
        fragment += "\n$ "
    return f"{screen or ''}\n$ {cmd}\n{fragment}", ""


def clear_screen():
    return "[screen cleared]\n$ "


# ------------------------------------------------------------------ render
def render() -> dict:
    with gr.Row():
        gr.Markdown("## 💻 DIRECT SSH TERMINAL\n"
                    "<span class='cyber-sub'>PARAMIKO SECURE SHELL · STREAMING STDOUT/STDERR · "
                    "BLANK HOST → LOCAL SANDBOX MODE</span>")
    with gr.Row():
        with gr.Column(scale=3):
            gr.Markdown("#### 🔐 CONNECTION")
            host = gr.Textbox(label="HOST IP",
                               placeholder="203.0.113.10 (blank = local sandbox)")
            with gr.Row():
                port = gr.Number(label="PORT", value=22, precision=0)
                user = gr.Textbox(label="USERNAME", value="root")
            password = gr.Textbox(label="PASSWORD", type="password")
            key = gr.Textbox(label="PRIVATE KEY (paste PEM, optional)",
                              lines=3, max_lines=6)
            with gr.Row():
                conn_btn = gr.Button("🔌 CONNECT", variant="primary")
                disc_btn = gr.Button("✂ DISCONNECT", variant="stop")
            conn_status = gr.Markdown("⚫ NO ACTIVE SHELL SESSION")
            gr.Markdown(
                "<span class='cyber-sub'>Security note: credentials are used for the "
                "paramiko handshake only and are never persisted to disk.</span>")
        with gr.Column(scale=9):
            screen = gr.Code(language="shell", lines=22, label="SHELL OUTPUT",
                              value="[awaiting connection…]\n$ ",
                              elem_classes="term-screen")
            with gr.Row():
                cmd = gr.Textbox(label="COMMAND",
                                  placeholder="type a command and hit ENTER",
                                  scale=7, elem_classes="term-input")
                run_btn = gr.Button("⏎ EXECUTE", variant="primary", scale=1)
            with gr.Row():
                q1 = gr.Button("uname -a", size="sm")
                q2 = gr.Button("df -h", size="sm")
                q3 = gr.Button("top snapshot", size="sm")
                q4 = gr.Button("listening ports", size="sm")
                q5 = gr.Button("nvidia-smi", size="sm")
                q6 = gr.Button("docker ps", size="sm")
                clear_btn = gr.Button("🧹 CLEAR", size="sm", variant="stop")

    conn_btn.click(connect, inputs=[host, port, user, password, key],
                   outputs=[screen, conn_status])
    disc_btn.click(disconnect, outputs=[screen, conn_status])
    run_btn.click(submit_command, inputs=[screen, cmd], outputs=[screen, cmd])
    cmd.submit(submit_command, inputs=[screen, cmd], outputs=[screen, cmd])
    clear_btn.click(clear_screen, outputs=[screen])

    for btn, command in ((q1, "uname -a"), (q2, "df -h"),
                          (q3, "ps aux --sort=-%cpu | head -8"),
                          (q4, "ss -tuln | head -12"),
                          (q5, "nvidia-smi || echo 'no GPU on this node'"),
                          (q6, "docker ps || echo 'docker unavailable'")):
        btn.click(lambda s, c=command: submit_command(s, c),
                  inputs=[screen], outputs=[screen, cmd])

    return {"screen": screen}
