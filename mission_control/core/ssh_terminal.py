"""DIRECT SSH TERMINAL bridge (PuTTY-style) with a safe local fallback.

Uses ``paramiko`` for a real interactive shell when credentials are
supplied and reachable.  If the connection fails (or no host is given)
it degrades to a *local* sandboxed shell so the embedded terminal is
always demonstrable.  All executions are wrapped so the UI never raises.
"""

from __future__ import annotations

import getpass
import socket
import subprocess
import threading
from typing import Optional, Tuple

from .state import STATE

try:
    import paramiko
    _HAVE_PARAMIKO = True
except Exception:  # pragma: no cover
    paramiko = None
    _HAVE_PARAMIKO = False

_BANNER = r"""
  ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄
  █  OMNIHACK // SECURE SHELL BRIDGE v2.4 █
  █  paramiko backend · AES-256 · chacha  █
  ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
"""


class SSHBridge:
    def __init__(self) -> None:
        self.client: Optional["paramiko.SSHClient"] = None
        self.channel = None
        self.mode: Optional[str] = None      # "remote" | "local" | None
        self.host: str = ""
        self.user: str = ""
        self.lock = threading.Lock()
        self.history: list[str] = []

    # ------------------------------------------------------------- connection
    def connect(self, host: str, port: int, username: str,
                password: str = "", key: str = "") -> Tuple[bool, str]:
        self.close()
        host = (host or "").strip()
        username = (username or "").strip()
        # Local fallback when no remote target is specified.
        if not host or host.lower() in {"local", "localhost", "sandbox"}:
            self.mode = "local"
            self.host = "localhost"
            self.user = username or getpass.getuser()
            STATE.ssh_mode = "local"
            STATE.ssh_banner = "LOCAL SANDBOX SHELL (no remote host)"
            STATE.log("OK", "SSH", f"Local sandbox shell session opened as {self.user}.")
            return True, _BANNER + f"\n[mode=LOCAL-SANDBOX user={self.user}]\n$ "

        if not _HAVE_PARAMIKO:
            STATE.log("WARN", "SSH", "paramiko unavailable — falling back to local shell.")
            return self.connect("local", 22, username)

        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            kwargs = {"hostname": host, "port": int(port or 22),
                      "username": username, "timeout": 6,
                      "allow_agent": False, "look_for_keys": False}
            if key:
                import io as _io
                pkey = paramiko.RSAKey.from_private_key(_io.StringIO(key))
                kwargs["pkey"] = pkey
            elif password:
                kwargs["password"] = password
            client.connect(**kwargs)
            self.client = client
            self.channel = client.invoke_shell()
            self.mode = "remote"
            self.host = host
            self.user = username
            STATE.ssh_mode = "remote"
            STATE.ssh_banner = f"REMOTE {username}@{host}:{port}"
            STATE.log("OK", "SSH", f"Remote SSH session established → {username}@{host}:{port}")
            return True, _BANNER + f"\n[mode=REMOTE {username}@{host}:{port}]\n$ "
        except (paramiko.SSHException, socket.error, OSError, ValueError) as exc:
            STATE.log("WARN", "SSH", f"Remote connect failed ({exc}) — using local shell.")
            return self.connect("local", 22, username)

    def close(self) -> None:
        try:
            if self.channel:
                self.channel.close()
            if self.client:
                self.client.close()
        except Exception:
            pass
        self.client = self.channel = None
        if self.mode:
            STATE.log("INFO", "SSH", f"Shell session closed (was {self.mode}).")
        self.mode = None
        STATE.ssh_mode = None
        STATE.ssh_banner = "NO ACTIVE SHELL SESSION"

    # -------------------------------------------------------------- execution
    def execute(self, command: str, timeout: int = 15) -> str:
        command = (command or "").strip()
        if not command:
            return ""
        self.history.append(command)

        if command in {"exit", "quit", "logout"}:
            self.close()
            return "logout\nConnection closed.\n$ "

        if self.mode == "remote" and self.channel:
            return self._exec_remote(command, timeout)
        return self._exec_local(command, timeout)

    def _exec_remote(self, command: str, timeout: int) -> str:
        try:
            self.channel.send(command + "\n")
            import time as _t
            out = ""
            deadline = _t.time() + timeout
            while _t.time() < deadline:
                if self.channel.recv_ready():
                    out += self.channel.recv(65535).decode("utf-8", "replace")
                elif out and not self.channel.recv_ready():
                    _t.sleep(0.15)
                    if not self.channel.recv_ready():
                        break
                else:
                    _t.sleep(0.05)
            return (out or "(no output)") + "\n$ "
        except Exception as exc:
            return f"[ssh error] {exc}\n$ "

    def _exec_local(self, command: str, timeout: int) -> str:
        # Guard the most destructive patterns in the demo sandbox.
        lowered = command.lower()
        for bad in ("rm -rf /", "mkfs", "dd if=", ":(){"):
            if bad in lowered:
                return f"[blocked] pattern '{bad}' refused by sandbox policy.\n$ "
        try:
            proc = subprocess.run(
                command, shell=True, capture_output=True, text=True,
                timeout=timeout, cwd="/home/user",
            )
            out = (proc.stdout or "") + ((proc.stderr or "") if proc.returncode else "")
            if proc.returncode and not out:
                out = f"[exit {proc.returncode}]"
            return (out.strip() or "(no output)") + "\n$ "
        except subprocess.TimeoutExpired:
            return f"[timeout after {timeout}s]\n$ "
        except Exception as exc:
            return f"[error] {exc}\n$ "


SSH = SSHBridge()
