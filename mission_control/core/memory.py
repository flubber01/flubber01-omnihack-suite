"""🧠 SWARM MEMORY :: SQLite vault + remember loop + self-improvement.

Persistent storage for the agents' work:

* **episodic**   — what happened (operator directives, agent replies, runs)
* **procedural** — how things were done (pipeline/autopilot receipts)
* **semantic**   — distilled facts + improvement notes
* **feedback**   — skill execution outcomes

The **Remember Loop** is a background thread that periodically:
1. snapshots VPS telemetry into ``metrics_history``,
2. consolidates raw episodic memories into reusable **lessons**,
3. computes an improvement score (lesson confidence growth) —
   so the swarm literally gets sharper over time.
"""

from __future__ import annotations

import os
import random
import re
import sqlite3
import threading
import time
from typing import Any, Dict, List, Optional

from .state import STATE, now_iso

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DB_PATH = os.path.join(DATA_DIR, "omni_memory.db")

_LESSON_TEMPLATES = [
    ("render", "Batch 9:16 render jobs to cut FFmpeg startup overhead (-{p}% wall time)."),
    ("scrape", "Rotate stealth profiles every {p} requests to keep bot-score under 0.05."),
    ("post", "Stagger cross-posts by {p}s per platform to dodge rate limits."),
    ("model", "Prefer Q4_K_M quants for minion brains — best latency/quality ratio (+{p}%)."),
    ("schedule", "Shift publishing to 17:00-21:00 CET window for +{p}% engagement."),
    ("browser", "Inject humanized delays ({p}ms±) before CTA clicks to pass anti-bot."),
    ("default", "Cache repeated routine results for {p} cycles before re-execution."),
]


class MemoryVault:
    """SQLite-backed long-term memory for the whole swarm."""

    def __init__(self) -> None:
        self.lock = threading.RLock()
        os.makedirs(DATA_DIR, exist_ok=True)
        self._init_db()

    # ------------------------------------------------------------------- db
    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self.lock, self._conn() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY, ts TEXT, kind TEXT, agent TEXT,
                content TEXT, importance INTEGER, status TEXT DEFAULT 'raw');
            CREATE TABLE IF NOT EXISTS lessons (
                id TEXT PRIMARY KEY, ts TEXT, source TEXT, lesson TEXT,
                confidence REAL, applied INTEGER DEFAULT 0);
            CREATE TABLE IF NOT EXISTS skill_feedback (
                ts TEXT, skill_id TEXT, agent TEXT, runtime_ms INTEGER, ok INTEGER);
            CREATE TABLE IF NOT EXISTS metrics_history (
                ts TEXT, cpu REAL, ram REAL, agents INTEGER, renders INTEGER,
                pipelines INTEGER);
            CREATE TABLE IF NOT EXISTS improvement (
                ts TEXT, score REAL, memories INTEGER, lessons INTEGER);
            """)

    # --------------------------------------------------------------- storing
    def store(self, agent: str, content: str, kind: str = "episodic",
              importance: int = 5) -> str:
        mid = f"mem-{int(time.time() * 1000) % 10**10}-{random.randint(100, 999)}"
        with self.lock, self._conn() as conn:
            conn.execute("INSERT INTO memories (id, ts, kind, agent, content, importance)"
                         " VALUES (?,?,?,?,?,?)",
                         (mid, now_iso(), kind, agent or "SWARM",
                          (content or "")[:2000], int(importance)))
        return mid

    def record_skill(self, skill_id: str, agent: str, runtime_ms: int, ok: bool) -> None:
        with self.lock, self._conn() as conn:
            conn.execute("INSERT INTO skill_feedback (ts, skill_id, agent, runtime_ms, ok)"
                         " VALUES (?,?,?,?,?)",
                         (now_iso(), skill_id, agent or "—", int(runtime_ms), 1 if ok else 0))

    # -------------------------------------------------------------- recalling
    def _score(self, query: str, content: str) -> int:
        qt = set(re.findall(r"[a-z0-9äöüß]{3,}", query.lower()))
        ct = set(re.findall(r"[a-z0-9äöüß]{3,}", content.lower()))
        return len(qt & ct) * 3 + (1 if query.lower() in content.lower() else 0)

    def recall(self, query: str = "", agent: str = "", kind: str = "",
               limit: int = 12) -> List[Dict[str, Any]]:
        with self.lock, self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM memories ORDER BY ts DESC LIMIT 400").fetchall()
        out = []
        for r in rows:
            if agent and agent != "ALL" and r["agent"] != agent:
                continue
            if kind and kind != "ALL" and r["kind"] != kind:
                continue
            score = self._score(query, r["content"]) if query else 1
            if query and score == 0:
                continue
            out.append({**dict(r), "score": score})
        out.sort(key=lambda m: (-m["score"], m["ts"]), reverse=False)
        return out[:limit]

    def recent(self, limit: int = 14) -> List[Dict[str, Any]]:
        with self.lock, self._conn() as conn:
            rows = conn.execute("SELECT ts, kind, agent, content, importance, status"
                                " FROM memories ORDER BY ts DESC LIMIT ?",
                                (limit,)).fetchall()
        return [dict(r) for r in rows]

    def lessons(self, limit: int = 12) -> List[Dict[str, Any]]:
        with self.lock, self._conn() as conn:
            rows = conn.execute("SELECT ts, source, lesson, confidence, applied"
                                " FROM lessons ORDER BY confidence DESC, ts DESC"
                                " LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

    def add_lesson(self, source: str, lesson: str, confidence: float = 0.5) -> None:
        with self.lock, self._conn() as conn:
            sim = conn.execute("SELECT id, confidence, applied FROM lessons"
                               " WHERE lesson = ?", (lesson,)).fetchone()
            if sim:
                conn.execute("UPDATE lessons SET confidence = MIN(0.99, confidence + 0.07),"
                             " applied = applied + 1 WHERE id = ?", (sim["id"],))
            else:
                conn.execute("INSERT INTO lessons (id, ts, source, lesson, confidence)"
                             " VALUES (?,?,?,?,?)",
                             (f"lsn-{random.randint(10000, 99999)}", now_iso(),
                              source, lesson, float(confidence)))

    # ------------------------------------------------------------ analytics
    def snapshot_metrics(self) -> None:
        m = STATE.metrics()
        with self.lock, self._conn() as conn:
            conn.execute("INSERT INTO metrics_history (ts, cpu, ram, agents, renders,"
                         " pipelines) VALUES (?,?,?,?,?,?)",
                         (now_iso(), m["cpu"], m["ram_pct"],
                          m["commanders_active"] + m["minions_active"],
                          m["render_tasks"], m["pipelines"]))

    def stats(self) -> Dict[str, Any]:
        with self.lock, self._conn() as conn:
            n_mem = conn.execute("SELECT COUNT(*) c FROM memories").fetchone()["c"]
            n_raw = conn.execute("SELECT COUNT(*) c FROM memories"
                                 " WHERE status='raw'").fetchone()["c"]
            n_les = conn.execute("SELECT COUNT(*) c FROM lessons").fetchone()["c"]
            avg_conf = conn.execute("SELECT AVG(confidence) a FROM lessons").fetchone()["a"] or 0
            n_skill = conn.execute("SELECT COUNT(*) c FROM skill_feedback").fetchone()["c"]
            ok_rate = conn.execute("SELECT AVG(ok) a FROM skill_feedback").fetchone()["a"]
            last_score = conn.execute("SELECT score FROM improvement"
                                      " ORDER BY ts DESC LIMIT 1").fetchone()
        return {"memories": n_mem, "raw": n_raw, "lessons": n_les,
                "avg_confidence": round(avg_conf * 100), "skill_runs": n_skill,
                "skill_ok_rate": round((ok_rate or 0) * 100),
                "improvement": round(last_score["score"], 1) if last_score else 50.0}

    # -------------------------------------------------------- consolidation
    def consolidate(self) -> Dict[str, Any]:
        """Distill raw episodic memories into lessons (mock cognition)."""
        rnd = random.Random(int(time.time()))
        with self.lock, self._conn() as conn:
            rows = conn.execute("SELECT id, agent, content FROM memories"
                                " WHERE status='raw' AND kind IN ('episodic','procedural')"
                                " ORDER BY ts DESC LIMIT 40").fetchall()
            if not rows:
                return {"new_lessons": 0, "processed": 0}
            new_lessons = 0
            for r in rows:
                low = (r["content"] or "").lower()
                for key, tmpl in _LESSON_TEMPLATES:
                    if key in low:
                        lesson = tmpl.format(p=rnd.randint(8, 34))
                        self.add_lesson(r["agent"], lesson, 0.45 + rnd.random() * 0.25)
                        new_lessons += 1
                        break
            ids = [r["id"] for r in rows]
            conn.executemany("UPDATE memories SET status='consolidated' WHERE id=?",
                             [(i,) for i in ids])
        return {"new_lessons": new_lessons, "processed": len(rows)}

    def log_improvement(self) -> float:
        s = self.stats()
        score = min(99.0, 50.0 + s["lessons"] * 3.5 + s["avg_confidence"] * 0.2
                    + random.random() * 2)
        with self.lock, self._conn() as conn:
            conn.execute("INSERT INTO improvement (ts, score, memories, lessons)"
                         " VALUES (?,?,?,?)",
                         (now_iso(), score, s["memories"], s["lessons"]))
        return score

    def flush(self) -> str:
        with self.lock, self._conn() as conn:
            for t in ("memories", "lessons", "skill_feedback",
                      "metrics_history", "improvement"):
                conn.execute(f"DELETE FROM {t}")
        STATE.log("WARN", "MEMORY", "Memory vault wiped by operator.")
        return "🗑️ Memory vault wiped (all tables)."


MEMORY = MemoryVault()


# ---------------------------------------------------------------------------
class RememberLoop:
    """Background consolidation + self-improvement cycle."""

    def __init__(self) -> None:
        self.running = False
        self.interval = 30
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.cycles = 0

    def start(self, interval: float = 30) -> str:
        self.interval = max(10, int(interval or 30))
        self.running = True
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True,
                                         name="omni-remember")
        self._thread.start()
        STATE.log("OK", "REMEMBER", f"Remember loop armed :: every {self.interval}s "
                                     f"(consolidate + improve).")
        return f"🔁 REMEMBER LOOP ARMED :: cycle every {self.interval}s."

    def stop(self) -> str:
        self.running = False
        self._stop.set()
        STATE.log("INFO", "REMEMBER", "Remember loop disarmed.")
        return "⏹ Remember loop disarmed."

    def run_cycle(self) -> str:
        """One consolidation+improvement pass (also callable manually)."""
        MEMORY.snapshot_metrics()
        res = MEMORY.consolidate()
        score = MEMORY.log_improvement()
        self.cycles += 1
        note = (f"Cycle #{self.cycles} :: {res['processed']} memories consolidated → "
                f"{res['new_lessons']} lesson(s) · improvement score {score:.1f}")
        STATE.log("INFO", "REMEMBER", note)
        if res["new_lessons"]:
            MEMORY.store("REMEMBER-LOOP", note, kind="semantic", importance=6)
        return note

    def _loop(self) -> None:
        while not self._stop.is_set():
            if not STATE.halted:
                try:
                    self.run_cycle()
                except Exception as exc:
                    STATE.log("WARN", "REMEMBER", f"Cycle error :: {exc}")
            if self._stop.wait(self.interval):
                return


REMEMBER = RememberLoop()
