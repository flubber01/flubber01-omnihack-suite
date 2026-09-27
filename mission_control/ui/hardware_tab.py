"""🔌 HARDWARE HUB :: device matrix, docker fleet, power telemetry."""

from __future__ import annotations

import gradio as gr

from ..core.state import STATE
from . import visibility as vis


def device_rows():
    return [[name, d["kind"], d["chip"], d["status"], f"{d['load']}%",
             f"{d['temp']}°C", f"{d['power_w']}W"]
            for name, d in STATE.hardware.items()]


def container_rows():
    return [[c["name"], c["image"], c["status"], c["cpu"], c["mem"]]
            for c in STATE.docker_containers]


def toggle_device(name):
    d = STATE.hardware.get(name)
    if not d:
        return device_rows(), "❌ Unknown device.", gr.skip()
    d["status"] = "STANDBY" if d["status"] != "STANDBY" else "ONLINE"
    if d["status"] == "STANDBY":
        d["load"] = 0
    STATE.log("INFO", "HARDWARE", f"{name} → {d['status']}")
    return device_rows(), f"🔌 {name} switched to **{d['status']}**.", gr.skip()


def set_load(name, load):
    d = STATE.hardware.get(name)
    if not d or d["status"] == "STANDBY":
        return device_rows(), "⚠ Device offline — ignoring load change."
    d["load"] = int(load)
    d["temp"] = 35 + int(load) // 3
    d["power_w"] = int(d["power_w"] * (0.6 + 0.4 * load / 100))
    return device_rows(), f"⚙ {name} load set to {int(load)}% (temp {d['temp']}°C)."


def power_summary():
    total = sum(d["power_w"] for d in STATE.hardware.values() if d["status"] != "STANDBY")
    online = sum(1 for d in STATE.hardware.values() if d["status"] != "STANDBY")
    return (f"**POWER DRAW:** {total:,} W across {online} online device(s) · "
            f"est. {total * 24 / 1000:.1f} kWh/day")


def toggle_container(name):
    for c in STATE.docker_containers:
        if c["name"] == name:
            if c["status"] == "running":
                c["status"] = "exited"
                c["cpu"], c["mem"] = "0%", "0B"
                STATE.log("INFO", "DOCKER", f"container {name} stopped.")
            else:
                c["status"] = "running"
                c["cpu"], c["mem"] = "3%", "256M"
                STATE.log("OK", "DOCKER", f"container {name} started.")
            return container_rows(), f"🐳 `{name}` → {c['status']}"
    return container_rows(), "❌ Unknown container."


# ------------------------------------------------------------------ render
def render() -> dict:
    with gr.Row():
        gr.Markdown("## 🔌 HARDWARE HUB\n"
                    "<span class='cyber-sub'>GPU RIGS · EDGE CLUSTERS · DOCKER FLEET · "
                    "POWER TELEMETRY</span>")
    with gr.Row():
        with gr.Column(scale=7):
            gr.Markdown("#### 🖥️ DEVICE MATRIX")
            dev_table = gr.Dataframe(value=device_rows, interactive=False,
                                      headers=["DEVICE", "KIND", "CHIP", "STATUS",
                                               "LOAD", "TEMP", "POWER"], max_height=250)
            with gr.Row():
                dev_name = gr.Dropdown(list(STATE.hardware.keys()),
                                        value=list(STATE.hardware.keys())[0],
                                        label="DEVICE")
                toggle_btn = gr.Button("⏻ TOGGLE POWER", variant="secondary")
            with gr.Row() as load_row:
                load_slider = gr.Slider(0, 100, value=50, step=1, label="SET LOAD %")
                load_btn = gr.Button("⚙ APPLY LOAD", variant="primary")
            vis.register("hardware.load", load_row, "Hardware: load-tuning row")
            dev_msg = gr.Markdown("")
            power_md = gr.Markdown(power_summary, elem_classes="cyber-panel")
        with gr.Column(scale=5):
            gr.Markdown("#### 🐳 DOCKER FLEET (VPS)")
            ctr_table = gr.Dataframe(value=container_rows, interactive=False,
                                      headers=["CONTAINER", "IMAGE", "STATUS", "CPU", "MEM"],
                                      max_height=250)
            ctr_name = gr.Dropdown([c["name"] for c in STATE.docker_containers],
                                    value=STATE.docker_containers[0]["name"],
                                    label="CONTAINER")
            ctr_btn = gr.Button("⏯ START/STOP", variant="primary")
            ctr_msg = gr.Markdown("")

    toggle_btn.click(toggle_device, inputs=[dev_name], outputs=[dev_table, dev_msg, load_slider])
    load_btn.click(set_load, inputs=[dev_name, load_slider], outputs=[dev_table, dev_msg])
    ctr_btn.click(toggle_container, inputs=[ctr_name], outputs=[ctr_table, ctr_msg])

    timer = gr.Timer(5.0)
    timer.tick(device_rows, outputs=[dev_table])
    timer.tick(power_summary, outputs=[power_md])

    return {}
