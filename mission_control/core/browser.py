"""LIVE BROWSER STREAM :: simulated remote browser with screenshot stream.

Renders a convincing headless-browser viewport with Pillow (chrome bar,
URL field, dynamic content seeded from the URL), tracks a DOM tree, records
click/type/scroll actions, and exposes an "Ollama bridge" where a bound
model reads the DOM + screenshot and injects inputs to drive the page.

When a real Playwright/browser-use stack is attached to the VPS the same
call surface applies — every method here is the integration seam.
"""

from __future__ import annotations

import hashlib
import io
import random
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

from .state import STATE

try:
    from .theme import BG_DEEP, GRID_LINE, NEON_AMBER, NEON_CYAN, NEON_GREEN, NEON_MAGENTA, NEON_RED
except Exception:  # pragma: no cover
    BG_DEEP, GRID_LINE = "#03060b", "#0e2233"
    NEON_GREEN, NEON_CYAN = "#00ff9f", "#00e5ff"
    NEON_MAGENTA, NEON_AMBER, NEON_RED = "#ff2bd6", "#ffb300", "#ff3b5c"

WIDTH, HEIGHT = 1024, 640

_HEADLINES = [
    "Swarm telemetry index climbs 4.2% as edge clusters expand",
    "QuantFactory pushes Mistral-7B GGUF quants to mirror network",
    "Autonomous render farm hits 1,200 shorts/day milestone",
    "VPS spot pricing dips — arbitrage windows open in eu-central",
    "Browser-use 3.0 lands stealth fingerprint rotation",
    "Neural voiceover packs licensed for commercial shorts",
    "Grid operators report zero downtime during firmware flash",
    "Underclass minion pool autoscales past 64 concurrent workers",
]
_SIDEBAR = ["#mission-control", "#render-farm", "#hf-models", "#browser-ops",
            "#social-daemons", "#skill-lab", "#ssh-bridge", "#kill-switch"]
_TICKER = ["OMNI", "FLUX", "NEON", "GRID", "VOLT", "PULSE", "ZERO", "APEX"]


def _seeded(url: str, salt: int = 0) -> random.Random:
    h = int(hashlib.sha256(f"{url}:{salt}".encode()).hexdigest(), 16)
    return random.Random(h)


class BrowserInstance:
    """State machine behind the screenshot stream + AI control bridge."""

    def __init__(self) -> None:
        self.url = "https://nexus.grid/portal"
        self.title = "NEXUS // Mission Portal"
        self.scroll = 0
        self.typed_buffer = ""
        self.last_click: Optional[Tuple[int, int]] = None
        self.actions: List[Dict[str, Any]] = []
        self.ai_log: List[str] = []
        self.page_version = 0

    # ------------------------------------------------------------------ utils
    def _record(self, kind: str, detail: str) -> Dict[str, Any]:
        entry = {"ts": time.strftime("%H:%M:%S"), "kind": kind, "detail": detail,
                 "url": self.url}
        self.actions.append(entry)
        STATE.browser_actions = self.actions[-40:]
        STATE.log("INFO", "BROWSER", f"{kind.upper()} :: {detail}")
        self.page_version += 1
        return entry

    # -------------------------------------------------------------- navigation
    def navigate(self, url: str) -> str:
        url = (url or "").strip() or self.url
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        self.url = url
        host = url.split("//", 1)[-1].split("/", 1)[0]
        self.title = f"{host.split('.')[0].upper()} // Remote Session"
        self.scroll = 0
        self.typed_buffer = ""
        self._record("goto", url)
        return f"🌐 NAVIGATED → {url}"

    def click(self, x: int, y: int) -> str:
        x = max(0, min(WIDTH, int(x)))
        y = max(0, min(HEIGHT, int(y)))
        self.last_click = (x, y)
        zone = self._zone_for(x, y)
        self._record("click", f"({x}, {y}) → {zone}")
        return f"🖱️ CLICK ({x},{y}) hit **{zone}** — DOM event dispatched."

    def _zone_for(self, x: int, y: int) -> str:
        if y < 64:
            return "chrome/tab-bar" if x < 500 else "url-field"
        if x < 230:
            return "sidebar-nav"
        if y > HEIGHT - 40:
            return "status-bar"
        return "content-card"

    def type_text(self, text: str) -> str:
        text = (text or "").strip()
        if not text:
            return "⌨️ Nothing to type."
        self.typed_buffer = text
        self._record("type", f"{len(text)} chars into focused field")
        return f"⌨️ TYPED {len(text)} chars → focused input."

    def scroll_by(self, dy: int) -> str:
        self.scroll = max(0, self.scroll + int(dy))
        self._record("scroll", f"Δy={dy}px (now {self.scroll}px)")
        return f"📜 SCROLLED Δ{dy}px — viewport at {self.scroll}px."

    # -------------------------------------------------------------------- DOM
    def dom_summary(self) -> str:
        rnd = _seeded(self.url, self.page_version)
        cards = rnd.randint(4, 7)
        lines = [
            f"DOM SNAPSHOT :: {self.url}  (rev {self.page_version}, scroll {self.scroll}px)",
            "├─ <html lang=\"en\">",
            "│  ├─ <header class=\"chrome\">",
            f"│  │  ├─ <input id=\"url\" value=\"{self.url}\">",
            "│  │  └─ <button id=\"reload\">",
            "│  ├─ <nav class=\"sidebar\">",
        ]
        lines += [f"│  │  ├─ <a href=\"#{s.strip('#')}\">{s}</a>" for s in _SIDEBAR[:5]]
        lines.append("│  ├─ <main class=\"feed\">")
        for i in range(cards):
            headline = rnd.choice(_HEADLINES)
            lines.append(f"│  │  ├─ <article id=\"card-{i}\">")
            lines.append(f"│  │  │  ├─ <h2>{headline}</h2>")
            lines.append(f"│  │  │  ├─ <span class=\"ticker\">${rnd.choice(_TICKER)} "
                         f"+{rnd.uniform(0.1, 9.9):.1f}%</span>")
            lines.append("│  │  │  └─ <button class=\"cta\">ENGAGE</button>")
        lines.append("│  └─ <footer class=\"status\">session=encrypted · bot-score=0.02</footer>")
        lines.append(f"└─ focused: <input id=\"search\" value=\"{self.typed_buffer}\">")
        return "\n".join(lines)

    # -------------------------------------------------------------- AI bridge
    def ai_inspect(self, model: str) -> str:
        rnd = _seeded(self.url, self.page_version * 7 + 1)
        plan = [
            f"[VISION] Screenshot ingested by {model} ({WIDTH}x{HEIGHT}, rev {self.page_version}).",
            f"[DOM] Parsed {rnd.randint(120, 420)} nodes; bot-score 0.02 — stealth profile clean.",
            f"[GOAL] Infer operator intent → drive engagement loop on {self.url.split('//')[-1].split('/')[0]}.",
            f"[PLAN-1] click sidebar '#{rnd.choice(_SIDEBAR).strip('#')}' ({rnd.randint(30, 200)}, {rnd.randint(120, 520)})",
            f"[PLAN-2] type query '{rnd.choice(['swarm status', 'hf models', 'render queue', 'proxy pool'])}' into #search",
            f"[PLAN-3] click content-card #{rnd.randint(0, 3)} CTA after {rnd.randint(300, 900)}ms humanized delay",
            "[SAFETY] No credential fields detected. Rate limiter respected.",
        ]
        self.ai_log = plan
        STATE.log("INFO", "AI-BRIDGE", f"{model} inspected DOM+screenshot of {self.url}")
        return "\n".join(plan)

    def ai_autopilot(self, model: str) -> List[str]:
        """Execute the planned actions — the model drives keyboard/mouse."""
        if not self.ai_log:
            self.ai_inspect(model)
        rnd = _seeded(self.url, self.page_version * 13)
        results: List[str] = []
        x, y = rnd.randint(30, 210), rnd.randint(140, 540)
        self.click(x, y)
        results.append(f"✔ {model} clicked sidebar ({x},{y})")
        query = rnd.choice(["swarm status", "hf models", "render queue", "proxy pool"])
        self.type_text(query)
        results.append(f"✔ {model} typed '{query}' into #search")
        self.scroll_by(rnd.randint(120, 420))
        results.append(f"✔ {model} scrolled {self.scroll}px")
        cx, cy = rnd.randint(260, 980), rnd.randint(120, 560)
        self.click(cx, cy)
        results.append(f"✔ {model} clicked CTA card ({cx},{cy}) — anti-bot score 0.02")
        STATE.log("OK", "AI-BRIDGE", f"{model} executed 4-step autopilot on {self.url}")
        return results


BROWSER = BrowserInstance()


# ---------------------------------------------------------------------------
# Screenshot rendering (Pillow)
# ---------------------------------------------------------------------------
def _font(size: int) -> ImageFont.FreeTypeFont:
    for path in ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def screenshot() -> Image.Image:
    """Render the current page state to a PIL image (fake live stream)."""
    rnd = _seeded(BROWSER.url, BROWSER.page_version + BROWSER.scroll // 40)
    img = Image.new("RGB", (WIDTH, HEIGHT), "#05080d")
    dr = ImageDraw.Draw(img)

    # subtle grid
    for gx in range(0, WIDTH, 64):
        dr.line([(gx, 0), (gx, HEIGHT)], fill="#0a141f", width=1)
    for gy in range(0, HEIGHT, 64):
        dr.line([(0, gy), (WIDTH, gy)], fill="#0a141f", width=1)

    # chrome bar
    dr.rectangle([0, 0, WIDTH, 64], fill="#0a1119")
    dr.line([(0, 64), (WIDTH, 64)], fill=NEON_CYAN, width=1)
    for i, color in enumerate([NEON_RED, NEON_AMBER, NEON_GREEN]):
        dr.ellipse([14 + i * 22, 12, 28 + i * 22, 26], fill=color)
    dr.rectangle([100, 10, 480, 34], fill="#101c29", outline=GRID_LINE)
    dr.text((110, 14), f"◉ {BROWSER.title[:38]}", font=_font(13), fill=NEON_GREEN)
    dr.rectangle([100, 40, 930, 58], fill="#060d15", outline="#1c3448")
    dr.text((110, 42), f"🔒 {BROWSER.url[:96]}", font=_font(12), fill="#9adcff")
    dr.rectangle([940, 12, 1010, 52], fill="#0d2233", outline=NEON_CYAN)
    dr.text((952, 18), "STEALTH", font=_font(11), fill=NEON_CYAN)

    # sidebar
    dr.rectangle([0, 64, 230, HEIGHT - 28], fill="#070d15")
    dr.line([(230, 64), (230, HEIGHT - 28)], fill=GRID_LINE)
    for i, item in enumerate(_SIDEBAR):
        y = 92 + i * 44 - (BROWSER.scroll // 6) % 44
        if 64 < y < HEIGHT - 60:
            active = i == (BROWSER.page_version % len(_SIDEBAR))
            if active:
                dr.rectangle([6, y - 8, 224, y + 18], fill="#0c2a20", outline=NEON_GREEN)
            dr.text((16, y - 4), item, font=_font(13),
                    fill=NEON_GREEN if active else "#5d8aa8")

    # content cards
    card_y = 84 - (BROWSER.scroll % 150)
    n = 0
    while card_y < HEIGHT - 60 and n < 6:
        cx = 250 + (n % 2) * 380
        cy = card_y + (n // 2) * 150
        if cy > 60:
            dr.rectangle([cx, cy, cx + 360, cy + 132], fill="#0a1420", outline="#1c3448")
            dr.rectangle([cx, cy, cx + 4, cy + 132], fill=NEON_MAGENTA if n % 2 else NEON_CYAN)
            headline = rnd.choice(_HEADLINES)
            words = headline.split()
            l1 = " ".join(words[:5])
            l2 = " ".join(words[5:])
            dr.text((cx + 16, cy + 12), l1[:42], font=_font(13), fill="#d7ffe9")
            dr.text((cx + 16, cy + 30), l2[:42], font=_font(12), fill="#7fa8c9")
            ticker = f"${rnd.choice(_TICKER)} {'+' if rnd.random() > .3 else '-'}{rnd.uniform(0.2, 8.8):.1f}%"
            up = ticker.startswith("$") and "+" in ticker
            dr.text((cx + 16, cy + 58), ticker, font=_font(14),
                    fill=NEON_GREEN if up else NEON_RED)
            dr.rectangle([cx + 16, cy + 88, cx + 130, cy + 116], fill="#06231a", outline=NEON_GREEN)
            dr.text((cx + 30, cy + 93), "▶ ENGAGE", font=_font(12), fill=NEON_GREEN)
            spark = [(cx + 160 + k * 18, cy + 112 - rnd.randint(6, 44)) for k in range(11)]
            dr.line(spark, fill=NEON_CYAN, width=2)
        n += 1
        if n % 2 == 0:
            card_y += 150

    # status bar
    dr.rectangle([0, HEIGHT - 28, WIDTH, HEIGHT], fill="#0a1119")
    dr.line([(0, HEIGHT - 28), (WIDTH, HEIGHT - 28)], fill=GRID_LINE)
    dr.text((12, HEIGHT - 24),
            f"SESSION secure · bot-score 0.02 · scroll {BROWSER.scroll}px · "
            f"rev {BROWSER.page_version} · {datetime.now().strftime('%H:%M:%S')}",
            font=_font(11), fill="#5d8aa8")
    dr.text((WIDTH - 200, HEIGHT - 24), "OMNI-BROWSER v2.4", font=_font(11), fill=NEON_MAGENTA)

    # last-click crosshair
    if BROWSER.last_click:
        x, y = BROWSER.last_click
        dr.line([(x - 14, y), (x + 14, y)], fill=NEON_AMBER, width=2)
        dr.line([(x, y - 14), (x, y + 14)], fill=NEON_AMBER, width=2)
        dr.ellipse([x - 8, y - 8, x + 8, y + 8], outline=NEON_AMBER, width=2)

    return img


def screenshot_png_bytes() -> bytes:
    buf = io.BytesIO()
    screenshot().save(buf, format="PNG")
    return buf.getvalue()
