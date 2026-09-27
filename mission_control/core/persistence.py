"""CONFIG EXPORT / IMPORT :: serialize the entire swarm state to config.json."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Tuple

from .state import STATE

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
CONFIG_PATH = os.path.join(DATA_DIR, "config.json")


def _ensure_data_dir() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)


def export_config() -> Tuple[str, str]:
    """Write full mission state to config.json; return (path, summary)."""
    _ensure_data_dir()
    try:
        from .memory import MEMORY
        memory_stats = MEMORY.stats()
    except Exception:
        memory_stats = {"memories": 0, "lessons": 0}
    payload: Dict[str, Any] = {
        "meta": {"app": "OMNIHACK MISSION CONTROL", "version": "2.2.0",
                 "memory": memory_stats},
        "ollama_url": STATE.ollama_url,
        "hf_models": STATE.hf_models,
        "agents": STATE.agents,
        "connectors": STATE.connectors,
        "profiles": STATE.profiles,
        "daemons": STATE.daemons,
        "workflows": STATE.workflows,
        "github_cfg": STATE.github_cfg,
        "azure_cfg": STATE.azure_cfg,
        "content_queue": STATE.content_queue,
        "schedule": STATE.schedule,
        "hardware": STATE.hardware,
    }
    with open(CONFIG_PATH, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, default=str)
    size_kb = os.path.getsize(CONFIG_PATH) / 1024
    summary = (f"✅ Exported {len(STATE.agents)} agents · {len(STATE.profiles)} profiles · "
               f"{len(STATE.workflows)} workflows · {len(STATE.hf_models)} HF models "
               f"→ config.json ({size_kb:.1f} KB)")
    STATE.log("OK", "CONFIG", summary)
    return CONFIG_PATH, summary


def import_config(path: str) -> str:
    """Restore mission state from an uploaded config.json."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
    except Exception as exc:
        return f"❌ Import failed :: {exc}"

    STATE.ollama_url = payload.get("ollama_url", STATE.ollama_url)
    STATE.agents = payload.get("agents", STATE.agents) or {}
    STATE.connectors = payload.get("connectors", STATE.connectors) or {}
    STATE.profiles = payload.get("profiles", STATE.profiles) or {}
    STATE.daemons = payload.get("daemons", STATE.daemons) or {}
    STATE.workflows = payload.get("workflows", STATE.workflows) or {}
    STATE.github_cfg = payload.get("github_cfg", STATE.github_cfg) or {}
    STATE.azure_cfg = payload.get("azure_cfg", STATE.azure_cfg) or {}
    STATE.hf_models = payload.get("hf_models", STATE.hf_models) or []
    STATE.content_queue = payload.get("content_queue", []) or []
    STATE.schedule = payload.get("schedule", []) or []
    if payload.get("hardware"):
        STATE.hardware = payload["hardware"]
    summary = (f"✅ Config restored :: {len(STATE.agents)} agents · "
               f"{len(STATE.profiles)} profiles · {len(STATE.workflows)} workflows · "
               f"{len(STATE.connectors)} connector sets.")
    STATE.log("OK", "CONFIG", f"Import complete :: {summary}")
    return summary


# ---------------------------------------------------------------------------
# lightweight per-domain persistence (social connectors / profiles)
# ---------------------------------------------------------------------------
def save_connectors() -> str:
    _ensure_data_dir()
    p = os.path.join(DATA_DIR, "connectors.json")
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(STATE.connectors, fh, indent=2)
    return f"💾 Connector vault persisted → {p}"


def save_profiles() -> str:
    _ensure_data_dir()
    p = os.path.join(DATA_DIR, "profiles.json")
    with open(p, "w", encoding="utf-8") as fh:
        json.dump({"profiles": STATE.profiles, "daemons": STATE.daemons}, fh, indent=2)
    return f"💾 Profile matrix persisted → {p}"


def load_persisted() -> str:
    _ensure_data_dir()
    notes = []
    p = os.path.join(DATA_DIR, "connectors.json")
    if os.path.isfile(p):
        try:
            STATE.connectors = json.load(open(p, encoding="utf-8"))
            notes.append(f"{len(STATE.connectors)} connectors")
        except Exception:
            pass
    p = os.path.join(DATA_DIR, "profiles.json")
    if os.path.isfile(p):
        try:
            blob = json.load(open(p, encoding="utf-8"))
            STATE.profiles = blob.get("profiles", {})
            STATE.daemons = blob.get("daemons", {})
            notes.append(f"{len(STATE.profiles)} profiles")
        except Exception:
            pass
    if notes:
        STATE.log("INFO", "CONFIG", f"Persisted vault loaded :: {', '.join(notes)}.")
    return " | ".join(notes) or "no persisted vault yet"
