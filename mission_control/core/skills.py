"""SKILL LAB :: a registry of 200+ mock/stubbed functional skills.

Each skill is a dict with ``id``, ``name``, ``domain``, ``desc`` and a
``handler`` callable that returns a simulated execution receipt.  Domains:

* OS & File Operations
* Network & Hacking
* Data Science & Math
* Web & Scrape
* Media & Vision
* Business & DevOps

The registry is deterministic (seeded) so skill IDs stay stable across runs,
which lets agent assignments survive config export/import.
"""

from __future__ import annotations

import random
from typing import Any, Callable, Dict, List

_RND = random.Random(1337)
SKILL_REGISTRY: Dict[str, Dict[str, Any]] = {}


def _receipt(skill_id: str, name: str, domain: str, **kwargs: Any) -> Dict[str, Any]:
    """Simulated executor — every skill returns a plausible mock receipt."""
    ms = _RND.randint(40, 4200)
    return {
        "skill_id": skill_id,
        "skill": name,
        "domain": domain,
        "status": "SIMULATED_OK",
        "runtime_ms": ms,
        "exit_code": 0,
        "params": kwargs,
        "output": f"[{domain}] {name} executed in simulated sandbox ({ms}ms).",
        "artifacts": [],
    }


def _register(domain: str, slug: str, name: str, desc: str,
              handler: Callable[..., Dict[str, Any]] | None = None) -> str:
    sid = f"{domain.split(' ')[0].lower()}.{slug}"
    SKILL_REGISTRY[sid] = {
        "id": sid,
        "name": name,
        "domain": domain,
        "desc": desc,
        "handler": handler or (lambda **kw: _receipt(sid, name, domain, **kw)),
    }
    return sid


def execute_skill(skill_id: str, **params: Any) -> Dict[str, Any]:
    """Run a skill by id; unknown ids return a failure receipt."""
    skill = SKILL_REGISTRY.get(skill_id)
    if skill is None:
        return {"skill_id": skill_id, "status": "NOT_FOUND", "exit_code": 127,
                "output": f"Skill '{skill_id}' is not registered."}
    try:
        return skill["handler"](**params)
    except Exception as exc:  # never let a stubbed skill crash the UI
        return {"skill_id": skill_id, "status": "SIMULATED_ERROR", "exit_code": 1,
                "output": f"{skill['name']} raised: {exc}"}


def search_skills(query: str = "", domain: str = "ALL") -> List[str]:
    """Return skill ids matching a fuzzy query + domain filter."""
    q = (query or "").strip().lower()
    out = []
    for sid, s in SKILL_REGISTRY.items():
        if domain and domain != "ALL" and s["domain"] != domain:
            continue
        if q and q not in s["name"].lower() and q not in s["desc"].lower() \
                and q not in sid.lower():
            continue
        out.append(sid)
    return sorted(out)


def skill_label(sid: str) -> str:
    s = SKILL_REGISTRY.get(sid)
    return f"[{sid}] {s['name']}" if s else sid


def domain_counts() -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for s in SKILL_REGISTRY.values():
        counts[s["domain"]] = counts.get(s["domain"], 0) + 1
    return counts


# ===========================================================================
# Registration — every skill is individually named so the lab feels real.
# ===========================================================================
def _build_registry() -> None:
    # ------------------------------------------------------------------ OS
    d = "OS & File Operations"
    _register(d, "zip.gz", "Gzip Compressor", "Compress files/dirs with gzip -9 streaming.")
    _register(d, "zip.zstd", "Zstd Fast Compressor", "Zstandard level 19 compression with dictionary reuse.")
    _register(d, "zip.7z", "7z Archive Packer", "LZMA2 ultra archive creation with AES headers.")
    _register(d, "log.parse", "Log Line Parser", "Regex-driven syslog/JSON log parser into records.")
    _register(d, "log.tail", "Live Log Tailer", "Follow log growth and emit delta chunks.")
    _register(d, "log.rotate", "Log Rotator", "Size/time based rotation with retention windows.")
    _register(d, "dir.watch", "Directory Watcher", "inotify-based create/modify/delete event stream.")
    _register(d, "dir.tree", "Directory Tree Mapper", "Recursive tree dump with size rollups.")
    _register(d, "dir.sync", "Rsync Mirror", "Delta-sync between local and remote trees.")
    _register(d, "file.dedupe", "Duplicate File Finder", "SHA-256 content hashing to find duplicates.")
    _register(d, "file.rename", "Bulk Renamer", "Pattern-based batch rename with dry-run.")
    _register(d, "file.shred", "Secure Shredder", "DoD 5220.22-M multi-pass secure delete.")
    _register(d, "perm.audit", "Permission Auditor", "Find world-writable / SUID anomalies.")
    _register(d, "perm.chmod", "Permission Fixer", "Apply sane 750/640 baselines recursively.")
    _register(d, "cron.lint", "Crontab Linter", "Validate cron expressions and overlap warnings.")
    _register(d, "proc.monitor", "Process Monitor", "Poll /proc for CPU/RSS anomalies per PID.")
    _register(d, "proc.killtree", "Process Tree Killer", "Kill a PID and all descendants atomically.")
    _register(d, "fs.quota", "Disk Quota Reporter", "Per-directory quota and inode usage report.")
    _register(d, "fs.journal", "FS Journal Snapshot", "Capture ext4/xfs journal state for forensics.")
    _register(d, "env.vault", "Env Vault Loader", "Load .env trees with AES-GCM at-rest encryption.")
    _register(d, "tmp.sweep", "Temp Sweeper", "Purge stale tmp artifacts older than TTL.")
    _register(d, "snapshot.zfs", "ZFS Snapshotter", "Create/prune ZFS snapshots with labels.")
    _register(d, "mount.probe", "Mount Health Probe", "Verify mounts, fstab drift, SMART status.")
    _register(d, "backup.borg", "Borg Backup Runner", "Deduplicated incremental borg backups.")
    _register(d, "backup.verify", "Backup Verifier", "Restore-to-tmp integrity verification.")
    _register(d, "sysd.unit", "Systemd Unit Manager", "Enable/disable/inspect unit files safely.")
    _register(d, "sysd.journal", "Journalctl Extractor", "Structured extraction of journald entries.")
    _register(d, "tty.record", "TTY Session Recorder", "Record terminal sessions to asciinema cast.")
    _register(d, "swap.tune", "Swappiness Tuner", "Adjust vm.swappiness + zram sizing.")
    _register(d, "iocounters", "IO Counter Sampler", "Read disk IO counters and deltas.")

    # ------------------------------------------------------- Network & Hacking
    d = "Network & Hacking"
    _register(d, "scan.port", "TCP Port Scanner", "SYN-style port sweep with service fingerprint stub.")
    _register(d, "scan.udp", "UDP Port Scanner", "UDP probe sweep with ICMP rate handling.")
    _register(d, "scan.subnet", "Subnet Discovery Sweep", "ARP/ping sweep of a CIDR to map live hosts.")
    _register(d, "sniff.packets", "Packet Sniffer (sim)", "libpcap-style capture summary simulation.")
    _register(d, "sniff.dns", "DNS Query Tapper (sim)", "Observe DNS resolution patterns (simulated).")
    _register(d, "api.stress", "API Stress Tester", "Controlled RPS ramp with latency percentiles.")
    _register(d, "api.fuzz", "API Parameter Fuzzer", "Boundary-value fuzzing of query params.")
    _register(d, "tls.probe", "TLS Handshake Prober", "Cipher suite + cert chain inspection.")
    _register(d, "tls.expiry", "Cert Expiry Watchdog", "Monitor cert TTLs across domains.")
    _register(d, "dns.recon", "DNS Recon", "A/AAAA/MX/TXT/AXFR enumeration (passive).")
    _register(d, "dns.spoofcheck", "SPF/DKIM Checker", "Email auth record validation.")
    _register(d, "http.headers", "Security Header Audit", "HSTS/CSP/XFO header scoring.")
    _register(d, "waf.detect", "WAF Fingerprinter", "CDN/WAF vendor detection via response quirks.")
    _register(d, "ssh.audit", "SSH Config Auditor", "Weak key exchange / MAC detection.")
    _register(d, "banner.grab", "Service Banner Grabber", "Grab and normalize service banners.")
    _register(d, "wifi.survey", "WiFi Survey (sim)", "Channel/SSID survey simulation.")
    _register(d, "vpn.mesh", "WireGuard Mesh Mapper", "Visualize mesh peers and handshakes.")
    _register(d, "fw.ruleset", "Firewall Ruleset Diff", "Diff iptables/nftables snapshots.")
    _register(d, "cve.lookup", "CVE Correlator", "Map installed packages to CVE feeds.")
    _register(d, "hash.crackbench", "Hash Benchmark (sim)", "Hashcat-style speed benchmark simulation.")
    _register(d, "proxy.chain", "Proxy Chain Validator", "Validate SOCKS/HTTP egress chain latency.")
    _register(d, "exfil.canary", "Canary Token Dropper", "Deploy tracking canaries (defensive).")
    _register(d, "netflow.top", "NetFlow Top Talkers", "Rank talkers by bytes (simulated flows).")
    _register(d, "icmp.trace", "MTR-style Traceroute", "Hop latency + loss path tracing.")
    _register(d, "ntp.drift", "NTP Drift Checker", "Clock offset vs pool.ntp.org.")
    _register(d, "bgp.watch", "BGP Prefix Watcher", "Announce/withdraw monitor (RIPE stub).")

    # ------------------------------------------------------- Data Science & Math
    d = "Data Science & Math"
    _register(d, "mat.mul", "Matrix Multiplication", "NxM GEMM with BLAS backend selection.")
    _register(d, "mat.inv", "Matrix Inversion", "LU-decomposition based inverse + condition no.")
    _register(d, "mat.eig", "Eigen Decomposition", "Eigenvectors/values for symmetric matrices.")
    _register(d, "stat.regress", "Linear Regression", "OLS fit with R², p-values, residuals.")
    _register(d, "stat.logistic", "Logistic Regression", "Binary classifier with AUC report.")
    _register(d, "stat.polyfit", "Polynomial Curve Fit", "Degree-n fit with overfit warning.")
    _register(d, "anom.zscore", "Z-Score Anomaly Detector", "Rolling z-score outlier flags.")
    _register(d, "anom.isoforest", "Isolation Forest Detector", "Unsupervised anomaly scoring.")
    _register(d, "anom.mad", "MAD Outlier Scanner", "Median absolute deviation robustness.")
    _register(d, "ts.arima", "ARIMA Forecaster", "ARIMA(p,d,q) forecast stub with CI bands.")
    _register(d, "ts.seasonal", "Seasonal Decomposer", "STL trend/seasonal/residual split.")
    _register(d, "ts.fft", "FFT Spectrum Analyzer", "Power spectral density of a series.")
    _register(d, "cluster.kmeans", "K-Means Clustering", "Elbow-method k selection + centroids.")
    _register(d, "cluster.hdb", "HDBSCAN Clustering", "Density clustering with noise labels.")
    _register(d, "dim.pca", "PCA Dimensionality Reduction", "Variance-explained PCA projection.")
    _register(d, "dim.umap", "UMAP Embedder", "2D UMAP embedding stub for visualization.")
    _register(d, "feat.corr", "Correlation Matrix", "Pearson/Spearman correlation heatmap data.")
    _register(d, "feat.select", "Feature Importance Ranker", "Permutation importance ranking.")
    _register(d, "sim.montecarlo", "Monte Carlo Simulator", "N-trial stochastic outcome distribution.")
    _register(d, "sim.markov", "Markov Chain Simulator", "State transition chain walker.")
    _register(d, "opt.grad", "Gradient Descent Solver", "Batch GD with learning-rate schedule.")
    _register(d, "opt.simplex", "Simplex LP Solver", "Linear programming via simplex tableau.")
    _register(d, "prob.bayes", "Bayes Posterior Updater", "Conjugate prior posterior updates.")
    _register(d, "graph.pagerank", "PageRank Scorer", "Directed graph PageRank with damping.")
    _register(d, "graph.shortest", "Dijkstra Shortest Path", "Weighted shortest path solver.")
    _register(d, "cv.auc", "ROC/AUC Evaluator", "ROC curve + AUC for scored labels.")

    # ------------------------------------------------------------- Web & Scrape
    d = "Web & Scrape"
    _register(d, "js.render", "Dynamic JS Renderer", "Headless render of JS-heavy pages (bypass stub).")
    _register(d, "js.antibot", "Anti-Bot Bypass Profile", "Stealth fingerprint + CDP patch profile.")
    _register(d, "rss.aggregate", "RSS Aggregator", "Merge/score RSS+Atom feeds, dedupe by GUID.")
    _register(d, "rss.watch", "Feed Change Watcher", "Delta detection on feed entries.")
    _register(d, "seo.audit", "SEO Site Auditor", "Meta/heading/canonical/link audit scoring.")
    _register(d, "seo.keywords", "Keyword Density Analyzer", "TF density + n-gram keyword extraction.")
    _register(d, "seo.backlinks", "Backlink Graph Puller", "Backlink graph stub with DR scores.")
    _register(d, "scrape.tables", "HTML Table Extractor", "Extract <table> data to CSV/JSON.")
    _register(d, "scrape.readability", "Article Readability Extractor", "Main-content extraction (readability).")
    _register(d, "scrape.sitemap", "Sitemap Crawler", "sitemap.xml walker with URL budget.")
    _register(d, "scrape.price", "Price Tracker", "CSS-selector price watchers with history.")
    _register(d, "scrape.paginate", "Pagination Walker", "Next-page traversal with rate limits.")
    _register(d, "scrape.forms", "Form Auto-Filler", "Discover + fill forms (browser-use hook).")
    _register(d, "http.archive", "Wayback Snapshot Fetcher", "Pull archived page versions.")
    _register(d, "http.diff", "Page Diff Watcher", "Hash + DOM diff of a page over time.")
    _register(d, "robots.parse", "Robots.txt Parser", "Crawl-rule parser + politeness check.")
    _register(d, "meta.opengraph", "OpenGraph Scraper", "OG/Twitter card metadata extractor.")
    _register(d, "cdn.purge", "CDN Cache Purger", "Invalidate CDN paths (API stub).")
    _register(d, "uptime.ping", "Uptime Probe", "HTTP(S) uptime + TLS latency probe.")
    _register(d, "serp.rank", "SERP Rank Checker", "Search position tracker (API stub).")
    _register(d, "proxy.rotate", "Rotating Proxy Manager", "Proxy pool health + rotation policy.")
    _register(d, "dom.query", "DOM CSS Query Engine", "Run CSS selectors against stored DOM.")
    _register(d, "cookie.jar", "Cookie Jar Manager", "Persistent per-profile cookie store.")
    _register(d, "webhook.listen", "Webhook Listener", "Register endpoint + log inbound payloads.")

    # ------------------------------------------------------------- Media & Vision
    d = "Media & Vision"
    _register(d, "img.resize", "Image Resizer", "Aspect-aware resize with Lanczos.")
    _register(d, "img.crop", "Smart Cropper", "Saliency-aware crop stub.")
    _register(d, "img.upscale", "AI Upscaler (ESRGAN stub)", "4x neural upscale simulation.")
    _register(d, "img.bgremove", "Background Remover", "Matting-based background removal stub.")
    _register(d, "img.watermark", "Watermark Stamper", "Tiled/anchor watermark overlay.")
    _register(d, "img.exif", "EXIF Scrubber", "Strip metadata for privacy.")
    _register(d, "vid.concat", "FFmpeg Concat Wrapper", "Concat demuxer joins with re-encode.")
    _register(d, "vid.trim", "FFmpeg Trim/Cut", "Frame-accurate cut without re-encode.")
    _register(d, "vid.subtitles", "Subtitle Burner", "ASS/SRT hardsub burn-in.")
    _register(d, "vid.transcode", "Transcoder (H.264/H.265)", "Codec/profile transcode presets.")
    _register(d, "vid.thumbnail", "Thumbnail Grid Maker", "Contact-sheet thumbnails via ffmpeg.")
    _register(d, "vid.shortrender", "Shorts Render Composer", "9:16 vertical short render pipeline.")
    _register(d, "aud.transcribe", "Audio Transcriber (stub)", "Whisper-style transcription stub.")
    _register(d, "aud.tts", "TTS Voiceover Synth", "Neural TTS hook with voice presets.")
    _register(d, "aud.normalize", "Loudness Normalizer", "EBU-R128 loudness normalization.")
    _register(d, "aud.denoise", "Noise Reducer", "Spectral denoise stub.")
    _register(d, "aud.split", "Silence Splitter", "Silence-based segment splitter.")
    _register(d, "ocr.extract", "OCR Extractor", "Tesseract-style OCR stub on frames.")
    _register(d, "vision.detect", "Object Detector (YOLO stub)", "Bbox detection simulation.")
    _register(d, "vision.faces", "Face Detector (stub)", "Face bbox + landmark stub.")
    _register(d, "vision.scene", "Scene Change Detector", "Shot boundary detection for editing.")
    _register(d, "caption.gen", "Caption Generator", "Image caption LLM hook.")
    _register(d, "gif.make", "GIF Composer", "Frame-sequence GIF encoder.")
    _register(d, "wave.render", "Waveform Renderer", "Audio waveform PNG renderer.")

    # --------------------------------------------------------- Business & DevOps
    d = "Business & DevOps"
    _register(d, "docker.ctl", "Docker Container Controller", "Start/stop/inspect containers via API stub.")
    _register(d, "docker.compose", "Compose Stack Manager", "Up/down/scale compose projects.")
    _register(d, "docker.prune", "Docker Pruner", "Reclaim images/volumes/build cache.")
    _register(d, "k8s.pods", "K8s Pod Inspector", "Pod status/logs/evict (kubeconfig stub).")
    _register(d, "k8s.deploy", "K8s Rollout Manager", "Rolling deploy + rollback controller.")
    _register(d, "cloud.cost", "Cloud Cost Calculator", "AWS/GCP/Azure spend estimator.")
    _register(d, "cloud.spot", "Spot Price Comparator", "Cross-cloud spot instance pricing.")
    _register(d, "iac.plan", "Terraform Plan Runner", "Plan-only terraform runs with drift notes.")
    _register(d, "ci.trigger", "CI Pipeline Trigger", "Fire GH Actions/Azure pipelines (stub).")
    _register(d, "ci.badges", "Build Badge Aggregator", "Collect shield badges across repos.")
    _register(d, "jira.ticket", "JIRA Ticket Generator", "Create/update JIRA issues via REST stub.")
    _register(d, "jira.burndown", "Sprint Burndown Puller", "Fetch sprint metrics snapshot.")
    _register(d, "git.housekeep", "Git Repo Housekeeper", "Branch pruning + shallow GC.")
    _register(d, "secret.scan", "Secrets Scanner", "Detect leaked keys/tokens in trees.")
    _register(d, "secret.rotate", "Secret Rotator", "Rotate + re-inject credentials safely.")
    _register(d, "db.backup", "Database Backup Runner", "pg/mongo dump + encrypt + ship.")
    _register(d, "db.migrate", "Schema Migration Runner", "Apply/check schema migrations.")
    _register(d, "report.invoice", "Invoice PDF Generator", "Invoice rendering from JSON template.")
    _register(d, "report.kpi", "KPI Dashboard Snapshot", "Compile KPI summary markdown.")
    _register(d, "email.digest", "Email Digest Sender", "Scheduled digest mailer (SMTP stub).")
    _register(d, "slack.post", "Slack Notifier", "Post blocks to channels (webhook stub).")
    _register(d, "crm.lead", "CRM Lead Enricher", "Enrich leads with firmographics stub.")
    _register(d, "support.triage", "Support Ticket Triager", "Classify + route inbound tickets.")
    _register(d, "okrs.track", "OKR Progress Tracker", "Roll objective progress percentages.")
    _register(d, "slo.budget", "Error Budget Calculator", "SLO burn-rate + budget remaining.")
    _register(d, "vend.cmp", "Vendor Quote Comparator", "Normalize + rank vendor quotes.")


def _build_registry_wave2() -> None:
    """Second wave — pushes the registry past the 200-skill guarantee."""
    d = "OS & File Operations"
    _register(d, "file.split", "File Splitter", "Split/join multi-GB files with checksums.")
    _register(d, "file.checksum", "Integrity Checksummer", "SHA/BLAKE3 manifest verify.")
    _register(d, "dir.flatten", "Directory Flattener", "Collapse nested trees with collision policy.")
    _register(d, "proc.renice", "Priority Renicer", "Adjust nice/ionice classes per workload.")
    _register(d, "fs.acl", "ACL Manager", "POSIX ACL grant/revoke auditor.")
    _register(d, "cron.sched", "Dynamic Cron Scheduler", "Install/remove crontab entries atomically.")
    _register(d, "sysd.timer", "Systemd Timer Builder", "Generate .timer/.service pairs.")
    _register(d, "tmp.ramdisk", "Tmpfs Ramdisk Provisioner", "Size-capped tmpfs scratch volumes.")

    d = "Network & Hacking"
    _register(d, "scan.masssim", "Mass-Sweep Simulator", "Internet-scale scan simulator (defensive).")
    _register(d, "sniff.http", "HTTP Flow Inspector", "Summarize request/response flows (sim).")
    _register(d, "api.replay", "Request Replay Engine", "Replay captured traffic with mutation.")
    _register(d, "tls.pin", "TLS Pin Validator", "HPKP-style pin set verification.")
    _register(d, "dns.doh", "DoH Resolver Probe", "DNS-over-HTTPS resolver benchmarking.")
    _register(d, "http.smuggle", "Request Smuggling Checker", "CL/TE desync safety probe.")
    _register(d, "arp.watch", "ARP Spoof Watchdog", "Detect gratuitous ARP anomalies.")
    _register(d, "lat.matrix", "Latency Matrix Builder", "All-pairs RTT matrix across targets.")

    d = "Data Science & Math"
    _register(d, "stat.bootstrap", "Bootstrap CI Estimator", "Resampled confidence intervals.")
    _register(d, "ts.holt", "Holt-Winters Forecaster", "Triple exponential smoothing forecast.")
    _register(d, "cluster.gmm", "Gaussian Mixture Clustering", "Soft-assignment GMM with BIC selection.")
    _register(d, "dim.tsne", "t-SNE Embedder", "Non-linear 2D embedding stub.")
    _register(d, "graph.community", "Community Detector", "Louvain modularity communities.")
    _register(d, "prob.abtest", "A/B Test Significance", "Frequentist + Bayesian AB testing.")

    d = "Web & Scrape"
    _register(d, "js.shadow", "Shadow-DOM Extractor", "Pierce shadow roots during scrape.")
    _register(d, "scrape.jsonapi", "JSON:API Crawler", "Follow relationships with sparse fields.")
    _register(d, "seo.cwv", "Core Web Vitals Auditor", "LCP/CLS/INP budget auditing.")
    _register(d, "meta.schema", "Schema.org Validator", "JSON-LD structured data validation.")
    _register(d, "robots.gen", "Robots.txt Generator", "Emit crawl policies per agent.")
    _register(d, "http.h2", "HTTP/2 Probe", "ALPN + SETTINGS frame inspection.")
    _register(d, "serp.snippet", "SERP Snippet Previewer", "Title/description pixel-width preview.")
    _register(d, "cookie.sync", "Cross-Profile Cookie Sync", "Sync consent cookies across personas.")

    d = "Media & Vision"
    _register(d, "img.grade", "Cinematic Color Grader", "LUT application + teal-orange grade.")
    _register(d, "img.hdr", "HDR Tone Mapper", "Merge bracketed exposures stub.")
    _register(d, "vid.stab", "Video Stabilizer", "vid.stab motion smoothing pass.")
    _register(d, "vid.speed", "Speed Ramp Editor", "Time remapping with pitch correction.")
    _register(d, "aud.pitch", "Pitch Shifter", "Formant-preserving pitch control.")
    _register(d, "vision.qr", "QR/Barcode Scanner", "Decode QR/Code128 from frames.")
    _register(d, "caption.i18n", "Caption Translator", "Translate captions to N locales.")
    _register(d, "wave.eq", "Podcast EQ Chain", "Voice-tuned equalizer preset chain.")

    d = "Business & DevOps"
    _register(d, "docker.reg", "Registry Garbage Collector", "Prune untagged manifests in registry.")
    _register(d, "k8s.hpa", "HPA Autoscale Tuner", "Right-size horizontal pod autoscalers.")
    _register(d, "cloud.rightsize", "Instance Right-Sizer", "Recommend instance shapes from usage.")
    _register(d, "ci.cache", "CI Cache Optimizer", "Cache key strategy + hit-rate report.")
    _register(d, "jira.roadmap", "Roadmap Sync", "Push epics to roadmap views.")
    _register(d, "db.index", "Index Advisor", "Suggest missing indexes from slow log.")
    _register(d, "report.weekly", "Weekly Ops Report", "Compile uptime/incident weekly digest.")
    _register(d, "support.faq", "FAQ Auto-Builder", "Cluster tickets into FAQ drafts.")


_build_registry()
_build_registry_wave2()

# sanity: guarantee the advertised size
assert len(SKILL_REGISTRY) >= 200, f"Skill registry too small: {len(SKILL_REGISTRY)}"
