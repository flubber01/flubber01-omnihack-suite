"""🤖 HIERARCHICAL AGENT CONFIGURATOR :: prompts, HF engine, job compiler."""

from __future__ import annotations

import gradio as gr

from ..core import swarm
from ..core.ollama import ENGINE, DEFAULT_MODELS_DIR, bind_model_to_agent
from ..core.skills import skill_label
from ..core.state import STATE


# ------------------------------------------------------------------ helpers
def _model_dd():
    names = ENGINE.all_model_names()
    return gr.Dropdown(choices=names, value=names[0] if names else None,
                       allow_custom_value=True)


def _cmdr_dd():
    names = swarm.agent_choices("commander")
    return gr.Dropdown(choices=names, value=names[0] if names else None)


def _all_dd():
    names = swarm.agent_choices()
    return gr.Dropdown(choices=names, value=names[0] if names else None)


def _tag_rows():
    return [[m["name"], f"{m.get('size', 0) / 1e9:.2f} GB",
             m.get("details", {}).get("quantization", "—"),
             m.get("origin", "ollama")] for m in ENGINE.list_tags()]


def _hf_rows():
    return [[m["name"], m["quantization"], str(m["size"]),
             ", ".join(m["bound_agents"]) or "—", m["pulled_at"]]
            for m in STATE.hf_models]


# ------------------------------------------------------------------ identity
def show_agent(name):
    agent = STATE.agents.get(swarm.agent_id_by_name(name or ""))
    if not agent:
        return "_select an agent_", "", "—", "—"
    skills_txt = "\n".join(f"• {skill_label(s)}" for s in agent["skills"]) or "_none_"
    info = (f"**TIER** `{agent['tier'].upper()}` · **MODEL** `{agent['model']}` · "
            f"**STATUS** `{agent['status']}` · **CREATED** {agent['created_at']}\n\n"
            f"**SKILLS ({len(agent['skills'])})**\n{skills_txt}\n\n"
            f"**ROUTINES:** {', '.join(agent['routines']) or '—'}")
    return agent["system_prompt"], info, agent["model"], agent["role"]


def save_agent(name, prompt, model, role):
    aid = swarm.agent_id_by_name(name)
    if not aid:
        return "❌ No agent selected.", gr.skip(), gr.skip()
    agent = STATE.agents[aid]
    agent["system_prompt"] = prompt or agent["system_prompt"]
    agent["model"] = model or agent["model"]
    agent["role"] = role or agent["role"]
    STATE.log("OK", "AGENT-CFG", f"'{agent['name']}' identity re-flashed "
                                 f"(model={agent['model']}).")
    return (f"✅ '{agent['name']}' system prompt + model + role saved & live.",
            swarm.agent_tree_text(), swarm.ops_table_rows())


def spawn_commander(name, role, model):
    if not (name or "").strip():
        return "❌ Commander name required.", gr.skip(), gr.skip(), gr.skip()
    swarm.make_agent(name, "commander", role=role, model=model)
    return (f"✅ Commander '{name.strip().upper()}' deployed.",
            _cmdr_dd(), swarm.agent_tree_text(), swarm.ops_table_rows())


def spawn_minion(name, parent_name, role, model):
    if not (name or "").strip():
        return "❌ Minion name required.", gr.skip(), gr.skip(), gr.skip()
    parent_id = swarm.agent_id_by_name(parent_name) if parent_name else None
    agent = swarm.make_agent(name, "minion", parent_id=parent_id, role=role, model=model)
    return (f"✅ Minion '{agent['name']}' spawned under "
            f"{STATE.agents.get(agent['parent'], {}).get('name', 'auto')}.",
            _all_dd(), swarm.agent_tree_text(), swarm.ops_table_rows())


def decommission(name):
    aid = swarm.agent_id_by_name(name)
    if not aid:
        return "❌ Select an agent.", gr.skip(), gr.skip(), gr.skip()
    msg = swarm.delete_agent(aid)
    return msg, _all_dd(), swarm.agent_tree_text(), swarm.ops_table_rows()


# ------------------------------------------------------------------ HF engine
def ollama_connect(url):
    ENGINE.set_url(url)
    res = ENGINE.ping()
    status = ("🟢 **LIVE DAEMON**" if res["connected"] else
              "🟡 **SIMULATED ENGINE** (daemon offline — mock catalogue served)")
    return (f"**OLLAMA CORE** :: `{ENGINE.base_url}` · v{res['version']} · {status}",
            _tag_rows(), _model_dd())


def ollama_pull(tag):
    if not (tag or "").strip():
        return "❌ Enter a model tag (e.g. `llama3.1:70b`).", gr.skip(), gr.skip()
    res = ENGINE.pull(tag)
    if not res.get("ok"):
        return f"❌ {res.get('error')}", gr.skip(), gr.skip()
    return (f"✅ Pulled `{res['tag']}` ({res['size']})"
            f"{' · simulated' if res.get('simulated') else ' · live daemon'}",
            _tag_rows(), _model_dd())


def hf_pull(repo_id, filename):
    res = ENGINE.pull_hf(repo_id, filename)
    if not res.get("ok"):
        return f"❌ {res.get('error')}", gr.skip(), gr.skip()
    return (f"✅ HuggingFace model online :: `{res['tag']}` — bindable to any agent instantly.",
            _hf_rows(), _model_dd())


def hf_scan(root):
    files = ENGINE.scan_gguf_directory(root or DEFAULT_MODELS_DIR)
    return [[f["path"], f"{f['size_gb']:.2f} GB"] for f in files]


def hf_build_modelfile(gguf_path, model_name, system_prompt):
    if not (gguf_path or "").strip():
        return "❌ Paste a GGUF path from the scan table.", gr.skip()
    res = ENGINE.build_modelfile(gguf_path, model_name, system_prompt)
    return (f"✅ Modelfile `{res['model']}` registered"
            f"{' (simulated)' if res['simulated'] else ' (live)'}\n\n```dockerfile\n"
            f"{res['modelfile']}```", _model_dd())


def bind_model(agent_name, model):
    aid = swarm.agent_id_by_name(agent_name)
    if not aid or not model:
        return "❌ Select both an agent and a model.", gr.skip()
    return bind_model_to_agent(aid, model), swarm.ops_table_rows()


# ---------------------------------------------------------------- job compile
def define_job(job_text):
    if not (job_text or "").strip():
        return "❌ Describe the mission first.", gr.skip(), gr.skip(), gr.skip()
    plan = swarm.compile_job_intent(job_text)
    blueprint = ["### 🧠 INTENT COMPILED → MISSION BLUEPRINT",
                 f"**Commander:** `{plan['commander']['name']}` — {plan['commander']['role']}",
                 "**Deployment plan:**"]
    blueprint += [f"- {s}" for s in plan["summary"]]
    result = swarm.materialize_job_plan(plan)
    return ("\n".join(blueprint) + "\n\n```\n" + result + "\n```",
            _cmdr_dd(), _all_dd(), swarm.agent_tree_text())


# -------------------------------------------------------------------- render
def render(ops_table) -> dict:
    """`ops_table` = live ops Dataframe from the Swarm Ops tab (cross-wired)."""
    with gr.Row():
        gr.Markdown("## 🤖 HIERARCHICAL AGENT CONFIGURATOR\n"
                    "<span class='cyber-sub'>COMMANDERS ➔ UNDERCLASS MINIONS · "
                    "PROMPTABLE ROLES · UNIVERSAL HF ENGINE</span>")

    with gr.Tabs(elem_classes="omni-tabs"):
        # ---------------------------------------------------------- identity
        with gr.Tab("🧬 AGENT IDENTITY & PROMPTS"):
            with gr.Row():
                with gr.Column(scale=3):
                    agent_dd = gr.Dropdown(swarm.agent_choices(), label="🎯 SELECT AGENT",
                                            allow_custom_value=False)
                    with gr.Accordion("➕ SPAWN NEW COMMANDER", open=False):
                        c_name = gr.Textbox(label="Commander Name", placeholder="e.g. VANGUARD")
                        c_role = gr.Textbox(label="Role", value="Commander / Strategy Specialist")
                        c_model = gr.Dropdown(ENGINE.all_model_names(),
                                              value=ENGINE.all_model_names()[0],
                                              label="Brain Model", allow_custom_value=True)
                        c_btn = gr.Button("🚀 DEPLOY COMMANDER", variant="primary")
                    with gr.Accordion("➕ SPAWN UNDERCLASS MINION", open=False):
                        m_name = gr.Textbox(label="Minion Name", placeholder="e.g. SCRAPE-UNIT-β")
                        m_parent = gr.Dropdown(swarm.agent_choices("commander"),
                                               label="Parent Commander")
                        m_role = gr.Textbox(label="Role", value="Minion / Task Worker")
                        m_model = gr.Dropdown(ENGINE.all_model_names(),
                                              value=ENGINE.all_model_names()[0],
                                              label="Brain Model", allow_custom_value=True)
                        m_btn = gr.Button("🐣 SPAWN MINION", variant="primary")
                    del_btn = gr.Button("☠️ DECOMMISSION SELECTED", variant="stop")
                with gr.Column(scale=7):
                    role_txt = gr.Textbox(label="ROLE TAG", value="—")
                    sys_prompt = gr.Textbox(
                        label=("🧠 SYSTEM PROMPT / ROLE DEFINITION — live-prompt this agent's "
                               "core identity, cognitive boundaries, behavior quirks & "
                               "precise workflow rules"),
                        lines=14, max_lines=26, value="_select an agent_")
                    model_dd = gr.Dropdown(ENGINE.all_model_names(), label="🔌 BOUND MODEL",
                                            allow_custom_value=True)
                    save_btn = gr.Button("💾 FLASH IDENTITY TO AGENT", variant="primary")
                    save_msg = gr.Markdown("")
                    agent_info = gr.Markdown("", elem_classes="cyber-panel")

        # ----------------------------------------------------------- HF engine
        with gr.Tab("⚡ OLLAMA + HF ENGINE"):
            with gr.Row():
                with gr.Column(scale=4):
                    gr.Markdown("#### ⚙️ OLLAMA CORE LINK")
                    oll_url = gr.Textbox(label="Ollama Host", value=STATE.ollama_url)
                    conn_btn = gr.Button("🔗 CONNECT / SCAN /api/tags", variant="primary")
                    conn_status = gr.Markdown("_not connected_")
                    gr.Markdown("#### ⬇️ PULL NATIVE MODEL")
                    pull_tag = gr.Textbox(label="Model Tag", placeholder="llama3.1:70b")
                    pull_btn = gr.Button("⬇️ PULL MODEL", variant="secondary")
                    pull_msg = gr.Markdown("")
                    gr.Markdown("#### 🤗 UNIVERSAL HF ENGINE")
                    hf_repo = gr.Textbox(label="HF Repo ID (GGUF)",
                                          value="QuantFactory/Mistral-7B-Instruct-v0.3-GGUF")
                    hf_file = gr.Textbox(label="Specific File (optional)",
                                          placeholder="auto → largest GGUF")
                    hf_btn = gr.Button("🤗 PULL HUGGINGFACE MODEL", variant="primary")
                    hf_msg = gr.Markdown("")
                    gr.Markdown("#### 🗂️ LOCAL GGUF VAULT → MODELFILE")
                    gguf_root = gr.Textbox(label="Scan Directory", value=DEFAULT_MODELS_DIR)
                    scan_btn = gr.Button("🔍 SCAN FOR *.GGUF", variant="secondary")
                    gguf_table = gr.Dataframe(headers=["GGUF PATH", "SIZE"],
                                               interactive=False, max_height=120)
                    mf_path = gr.Textbox(label="GGUF Path (from scan)",
                                          placeholder="/home/models/….gguf")
                    mf_name = gr.Textbox(label="New Model Name", placeholder="my-mistral-custom")
                    mf_sys = gr.Textbox(label="SYSTEM line baked into Modelfile",
                                         lines=2, placeholder="You are…")
                    mf_btn = gr.Button("🏗️ BUILD MODELFILE + REGISTER", variant="secondary")
                    mf_out = gr.Markdown("")
                with gr.Column(scale=6):
                    gr.Markdown("#### 📦 LOADED MODEL MATRIX (`/api/tags`)")
                    tag_table = gr.Dataframe(value=_tag_rows,
                                              headers=["MODEL", "SIZE", "QUANT", "ORIGIN"],
                                              interactive=False, max_height=210)
                    gr.Markdown("#### 🤗 HUGGINGFACE PULLS (hf.co/*)")
                    hf_table = gr.Dataframe(value=_hf_rows,
                                             headers=["TAG", "QUANT", "SIZE",
                                                      "BOUND AGENTS", "PULLED"],
                                             interactive=False, max_height=140)
                    gr.Markdown("#### 🔥 INSTANT MODEL BIND")
                    with gr.Row():
                        bind_agent = gr.Dropdown(swarm.agent_choices(),
                                                  label="Target Agent")
                        bind_model_dd = gr.Dropdown(ENGINE.all_model_names(),
                                                     label="Model (native · hf.co · custom)",
                                                     allow_custom_value=True)
                    bind_btn = gr.Button("⚡ BIND MODEL TO AGENT", variant="primary")
                    bind_msg = gr.Markdown("")

        # ----------------------------------------------------------- job comp
        with gr.Tab("🧠 DEFINE AI'S JOB"):
            job_text = gr.Textbox(
                label="MISSION INTENT — describe the job in plain language",
                lines=3, placeholder="e.g. Scrape trending AI news, render daily shorts and "
                                     "post them to TikTok + YouTube automatically.")
            job_btn = gr.Button("🧠 COMPILE INTENT → SPAWN HIERARCHY", variant="primary")
            job_out = gr.Markdown("")
            tree_view = gr.Markdown(swarm.agent_tree_text, elem_classes="agent-tree")

    # ---------------------------------------------------------- events: identity
    agent_dd.change(show_agent, inputs=[agent_dd],
                    outputs=[sys_prompt, agent_info, model_dd, role_txt])
    save_btn.click(save_agent, inputs=[agent_dd, sys_prompt, model_dd, role_txt],
                   outputs=[save_msg, tree_view, ops_table])
    c_btn.click(spawn_commander, inputs=[c_name, c_role, c_model],
                outputs=[save_msg, m_parent, tree_view, ops_table])
    m_btn.click(spawn_minion, inputs=[m_name, m_parent, m_role, m_model],
                outputs=[save_msg, agent_dd, tree_view, ops_table])
    del_btn.click(decommission, inputs=[agent_dd],
                  outputs=[save_msg, agent_dd, tree_view, ops_table])

    # --------------------------------------------------------- events: HF engine
    conn_btn.click(ollama_connect, inputs=[oll_url],
                   outputs=[conn_status, tag_table, model_dd])
    pull_btn.click(ollama_pull, inputs=[pull_tag],
                   outputs=[pull_msg, tag_table, model_dd])
    hf_btn.click(hf_pull, inputs=[hf_repo, hf_file],
                 outputs=[hf_msg, hf_table, model_dd])
    scan_btn.click(hf_scan, inputs=[gguf_root], outputs=[gguf_table])
    mf_btn.click(hf_build_modelfile, inputs=[mf_path, mf_name, mf_sys],
                 outputs=[mf_out, model_dd])
    bind_btn.click(bind_model, inputs=[bind_agent, bind_model_dd],
                   outputs=[bind_msg, ops_table])

    # --------------------------------------------------------- events: job comp
    job_btn.click(define_job, inputs=[job_text],
                  outputs=[job_out, m_parent, agent_dd, tree_view])

    return {"agent_dd": agent_dd, "model_dd": model_dd, "tree_view": tree_view}
