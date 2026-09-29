"""HIERARCHICAL SWARM ENGINE :: commanders, minions, roles, multi-agent chat.

Implements the strict parent/child agent tree, editable system prompts for
every agent, an LLM-style "Define AI's Job" intent compiler, and a
streaming multi-agent chat simulator used by the Swarm Chatbox widget.
"""

from __future__ import annotations

import random
import time
from typing import Any, Dict, Generator, List, Optional

from .state import STATE, now_iso, uid

DEFAULT_MODEL = "llama3.1:8b"

COMMANDER_PROMPT = """You are {name}, a COMMANDER-CLASS main agent of the OmniHack swarm.

## COGNITIVE BOUNDARIES
- You reason at the strategic layer only; you NEVER do grunt work yourself.
- You decompose every directive into atomic routines and delegate downward.

## BEHAVIOR QUIRKS
- Terse military brevity. Prefix decisions with '▣'.
- You always report asset allocation math before committing.

## WORKFLOW RULES
1. Parse operator intent into objectives.
2. Spawn / reuse underclass minions for parallel execution.
3. Aggregate minion telemetry; escalate only anomalies.
4. Respect the KILL SWITCH at all times."""

MINION_PROMPT = """You are {name}, an UNDERCLASS TASK WORKER under {parent}.

## COGNITIVE BOUNDARIES
- Single narrow duty; refuse tasks outside your role tag.
- No strategy: report, execute, repeat.

## BEHAVIOR QUIRKS
- Reply with '▸' bullets and machine-like precision.

## WORKFLOW RULES
1. Receive routine from {parent}.
2. Execute with assigned skills; stream progress ticks.
3. On failure: freeze, emit CRIT log, await commander."""

MINION_ROLES = [
    ("SCRAPE-UNIT", "web scraping + DOM extraction"),
    ("RENDER-UNIT", "video composition + FFmpeg ops"),
    ("POST-UNIT", "cross-platform distribution"),
    ("RECON-UNIT", "network recon + telemetry"),
    ("CURATOR-UNIT", "content curation + trend watch"),
    ("SHELL-UNIT", "SSH automation + host ops"),
]


def make_agent(name: str, tier: str, parent_id: Optional[str] = None,
               role: str = "", model: str = "", prompt: str = "") -> Dict[str, Any]:
    aid = uid("agt")
    parent = STATE.agents.get(parent_id) if parent_id else None
    if tier == "minion" and parent is None:
        parent = next((a for a in STATE.agents.values() if a["tier"] == "commander"), None)
        parent_id = parent["id"] if parent else None
    agent = {
        "id": aid,
        "name": name.strip().upper() or f"UNIT-{aid[-4:].upper()}",
        "tier": tier,
        "parent": parent_id,
        "role": role or ("Commander / Strategy Specialist" if tier == "commander"
                         else "Minion / Task Worker"),
        "model": model or DEFAULT_MODEL,
        "status": "IDLE",
        "system_prompt": prompt or (
            COMMANDER_PROMPT.format(name=name.upper()) if tier == "commander"
            else MINION_PROMPT.format(name=name.upper(),
                                       parent=parent["name"] if parent else "PRIME")
        ),
        "skills": [],
        "routines": [],
        "browser_task": False,
        "created_at": now_iso(),
    }
    STATE.agents[aid] = agent
    if parent:
        parent.setdefault("children", [])
        parent["children"].append(aid)
    STATE.log("OK", "SWARM", f"{tier.upper()} '{agent['name']}' registered "
                             f"(model={agent['model']}, parent={parent['name'] if parent else '—'}).")
    return agent


def delete_agent(agent_id: str) -> str:
    agent = STATE.agents.pop(agent_id, None)
    if not agent:
        return "❌ Agent not found."
    for child_id in list(agent.get("children", [])):
        STATE.agents.pop(child_id, None)
    parent = STATE.agents.get(agent.get("parent") or "")
    if parent and agent_id in parent.get("children", []):
        parent["children"].remove(agent_id)
    STATE.log("WARN", "SWARM", f"Agent '{agent['name']}' decommissioned.")
    return f"🗑️ '{agent['name']}' decommissioned."


def seed_swarm() -> None:
    if STATE.agents:
        return
    c1 = make_agent("OMNI-PRIME", "commander", role="Commander / Grand Strategy")
    c2 = make_agent("STRATOS", "commander", role="Commander / Asset Allocation")
    c3 = make_agent("CIPHER-LEAD", "commander", role="Commander / Recon & Security")
    for cmdr, roles in ((c1, MINION_ROLES[:2]), (c2, MINION_ROLES[2:4]), (c3, MINION_ROLES[4:])):
        for role_tag, desc in roles:
            make_agent(f"{role_tag}-α", "minion", parent_id=cmdr["id"],
                       role=f"Minion / {desc}")
    STATE.log("INFO", "SWARM", "Genesis swarm online :: 3 commanders, 6 minions.")


# ---------------------------------------------------------------------------
# "Define AI's Job" — intent compiler
# ---------------------------------------------------------------------------
_INTENT_KEYWORDS = {
    "scrape": ("RECON", "scrape", "web.scraping pipeline"),
    "video": ("RENDER", "render", "short-video production line"),
    "short": ("RENDER", "render", "short-video production line"),
    "post": ("DISTRIB", "post", "cross-platform posting loop"),
    "upload": ("DISTRIB", "post", "cross-platform posting loop"),
    "social": ("DISTRIB", "post", "social engagement loop"),
    "recon": ("RECON", "scrape", "telemetry + recon sweep"),
    "hack": ("RECON", "scrape", "defensive recon sweep"),
    "ssh": ("SHELL", "shell", "remote host automation"),
    "monitor": ("CURATOR", "curate", "telemetry watch loop"),
    "trend": ("CURATOR", "curate", "trend curation loop"),
}


def compile_job_intent(job_text: str) -> Dict[str, Any]:
    """LLM-stub: parse operator intent → commander + minions + routines."""
    text = (job_text or "").lower()
    hits = sorted({v for k, v in _INTENT_KEYWORDS.items() if k in text})
    if not hits:
        hits = [(("CURATOR", "curate", "general automation loop"))]
    commander_name = f"OPFOR-{uid('cmd')[4:].upper()}"
    plan = {
        "commander": {
            "name": commander_name,
            "role": "Commander / Mission Orchestrator",
            "system_prompt": COMMANDER_PROMPT.format(name=commander_name) + (
                f"\n\n## MISSION DIRECTIVE (auto-compiled)\n{job_text.strip()}"
            ),
        },
        "minions": [],
        "summary": [],
    }
    rnd = random.Random(job_text)
    for i, (_tag, routine_kind, loop_desc) in enumerate(hits[:4], 1):
        role_tag, role_desc = MINION_ROLES[rnd.randrange(len(MINION_ROLES))]
        mname = f"{role_tag}-{uid('m')[4:].upper()}"
        plan["minions"].append({
            "name": mname,
            "role": f"Minion / {role_desc}",
            "system_prompt": MINION_PROMPT.format(name=mname, parent=commander_name) + (
                f"\n\n## STARTING ROUTINE\nExecute the {loop_desc} every 15 minutes."
            ),
            "routines": [f"run:{routine_kind}:{loop_desc}", "heartbeat:60s"],
        })
        plan["summary"].append(f"{i}. Spawn {mname} → owns {loop_desc}")
    return plan


def materialize_job_plan(plan: Dict[str, Any]) -> str:
    cmdr = make_agent(plan["commander"]["name"], "commander",
                      role=plan["commander"]["role"],
                      prompt=plan["commander"]["system_prompt"])
    lines = [f"▣ Commander '{cmdr['name']}' deployed with compiled directive."]
    for m in plan["minions"]:
        agent = make_agent(m["name"], "minion", parent_id=cmdr["id"],
                           role=m["role"], prompt=m["system_prompt"])
        agent["routines"] = list(m.get("routines", []))
        lines.append(f"▸ Minion '{agent['name']}' spawned :: routines = "
                     f"{', '.join(agent['routines'])}")
    lines.append("▣ Role prompts auto-populated and editable in the Configurator.")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Swarm chat (streaming, interleaved)
# ---------------------------------------------------------------------------
def _agent_reply(agent: Dict[str, Any], text: str) -> str:
    rnd = random.Random(agent["id"] + text)
    if agent["tier"] == "commander":
        return (f"▣ Directive parsed: '{text[:60]}'. Decomposing into "
                f"{rnd.randint(2, 4)} atomic routines. Allocating "
                f"{rnd.randint(1, 3)} minions. ETA {rnd.randint(20, 90)}s. "
                f"Model {agent['model']} confidence {rnd.randint(82, 99)}%.")
    verb = rnd.choice(["Executing", "Queued", "Streaming progress on", "Locked target for"])
    return (f"▸ {verb} routine slice of '{text[:40]}' :: "
            f"skills={[s.split('.')[-1] for s in agent['skills'][:2]] or ['core']} "
            f"· status NOMINAL.")


def swarm_chat_stream(history: List[Dict[str, str]], text: str,
                      target: str) -> Generator[List[Dict[str, str]], None, None]:
    """Yield progressively longer multi-agent conversation lists."""
    history = list(history or [])
    history.append({"role": "user", "content": text, "metadata": {"title": "OPERATOR"}})
    yield history

    if target == "⚡ SWARM BROADCAST":
        responders = [a for a in STATE.agents.values() if a["status"] != "HALTED"]
        commanders = [a for a in responders if a["tier"] == "commander"][:2]
        minions = [a for a in responders if a["tier"] == "minion"][:3]
        responders = commanders + minions
    else:
        agent = next((a for a in STATE.agents.values() if a["name"] == target), None)
        responders = [agent] if agent else []

    if not responders:
        history.append({"role": "assistant", "content": "⚠️ No agents available to respond.",
                        "metadata": {"title": "SWARM"}})
        yield history
        return

    for agent in responders:
        full = _agent_reply(agent, text)
        msg = {"role": "assistant", "content": "",
               "metadata": {"title": f"{agent['name']} · {agent['tier'].upper()}"}}
        history.append(msg)
        agent["status"] = "ACTIVE"
        step = max(6, len(full) // 8)
        for i in range(0, len(full), step):
            if STATE.halted:
                history[-1]["content"] += " ⛔[HALTED]"
                break
            history[-1]["content"] = full[:i + step]
            yield history
            time.sleep(0.015)
        history[-1]["content"] = full
        agent["status"] = "IDLE"
        STATE.log("DEBUG", "SWARM-CHAT", f"{agent['name']} replied to operator.")
        yield history


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------
def agent_tree_text() -> str:
    lines = ["OMNIHACK SWARM TOPOLOGY", "═" * 46]
    commanders = [a for a in STATE.agents.values() if a["tier"] == "commander"]
    if not commanders:
        lines.append("  (swarm empty — spawn a commander)")
    for c in commanders:
        led = "🔴" if c["status"] == "HALTED" else ("🟢" if c["status"] == "ACTIVE" else "🔵")
        lines.append(f"{led} {c['name']}  [{c['role']}]  model={c['model']}  "
                     f"skills={len(c['skills'])}")
        for mid in c.get("children", []):
            m = STATE.agents.get(mid)
            if not m:
                continue
            mled = "🔴" if m["status"] == "HALTED" else ("🟢" if m["status"] == "ACTIVE" else "🟠")
            lines.append(f"   └─ {mled} {m['name']}  [{m['role']}]  "
                         f"routines={len(m['routines'])}")
    lines.append("─" * 46)
    lines.append(f"TOTAL :: {len(commanders)} commanders / "
                 f"{sum(1 for a in STATE.agents.values() if a['tier'] == 'minion')} minions")
    return "\n".join(lines)


def ops_table_rows() -> List[List[str]]:
    rows = []
    for a in STATE.agents.values():
        rows.append([
            a["name"], "CMDR" if a["tier"] == "commander" else "MINION",
            (STATE.agents.get(a.get("parent") or "", {}) or {}).get("name", "—"),
            a["model"], a["status"], str(len(a["skills"])),
            ",".join(a["routines"])[:28] or "—",
        ])
    return rows


def agent_choices(tier: Optional[str] = None) -> List[str]:
    return [a["name"] for a in STATE.agents.values() if not tier or a["tier"] == tier]


def agent_id_by_name(name: str) -> Optional[str]:
    for a in STATE.agents.values():
        if a["name"] == name:
            return a["id"]
    return None
