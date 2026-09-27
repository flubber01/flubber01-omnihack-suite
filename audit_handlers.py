"""Full handler audit — exercises every UI handler incl. edge cases.

Run:  python3 audit_handlers.py
Exits non-zero on any crash. Used before release; safe to delete afterwards.
"""
import sys
import traceback

PASS, FAIL = 0, []


def check(name, fn, *args, **kw):
    global PASS
    try:
        fn(*args, **kw)
        PASS += 1
    except Exception as exc:
        FAIL.append((name, repr(exc)))
        traceback.print_exc(limit=2)


def drain(gen):
    out = None
    for out in gen:
        pass
    return out


import mission_control.app  # seeds everything like the live server
from mission_control.core.state import STATE

# ================================ TOPBAR =================================
from mission_control.ui import topbar
check("topbar.metrics_html", topbar.metrics_html)
check("topbar.kill_handler", lambda: __import__("mission_control.app", fromlist=["x"]).kill_handler())
check("topbar.resume_handler", lambda: __import__("mission_control.app", fromlist=["x"]).resume_handler())

# ============================== SWARM OPS ================================
from mission_control.ui import swarm_ops as so
check("so.ops_rows", so.ops_rows)
check("so.activity_feed", so.activity_feed)
check("so.ping_all", so.ping_all)
check("so.halt_agent none", so.halt_agent, None)
check("so.halt_agent", so.halt_agent, "OMNI-PRIME")
check("so.resume_agent", so.resume_agent, "OMNI-PRIME")
check("so.clear_chat", so.clear_chat)
check("so.chat_targets", so.chat_targets)
check("so.send empty", lambda: drain(so.send_to_swarm([], "", "⚡ SWARM BROADCAST")))
check("so.send broadcast", lambda: drain(so.send_to_swarm([], "audit probe", "⚡ SWARM BROADCAST")))
check("so.send targeted", lambda: drain(so.send_to_swarm([], "report", "OMNI-PRIME")))
check("so.send unknown target", lambda: drain(so.send_to_swarm([], "report", "NOBODY-HERE")))
for c in ["/help", "/clear", "/status", "/agents", "/tree", "/kill", "/resume",
          "/say OMNI-PRIME hi", "/say NOBODY hi", "/broadcast probe",
          "/model OMNI-PRIME phi3.5:3.8b", "/model NOBODY x",
          "/skills OMNI-PRIME", "/skills NOBODY", "plain text", "@OMNI-PRIME hi",
          "", "  ", "/unknowncmd"]:
    tgt = None if c.startswith(("/", "@")) or c in ("plain text", "", "  ") else "OMNI-PRIME"
    tgt = "OMNI-PRIME" if c == "plain text" else tgt
    check(f"so.term[{c[:14]!r}]", lambda cc=c, tt=tgt: drain(so.term_exec(so.TERM_BANNER, cc, tt)))

# ============================== AGENTS TAB ===============================
from mission_control.ui import agents_tab as at
check("at.show none", at.show_agent, None)
check("at.show", at.show_agent, "OMNI-PRIME")
check("at.save none", at.save_agent, None, "p", "m", "r")
check("at.save", at.save_agent, "OMNI-PRIME", "You are audited.", "llama3.1:8b", "Commander / Audit")
check("at.spawn_cmdr empty", at.spawn_commander, "", "r", "m")
check("at.spawn_cmdr", at.spawn_commander, "AUDIT-CMDR", "Commander / QA", "llama3.1:8b")
check("at.spawn_minion empty", at.spawn_minion, "", "AUDIT-CMDR", "r", "m")
check("at.spawn_minion", at.spawn_minion, "AUDIT-MIN", "AUDIT-CMDR", "Minion / QA", "llama3.1:8b")
check("at.decomm none", at.decommission, None)
check("at.decomm", at.decommission, "AUDIT-MIN")
check("at.decomm cmdr", at.decommission, "AUDIT-CMDR")
check("at.ollama_connect", at.ollama_connect, "http://localhost:11434")
check("at.ollama_pull empty", at.ollama_pull, "")
check("at.ollama_pull", at.ollama_pull, "audit-model:1b")
check("at.hf_pull empty", at.hf_pull, "", "")
check("at.hf_pull bad", at.hf_pull, "noslashrepo", "")
check("at.hf_pull", at.hf_pull, "AuditOrg/AuditRepo-GGUF", "q4.gguf")
check("at.hf_scan", at.hf_scan, "/home/models")
check("at.mf empty", at.hf_build_modelfile, "", "n", "s")
check("at.mf", at.hf_build_modelfile, "/home/models/x.gguf", "audit-modelfile", "You are X.")
check("at.bind none", at.bind_model, None, "m")
check("at.bind", at.bind_model, "OMNI-PRIME", "llama3.1:8b")
check("at.job empty", at.define_job, "")
check("at.job", at.define_job, "scrape data and post videos daily")

# ============================== BROWSER ==================================
from mission_control.ui import browser_tab as bt
check("bt.frame live=false", bt.grab_frame)
STATE.browser_live = True
check("bt.frame live", bt.grab_frame)
check("bt.start", bt.start_stream, 1.2)
check("bt.go empty", bt.go_url, "")
check("bt.go", bt.go_url, "example.org/path")
check("bt.click", bt.inject_click, 100, 200)
check("bt.click oob", bt.inject_click, -50, 9999)
check("bt.keys empty", bt.send_keys, "")
check("bt.keys", bt.send_keys, "audit probe")
check("bt.scroll", bt.scroll_page, -300)
check("bt.snap", bt.snapshot_now)
check("bt.stop", bt.stop_stream)
check("bt.dom", bt.dump_dom)
check("bt.inspect none-model", bt.ai_inspect, None)
check("bt.autopilot", bt.ai_autopilot, "llava:13b-v1.6")
check("bt.vnc", bt.load_vnc, "")
check("bt.vnc url", bt.load_vnc, "http://localhost:6080/vnc.html")

# ============================== CONTENT ==================================
from mission_control.ui import content_tab as ct
check("ct.create no plats", ct.create_job, "t", "Hype / Viral", 30, [], "ALEX-TECH")
check("ct.create", ct.create_job, "audit short", "Hype / Viral", 30, ["TikTok"], "ALEX-TECH")
jid = ct.PIPELINE_REF if hasattr(ct, "PIPELINE_REF") else None
from mission_control.core.pipeline import PIPELINE
last_job = list(PIPELINE.jobs)[-1]
check("ct.script", ct.write_script, last_job)
check("ct.script bad", ct.write_script, "nope")
check("ct.assets", ct.fetch_assets, last_job)
check("ct.assets bad", ct.fetch_assets, "nope")
check("ct.vo", ct.gen_voiceover, last_job, "ARIA-9 (fem, warm)")
check("ct.vo bad", ct.gen_voiceover, "nope", "v")
check("ct.render", lambda: drain(ct.render_job(last_job)))
check("ct.render bad", lambda: drain(ct.render_job("nope")))
check("ct.dist", ct.distribute_job, last_job)
check("ct.dist bad", ct.distribute_job, "nope")
check("ct.autopilot empty", ct.autopilot, "", "t", 30, ["TikTok"], "p", "v")
check("ct.autopilot", ct.autopilot, "audit auto", "Hype / Viral", 30, ["TikTok"], "ALEX-TECH", "ARIA-9 (fem, warm)")
check("ct.sched empty", ct.add_schedule, last_job, "", "daily", ["TikTok"])
check("ct.sched", ct.add_schedule, last_job, "2026-10-01 09:00", "daily", ["TikTok"])
check("ct.queue", ct.queue_rows)
check("ct.presets", lambda: [ct.apply_preset(k) for k in ct.CONTENT_PRESETS])
check("ct.preset bad", ct.apply_preset, "NOPE")
check("ct.profile_names", ct._profile_names)

# ============================== SOCIAL ===================================
from mission_control.ui import social_tab as st
check("st.save", st.save_connector, "TikTok", "k", "s", "t", "https://w.example/x")
check("st.test cfg", st.test_connector, "TikTok")
check("st.test empty", st.test_connector, "Facebook")
check("st.rows", st.connector_rows)
check("st.prof empty", st.create_profile, "", "ON-DEMAND", "")
check("st.prof", st.create_profile, "AUDIT-PERSONA", "ON-DEMAND", "qa")
check("st.bind no prof", st.bind_account, "NOPE", "TikTok", "@x")
check("st.bind no handle", st.bind_account, "AUDIT-PERSONA", "TikTok", "")
check("st.bind", st.bind_account, "AUDIT-PERSONA", "TikTok", "@audit")
check("st.unbind none", st.unbind_account, "AUDIT-PERSONA", "YouTube")
check("st.unbind", st.unbind_account, "AUDIT-PERSONA", "TikTok")
check("st.daemon no prof", st.toggle_daemon, "NOPE")
check("st.daemon on", st.toggle_daemon, "AUDIT-PERSONA")
check("st.daemon off", st.toggle_daemon, "AUDIT-PERSONA")
check("st.prof rows", st.profile_rows)

# ============================== SKILL LAB ================================
from mission_control.ui import skill_lab_tab as sk
check("sk.filter", sk.filter_skills, "ffmpeg", "ALL")
check("sk.filter dom", sk.filter_skills, "", "Media & Vision")
check("sk.detail none", sk.skill_detail, [])
check("sk.detail", sk.skill_detail, ["[media.vid.concat] FFmpeg Concat Wrapper"])
check("sk.test none", sk.test_skill, [])
check("sk.test", sk.test_skill, ["[media.vid.concat] FFmpeg Concat Wrapper"])
check("sk.assign no agent", sk.assign_skills, None, ["[media.vid.concat] x"], "")
check("sk.assign no skills", sk.assign_skills, "OMNI-PRIME", [], "")
check("sk.assign", sk.assign_skills, "OMNI-PRIME", ["[media.vid.concat] x"], "")
check("sk.assigned", sk.assigned_list, "OMNI-PRIME")
check("sk.strip no agent", sk.unassign_skill, None, "[media.vid.concat] x")
check("sk.strip", sk.unassign_skill, "OMNI-PRIME", "[media.vid.concat] x")
check("sk.stats", sk.registry_stats)

# ============================== SSH ======================================
from mission_control.ui import ssh_tab as sh
check("sh.connect local", sh.connect, "", 22, "auditor", "", "")
check("sh.cmd empty", lambda: sh.submit_command("[x]\n$ ", ""))
check("sh.cmd", lambda: sh.submit_command("[x]\n$ ", "echo AUDIT_SSH_OK"))
check("sh.cmd blocked", lambda: sh.submit_command("[x]\n$ ", "rm -rf /"))
check("sh.clear", sh.clear_screen)
check("sh.disconnect", sh.disconnect)
check("sh.cmd no session", lambda: sh.submit_command("[x]\n$ ", "ls"))

# ============================== WORKFLOW =================================
from mission_control.ui import workflow_tab as wf
check("wf.add", wf.add_step, "audit-flow", "🧠 Run Commander Review", "x=1")
check("wf.add2", wf.add_step, "audit-flow", "🎬 Render Short Video", "")
check("wf.rows", wf.steps_rows, "audit-flow")
check("wf.move up", wf.move_step, "audit-flow", "up")
check("wf.move dn", wf.move_step, "audit-flow", "down")
check("wf.move tiny", wf.move_step, "nope", "up")
check("wf.pop", wf.remove_step, "audit-flow")
check("wf.pop empty", wf.remove_step, "nope")
check("wf.run empty", lambda: drain(wf.run_workflow("empty-flow")))
check("wf.run", lambda: drain(wf.run_workflow("audit-flow")))
check("wf.run halted", lambda: (STATE.halt_all("AUDIT"), drain(wf.run_workflow("audit-flow")), STATE.resume_all()))
check("wf.clear", wf.clear_steps, "audit-flow")
check("wf.names", wf.workflow_names)
check("wf.load preset", wf.load_preset, "auto-short-factory")
check("wf.gh save", wf.save_github, "pat", "https://github.com/x/y", "main", "https://w")
check("wf.gh test no", lambda: (STATE.github_cfg.update(pat=""), wf.test_github()))
check("wf.gh test", lambda: (STATE.github_cfg.update(pat="x"), wf.test_github()))
check("wf.az save", wf.save_azure, "org", "proj", "pat", "1,2")
check("wf.az test no", lambda: (STATE.azure_cfg.update(pat=""), wf.test_azure()))
check("wf.az test", lambda: (STATE.azure_cfg.update(pat="x"), wf.test_azure()))
check("wf.brand fields", wf.brand_fields, "n8n")
check("wf.brand fields unk", wf.brand_fields, "UnknownBrand")
check("wf.brand save empty", wf.save_brand, "n8n", "", "")
check("wf.brand save", wf.save_brand, "n8n", "https://n8n.example/hook", "key")
check("wf.brand test no", wf.test_brand, "Stripe")
check("wf.brand test", wf.test_brand, "n8n")
check("wf.brand rows", wf.brand_rows)

# ============================== HARDWARE =================================
from mission_control.ui import hardware_tab as hw
check("hw.rows", hw.device_rows)
check("hw.toggle none", hw.toggle_device, "NOPE")
check("hw.toggle", hw.toggle_device, "FPGA-FARM")
check("hw.toggle back", hw.toggle_device, "FPGA-FARM")
check("hw.load standby", hw.set_load, "FPGA-FARM", 80) if STATE.hardware["FPGA-FARM"]["status"] == "STANDBY" else check("hw.load", hw.set_load, "GPU-RIG-01", 80)
check("hw.power", hw.power_summary)
check("hw.ctr none", hw.toggle_container, "NOPE")
check("hw.ctr", hw.toggle_container, "omni-vector-db")
check("hw.ctr back", hw.toggle_container, "omni-vector-db")
check("hw.ctr rows", hw.container_rows)

# ============================== LOGS =====================================
from mission_control.ui import logs_tab as lg
check("lg.rows", lg.log_rows, "ALL")
check("lg.rows crit", lg.log_rows, "CRIT")
check("lg.counts", lg.level_counts)
check("lg.clear", lg.clear_logs)

# ============================== MEMORY ===================================
from mission_control.ui import memory_tab as mt
check("mt.stats", mt.stats_md)
check("mt.stream", mt.stream_rows)
check("mt.lessons", mt.lesson_rows)
check("mt.store empty", mt.manual_store, "OPERATOR", "episodic", "", 5)
check("mt.store", mt.manual_store, "OPERATOR", "semantic", "audit memory", 7)
check("mt.recall", mt.do_recall, "audit", "ALL", "ALL")
check("mt.recall empty", mt.do_recall, "", "ALL", "ALL")
check("mt.cycle", mt.run_cycle_now)
check("mt.arm", mt.arm_loop, 10)
check("mt.arm floor", mt.arm_loop, 1)
check("mt.disarm", mt.disarm_loop)
check("mt.refresh", mt.auto_refresh)
check("mt.flush", mt.flush_vault)

# ============================== SETTINGS =================================
from mission_control.ui import settings_tab as se
check("se.skin", se.apply_skin, "JARVIS")
check("se.skin unk", se.apply_skin, "NOPE-SKIN")
check("se.skin back", se.apply_skin, "MILITARY OPS")
check("se.skin_payload", se.skin_payload)
check("se.cleanup", se.cleanup_choices)
check("se.tg status", se.tg_status)
check("se.tg arm empty", se.tg_arm, "", "")
check("se.tg disarm", se.tg_disarm)
check("se.tg log", se.tg_test_log)
check("se.export", se.do_export)
check("se.import none", se.do_import, None)

# ============================== HELPBOT ==================================
from mission_control.core import helpbot as hb
check("hb.chat", lambda: hb.chat([], "next"))
check("hb.chat empty", lambda: hb.chat([], ""))
check("hb.topics", lambda: hb.HELPBOT.reply("topics"))
check("hb.num", lambda: hb.HELPBOT.reply("2"))
check("hb.kw", lambda: hb.HELPBOT.reply("wie funktioniert telegram?"))
check("hb.unk", lambda: hb.HELPBOT.reply("zxyqv"))
check("hb.restart", lambda: hb.HELPBOT.reply("restart"))

# ============================== CORE MISC ================================
from mission_control.core.telegram_bridge import BRIDGE
for cmd in ["/help", "/status", "/agents", "/kill", "/resume", "/ping",
            "/skin jar", "/skin NOPE", "/say OMNI-PRIME hi", "/say NOBODY hi",
            "/short audit topic", "/unknown", ""]:
    check(f"tg.handle[{cmd[:12]!r}]", lambda c=cmd: BRIDGE.handle(c))
from mission_control.core.persistence import export_config, import_config
path, _ = export_config()
check("persist.import", import_config, path)
check("persist.import bad", import_config, "/nonexistent.json")
from mission_control.core.ollama import ENGINE
check("ollama.gen_stream", lambda: list(ENGINE.generate_stream("m", "p")))
check("ollama.gen_once", lambda: ENGINE.generate_once("m", "p"))

# ============================== KILL STATE CHAINS ========================
STATE.halt_all("AUDIT")
check("halted.chat", lambda: drain(so.send_to_swarm([], "probe while halted", "⚡ SWARM BROADCAST")))
check("halted.frame", bt.grab_frame)
STATE.resume_all()

print(f"\n{'=' * 60}\nAUDIT RESULT: {PASS} checks passed, {len(FAIL)} failures")
for name, err in FAIL:
    print(f"  ✗ {name}: {err}")
sys.exit(1 if FAIL else 0)
