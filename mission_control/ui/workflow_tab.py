"""🗺️ WORKFLOW BUILDER + GitHub/Azure/brand connectors (n8n, Kaggle, Gmail…)."""

from __future__ import annotations

import random
import time

import gradio as gr

from ..core.state import STATE

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
    "🔀 Relay to n8n",
    "📊 Kaggle Dataset Pull",
    "✉️ Publish via Gmail Connector",
    "📨 Send Slack/Discord Alert",
    "🧠 Run Commander Review",
    "🗄️ Persist Artifacts to NAS",
    "🔍 Skill Lab Capability Check",
]

# --------------------------------------------------------------- brands
BRANDS = {
    "n8n": {"fields": ["WEBHOOK URL", "API KEY"], "note": "workflow automation"},
    "Kaggle": {"fields": ["USERNAME", "API KEY"], "note": "datasets & comps"},
    "Gmail": {"fields": ["ADDRESS", "APP PASSWORD"], "note": "email publishing"},
    "Slack": {"fields": ["INCOMING WEBHOOK URL"], "note": "team alerts"},
    "Discord": {"fields": ["WEBHOOK URL"], "note": "community alerts"},
    "Notion": {"fields": ["INTEGRATION TOKEN", "DATABASE ID"], "note": "docs & wikis"},
    "OpenAI": {"fields": ["API KEY", "ORG ID (opt)"], "note": "hosted LLM fallback"},
    "Zapier": {"fields": ["HOOK URL"], "note": "cross-app zaps"},
    "HuggingFace": {"fields": ["ACCESS TOKEN"], "note": "hub pushes"},
    "Stripe": {"fields": ["SECRET KEY"], "note": "payment events"},
}
BRAND_DEFAULT_FIELDS = ["API KEY / TOKEN", "SECONDARY KEY (opt)"]


def brand_fields(name):
    fields = BRANDS.get(name, {}).get("fields", BRAND_DEFAULT_FIELDS)
    f1 = gr.Textbox(label=fields[0], type="password",
                     visible=True)
    f2 = gr.Textbox(label=fields[1] if len(fields) > 1 else "(not used by this brand)",
                     type="password", visible=len(fields) > 1)
    return f1, f2


def save_brand(brand, key1, key2):
    if not (key1 or "").strip() and not (key2 or "").strip():
        return "❌ Paste at least one key.", brand_rows()
    STATE.brand_connectors[brand] = {"key1": (key1 or "").strip(),
                                      "key2": (key2 or "").strip(),
                                      "status": "CONFIGURED"}
    STATE.log("OK", "BRANDS", f"{brand} connector vaulted.")
    return f"✅ {brand} key(s) vaulted — usable as a workflow node.", brand_rows()


def test_brand(brand):
    cfg = STATE.brand_connectors.get(brand)
    if not cfg:
        return f"❌ {brand} has no keys vaulted yet."
    ms = _RND.randint(40, 380)
    STATE.log("OK", "BRANDS", f"{brand} credential check passed (simulated, {ms}ms).")
    return f"🟢 {brand} credentials accepted · scope OK · {ms}ms (simulated)."


def brand_rows():
    rows = []
    for brand in BRANDS:
        cfg = STATE.brand_connectors.get(brand, {})
        key = cfg.get("key1", "")
        preview = (key[:4] + "…" + key[-4:]) if len(key) > 10 else ("✔ set" if key else "—")
        rows.append([brand, BRANDS[brand]["note"], preview,
                     cfg.get("status", "NOT SET")])
    return rows


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
    if wf and wf["steps"]:
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
        time.sleep(0.3)
        log[-1] = (f"[{i}/{len(wf['steps'])}] {step} … ✅ OK "
                   f"({_RND.randint(180, 2400)}ms)")
        yield "\n".join(log)
    wf["running"] = False
    STATE.pipeline_runs.append({"id": wf_name, "status": "COMPLETE",
                                "targets": len(wf["steps"])})
    log += ["", f"■ WORKFLOW '{wf_name}' COMPLETE — all nodes green."]
    STATE.log("OK", "WORKFLOW", f"Workflow '{wf_name}' executed end-to-end.")
    yield "\n".join(log)


def workflow_names():
    return sorted(STATE.workflows.keys()) or ["pipeline-alpha"]


def load_preset(name):
    """Load a pre-configured pipeline into the sequencer view."""
    return steps_rows(name), name


# ------------------------------------------------------------- connectors
def save_github(pat, repo, branch, webhook):
    STATE.github_cfg = {"pat": pat or "", "repo": repo or "",
                        "branch": branch or "", "webhook": webhook or ""}
    STATE.log("OK", "GITHUB", f"GitHub connector saved :: {repo or 'n/a'} @ {branch or 'n/a'}")
    return f"✅ GitHub connector vaulted :: `{repo}` @ `{branch}`"


def test_github():
    if not STATE.github_cfg.get("pat"):
        return "❌ No PAT vaulted yet."
    return "🟢 PAT valid · repo reachable · webhook `push` event armed (simulated)."


def save_azure(org, project, pat, pipeline_ids):
    STATE.azure_cfg = {"org": org or "", "project": project or "",
                       "pat": pat or "", "pipeline_ids": pipeline_ids or ""}
    STATE.log("OK", "AZURE", f"Azure DevOps connector saved :: {org}/{project}")
    return f"✅ Azure DevOps vaulted :: `{org}/{project}` pipelines `{pipeline_ids}`"


def test_azure():
    if not STATE.azure_cfg.get("pat"):
        return "❌ No Azure PAT vaulted yet."
    return "🟢 Org reachable · project found · pipeline queue healthy (simulated)."


# ------------------------------------------------------------------ render
def render() -> dict:
    with gr.Row():
        gr.Markdown("## 🗺️ ADVANCED WORKFLOW BUILDER\n"
                    "<span class='cyber-sub'>NODE SEQUENCER · GITHUB · AZURE · "
                    "n8n · KAGGLE · GMAIL + MAJOR BRAND CONNECTORS</span>")

    with gr.Row():
        # ------------------------------------------------------- sequencer
        with gr.Column(scale=5):
            gr.Markdown("#### ⛓️ NODE SEQUENCER")
            wf_name = gr.Textbox(label="WORKFLOW NAME", value="auto-short-factory")
            node_dd = gr.Dropdown(NODE_LIBRARY, value=NODE_LIBRARY[0], label="NODE PALETTE")
            node_args = gr.Textbox(label="NODE ARGS (optional)",
                                    placeholder="e.g. repo=flubber01/suite branch=main")
            with gr.Row():
                add_btn = gr.Button("➕ ADD", variant="primary")
                rm_btn = gr.Button("➖ POP", variant="secondary")
                up_btn = gr.Button("⬆", variant="secondary")
                dn_btn = gr.Button("⬇", variant="secondary")
                clr_btn = gr.Button("🧹", variant="stop")
            steps_table = gr.Dataframe(value=lambda: steps_rows("auto-short-factory"),
                                        headers=["#", "NODE"], interactive=False,
                                        max_height=210)
            run_btn = gr.Button("🚀 EXECUTE WORKFLOW", variant="primary")
            run_log = gr.Code(language="shell", lines=10, label="EXECUTION LOG",
                               elem_classes="term-screen")
        # ------------------------------------------------------- devops
        with gr.Column(scale=4):
            gr.Markdown("#### 🐙 GITHUB CONNECTOR")
            gh_pat = gr.Textbox(label="PERSONAL ACCESS TOKEN", type="password")
            gh_repo = gr.Textbox(label="REPOSITORY URL",
                                  placeholder="https://github.com/flubber01/repo")
            with gr.Row():
                gh_branch = gr.Textbox(label="BRANCH", value="main")
                gh_save = gr.Button("💾", variant="secondary")
            gh_webhook = gr.Textbox(label="WEBHOOK TRIGGER URL",
                                     placeholder="https://vps.example/hooks/github")
            gh_test = gr.Button("🧪 TEST", variant="secondary", size="sm")
            gh_msg = gr.Markdown("")
            gr.Markdown("#### ☁️ AZURE DEVOPS CONNECTOR")
            with gr.Row():
                az_org = gr.Textbox(label="ORGANIZATION", placeholder="my-org")
                az_project = gr.Textbox(label="PROJECT", placeholder="OmniHack")
            with gr.Row():
                az_pat = gr.Textbox(label="PAT", type="password")
                az_pipes = gr.Textbox(label="PIPELINE IDS", placeholder="101,102")
            with gr.Row():
                az_save = gr.Button("💾", variant="secondary")
                az_test = gr.Button("🧪 TEST", variant="secondary")
            az_msg = gr.Markdown("")
        # ------------------------------------------------------- presets
        with gr.Column(scale=3):
            gr.Markdown("#### 🧩 PRE-CONFIGURED PIPELINES")
            wf_list = gr.Dropdown(workflow_names(), value="auto-short-factory",
                                   label="SELECT WORKFLOW")
            load_btn = gr.Button("📥 LOAD INTO SEQUENCER", variant="primary")
            refresh_btn = gr.Button("🔄 REFRESH LIST", variant="secondary", size="sm")
            gr.Markdown(
                "<span class='cyber-sub'>Shipped blueprints:<br>"
                "• auto-short-factory — render + crosspost loop<br>"
                "• github-trend-digest — scrape ➔ gmail ➔ n8n<br>"
                "• kaggle-data-drop — dataset ➔ viz ➔ slack<br>"
                "• social-crosspost-loop — 4 personas, browser-use</span>")

    # ------------------------------------------------------- brand row
    with gr.Row():
        with gr.Column(scale=4):
            gr.Markdown("#### 🏢 MAJOR BRAND CONNECTORS — just paste the API key")
            brand_dd = gr.Dropdown(list(BRANDS.keys()), value="n8n", label="BRAND")
            with gr.Row():
                brand_f1 = gr.Textbox(label="WEBHOOK URL", type="password")
                brand_f2 = gr.Textbox(label="API KEY", type="password")
            with gr.Row():
                brand_save = gr.Button("💾 SAVE KEYS", variant="primary")
                brand_test = gr.Button("🧪 TEST", variant="secondary")
            brand_msg = gr.Markdown("")
        with gr.Column(scale=8):
            gr.Markdown("#### 🗂️ CONNECTOR MATRIX")
            brand_table = gr.Dataframe(value=brand_rows, interactive=False,
                                        headers=["BRAND", "PURPOSE", "KEY", "STATUS"],
                                        max_height=220)

    # ---------------------------------------------------------------- events
    add_btn.click(add_step, inputs=[wf_name, node_dd, node_args],
                  outputs=[steps_table, wf_name])
    rm_btn.click(remove_step, inputs=[wf_name], outputs=[steps_table])
    up_btn.click(lambda n: move_step(n, "up"), inputs=[wf_name], outputs=[steps_table])
    dn_btn.click(lambda n: move_step(n, "down"), inputs=[wf_name], outputs=[steps_table])
    clr_btn.click(clear_steps, inputs=[wf_name], outputs=[steps_table])
    run_btn.click(run_workflow, inputs=[wf_name], outputs=[run_log])
    wf_name.change(lambda n: steps_rows(n), inputs=[wf_name], outputs=[steps_table])
    load_btn.click(load_preset, inputs=[wf_list], outputs=[steps_table, wf_name])
    refresh_btn.click(workflow_names, outputs=[wf_list])

    gh_save.click(save_github, inputs=[gh_pat, gh_repo, gh_branch, gh_webhook],
                  outputs=[gh_msg])
    gh_test.click(test_github, outputs=[gh_msg])
    az_save.click(save_azure, inputs=[az_org, az_project, az_pat, az_pipes],
                  outputs=[az_msg])
    az_test.click(test_azure, outputs=[az_msg])

    brand_dd.change(lambda b: brand_fields(b), inputs=[brand_dd],
                    outputs=[brand_f1, brand_f2])
    brand_save.click(save_brand, inputs=[brand_dd, brand_f1, brand_f2],
                     outputs=[brand_msg, brand_table])
    brand_test.click(test_brand, inputs=[brand_dd], outputs=[brand_msg])

    return {"wf_name": wf_name}
