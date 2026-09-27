"""UNIVERSAL OLLAMA ENGINE with native HuggingFace model support.

Talks to a real Ollama instance when reachable (``/api/version``,
``/api/tags``, ``/api/pull``) and transparently falls back to a fully
simulated model manager so the Mission Control UI always works — even
with no daemon running on the VPS.

HuggingFace support
-------------------
* ``pull_hf("hf.co/QuantFactory/Mistral-7B-Instruct-v0.3-GGUF")`` style tags
  are first-class: they are pulled through the same pipeline and can be
  bound to any agent instantly.
* ``scan_gguf_directory()`` scans a local directory (default ``/home/models``)
  for ``*.gguf`` weights so a custom Modelfile can be generated on the fly.
"""

from __future__ import annotations

import json
import os
import random
import time
from typing import Any, Dict, Generator, List, Optional

import requests

from .state import STATE

DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODELS_DIR = "/home/models"

# Fallback catalogue returned when the daemon is unreachable.
MOCK_TAGS: List[Dict[str, Any]] = [
    {"name": "llama3.1:8b", "size": 4_900_000_000, "family": "llama",
     "modified_at": "2026-09-20T11:02:00Z", "details": {"quantization": "Q4_K_M"}},
    {"name": "qwen2.5-coder:14b", "size": 8_900_000_000, "family": "qwen2",
     "modified_at": "2026-09-18T09:41:00Z", "details": {"quantization": "Q4_K_M"}},
    {"name": "mistral-nemo:12b", "size": 7_100_000_000, "family": "mistral",
     "modified_at": "2026-09-15T22:10:00Z", "details": {"quantization": "Q5_K_S"}},
    {"name": "phi3.5:3.8b", "size": 2_200_000_000, "family": "phi3",
     "modified_at": "2026-09-12T07:55:00Z", "details": {"quantization": "Q4_0"}},
    {"name": "llava:13b-v1.6", "size": 8_000_000_000, "family": "llava",
     "modified_at": "2026-09-10T16:20:00Z", "details": {"quantization": "Q4_K_M"}},
    {"name": "nomic-embed-text:latest", "size": 274_000_000, "family": "bert",
     "modified_at": "2026-09-02T13:00:00Z", "details": {"quantization": "F16"}},
]

MOCK_GGUF_FILES = [
    {"path": "/home/models/mistral-7b-instruct-v0.3.Q4_K_M.gguf", "size_gb": 4.37},
    {"path": "/home/models/qwen2.5-14b-instruct.Q5_K_M.gguf", "size_gb": 10.2},
    {"path": "/home/models/llama-3.1-8b.Q8_0.gguf", "size_gb": 8.54},
    {"path": "/home/models/gemma-2-9b-it.Q4_K_S.gguf", "size_gb": 5.44},
]

_WORD_POOL = (
    "Affirmative — vector locked. Routing subtask to underclass workers. "
    "Objective parsed into 3 atomic routines. Allocation: 2 minions for scrape, "
    "1 minion for render. ETA 42 seconds. Telemetry nominal. Proceeding."
)


class OllamaEngine:
    """Connection + model manager facade used by every UI tab."""

    def __init__(self) -> None:
        self.base_url: str = DEFAULT_OLLAMA_URL
        self.connected: bool = False
        self.server_version: str = "SIMULATED"
        self._rnd = random.Random(4242)

    # ------------------------------------------------------------- connection
    def set_url(self, url: str) -> None:
        self.base_url = (url or DEFAULT_OLLAMA_URL).rstrip("/")
        STATE.ollama_url = self.base_url

    def ping(self) -> Dict[str, Any]:
        try:
            r = requests.get(f"{self.base_url}/api/version", timeout=2.5)
            r.raise_for_status()
            self.connected = True
            self.server_version = r.json().get("version", "unknown")
            STATE.ollama_connected = True
            STATE.log("OK", "OLLAMA", f"Connected to live daemon :: {self.base_url} "
                                      f"(v{self.server_version})")
            return {"connected": True, "version": self.server_version, "simulated": False}
        except Exception:
            self.connected = False
            self.server_version = "SIMULATED"
            STATE.ollama_connected = False
            STATE.log("WARN", "OLLAMA", f"No daemon at {self.base_url} — "
                                        f"entering SIMULATED ENGINE mode.")
            return {"connected": False, "version": "SIMULATED", "simulated": True}

    # ---------------------------------------------------------------- models
    def list_tags(self) -> List[Dict[str, Any]]:
        """Fetch loaded models from /api/tags, fallback to mock catalogue."""
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=2.5)
            r.raise_for_status()
            models = r.json().get("models", [])
            for m in models:
                m.setdefault("origin", "ollama")
            STATE.models = models
            return models
        except Exception:
            models = [dict(m, origin="ollama-sim") for m in MOCK_TAGS]
            STATE.models = models
            return models

    def all_model_names(self) -> List[str]:
        names = [m["name"] for m in STATE.models]
        names += [m["name"] for m in STATE.hf_models if m["name"] not in names]
        return names or [m["name"] for m in MOCK_TAGS]

    # ------------------------------------------------------------------ pulls
    def pull(self, tag: str) -> Dict[str, Any]:
        """Pull a model tag. Tries the real API, simulates on failure."""
        tag = (tag or "").strip()
        if not tag:
            return {"ok": False, "error": "Empty model tag."}
        if self.connected:
            try:
                r = requests.post(f"{self.base_url}/api/pull",
                                  json={"name": tag, "stream": False}, timeout=15)
                if r.ok:
                    STATE.log("OK", "OLLAMA", f"Live pull complete :: {tag}")
                    self.list_tags()
                    return {"ok": True, "tag": tag, "simulated": False,
                            "size": next((m.get("size", 0) for m in STATE.models
                                          if m["name"] == tag), "n/a")}
            except Exception:
                pass
        size = self._rnd.randint(2_000, 26_000) / 1000  # GB
        STATE.log("INFO", "OLLAMA", f"[SIM] Pulled {tag} ({size:.1f} GB) into model vault.")
        self.list_tags()
        STATE.models = [m for m in STATE.models if m["name"] != tag] + [{
            "name": tag, "size": int(size * 1e9), "family": tag.split(":")[0],
            "modified_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "details": {"quantization": "Q4_K_M"}, "origin": "ollama-sim",
        }]
        return {"ok": True, "tag": tag, "simulated": True, "size": f"{size:.1f} GB"}

    def pull_hf(self, repo_id: str, filename: Optional[str] = None) -> Dict[str, Any]:
        """Pull a HuggingFace repo model through Ollama.

        Accepts ``hf.co/Org/Repo-GGUF`` or bare ``Org/Repo-GGUF`` style ids,
        mirroring ``ollama run hf.co/QuantFactory/Mistral-7B-Instruct-v0.3-GGUF``.
        """
        repo_id = (repo_id or "").strip()
        if not repo_id:
            return {"ok": False, "error": "Empty HF repo id."}
        if "/" not in repo_id:
            return {"ok": False, "error": "HF repo id must look like 'Org/Repo-GGUF'."}
        tag = repo_id if repo_id.startswith("hf.co/") else f"hf.co/{repo_id}"
        receipt = self.pull(tag)
        entry = {
            "name": tag,
            "repo_id": repo_id,
            "filename": filename or "auto (largest GGUF)",
            "quantization": self._rnd.choice(["Q4_K_M", "Q5_K_M", "Q6_K", "Q8_0"]),
            "size": receipt.get("size", "n/a"),
            "bound_agents": [],
            "pulled_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        STATE.hf_models = [m for m in STATE.hf_models if m["name"] != tag] + [entry]
        STATE.log("OK", "HF-ENGINE", f"HuggingFace model online :: {tag}")
        return receipt

    # ------------------------------------------------------------- modelfiles
    def scan_gguf_directory(self, root: str = DEFAULT_MODELS_DIR) -> List[Dict[str, Any]]:
        """Scan a directory for local GGUF weights (mock entries if absent)."""
        found: List[Dict[str, Any]] = []
        root = (root or DEFAULT_MODELS_DIR).strip() or DEFAULT_MODELS_DIR
        try:
            if os.path.isdir(root):
                for dirpath, _dirs, files in os.walk(root):
                    for fn in files:
                        if fn.lower().endswith(".gguf"):
                            p = os.path.join(dirpath, fn)
                            found.append({"path": p,
                                          "size_gb": round(os.path.getsize(p) / 1e9, 2)})
        except OSError:
            pass
        if not found:
            found = [dict(f) for f in MOCK_GGUF_FILES]
            found[0]["path"] = os.path.join(root, os.path.basename(found[0]["path"]))
            STATE.log("WARN", "HF-ENGINE", f"{root} not readable on this host — "
                                           f"showing vault snapshot (simulated).")
        else:
            STATE.log("OK", "HF-ENGINE", f"Scanned {root} :: {len(found)} GGUF weight(s).")
        STATE.local_gguf = found
        return found

    def build_modelfile(self, gguf_path: str, model_name: str,
                        system_prompt: str = "") -> Dict[str, Any]:
        """Generate a Modelfile binding a local GGUF to a new Ollama model."""
        model_name = (model_name or "custom-gguf").strip().replace(" ", "-").lower()
        modelfile = (
            f"FROM {gguf_path}\n"
            f"PARAMETER temperature 0.7\n"
            f"PARAMETER num_ctx 8192\n"
            f'TEMPLATE """{{{{ .Prompt }}}}"""\n'
        )
        if system_prompt.strip():
            modelfile += f'SYSTEM """{system_prompt.strip()}"""\n'
        if self.connected:
            try:
                r = requests.post(f"{self.base_url}/api/create",
                                  json={"name": model_name, "modelfile": modelfile},
                                  timeout=15)
                if r.ok:
                    self.list_tags()
                    STATE.log("OK", "HF-ENGINE", f"Live Modelfile created :: {model_name}")
                    return {"ok": True, "model": model_name, "modelfile": modelfile,
                            "simulated": False}
            except Exception:
                pass
        STATE.models = [m for m in STATE.models if m["name"] != model_name] + [{
            "name": model_name, "size": 0, "family": "gguf-custom",
            "modified_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "details": {"quantization": "local-gguf"}, "origin": "modelfile",
        }]
        STATE.log("OK", "HF-ENGINE", f"[SIM] Modelfile registered :: {model_name} "
                                     f"← {gguf_path}")
        return {"ok": True, "model": model_name, "modelfile": modelfile, "simulated": True}

    # ------------------------------------------------------------- generation
    def generate_stream(self, model: str, prompt: str,
                        words_per_chunk: int = 6) -> Generator[str, None, None]:
        """Stream a simulated completion (word chunks) for any bound model."""
        base = (_WORD_POOL if not prompt else
                f"Model '{model}' engaged. Processing directive: "
                f"'{prompt[:120]}'. " + _WORD_POOL)
        words = base.split()
        for i in range(0, len(words), words_per_chunk):
            if STATE.halted:
                yield " ⛔ [HALTED BY KILL SWITCH]"
                return
            yield " ".join(words[i:i + words_per_chunk]) + " "
            time.sleep(0.03)

    def generate_once(self, model: str, prompt: str) -> str:
        return "".join(self.generate_stream(model, prompt))


ENGINE = OllamaEngine()


def bind_model_to_agent(agent_id: str, model: str) -> str:
    """Bind any model (native, hf.co or custom GGUF) to an agent instantly."""
    agent = STATE.agents.get(agent_id)
    if agent is None:
        return f"❌ Unknown agent '{agent_id}'."
    agent["model"] = model
    for m in STATE.hf_models:
        if m["name"] == model and agent_id not in m["bound_agents"]:
            m["bound_agents"].append(agent_id)
    STATE.log("OK", "HF-ENGINE", f"Model '{model}' hot-bound to agent '{agent['name']}'.")
    return f"✅ '{model}' bound to {agent['name']} — effective immediately."
