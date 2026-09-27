"""🗺️ WORKFLOW BUILDER + GitHub/Azure connectors + fail-safes."""

from __future__ import annotations

import random
import time

import gradio as gr

from ..core.persistence import export_config, import_config
from ..core.state import STATE, uid

_RND = random.Random(31)

NODE_LIBRARY = [
    "🐙 Fetch GitHub Repo",
    "🕷️ Spawn Underclass Scraper",
    "🌐 Execute Browser-Use Task",
    "🎬 Render Short Video",
    "📸 Post via Instagram Connector",
    "🎥 Post via YouTube Connector",
    "🎵 Post via TikTok Connector",
    "☁️ Trigger Azure Pipeline",
    "📨 Send Slack/Discord Alert",
    "🧠 Run Commander Review",
    "🗄️ Persist Artifacts to NAS",
    "🔍 Skill Lab Capability Check",
]


# ----------------------------------------------------------------- workflows
def steps_rows(name):
    wf = STATE.workflows.get(name or "")
    if not wf or not wf["steps"]:
        return [["—", "empty workflow"]]
    return [[str(i + 1), s] for i, s in enumerate(wf["steps"])]


def add_step(wf_name, node, args):
    wf_name = (wf_name or "").strip() or "pipeline-alpha"
    wf = STATE.workflows.setdefault(wf_name, {"steps": [], "running": False})
    label = node if not (args or "").strip() else f"{node} :: {args.strip()}"
    wf["steps"].append(label)
    STATE.log("OK", "WORKFLOW", f"Step {len(wf['steps'])} added to '{wf_name}': {label}")
    return steps_rows(wf_name), wf_name


def remove_step(wf_name):
    wf = STATE.workflows.get(wf_name)
    if not wf or not wf["steps"]:
        return steps_rows(wf_name)
    wf["steps"].pop()
    return steps_rows(wf_name)


def move_step(wf_name, direction):
    wf = STATE.workflows.get(wf_name)
    if not wf or len(wf["steps"]) < 2:
        return steps_rows(wf_name)
    steps = wf["steps"]
    idx = len(steps) - 1 if direction == "up" else 0
    j = idx - 1 if direction == "up" else idx + 1
    steps[idx], steps[j] = steps[j], steps[idx]
    return steps_rows(wf_name)


def clear_steps(wf_name):
    wf = STATE.workflows.get(wf_name)
    if wf:
        wf["steps"] = []
    return steps_rows(wf_name)


def run_workflow(wf_name):
    """Generator: streams simulated execution of every node."""
    wf = STATE.workflows.get(wf_name)
    if not wf or not wf["steps"]:
        yield "❌ Workflow empty — add nodes first."
        return
    wf["running"] = True
    log = [f"▶ EXECUTING WORKFLOW '{wf_name}' — {len(wf['steps'])} nodes", ""]
    yield "\n".join(log)
    for i, step in enumerate(wf["steps"], 1):
        if STATE.halted:
            log.append(f"⛔ ABORTED at node {i} by KILL SWITCH.")
            break
        log.append(f"[{i}/{len(wf['steps'])}] {step} … RUNNING")
        yield "\n".join(log)
        time.sleep(0.35)
        ms = _RND.randint(180, 2400)
        log[-1] = f"[{i}/{len(wf['steps'])}] {step} … ✅ OK ({ms}ms)"
        yield "\n".join(log)
    wf["running"] = False
    STATE.pipeline_runs.append({"id": wf_name, "status": "COMPLETE",
                                "targets": len(wf["steps"])})
    log.append("")
    log.append(f"■ WORKFLOW '{wf_name}' COMPLETE — all nodes green.")
    STATE.log("OK", "WORKFLOW", f"Workflow '{wf_name}' executed end-to-end.")
    yield "\n".join(log)


def workflow_names():
    return sorted(STATE.workflows.keys()) or ["pipeline-alpha"]


# ------------------------------------------------------------- connectors
def save_github(pat, repo, branch, webhook):
    STATE.github_cfg = {"pat": pat or "", "repo": repo or "",
                        "branch": branch or "", "webhook": webhook or ""}
    STATE.log("OK", "GITHUB", f"GitHub connector saved :: {repo or 'n/a'} @ {branch or 'n/a'}")
    return f"✅ GitHub connector vaulted :: `{repo}` @ `{branch}`"


def test_github():
    if not STATE.github_cfg.get("pat"):
        return "❌ No PAT vaulted yet."
    STATE.log("OK", "GITHUB", "PAT validated against api.github.com (simulated).")
    return ("🟢 PAT valid · repo reachable · webhook `push` event armed "
            "(simulated handshake).")


def save_azure(org, project, pat, pipeline_ids):
    STATE.azure_cfg = {"org": org or "", "project": project or "",
                       "pat": pat or "", "pipeline_ids": pipeline_ids or ""}
    STATE.log("OK", "AZURE", f"Azure DevOps connector saved :: {org}/{project}")
    return f"✅ Azure DevOps vaulted :: `{org}/{project}` pipelines `{pipeline_ids}`"


def test_azure():
    if not STATE.azure_cfg.get("pat"):
        return "❌ No Azure PAT vaulted yet."
    STATE.log("OK", "AZURE", "Azure DevOps org enumerated (simulated).")
    return "🟢 Org reachable · project found · pipeline queue healthy (simulated)."


# ------------------------------------------------------------- config io
def do_export():
    path, summary = export_config()
    return path, summary


def do_import(file):
    if file is None:
        return "❌ No file uploaded."
    path = file.name if hasattr(file, "name") else str(file)
    return import_config(path)


# ------------------------------------------------------------------ render
def render() -> dict:
    with gr.Row():
        gr.Markdown("## 🗺️ ADVANCED WORKFLOW BUILDER\n"
                    "<span class='cyber-sub'>CHAIN NODES · GITHUB + AZURE CONNECTORS · "
                    "CONFIG EXPORT/IMPORT</span>")

    with gr.Row():
        with gr.Column(scale=5):
            gr.Markdown("#### ⛓️ NODE SEQUENCER")
            wf_name = gr.Textbox(label="WORKFLOW NAME", value="pipeline-alpha")
            node_dd = gr.Dropdown(NODE_LIBRARY, value=NODE_LIBRARY[0], label="NODE PALETTE")
            node_args = gr.Textbox(label="NODE ARGS (optional)",
                                    placeholder="e.g. repo=flubber01/suite branch=main")
            with gr.Row():
                add_btn = gr.Button("➕ ADD STEP", variant="primary")
                rm_btn = gr.Button("➖ POP LAST", variant="secondary")
            with gr.Row():
                up_btn = gr.Button("⬆ SWAP ↑", variant="secondary")
                dn_btn = gr.Button("⬇ SWAP ↓", variant="secondary")
                clr_btn = gr.Button("🧹 CLEAR", variant="stop")
            steps_table = gr.Dataframe(value=lambda: steps_rows("pipeline-alpha"),
                                        headers=["#", "NODE"], interactive=False, max_height=220)
            run_btn = gr.Button("🚀 EXECUTE WORKFLOW", variant="primary")
            run_log = gr.Code(language="shell", lines=12, label="EXECUTION LOG",
                               elem_classes="term-screen")
        with gr.Column(scale=4):
            gr.Markdown("#### 🐙 GITHUB CONNECTOR")
            gh_pat = gr.Textbox(label="PERSONAL ACCESS TOKEN", type="password")
            gh_repo = gr.Textbox(label="REPOSITORY URL",
                                  placeholder="https://github.com/flubber01/repo")
            with gr.Row():
                gh_branch = gr.Textbox(label="BRANCH", value="main")
                gh_save = gr.Button("💾 SAVE", variant="secondary")
            gh_webhook = gr.Textbox(label="WEBHOOK TRIGGER URL",
                                     placeholder="https://vps.example/hooks/github")
            gh_test = gr.Button("🧪 TEST CONNECTOR", variant="secondary")
            gh_msg = gr.Markdown("")
            gr.Markdown("#### ☁️ AZURE DEVOPS CONNECTOR")
            az_org = gr.Textbox(label="ORGANIZATION", placeholder="my-org")
            az_project = gr.Textbox(label="PROJECT", placeholder="OmniHack")
            az_pat = gr.Textbox(label="PAT", type="password")
            az_pipes = gr.Textbox(label="PIPELINE IDS", placeholder="101,102,205")
            with gr.Row():
                az_save = gr.Button("💾 SAVE", variant="secondary")
                az_test = gr.Button("🧪 TEST", variant="secondary")
            az_msg = gr.Markdown("")
        with gr.Column(scale=3):
            gr.Markdown("#### 🛡️ FAIL-SAFES & CONFIG")
            gr.Markdown(
                "<span class='cyber-sub'>The EMERGENCY KILL SWITCH lives in the top "
                "status bar and freezes agents, browser tasks, renders and workflows "
                "instantly.</span>")
            exp_btn = gr.DownloadButton("⬇️ EXPORT config.json", variant="primary")
            exp_msg = gr.Markdown("")
            imp_file = gr.File(label="IMPORT config.json", file_types=[".json"])
            imp_msg = gr.Markdown("")
            gr.Markdown("#### 🗂️ SAVED WORKFLOWS")
            wf_list = gr.Dropdown(workflow_names(), value="pipeline-alpha",
                                   label="SELECT WORKFLOW")
            refresh_btn = gr.Button("🔄 REFRESH LIST", variant="secondary", size="sm")

    # ---------------------------------------------------------------- events
    add_btn.click(add_step, inputs=[wf_name, node_dd, node_args],
                  outputs=[steps_table, wf_name])
    rm_btn.click(remove_step, inputs=[wf_name], outputs=[steps_table])
    up_btn.click(lambda n: move_step(n, "up"), inputs=[wf_name], outputs=[steps_table])
    dn_btn.click(lambda n: move_step(n, "down"), inputs=[wf_name], outputs=[steps_table])
    clr_btn.click(clear_steps, inputs=[wf_name], outputs=[steps_table])
    run_btn.click(run_workflow, inputs=[wf_name], outputs=[run_log])
    wf_name.change(lambda n: steps_rows(n), inputs=[wf_name], outputs=[steps_table])
    wf_list.change(lambda n: (steps_rows(n), n), inputs=[wf_list],
                   outputs=[steps_table, wf_name])
    refresh_btn.click(workflow_names, outputs=[wf_list])

    gh_save.click(save_github, inputs=[gh_pat, gh_repo, gh_branch, gh_webhook],
                  outputs=[gh_msg])
    gh_test.click(test_github, outputs=[gh_msg])
    az_save.click(save_azure, inputs=[az_org, az_project, az_pat, az_pipes],
                  outputs=[az_msg])
    az_test.click(test_azure, outputs=[az_msg])

    exp_btn.click(do_export, outputs=[exp_btn, exp_msg])
    imp_file.upload(do_import, inputs=[imp_file], outputs=[imp_msg])

    return {"wf_name": wf_name}
