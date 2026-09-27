"""📡 SOCIAL CONNECTORS & STATIC PROFILE MATRIX."""

from __future__ import annotations

import random

import gradio as gr

from ..core.persistence import save_connectors, save_profiles
from ..core.state import STATE, uid

PLATFORMS = ["Twitter (X)", "YouTube", "TikTok", "Spotify", "Instagram", "Facebook"]
_RND = random.Random(77)


# -------------------------------------------------------------- connectors
def save_connector(platform, api_key, api_secret, oauth_token, webhook_url):
    STATE.connectors[platform] = {
        "api_key": (api_key or "").strip(),
        "api_secret": (api_secret or "").strip(),
        "oauth_token": (oauth_token or "").strip(),
        "webhook_url": (webhook_url or "").strip(),
        "status": "CONFIGURED",
    }
    STATE.log("OK", "SOCIAL", f"{platform} connector credentials vaulted.")
    note = save_connectors()
    return f"✅ {platform} connector saved. {note}", connector_rows()


def test_connector(platform):
    cfg = STATE.connectors.get(platform, {})
    if not cfg.get("api_key") and not cfg.get("oauth_token"):
        return f"❌ {platform} has no credentials vaulted yet."
    latency = _RND.randint(38, 320)
    STATE.log("OK", "SOCIAL", f"{platform} OAuth handshake OK ({latency}ms).")
    return (f"🟢 {platform} handshake simulated :: OAuth2 token exchange OK · "
            f"scopes granted · {latency}ms.")


def connector_rows():
    rows = []
    for p in PLATFORMS:
        cfg = STATE.connectors.get(p, {})
        rows.append([p,
                     "✔ vaulted" if cfg.get("api_key") else "—",
                     "✔ vaulted" if cfg.get("oauth_token") else "—",
                     cfg.get("webhook_url", "")[:38] or "—",
                     cfg.get("status", "NOT CONFIGURED")])
    return rows


# --------------------------------------------------------------- profiles
def profile_rows():
    rows = []
    for name, prof in STATE.profiles.items():
        bindings = ", ".join(f"{plat}:{acct}" for plat, acct in prof["accounts"].items())
        daemon = STATE.daemons.get(name, {}).get("status", "OFF")
        rows.append([name, prof["mode"], bindings or "—", daemon])
    return rows or [["—", "—", "no profiles yet", "—"]]


def create_profile(name, mode, desc):
    name = (name or "").strip()
    if not name:
        return "❌ Profile name required.", gr.skip(), gr.skip()
    STATE.profiles[name] = {"mode": mode, "desc": desc or "", "accounts": {}}
    STATE.log("OK", "PROFILES", f"Persona '{name}' registered ({mode}).")
    return (f"✅ Persona '{name}' created.", profile_dd_update(), profile_rows())


def bind_account(profile, platform, handle):
    if profile not in STATE.profiles:
        return "❌ Create the profile first.", gr.skip()
    if not (handle or "").strip():
        return "❌ Enter the account handle/ID.", gr.skip()
    STATE.profiles[profile]["accounts"][platform] = handle.strip()
    STATE.log("OK", "PROFILES", f"{profile} ⟷ {platform}:{handle.strip()}")
    save_profiles()
    return f"🔗 Bound {platform}:{handle.strip()} → {profile}", profile_rows()


def unbind_account(profile, platform):
    prof = STATE.profiles.get(profile)
    if not prof or platform not in prof["accounts"]:
        return "❌ Nothing to unbind.", gr.skip()
    del prof["accounts"][platform]
    save_profiles()
    return f"🔓 Unbound {platform} from {profile}", profile_rows()


def toggle_daemon(profile):
    if profile not in STATE.profiles:
        return "❌ Select a profile.", profile_rows()
    d = STATE.daemons.setdefault(profile, {"status": "OFF", "pid": None})
    if d["status"] == "RUNNING":
        d["status"] = "OFF"
        d["pid"] = None
        msg = f"⏹ Daemon for '{profile}' stopped."
        STATE.log("INFO", "DAEMON", msg)
    else:
        d["status"] = "RUNNING"
        d["pid"] = _RND.randint(10000, 60000)
        mode = STATE.profiles[profile]["mode"]
        msg = (f"▶ Daemon for '{profile}' running (pid {d['pid']}, mode={mode}, "
               f"persistent={'cron-loop' if mode == 'STATIC / ALWAYS-ON' else 'on-demand'}).")
        STATE.log("OK", "DAEMON", msg)
    save_profiles()
    return msg, profile_rows()


def profile_dd_update():
    names = list(STATE.profiles.keys())
    return gr.Dropdown(choices=names, value=names[0] if names else None)


# ------------------------------------------------------------------ render
def render() -> dict:
    with gr.Row():
        gr.Markdown("## 📡 SOCIAL CONNECTORS & STATIC PROFILE MATRIX\n"
                    "<span class='cyber-sub'>NATIVE API PANELS · MULTI-PERSONA BINDINGS · "
                    "ON-DEMAND + ALWAYS-ON DAEMONS</span>")

    with gr.Row():
        # -------------------------------------------------------- connectors
        with gr.Column(scale=6):
            gr.Markdown("#### 🔌 NATIVE API CONNECTION PANELS")
            connector_matrix = gr.Dataframe(value=connector_rows, interactive=False,
                                             headers=["PLATFORM", "API KEY", "OAUTH TOKEN",
                                                      "WEBHOOK", "STATUS"], max_height=190)
            platform_dd = gr.Dropdown(PLATFORMS, value=PLATFORMS[0], label="PLATFORM")
            with gr.Accordion("Twitter (X) / YouTube / TikTok / Spotify / Instagram / Facebook",
                              open=True):
                api_key = gr.Textbox(label="API KEY", placeholder="AKIA… / client_id", type="password")
                api_secret = gr.Textbox(label="API SECRET", type="password")
                oauth_token = gr.Textbox(label="OAUTH TOKEN", type="password")
                webhook_url = gr.Textbox(label="WEBHOOK URL",
                                          placeholder="https://vps.example/hooks/…")
            with gr.Row():
                save_conn = gr.Button("💾 SAVE CONNECTOR", variant="primary")
                test_conn = gr.Button("🧪 TEST HANDSHAKE", variant="secondary")
            conn_msg = gr.Markdown("")

        # -------------------------------------------------------- profiles
        with gr.Column(scale=6):
            gr.Markdown("#### 👤 STATIC PROFILE MATRIX (personas persisted on VPS)")
            profile_table = gr.Dataframe(value=profile_rows, interactive=False,
                                          headers=["PROFILE", "MODE", "BOUND ACCOUNTS",
                                                   "DAEMON"], max_height=170)
            with gr.Row():
                prof_name = gr.Textbox(label="PROFILE NAME", placeholder="e.g. Tech Guru")
                prof_mode = gr.Dropdown(["STATIC / ALWAYS-ON", "ON-DEMAND"],
                                          value="STATIC / ALWAYS-ON", label="MODE")
            prof_desc = gr.Textbox(label="PERSONA BRIEF",
                                    placeholder="Voice, niche, posting cadence…")
            create_prof = gr.Button("➕ CREATE PERSONA", variant="primary")
            prof_msg = gr.Markdown("")
            gr.Markdown("#### 🔗 ACCOUNT BINDINGS")
            prof_pick = gr.Dropdown(list(STATE.profiles.keys()), label="PROFILE",
                                      allow_custom_value=True)
            with gr.Row():
                bind_platform = gr.Dropdown(PLATFORMS, value=PLATFORMS[0], label="PLATFORM")
                bind_handle = gr.Textbox(label="ACCOUNT HANDLE / ID", placeholder="@techguru")
            with gr.Row():
                bind_btn = gr.Button("🔗 BIND", variant="primary")
                unbind_btn = gr.Button("🔓 UNBIND", variant="secondary")
            daemon_btn = gr.Button("⏯ TOGGLE BACKGROUND DAEMON", variant="secondary")

    # ---------------------------------------------------------------- events
    save_conn.click(save_connector,
                    inputs=[platform_dd, api_key, api_secret, oauth_token, webhook_url],
                    outputs=[conn_msg, connector_matrix])
    test_conn.click(test_connector, inputs=[platform_dd], outputs=[conn_msg])
    create_prof.click(create_profile, inputs=[prof_name, prof_mode, prof_desc],
                      outputs=[prof_msg, prof_pick, profile_table])
    bind_btn.click(bind_account, inputs=[prof_pick, bind_platform, bind_handle],
                   outputs=[prof_msg, profile_table])
    unbind_btn.click(unbind_account, inputs=[prof_pick, bind_platform],
                     outputs=[prof_msg, profile_table])
    daemon_btn.click(toggle_daemon, inputs=[prof_pick], outputs=[prof_msg, profile_table])

    return {"profile_dd": prof_pick, "profile_table": profile_table}
