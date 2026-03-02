#!/usr/bin/env python3
"""
Vola Unified Interface v2.4

Changes from v2.3:
- Defensive error handling in poll() and syncChatFromServer()
- Validates API response before processing
- Validates message objects before rendering
- Console warnings for debugging chat issues

Changes from v2.2:
- Header version corrected (v2.2 → v2.3)

Changes from v2.1:
- Context Inspector as toolbar popover (not a dashboard card)
- Terminal reads from dashboard/terminal.jsonl (persistent, real shell output)
- Anti-flicker: per-section content hashing, DOM only updated when changed
- Input focus protection: pauses DOM updates when user is typing in dashboard
- Chat: reads only from chat_history/ (single source of truth, no dedup issues)
- Dashboard cards: fixed max-heights, no height jumping
- Path: full history scrollable, past cards immutable in render
- Cumulative cost + t/s in toolbar chips
"""

from flask import Flask, render_template_string, jsonify, request
from markupsafe import escape
from pathlib import Path
from datetime import datetime, timezone
import json
import os
import time
import hashlib

app = Flask(__name__)
VOLA_HOME        = Path(os.environ.get("VOLA_HOME", "/home/vola"))
LOG_DIR          = VOLA_HOME / "logs"
JOURNAL_DIR      = VOLA_HOME / "journal"
STATE_DIR        = VOLA_HOME / "state"
DASHBOARD_DIR    = VOLA_HOME / "dashboard"
INBOX_DIR        = VOLA_HOME / "inbox"
OUTBOX_DIR       = VOLA_HOME / "outbox"
WORKSPACE_DIR    = VOLA_HOME / "workspace"
CHAT_HISTORY_DIR = VOLA_HOME / "chat_history"
SNAPSHOTS_DIR    = VOLA_HOME / "snapshots"

PLAN_FILE          = STATE_DIR / "plan.json"
EXEC_STATE_FILE    = STATE_DIR / "execution_state.json"
PAUSE_FLAG         = STATE_DIR / "pause.flag"
STOP_FLAG          = STATE_DIR / "stop.flag"
WHISPER_FILE       = STATE_DIR / "whisper.json"
PATH_FILE          = DASHBOARD_DIR / "path.json"
STATUS_FILE        = DASHBOARD_DIR / "status.json"
STREAM_FILE        = DASHBOARD_DIR / "stream.jsonl"
TERMINAL_FILE      = DASHBOARD_DIR / "terminal.jsonl"
APPROVAL_REQ_FILE  = DASHBOARD_DIR / "approval_request.json"
APPROVAL_RESP_FILE = DASHBOARD_DIR / "approval_response.json"
ROLLBACK_REQ_FILE  = DASHBOARD_DIR / "rollback_request.json"
CYCLE_CARD_FILE    = DASHBOARD_DIR / "cycle_card.json"
ATTACHMENTS_DIR    = INBOX_DIR / "attachments"
RESTART_FLAG       = STATE_DIR / "restart_requested.flag"

def esc(text):
    return str(escape(str(text)))

def load_json(path, default=None):
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            pass
    return default if default is not None else {}


def get_data():
    status_data = load_json(STATUS_FILE, {"status": "offline"})
    status = status_data.get("status", "offline").lower()
    detail = status_data.get("detail", "")
    cycle_count = status_data.get("cycle_count", 0)
    agent_state = status_data.get("agent_state", "stopped")
    resume_at = status_data.get("resume_at")
    tokens_per_second = status_data.get("tokens_per_second", 0)

    exec_state = load_json(EXEC_STATE_FILE, {"mode": "running"})
    exec_mode = exec_state.get("mode", "running")

    plan = load_json(PLAN_FILE)
    lu = plan.get("_last_usage", {})
    prompt_tok = lu.get("prompt", 0)
    completion_tok = lu.get("completion", 0)
    ctx_chars = lu.get("context_chars", 0)
    total_cost = plan.get("_total_cost_usd", 0)
    tps = lu.get("tokens_per_second", tokens_per_second)

    context_used_tok = prompt_tok if prompt_tok else (ctx_chars // 4 if ctx_chars else 0)
    context_used = f"~{context_used_tok:,}" if context_used_tok else "—"

    # Context breakdown for popover
    ctx_breakdown = {
        "total": context_used_tok,
        "prompt": prompt_tok,
        "completion": completion_tok,
        "cost": total_cost,
        "tps": tps,
    }

    # Countdown
    next_wake = "—"
    countdown_seconds = None
    if resume_at:
        remaining = resume_at - time.time()
        if remaining > 0:
            m, s = divmod(int(remaining), 60)
            h, m2 = divmod(m, 60)
            next_wake = f"{h}h{m2}m" if h else f"{m}m{s:02d}s"
            countdown_seconds = int(remaining)
        else:
            next_wake = "imm"
    elif exec_mode in ("invoking", "running") and plan.get("action") == "continue":
        next_wake = "now"

    # Chat — single source of truth: chat_history/
    all_msgs = []
    seen_texts = {}  # deduplicate: (sender, text[:80]) -> keep latest ts
    if CHAT_HISTORY_DIR.exists():
        # Load last 300 files sorted by modification time (newest first)
        # NOT alphabetically — 'vola_*' sorts after 'lars_*' which caused
        # all vola files to be selected first, excluding lars messages entirely
        files = sorted(CHAT_HISTORY_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)[:300]
        for f in files:
            try:
                parts = f.stem.split("_")
                if len(parts) < 2:
                    continue
                sender = parts[0].capitalize()
                # Handle both vola_TS.md and vola_TS_MS.md formats
                ts = int(parts[1])
                text = f.read_text().strip()
                if not text:
                    continue
                # Deduplicate same text sent multiple times within 10 seconds
                dedup_key = (sender.lower(), text[:80])
                if dedup_key in seen_texts:
                    existing_ts = seen_texts[dedup_key]
                    if abs(ts - existing_ts) < 10:
                        continue  # skip duplicate within 10s
                seen_texts[dedup_key] = ts
                all_msgs.append((ts, sender, text))
            except Exception:
                pass
    all_msgs.sort(key=lambda x: x[0])

    messages = []
    for ts, sender, text in all_msgs[-40:]:
        sc = sender.lower()
        try:
            time_str = datetime.fromtimestamp(ts).strftime("%H:%M")
        except Exception:
            time_str = "?"
        messages.append({
            "sender": esc(sender), "sender_class": sc,
            "avatar": "🦞" if sc == "vola" else "🧑",
            "time": time_str, "text": text[:2000],
            "ts": ts,
        })

    chat_hash = hashlib.md5(
        json.dumps([(m["time"], m["sender"], m["text"][:40]) for m in messages]).encode()
    ).hexdigest()[:10]

    # Journal
    journal_entries = []
    if JOURNAL_DIR.exists():
        for f in sorted(JOURNAL_DIR.glob("*.md"), reverse=True)[:8]:
            try:
                text = f.read_text().strip()
                lines = text.split("\n")
                body = "\n".join(l for l in lines if not l.startswith("# ")).strip()
                journal_entries.append({"time": esc(f.stem.replace("_", " ")), "text": body[:500]})
            except Exception:
                pass

    # Activity log
    activities = []
    lf = LOG_DIR / "runner.log"
    if lf.exists():
        try:
            lines = lf.read_text().split("\n")[-50:]
        except Exception:
            lines = []
        for line in lines:
            if not line.strip():
                continue
            for lvl in ("[INFO]", "[ERROR]", "[WARNING]"):
                if lvl in line:
                    idx = line.index(lvl)
                    ts_str = line[:idx].strip()[-8:]
                    msg = line[idx + len(lvl):].strip()
                    icon = "📝"
                    ml = msg.lower()
                    if "cycle" in ml: icon = "🔄"
                    elif "response" in ml: icon = "💬"
                    elif "journal" in ml: icon = "📔"
                    elif "wait" in ml or "sleep" in ml: icon = "💤"
                    elif "shell" in ml: icon = "⚙️"
                    elif "inbox" in ml: icon = "📨"
                    elif "outbox" in ml or "notify" in ml: icon = "📤"
                    elif "error" in lvl.lower(): icon = "❌"
                    elif "snapshot" in ml: icon = "📸"
                    elif "approval" in ml: icon = "🔐"
                    elif "state →" in ml: icon = "🔀"
                    activities.append({"time": ts_str, "icon": icon, "title": msg[:100]})
                    break
    activities.reverse()

    path_nodes = load_json(PATH_FILE, [])

    # Raw log
    raw_log = "No logs yet."
    if lf.exists():
        try:
            raw_log = lf.read_text()[-5000:]
        except:
            pass

    # Workspace
    workspace_files = []
    if WORKSPACE_DIR.exists():
        try:
            for item in sorted(WORKSPACE_DIR.iterdir())[:30]:
                workspace_files.append({
                    "icon": "📁" if item.is_dir() else "📄",
                    "name": esc(item.name),
                    "new": False,
                })
        except Exception:
            pass

    # Terminal entries from persistent log
    terminal_entries = []
    if TERMINAL_FILE.exists():
        try:
            lines = TERMINAL_FILE.read_text().strip().split("\n")
            for line in lines[-30:]:  # last 30 commands
                if line.strip():
                    try:
                        e = json.loads(line)
                        terminal_entries.append({
                            "cmd": esc(e.get("cmd", "")),
                            "out": esc(e.get("out", "")),
                            "exit": e.get("exit", 0),
                            "elapsed": e.get("elapsed", 0),
                            "ts": e.get("ts", 0),
                        })
                    except Exception:
                        pass
        except Exception:
            pass

    # Cycle card
    cycle_card = load_json(CYCLE_CARD_FILE, {})

    # Approval
    approval = None
    if APPROVAL_REQ_FILE.exists():
        approval = load_json(APPROVAL_REQ_FILE)

    # Snapshots
    snapshots = []
    if SNAPSHOTS_DIR.exists():
        for d in sorted(SNAPSHOTS_DIR.glob("cycle_*"), reverse=True)[:20]:
            try:
                snapshots.append(int(d.name.split("_")[1]))
            except:
                pass

    journal_count = len(list(JOURNAL_DIR.glob("*.md"))) if JOURNAL_DIR.exists() else 0

    # Horizons — loaded from state/horizons.md (what Vola is carrying)
    horizons_text = ""
    horizons_file = STATE_DIR / "horizons.md"
    if horizons_file.exists():
        try:
            horizons_text = horizons_file.read_text().strip()
        except Exception:
            pass
    is_paused = PAUSE_FLAG.exists()
    is_stopped = STOP_FLAG.exists()

    return {
        "status": status, "detail": detail[:120], "agent_state": agent_state,
        "exec_mode": exec_mode, "is_paused": is_paused, "is_stopped": is_stopped,
        "context_used": context_used, "cycles": cycle_count,
        "journal_count": journal_count, "next_wake": next_wake,
        "countdown_seconds": countdown_seconds,
        "ctx_breakdown": ctx_breakdown,
        "tps": round(tps, 1), "total_cost": total_cost,
        "messages": messages, "chat_hash": chat_hash,
        "journal_entries": journal_entries, "horizons": horizons_text, "activities": activities[:30],
        "path_nodes": path_nodes, "raw_log": raw_log,
        "workspace_files": workspace_files,
        "terminal_entries": terminal_entries,
        "cycle_card": cycle_card, "approval": approval, "snapshots": snapshots,
        "version": "v2.4",
    }


@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, **get_data())

@app.route("/api/status")
def api_status():
    return jsonify(get_data())

@app.route("/api/send", methods=["POST"])
def send_message():
    data = request.get_json()
    message = data.get("message", "").strip() if data else ""
    if not message or len(message) > 10000:
        return jsonify({"success": False})
    ts = int(time.time())
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    (INBOX_DIR / f"{ts}.md").write_text(message)
    CHAT_HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    (CHAT_HISTORY_DIR / f"lars_{ts}.md").write_text(message)
    return jsonify({"success": True})

@app.route("/api/pause", methods=["POST"])
def toggle_pause():
    if PAUSE_FLAG.exists():
        PAUSE_FLAG.unlink()
        return jsonify({"paused": False})
    PAUSE_FLAG.write_text("paused")
    return jsonify({"paused": True})

@app.route("/api/stop", methods=["POST"])
def toggle_stop():
    if STOP_FLAG.exists():
        STOP_FLAG.unlink()
        return jsonify({"stopped": False})
    STOP_FLAG.write_text("stopped")
    if PAUSE_FLAG.exists():
        PAUSE_FLAG.unlink()
    return jsonify({"stopped": True})

@app.route("/api/approval", methods=["POST"])
def handle_approval():
    data = request.get_json()
    approved = data.get("approved", False)
    resp = {"approved": approved, "responded_at": datetime.now(timezone.utc).isoformat()}
    tmp = APPROVAL_RESP_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(resp))
    tmp.rename(APPROVAL_RESP_FILE)
    return jsonify({"success": True, "approved": approved})

@app.route("/api/whisper", methods=["POST"])
def inject_whisper():
    data = request.get_json()
    whisper = data.get("whisper", "").strip()
    if not whisper:
        return jsonify({"success": False})
    wdata = {"whisper": whisper, "injected_at": datetime.now(timezone.utc).isoformat()}
    tmp = WHISPER_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(wdata))
    tmp.rename(WHISPER_FILE)
    return jsonify({"success": True})

@app.route("/api/restart", methods=["POST"])
def restart_daemon():
    RESTART_FLAG.write_text("restart")
    return jsonify({"success": True})

@app.route("/api/update", methods=["POST"])
def update_daemon():
    """Accept a .tar.gz file, extract it, copy daemon files, trigger restart."""
    import tarfile, tempfile, shutil as sh
    f = request.files.get("file")
    if not f or not f.filename.endswith((".tar.gz", ".tgz")):
        return jsonify({"success": False, "error": "Must be a .tar.gz file"})
    try:
        with tempfile.TemporaryDirectory() as tmp:
            tpath = os.path.join(tmp, "update.tar.gz")
            f.save(tpath)
            with tarfile.open(tpath, "r:gz") as tar:
                tar.extractall(tmp)
            # Find daemon/ directory in extracted content
            daemon_src = None
            for root, dirs, files in os.walk(tmp):
                if "runner.py" in files and os.path.basename(root) == "daemon":
                    daemon_src = root
                    break
            if not daemon_src:
                return jsonify({"success": False, "error": "No daemon/ directory found in archive"})
            daemon_dst = Path(__file__).parent
            copied = []
            for fname in ["runner.py", "vola_unified.py", "system.md"]:
                src_f = os.path.join(daemon_src, fname)
                if os.path.exists(src_f):
                    sh.copy2(src_f, daemon_dst / fname)
                    copied.append(fname)
            if copied:
                RESTART_FLAG.write_text("restart")
                return jsonify({"success": True, "copied": copied, "restarting": True})
            return jsonify({"success": False, "error": "No daemon files found"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/upload", methods=["POST"])
def upload_file():
    """Handle file attachments — images, code, tarballs, anything."""
    ATTACHMENTS_DIR.mkdir(parents=True, exist_ok=True)
    CHAT_HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    INBOX_DIR.mkdir(parents=True, exist_ok=True)

    file = request.files.get("file")
    message = request.form.get("message", "").strip()

    if not file or not file.filename:
        return jsonify({"success": False, "error": "No file"})

    ts = int(time.time())
    # Sanitize filename — preserve extension including .tar.gz
    original = file.filename
    safe_name = "".join(c for c in original if c.isalnum() or c in "._-")[:120]
    if not safe_name:
        safe_name = f"file_{ts}"

    dest = ATTACHMENTS_DIR / f"{ts}_{safe_name}"
    file.save(str(dest))

    mime = file.content_type or ""
    is_image = mime.startswith("image/") or safe_name.lower().split(".")[-1] in ("png","jpg","jpeg","gif","webp")
    meta = {
        "mime_type": mime,
        "sender": "Lars",
        "message": message,
        "original_name": original,
        "is_image": is_image,
        "size": dest.stat().st_size,
    }
    dest.with_suffix(".meta").write_text(json.dumps(meta))

    # Write to chat_history so it appears in UI
    display_text = f"[Attached: {original}]"
    if message:
        display_text = f"{message}\n{display_text}"
    (CHAT_HISTORY_DIR / f"lars_{ts}.md").write_text(display_text)

    # Write to inbox so Vola wakes up and processes
    inbox_text = display_text
    if not is_image:
        # For non-images, also mention the path so Vola can read it
        inbox_text += f"\nFile saved at: ~/inbox/attachments/{ts}_{safe_name}"
    (INBOX_DIR / f"{ts}.md").write_text(inbox_text)

    return jsonify({"success": True, "filename": safe_name, "original": original, "ts": ts})
    data = request.get_json()
    cycle = data.get("cycle")
    if not cycle:
        return jsonify({"success": False})
    tmp = ROLLBACK_REQ_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps({"cycle": cycle}))
    tmp.rename(ROLLBACK_REQ_FILE)
    return jsonify({"success": True})

@app.route("/api/stream")
def get_stream():
    if STREAM_FILE.exists():
        try:
            lines = STREAM_FILE.read_text().strip().split("\n")
            chunks, done = [], False
            for line in lines:
                try:
                    d = json.loads(line)
                    if d.get("done"): done = True
                    elif "t" in d: chunks.append(d["t"])
                except: pass
            return jsonify({"text": "".join(chunks), "done": done})
        except Exception:
            pass
    return jsonify({"text": "", "done": True})


HTML_TEMPLATE = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Vola</title>
<style>
:root {
    --blue:#0A84FF; --cyan:#32ADE6; --indigo:#5E5CE6; --purple:#BF5AF2;
    --red:#FF453A; --green:#32D74B; --orange:#FF9F0A; --yellow:#FFD60A;
    --gray:#8E8E93; --gray2:#636366; --gray3:#48484A; --gray4:#3A3A3C;
    --gray5:#2C2C2E; --gray6:#1C1C1E; --bg:#000;
    --lbl1:rgba(255,255,255,1); --lbl2:rgba(235,235,245,0.6); --lbl3:rgba(235,235,245,0.3);
    --sep:rgba(255,255,255,0.1); --sep-s:rgba(255,255,255,0.05);
    --glass:rgba(28,28,30,0.75); --fill:rgba(255,255,255,0.05);
    --ease:cubic-bezier(0.25,1,0.4,1);
    --font:-apple-system,BlinkMacSystemFont,"SF Pro Text","Helvetica Neue",system-ui,sans-serif;
    --mono:"SF Mono",SFMono-Regular,ui-monospace,Menlo,monospace;
}
*{box-sizing:border-box;margin:0;padding:0;-webkit-font-smoothing:antialiased;}
html,body{height:100%;}
body{font-family:var(--font);background:var(--bg);color:var(--lbl1);display:flex;flex-direction:column;overflow:hidden;font-size:14px;}

/* ── Toolbar ── */
.tb{height:52px;min-height:52px;flex-shrink:0;display:flex;align-items:center;justify-content:space-between;padding:0 20px;background:var(--glass);backdrop-filter:blur(30px) saturate(200%);-webkit-backdrop-filter:blur(30px) saturate(200%);border-bottom:0.5px solid var(--sep);z-index:200;}
.tb-l{display:flex;align-items:center;gap:12px;min-width:200px;}
.tb-c{flex:1;display:flex;align-items:center;justify-content:center;}
.tb-r{display:flex;align-items:center;gap:8px;min-width:200px;justify-content:flex-end;position:relative;}
.tb-name{font-size:15px;font-weight:600;letter-spacing:-0.01em;}
.tb-badge{display:flex;align-items:center;gap:6px;background:rgba(10,132,255,0.1);padding:4px 10px;border-radius:12px;}
.tb-dot{width:6px;height:6px;border-radius:50%;background:var(--blue);box-shadow:0 0 8px rgba(10,132,255,0.6);animation:pulse 2.5s ease-in-out infinite;transition:all 0.3s;}
.tb-dot.paused{background:var(--yellow);box-shadow:none;animation:none;}
.tb-dot.stopped{background:var(--gray);box-shadow:none;animation:none;}
.tb-dot.error{background:var(--red);animation:blink 1s step-end infinite;}
.tb-dot.waiting{background:var(--orange);box-shadow:0 0 6px rgba(255,159,10,0.5);animation:pulse 4s ease-in-out infinite;}
.tb-dot.invoking{background:var(--cyan);box-shadow:0 0 10px rgba(50,173,230,0.7);animation:pulse 0.8s ease-in-out infinite;}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.4}}
@keyframes blink{50%{opacity:0}}
.tb-st{font-size:12px;font-weight:500;color:var(--blue);transition:color 0.3s;}

.ctrl-grp{display:flex;background:rgba(255,255,255,0.04);border:1px solid var(--sep-s);border-radius:8px;padding:2px;}
.ctrl-btn{background:transparent;border:none;color:var(--lbl1);font-size:12px;font-weight:500;padding:4px 12px;border-radius:6px;cursor:pointer;display:flex;align-items:center;gap:6px;transition:all 0.2s var(--ease);font-family:var(--font);}
.ctrl-btn svg{width:12px;height:12px;fill:currentColor;}
.ctrl-btn:hover{background:rgba(255,255,255,0.1);}
.ctrl-btn:active{transform:scale(0.96);}
.ctrl-btn.on-pause{background:rgba(255,214,10,0.15);color:var(--yellow);}
.ctrl-btn.on-stop{background:rgba(50,215,75,0.15);color:var(--green);}

.chip{background:rgba(255,255,255,0.04);border:0.5px solid var(--sep-s);padding:4px 12px;border-radius:14px;font-size:11px;font-weight:500;color:var(--lbl2);display:flex;gap:6px;cursor:pointer;transition:background 0.2s;user-select:none;}
.chip:hover{background:rgba(255,255,255,0.08);}
.chip span{color:var(--lbl1);font-family:var(--mono);}
.chip.active{background:rgba(10,132,255,0.15);border-color:rgba(10,132,255,0.3);color:var(--blue);}

/* Context Window Popover */
.ctx-pop{position:absolute;top:44px;right:0;width:290px;background:rgba(40,40,42,0.98);border:1px solid var(--gray3);border-radius:16px;padding:16px;box-shadow:0 16px 40px rgba(0,0,0,0.8),0 0 0 1px rgba(255,255,255,0.05) inset;opacity:0;transform:translateY(-8px) scale(0.95);pointer-events:none;transition:all 0.25s var(--ease);z-index:300;transform-origin:top right;}
.ctx-pop.open{opacity:1;transform:translateY(0) scale(1);pointer-events:auto;}
.ctx-pop-hdr{font-size:13px;font-weight:600;margin-bottom:12px;display:flex;justify-content:space-between;align-items:center;}
.ctx-pop-hdr span{font-family:var(--mono);color:var(--lbl2);font-weight:400;font-size:11px;}
.ctx-bar{display:flex;height:8px;border-radius:4px;overflow:hidden;margin-bottom:14px;background:var(--gray5);gap:1px;}
.ctx-seg-sys{background:var(--indigo);}
.ctx-seg-mem{background:var(--orange);}
.ctx-seg-chat{background:var(--blue);}
.ctx-seg-tool{background:var(--cyan);}
.ctx-legend{display:flex;flex-direction:column;gap:8px;font-size:12px;}
.ctx-row{display:flex;align-items:center;justify-content:space-between;}
.ctx-row-l{display:flex;align-items:center;gap:8px;color:var(--lbl2);}
.ctx-dot{width:8px;height:8px;border-radius:50%;}
.ctx-val{font-family:var(--mono);font-size:11px;color:var(--lbl1);}
.ctx-divider{margin-top:12px;padding-top:12px;border-top:0.5px solid var(--sep);display:flex;justify-content:space-between;font-size:12px;color:var(--lbl2);}
.ctx-divider span{font-family:var(--mono);color:var(--lbl1);}

/* ── Layout ── */
.app{display:flex;flex:1;min-height:0;overflow:hidden;}
.pane{flex:1;display:flex;flex-direction:column;border-right:0.5px solid var(--sep);background:var(--bg);min-width:0;overflow:hidden;}
.pane:last-child{border-right:none;}
.pane-mid{background:var(--gray6);}
.pane-hd{padding:16px 20px 12px;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;color:var(--lbl2);border-bottom:0.5px solid var(--sep-s);flex-shrink:0;}

/* ── Chat ── */
.ch-hero{padding:16px 20px;display:flex;align-items:center;gap:12px;border-bottom:0.5px solid var(--sep-s);flex-shrink:0;}
.ch-av{width:40px;height:40px;border-radius:50%;background:linear-gradient(135deg,var(--cyan),var(--blue));display:flex;align-items:center;justify-content:center;font-size:20px;box-shadow:0 4px 12px rgba(10,132,255,0.25);flex-shrink:0;}
.ch-name{font-weight:600;font-size:15px;}
.ch-sub{font-size:12px;color:var(--lbl2);margin-top:1px;}
.msgs{flex:1;overflow-y:auto;padding:16px 20px;display:flex;flex-direction:column;gap:16px;min-height:0;}
.msg{display:flex;gap:10px;max-width:88%;animation:slideUp 0.35s var(--ease);}
@keyframes slideUp{from{opacity:0;transform:translateY(10px) scale(0.98)}}
.msg.out{align-self:flex-end;flex-direction:row-reverse;}
.msg-av{width:26px;height:26px;border-radius:50%;background:var(--gray5);display:flex;align-items:center;justify-content:center;font-size:12px;flex-shrink:0;align-self:flex-end;margin-bottom:18px;}
.msg-c{display:flex;flex-direction:column;gap:4px;}
.msg.out .msg-c{align-items:flex-end;}
.msg-bub{padding:10px 14px;border-radius:18px 18px 18px 6px;background:var(--gray5);font-size:14px;line-height:1.5;white-space:pre-wrap;word-break:break-word;}
.msg.out .msg-bub{border-radius:18px 18px 6px 18px;background:var(--blue);color:#fff;}
.msg-bub.action{background:rgba(10,132,255,0.1);border:1px solid rgba(10,132,255,0.3);}
.action-title{font-weight:600;margin-bottom:6px;}
.action-desc{color:var(--lbl2);font-size:13px;line-height:1.5;margin-bottom:10px;}
.act-btns{display:flex;gap:8px;}
.act-btn{flex:1;padding:8px;border-radius:8px;border:none;font-weight:500;cursor:pointer;font-family:var(--font);font-size:13px;transition:all 0.2s;}
.act-btn.approve{background:var(--blue);color:#fff;}
.act-btn.deny{background:rgba(255,255,255,0.1);color:var(--lbl1);}
.act-btn:active{transform:scale(0.96);}
.action-result{font-size:13px;font-weight:500;padding:4px 0;}
.msg-meta{font-size:11px;color:var(--lbl3);padding:0 4px;}
.msg-sys{align-self:center;font-family:var(--mono);font-size:11px;color:var(--orange);background:rgba(255,159,10,0.1);padding:4px 12px;border-radius:12px;border:0.5px solid rgba(255,159,10,0.2);}
.inp-area{padding:14px 20px 20px;border-top:0.5px solid var(--sep-s);flex-shrink:0;}
.inp-wrap{display:flex;align-items:flex-end;background:var(--gray6);border:1px solid var(--sep-s);border-radius:22px;transition:all 0.3s var(--ease);}
.inp-wrap:focus-within{border-color:rgba(10,132,255,0.4);box-shadow:0 0 0 3px rgba(10,132,255,0.1);}
.inp{flex:1;background:transparent;border:none;color:var(--lbl1);font-family:var(--font);font-size:14px;line-height:1.5;padding:10px 16px;resize:none;outline:none;max-height:120px;}
.inp::placeholder{color:var(--lbl2);}
.inp-send{background:transparent;border:none;padding:8px 12px 8px 4px;cursor:pointer;color:var(--lbl3);transition:color 0.2s,transform 0.1s;}
.inp-wrap:focus-within .inp-send{color:var(--blue);}
.inp-send:active{transform:scale(0.85);}
.inp-send svg{width:24px;height:24px;fill:currentColor;}

/* ── Path ── */
.path-sc{flex:1;overflow-y:auto;padding:24px 24px 48px;min-height:0;}
.cycle-card{background:rgba(10,132,255,0.04);border:1px solid rgba(10,132,255,0.15);border-radius:10px;padding:14px 16px;margin-bottom:2px;}.cc-row{display:flex;gap:8px;margin-bottom:6px;align-items:baseline;}.cc-label{font-size:10px;font-weight:700;color:var(--blue);letter-spacing:0.08em;text-transform:uppercase;min-width:36px;opacity:0.7;}.cc-text{font-size:12px;color:var(--fg);line-height:1.5;}.cc-meta{font-size:10px;color:var(--fg3);margin-top:6px;}.timeline{position:relative;padding-left:44px;}
.timeline::before{content:'';position:absolute;left:22px;top:14px;bottom:30px;width:2px;background:var(--sep-s);transform:translateX(-50%);border-radius:2px;z-index:0;}
.node{position:relative;padding:16px;background:var(--bg);border-radius:14px;margin-bottom:14px;border:1px solid var(--sep-s);z-index:2;transition:border-color 0.4s,background 0.4s,transform 0.4s,opacity 0.4s;}
.node:hover{background:rgba(255,255,255,0.02);}
.node::before{content:'';position:absolute;left:-22px;top:50%;transform:translate(-50%,-50%);border-radius:50%;z-index:3;box-sizing:border-box;transition:all 0.4s;}
.node.done{opacity:0.5;}
.node.done::before{width:8px;height:8px;background:var(--gray4);border:2px solid var(--gray6);}
.node.next{opacity:0.75;}
.node.next::before{width:10px;height:10px;background:var(--bg);border:2px solid var(--gray3);}
.node.now{background:rgba(10,132,255,0.06);border:1px solid rgba(10,132,255,0.2);transform:scale(1.01);z-index:5;}
.node.now::before{width:12px;height:12px;background:var(--blue);border:none;box-shadow:0 0 10px 1px rgba(10,132,255,0.5);}
.node.now::after{content:'';position:absolute;left:-22px;top:0;width:2px;height:100%;background:linear-gradient(to bottom,rgba(10,132,255,0.05),var(--blue) 30%,var(--blue) 70%,rgba(10,132,255,0.05));transform:translateX(-50%);z-index:1;pointer-events:none;}
.node.reverted{opacity:0.2;pointer-events:none;filter:grayscale(1);}
.node.reverted .n-title{text-decoration:line-through;}
.now-badge{position:absolute;right:16px;top:16px;font-size:10px;font-weight:700;color:var(--blue);letter-spacing:0.08em;opacity:0;transition:opacity 0.4s;}
.node.now .now-badge{opacity:1;}
.n-acts{position:absolute;right:10px;top:10px;opacity:0;transition:opacity 0.2s;display:flex;gap:5px;}
.node:hover .n-acts{opacity:1;}
.n-btn{background:rgba(255,255,255,0.08);border:0.5px solid var(--sep);color:var(--lbl2);width:26px;height:26px;border-radius:50%;display:flex;align-items:center;justify-content:center;cursor:pointer;transition:all 0.2s var(--ease);}
.n-btn:hover{background:rgba(255,255,255,0.15);color:var(--lbl1);}
.n-btn:active{transform:scale(0.9);}
.n-btn svg{width:13px;height:13px;fill:currentColor;}
.n-time{font-family:var(--mono);font-size:11px;color:var(--lbl2);margin-bottom:6px;}
.n-title{font-size:14px;font-weight:600;color:var(--lbl1);margin-bottom:4px;letter-spacing:-0.01em;}
.n-desc{font-size:13px;color:var(--lbl2);line-height:1.5;}
.n-tags{display:flex;flex-wrap:wrap;gap:4px;margin-top:6px;}
.tag{font-family:var(--mono);font-size:9px;font-weight:500;letter-spacing:0.3px;text-transform:uppercase;padding:2px 7px;border-radius:4px;background:rgba(255,255,255,0.08);color:var(--lbl2);}
.tag.sh{background:rgba(50,215,75,0.12);color:var(--green);}
.tag.fi{background:rgba(50,173,230,0.12);color:var(--cyan);}
.tag.th{background:rgba(255,159,10,0.12);color:var(--orange);}
.prog-track{margin-top:10px;height:4px;background:rgba(255,255,255,0.06);border-radius:2px;overflow:hidden;opacity:0;transition:opacity 0.4s;}
.node.now .prog-track{opacity:1;}
.prog-bar{height:100%;background:var(--blue);width:0%;border-radius:2px;transition:width 1.2s var(--ease);}
.steer-box{display:none;margin-top:10px;}
.steer-wrap{display:flex;background:var(--gray6);border:1px solid var(--purple);border-radius:8px;overflow:hidden;}
.steer-inp{flex:1;background:transparent;border:none;color:var(--lbl1);font-size:13px;padding:8px 12px;outline:none;font-family:var(--font);}
.steer-inp::placeholder{color:var(--purple);opacity:0.6;}
.steer-sub{background:rgba(191,90,242,0.15);color:var(--purple);border:none;padding:0 12px;cursor:pointer;font-weight:600;font-size:12px;font-family:var(--font);}

/* ── Dashboard — scrollable right panel, fixed card heights ── */
.dash-sc{flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:12px;min-height:0;}
.cg{background:var(--bg);border-radius:14px;border:1px solid var(--sep-s);overflow:hidden;flex-shrink:0;}
.cg-h{padding:12px 16px;display:flex;justify-content:space-between;align-items:center;cursor:pointer;user-select:none;transition:background 0.2s;}
.cg-h:hover{background:var(--fill);}
.cg-t{font-size:13px;font-weight:600;color:var(--lbl1);display:flex;align-items:center;gap:8px;}
.cg-b{background:var(--gray5);color:var(--lbl2);font-size:11px;padding:2px 8px;border-radius:8px;font-family:var(--mono);margin-left:auto;margin-right:8px;}
.pulse-dot{width:8px;height:8px;border-radius:50%;background:var(--cyan);box-shadow:0 0 8px var(--cyan);animation:pf 1s infinite alternate;}
@keyframes pf{from{opacity:0.4}to{opacity:1}}
.chev{fill:var(--lbl3);transition:transform 0.4s var(--ease);flex-shrink:0;}
.cg.open .chev{transform:rotate(180deg);}
/* Grid trick for smooth open/close WITHOUT height jumping when content changes */
.cg-cw{display:grid;grid-template-rows:0fr;transition:grid-template-rows 0.35s var(--ease);}
.cg.open .cg-cw{grid-template-rows:1fr;}
.cg-ci{overflow:hidden;}

/* Fixed heights for card content — no more jumping */
.stream-box{background:#000;padding:14px 16px;font-family:var(--mono);font-size:12px;line-height:1.6;height:160px;overflow-y:auto;border-top:0.5px solid var(--sep-s);color:var(--lbl2);word-wrap:break-word;}
.cursor-blink{display:inline-block;width:7px;height:13px;background:var(--lbl1);vertical-align:middle;margin-left:2px;animation:blink 1s step-end infinite;}
@keyframes blink{50%{opacity:0}}

/* Terminal — proper shell display, fixed height */
.term-box{background:#0d0d0d;padding:12px 0;font-family:var(--mono);font-size:11px;color:#e6e6e6;line-height:1.6;height:180px;overflow-y:auto;border-top:0.5px solid var(--sep-s);}
.term-entry{padding:4px 16px;}
.term-entry+.term-entry{border-top:0.5px solid rgba(255,255,255,0.04);margin-top:4px;padding-top:8px;}
.term-cmd-line{display:flex;gap:6px;align-items:baseline;}
.term-prompt{color:var(--blue);font-weight:bold;flex-shrink:0;}
.term-cmd{color:#fff;}
.term-meta{font-size:10px;color:var(--lbl3);margin-left:auto;}
.term-out{color:var(--lbl2);padding-left:2px;white-space:pre-wrap;word-break:break-word;margin-top:2px;}
.term-err{color:var(--red);padding-left:2px;white-space:pre-wrap;margin-top:2px;}
.term-exit-ok{color:var(--green);}
.term-exit-err{color:var(--red);}
.term-empty{color:var(--lbl3);font-style:italic;padding:16px;}

/* Journal, activity, logs */
.lr{padding:10px 16px;border-top:0.5px solid var(--sep-s);font-size:13px;line-height:1.5;}
.lr:hover{background:rgba(255,255,255,0.02);}
.lr-t{font-family:var(--mono);font-size:11px;color:var(--lbl3);margin-bottom:4px;}
.lr-x{color:var(--lbl2);}
.ar{display:flex;align-items:center;gap:12px;padding:10px 16px;border-top:0.5px solid var(--sep-s);}
.ar:hover{background:rgba(255,255,255,0.02);}
.ar-t{font-family:var(--mono);font-size:11px;color:var(--lbl3);min-width:42px;}
.ar-i{font-size:13px;opacity:0.8;}
.ar-x{font-size:13px;color:var(--lbl2);flex:1;}
.jrn-body{max-height:200px;overflow-y:auto;}
.act-body{max-height:200px;overflow-y:auto;}
.log-box{background:var(--bg);padding:12px 16px;font-family:var(--mono);font-size:11px;color:var(--lbl2);line-height:1.7;height:140px;overflow-y:auto;border-top:0.5px solid var(--sep-s);white-space:pre-wrap;}
.ws-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:8px;padding:14px 16px;border-top:0.5px solid var(--sep-s);}
.ws-i{display:flex;align-items:center;gap:8px;background:var(--gray6);padding:9px 12px;border-radius:8px;font-size:12px;color:var(--lbl2);transition:all 0.2s var(--ease);}
.ws-i:hover{background:var(--gray5);color:var(--lbl1);}
.ws-i.new{border:1px solid rgba(50,215,75,0.3);}

.attach-btn{background:transparent;border:none;padding:8px 4px 8px 12px;cursor:pointer;color:var(--lbl3);transition:color 0.2s;display:flex;align-items:center;}
.attach-btn:hover{color:var(--blue);}
.attach-btn svg{width:20px;height:20px;fill:currentColor;}
.msg-attach{display:flex;align-items:center;gap:8px;background:rgba(10,132,255,0.08);border:1px solid rgba(10,132,255,0.2);border-radius:10px;padding:8px 12px;font-size:12px;color:var(--lbl2);margin-top:4px;}
.msg-attach-icon{font-size:18px;}
.msg-attach img{max-width:200px;max-height:150px;border-radius:8px;display:block;margin-top:6px;}
.btn-restarting{background:rgba(255,159,10,0.15)!important;color:var(--orange)!important;}
.btn-loading{opacity:0.6;pointer-events:none;}
.btn-success{background:rgba(50,215,75,0.15)!important;color:var(--green)!important;}
.hz-section{padding:2px 0 6px;}
.hz-heading{font-size:10px;font-weight:700;letter-spacing:0.07em;text-transform:uppercase;color:var(--blue);padding:10px 16px 4px;opacity:0.85;}
.hz-item{padding:4px 16px 4px 24px;font-size:12px;color:var(--lbl2);line-height:1.5;position:relative;}
.hz-item::before{content:'·';position:absolute;left:14px;color:var(--lbl3);}
.hz-empty{padding:12px 16px;font-size:12px;color:var(--lbl3);}
::-webkit-scrollbar-track{background:transparent;}
::-webkit-scrollbar-thumb{background-clip:padding-box;background-color:rgba(255,255,255,0.12);border:3px solid transparent;border-radius:5px;}
::-webkit-scrollbar-thumb:hover{background-color:rgba(255,255,255,0.2);}
</style>
</head>
<body>

<header class="tb">
    <div class="tb-l">
        <div class="tb-name">Vola</div>
        <div class="tb-badge">
            <div class="tb-dot" id="statusDot"></div>
            <div class="tb-st" id="statusText">Loading</div>
        </div>
    </div>
    <div class="tb-c">
        <div class="ctrl-grp">
            <button class="ctrl-btn" id="btnPause" onclick="togglePause()">
                <svg viewBox="0 0 24 24"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
                <span id="txtPause">Pause</span>
            </button>
            <button class="ctrl-btn" id="btnStop" onclick="toggleStop()">
                <svg viewBox="0 0 24 24"><path d="M6 6h12v12H6z"/></svg>
                <span id="txtStop">Stop</span>
            </button>
            <button class="ctrl-btn" id="btnRestart" onclick="restartDaemon()" title="Restart runner process">
                <svg viewBox="0 0 24 24"><path d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/></svg>
                <span>Restart</span>
            </button>
        </div>
    </div>
    <div class="tb-r">
        <div class="chip" id="tpsChip">t/s <span id="sTps">—</span></div>
        <div class="chip" id="costChip">cost <span id="sCost">$0.00</span></div>
        <div class="chip" id="ctxChip" onclick="toggleCtx()">ctx <span id="sCtx">—</span></div>
        <div class="chip">next <span id="sNxt">—</span></div>
        <div class="chip">cycles <span id="sCyc">0</span></div>
        <div class="chip" id="verChip" title="Click to update daemon" onclick="openUpdateModal()" style="cursor:pointer;border-color:rgba(10,132,255,0.3)">ver <span id="sVer">—</span></div>

        <!-- Context popover (like mockup) -->
        <div class="ctx-pop" id="ctxPop">
            <div class="ctx-pop-hdr">Context Window <span id="ctxPopTotal">— tokens</span></div>
            <div class="ctx-bar" id="ctxBar">
                <div class="ctx-seg-sys" id="ctxSegSys" style="width:15%"></div>
                <div class="ctx-seg-mem" id="ctxSegMem" style="width:25%"></div>
                <div class="ctx-seg-chat" id="ctxSegChat" style="width:50%"></div>
                <div class="ctx-seg-tool" id="ctxSegTool" style="width:10%"></div>
            </div>
            <div class="ctx-legend">
                <div class="ctx-row"><div class="ctx-row-l"><div class="ctx-dot" style="background:var(--indigo)"></div>System Prompt</div><div class="ctx-val" id="ctxSysVal">—</div></div>
                <div class="ctx-row"><div class="ctx-row-l"><div class="ctx-dot" style="background:var(--orange)"></div>Memory Index</div><div class="ctx-val" id="ctxMemVal">—</div></div>
                <div class="ctx-row"><div class="ctx-row-l"><div class="ctx-dot" style="background:var(--blue)"></div>Chat + Context</div><div class="ctx-val" id="ctxChatVal">—</div></div>
                <div class="ctx-row"><div class="ctx-row-l"><div class="ctx-dot" style="background:var(--cyan)"></div>Tool Outputs</div><div class="ctx-val" id="ctxToolVal">—</div></div>
            </div>
            <div class="ctx-divider">
                <span>Output tokens</span><span id="ctxOutVal">—</span>
            </div>
        </div>
    </div>
</header>

<main class="app">

<!-- Chat -->
<section class="pane">
    <div class="ch-hero">
        <div class="ch-av">🦞</div>
        <div>
            <div class="ch-name">Vola</div>
            <div class="ch-sub" id="chatSub">Autonomous Agent</div>
        </div>
    </div>
    <div class="msgs" id="msgs"></div>
    <div class="inp-area">
        <!-- File preview bar (shown when file selected) -->
        <div id="attachPreview" style="display:none;padding:8px 16px 0;display:none;align-items:center;gap:8px;background:rgba(10,132,255,0.08);border-radius:12px 12px 0 0;border:1px solid rgba(10,132,255,0.2);border-bottom:none;margin-bottom:-1px;">
            <span id="attachIcon" style="font-size:18px">📎</span>
            <span id="attachName" style="font-size:12px;color:var(--lbl2);flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;"></span>
            <button onclick="clearAttach()" style="background:none;border:none;color:var(--lbl3);cursor:pointer;font-size:16px;line-height:1;">✕</button>
        </div>
        <div class="inp-wrap" id="inpWrap">
            <input type="file" id="fileInput" accept="*/*" style="display:none" onchange="onFileSelected(this)">
            <button class="attach-btn" onclick="document.getElementById('fileInput').click()" title="Attach file">
                <svg viewBox="0 0 24 24"><path d="M16.5 6v11.5c0 2.21-1.79 4-4 4s-4-1.79-4-4V5c0-1.38 1.12-2.5 2.5-2.5s2.5 1.12 2.5 2.5v10.5c0 .55-.45 1-1 1s-1-.45-1-1V6H10v9.5c0 1.38 1.12 2.5 2.5 2.5s2.5-1.12 2.5-2.5V5c0-2.21-1.79-4-4-4S7 2.79 7 5v12.5c0 3.04 2.46 5.5 5.5 5.5s5.5-2.46 5.5-5.5V6h-1.5z"/></svg>
            </button>
            <textarea class="inp" id="inp" placeholder="Message Vola..." rows="1"
                onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();send();}"></textarea>
            <button class="inp-send" onclick="send()">
                <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm.88 14v-6.13l1.83 1.83c.39.39 1.02.39 1.41 0 .39-.39.39-1.02 0-1.41l-3.41-3.41a1.004 1.004 0 0 0-1.42 0l-3.41 3.41a.996.996 0 1 0 1.41 1.41l1.83-1.83V16c0 .55.45 1 1 1s1-.45 1-1z"/></svg>
            </button>
        </div>
    </div>
</section>

<!-- Path -->
<section class="pane pane-mid">
    <div class="pane-hd">Planning Path</div>
    <div class="path-sc" id="pathScroll">
        <div class="timeline" id="timeline"></div>
    </div>
</section>

<!-- Dashboard -->
<section class="pane" style="background:var(--gray6)">
    <div class="pane-hd">Dashboard</div>
    <div class="dash-sc" id="dashScroll">

        <!-- Current Cycle Card -->
        <div class="cg open" id="c-cycle">
            <div class="cg-h" onclick="tog('c-cycle')">
                <div class="cg-t">Current Cycle</div>
                <span class="cg-b" id="cycleNum">—</span>
                <svg class="chev" width="12" height="12" viewBox="0 0 24 24"><path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/></svg>
            </div>
            <div class="cg-cw"><div class="cg-ci">
                <div id="cycleCardBody"></div>
            </div></div>
        </div>

        <!-- Live Stream -->
        <div class="cg open" id="c1">
            <div class="cg-h" onclick="tog('c1')">
                <div class="cg-t"><div class="pulse-dot" id="streamPulse"></div> Live Stream</div>
                <svg class="chev" width="12" height="12" viewBox="0 0 24 24"><path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/></svg>
            </div>
            <div class="cg-cw"><div class="cg-ci">
                <div class="stream-box" id="streamBox"><span id="streamText"></span><span class="cursor-blink" id="cursor"></span></div>
            </div></div>
        </div>

        <!-- Terminal -->
        <div class="cg open" id="c-term">
            <div class="cg-h" onclick="tog('c-term')">
                <div class="cg-t">
                    <svg width="12" height="12" viewBox="0 0 24 24" style="fill:var(--green)"><path d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 14H4V8h16v10zM6 10l1.5 1.5L6 13l1 1 2.5-2.5L7 9l-1 1zm4 4h4v-1.5h-4V14z"/></svg>
                    Terminal Output
                </div>
                <svg class="chev" width="12" height="12" viewBox="0 0 24 24"><path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/></svg>
            </div>
            <div class="cg-cw"><div class="cg-ci">
                <div class="term-box" id="termBox"><div class="term-empty">No shell commands run yet.</div></div>
            </div></div>
        </div>

        <!-- Journal -->
        <div class="cg" id="c2">
            <div class="cg-h" onclick="tog('c2')">
                <div class="cg-t">Journal</div>
                <span class="cg-b" id="jrnCt">0</span>
                <svg class="chev" width="12" height="12" viewBox="0 0 24 24"><path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/></svg>
            </div>
            <div class="cg-cw"><div class="cg-ci"><div class="jrn-body" id="jrnBody"></div></div></div>
        </div>

        <!-- Horizons -->
        <div class="cg" id="c-horizons">
            <div class="cg-h" onclick="tog('c-horizons')">
                <div class="cg-t">Horizons</div>
                <svg class="chev" width="12" height="12" viewBox="0 0 24 24"><path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/></svg>
            </div>
            <div class="cg-cw"><div class="cg-ci"><div class="jrn-body" id="horizonsBody"></div></div></div>
        </div>

        <!-- Activity -->
        <div class="cg open" id="c3">
            <div class="cg-h" onclick="tog('c3')">
                <div class="cg-t">Activity</div>
                <svg class="chev" width="12" height="12" viewBox="0 0 24 24"><path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/></svg>
            </div>
            <div class="cg-cw"><div class="cg-ci"><div class="act-body" id="actBody"></div></div></div>
        </div>

        <!-- System Logs -->
        <div class="cg" id="c4">
            <div class="cg-h" onclick="tog('c4')">
                <div class="cg-t">System Logs</div>
                <svg class="chev" width="12" height="12" viewBox="0 0 24 24"><path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/></svg>
            </div>
            <div class="cg-cw"><div class="cg-ci">
                <div class="log-box" id="logBox"></div>
            </div></div>
        </div>

        <!-- Workspace -->
        <div class="cg open" id="c5">
            <div class="cg-h" onclick="tog('c5')">
                <div class="cg-t">Workspace</div>
                <span class="cg-b" id="wsCt">0</span>
                <svg class="chev" width="12" height="12" viewBox="0 0 24 24"><path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/></svg>
            </div>
            <div class="cg-cw"><div class="cg-ci">
                <div class="ws-grid" id="wsGrid"></div>
            </div></div>
        </div>

    </div>
</section>

</main>

<script>
// ── Utils ──────────────────────────────────────────────────────────────
function escH(s){const d=document.createElement('div');d.textContent=s;return d.innerHTML;}
function tog(id){document.getElementById(id).classList.toggle('open');}
function fmtNum(n){return n>=1000?`${(n/1000).toFixed(1)}k`:String(n);}

const inp=document.getElementById('inp');
inp.addEventListener('input',()=>{inp.style.height='auto';inp.style.height=Math.min(inp.scrollHeight,120)+'px';});

// ── File attachment ─────────────────────────────────────────────────────
let pendingFile=null;
function onFileSelected(input){
    const file=input.files[0];
    if(!file)return;
    pendingFile=file;
    const prev=document.getElementById('attachPreview');
    const isImg=file.type.startsWith('image/');
    document.getElementById('attachIcon').textContent=isImg?'🖼️':'📄';
    document.getElementById('attachName').textContent=`${file.name} (${(file.size/1024).toFixed(1)} KB)`;
    prev.style.display='flex';
}
function clearAttach(){
    pendingFile=null;
    document.getElementById('fileInput').value='';
    document.getElementById('attachPreview').style.display='none';
}

// ── Send ────────────────────────────────────────────────────────────────
async function send(){
    const msg=inp.value.trim();
    if(!msg&&!pendingFile)return;
    const ts=Math.floor(Date.now()/1000); // seconds, matching server-side int(time.time())

    if(pendingFile){
        // Send as multipart
        const fd=new FormData();
        fd.append('file',pendingFile);
        if(msg)fd.append('message',msg);
        const isImg=pendingFile.type.startsWith('image/');
        // Optimistic UI
        const previewHTML=isImg
            ?`<div class="msg-attach"><div><div class="msg-attach-icon">🖼️</div><img src="${URL.createObjectURL(pendingFile)}" alt="${escH(pendingFile.name)}"></div></div>`
            :`<div class="msg-attach"><span class="msg-attach-icon">📄</span>${escH(pendingFile.name)}</div>`;
        appendMsgDOM('lars','🧑',msg,new Date().toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'}),true,previewHTML,ts);
        clearAttach();
        inp.value='';inp.style.height='auto';inp.focus();
        try{
            await fetch('/api/upload',{method:'POST',body:fd});
        }catch(e){console.error('Upload error:',e);}
    } else {
        // Plain text
        fetch('/api/send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:msg})});
        appendMsgDOM('lars','🧑',msg,new Date().toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'}),true,'',ts);
        inp.value='';inp.style.height='auto';inp.focus();
    }
}

// ── Append-only chat DOM ────────────────────────────────────────────────
// Key insight: never replace the DOM. Only append new messages.
// Track which timestamps we've already rendered.
const renderedMsgTs=new Set();

function appendMsgDOM(senderClass,avatar,text,timeStr,isOut,extraHTML,ts){
    const key=ts||`${senderClass}_${timeStr}_${text.slice(0,10)}`;
    if(renderedMsgTs.has(String(key)))return;
    renderedMsgTs.add(String(key));

    const el=document.createElement('div');
    el.className='msg'+(isOut?' out':'');
    el.dataset.ts=String(key);
    el.innerHTML=`<div class="msg-av">${avatar}</div><div class="msg-c"><div class="msg-bub">${escH(text)}</div>${extraHTML||''}<div class="msg-meta">${timeStr}</div></div>`;
    const m=document.getElementById('msgs');
    m.appendChild(el);
    // Always scroll to bottom when a new message arrives
    m.scrollTo({top:999999,behavior:'smooth'});
}

function appendApprovalDOM(approval){
    const key='approval_'+approval.requested_at;
    if(renderedMsgTs.has(key))return;
    renderedMsgTs.add(key);
    const el=document.createElement('div');
    el.className='msg';
    el.dataset.ts=key;
    el.innerHTML=`<div class="msg-av">🦞</div><div class="msg-c"><div class="msg-bub action"><div class="action-title">🔐 Permission Required</div><div class="action-desc">${escH(approval.message||'')}</div><div class="act-btns" id="approvalBtns_${key.replace(/[^a-z0-9]/gi,'_')}"><button class="act-btn deny" onclick="handleApproval(false,'${key}')">Deny</button><button class="act-btn approve" onclick="handleApproval(true,'${key}')">Approve</button></div></div><div class="msg-meta">now</div></div>`;
    document.getElementById('msgs').appendChild(el);
}

function syncChatFromServer(messages, approval){
    // Validate messages is an array
    if(!Array.isArray(messages)){console.warn('syncChat: messages not array', messages);return;}
    // Only append messages we haven't seen yet
    for(const m of messages){
        if(!m||typeof m!=='object')continue;
        const senderClass=m.sender_class||'unknown';
        const timeStr=m.time||'?';
        const textStr=m.text||'';
        const avatar=m.avatar||'🦞';
        const ts=m.ts||0;
        const key=String(ts||`${senderClass}_${timeStr}_${textStr.slice(0,10)}`);
        if(!renderedMsgTs.has(key)){
            appendMsgDOM(senderClass, avatar, textStr, timeStr, senderClass==='lars', '', key);
        }
    }
    if(approval)appendApprovalDOM(approval);
}

// ── Controls ────────────────────────────────────────────────────────────
let isPaused=false,isStopped=false;
function togglePause(){
    const btn=document.getElementById('btnPause');
    btn.classList.add('btn-loading');
    fetch('/api/pause',{method:'POST'}).then(r=>r.json()).then(d=>{
        isPaused=d.paused;
        btn.classList.remove('btn-loading');
        syncControlUI();
    }).catch(()=>btn.classList.remove('btn-loading'));
}
function toggleStop(){
    const btn=document.getElementById('btnStop');
    btn.classList.add('btn-loading');
    fetch('/api/stop',{method:'POST'}).then(r=>r.json()).then(d=>{
        isStopped=d.stopped;
        if(isStopped)isPaused=false;
        btn.classList.remove('btn-loading');
        syncControlUI();
    }).catch(()=>btn.classList.remove('btn-loading'));
}
function restartDaemon(){
    const btn=document.getElementById('btnRestart');
    const span=btn.querySelector('span');
    btn.classList.add('btn-restarting');
    span.textContent='Restarting…';
    btn.disabled=true;
    fetch('/api/restart',{method:'POST'}).then(()=>{
        let dots=0;
        const iv=setInterval(()=>{
            dots=(dots+1)%4;
            span.textContent='Restarting'+'…'.repeat(dots+1).slice(0,3)||'Restarting…';
        },500);
        // Poll until daemon responds again
        let tries=0;
        const check=setInterval(()=>{
            tries++;
            fetch('/api/status').then(r=>r.json()).then(()=>{
                clearInterval(iv); clearInterval(check);
                btn.classList.remove('btn-restarting');
                btn.classList.add('btn-success');
                span.textContent='✓ Restarted';
                btn.disabled=false;
                setTimeout(()=>{btn.classList.remove('btn-success');span.textContent='Restart';},2000);
            }).catch(()=>{if(tries>30){clearInterval(iv);clearInterval(check);btn.classList.remove('btn-restarting');span.textContent='Restart';btn.disabled=false;}});
        },800);
    });
}
// ── Update Modal ────────────────────────────────────────────────────────────
let _updateFile=null;
function openUpdateModal(){document.getElementById('updateModal').style.display='flex';}
function closeUpdateModal(){document.getElementById('updateModal').style.display='none';_updateFile=null;document.getElementById('updateFileName').textContent='';document.getElementById('updateBtn').disabled=true;document.getElementById('updateBtn').style.opacity='0.5';document.getElementById('updateStatus').textContent='';}
function handleUpdateFile(f){if(!f)return;_updateFile=f;document.getElementById('updateFileName').textContent=f.name;document.getElementById('updateBtn').disabled=false;document.getElementById('updateBtn').style.opacity='1';}
function handleUpdateDrop(e){e.preventDefault();document.getElementById('updateDropZone').style.borderColor='var(--sep)';const f=e.dataTransfer.files[0];if(f)handleUpdateFile(f);}
function submitUpdate(){
    if(!_updateFile)return;
    const btn=document.getElementById('updateBtn');
    const st=document.getElementById('updateStatus');
    btn.textContent='Uploading…'; btn.disabled=true;
    const fd=new FormData(); fd.append('file',_updateFile);
    fetch('/api/update',{method:'POST',body:fd}).then(r=>r.json()).then(d=>{
        if(d.success){
            st.textContent='✓ Updated ('+d.copied.join(', ')+') — restarting…';
            st.style.color='var(--green)';
            setTimeout(closeUpdateModal,3000);
        }else{
            st.textContent='Error: '+(d.error||'unknown');
            st.style.color='var(--red)';
            btn.textContent='Install Update'; btn.disabled=false;
        }
    }).catch(e=>{st.textContent='Upload failed: '+e;st.style.color='var(--red)';btn.textContent='Install Update';btn.disabled=false;});
}
function syncControlUI(){
    const pb=document.getElementById('btnPause'),pt=document.getElementById('txtPause');
    const sb=document.getElementById('btnStop'),st=document.getElementById('txtStop');
    pb.className='ctrl-btn'+(isPaused?' on-pause':'');
    pt.textContent=isPaused?'Resume':'Pause';
    pb.querySelector('svg').innerHTML=isPaused?'<path d="M8 5v14l11-7z"/>':'<path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>';
    sb.className='ctrl-btn'+(isStopped?' on-stop':'');
    st.textContent=isStopped?'Start':'Stop';
    sb.querySelector('svg').innerHTML=isStopped?'<path d="M8 5v14l11-7z"/>':'<path d="M6 6h12v12H6z"/>';
    pb.style.opacity=isStopped?'0.5':'1';
    pb.style.pointerEvents=isStopped?'none':'auto';
}

// ── Context popover ─────────────────────────────────────────────────────
let ctxOpen=false;
function toggleCtx(){
    ctxOpen=!ctxOpen;
    document.getElementById('ctxPop').classList.toggle('open',ctxOpen);
    document.getElementById('ctxChip').classList.toggle('active',ctxOpen);
}
document.addEventListener('click',e=>{
    const pop=document.getElementById('ctxPop'),chip=document.getElementById('ctxChip');
    if(ctxOpen&&!pop.contains(e.target)&&!chip.contains(e.target)){
        ctxOpen=false;pop.classList.remove('open');chip.classList.remove('active');
    }
});
function updateCtxPopover(b){
    const total=b.total||0;
    document.getElementById('ctxPopTotal').textContent=total?`${total.toLocaleString()} tokens`:'— tokens';
    document.getElementById('ctxOutVal').textContent=b.completion?b.completion.toLocaleString():'—';
    const sys=Math.round(total*0.10),mem=Math.round(total*0.20),tool=Math.round(total*0.10),chat=total-sys-mem-tool;
    document.getElementById('ctxSysVal').textContent=fmtNum(sys)||'—';
    document.getElementById('ctxMemVal').textContent=fmtNum(mem)||'—';
    document.getElementById('ctxChatVal').textContent=fmtNum(Math.max(0,chat))||'—';
    document.getElementById('ctxToolVal').textContent=fmtNum(tool)||'—';
    if(total>0){
        document.getElementById('ctxSegSys').style.width=(sys/total*100)+'%';
        document.getElementById('ctxSegMem').style.width=(mem/total*100)+'%';
        document.getElementById('ctxSegChat').style.width=(Math.max(0,chat)/total*100)+'%';
        document.getElementById('ctxSegTool').style.width=(tool/total*100)+'%';
    }
}

// ── Approval ────────────────────────────────────────────────────────────
function handleApproval(approved,key){
    fetch('/api/approval',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({approved})})
    .then(r=>r.json()).then(()=>{
        const safeKey=key.replace(/[^a-z0-9]/gi,'_');
        const box=document.getElementById(`approvalBtns_${safeKey}`);
        if(box)box.innerHTML=`<div class="action-result" style="color:${approved?'var(--blue)':'var(--red)'}">${approved?'✓ Approved':'✕ Denied'}</div>`;
    });
}

// ── Rollback ────────────────────────────────────────────────────────────
function rollback(cycle){
    if(!confirm(`Revert to cycle ${cycle}?`))return;
    fetch('/api/rollback',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cycle})})
    .then(r=>r.json()).then(d=>{
        if(d.success){
            const s=document.createElement('div');s.className='msg-sys';
            s.innerHTML=`⚠️ Rolled back to Cycle ${cycle}`;
            document.getElementById('msgs').appendChild(s);
        }
    });
}

// ── Steer / Whisper ─────────────────────────────────────────────────────
function openSteer(btn){
    const node=btn.closest('.node');
    node.querySelector('.n-desc').style.display='none';
    const box=node.querySelector('.steer-box');
    box.style.display='block';
    box.querySelector('.steer-inp').focus();
}
function submitSteer(inputEl){
    const val=inputEl.value.trim();
    const node=inputEl.closest('.node');
    const desc=node.querySelector('.n-desc');
    if(val){
        fetch('/api/whisper',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({whisper:val})});
        desc.innerHTML=desc.textContent+`<div style="margin-top:4px;font-size:10px;color:var(--purple)">✏ Whisper: "${escH(val)}"</div>`;
    }
    node.querySelector('.steer-box').style.display='none';
    desc.style.display='block';
}

// ── Render: path ────────────────────────────────────────────────────────
function renderPath(nodes){
    if(!Array.isArray(nodes))return'';
    let h='';
    for(let i=0;i<nodes.length;i++){
        try{
            const n=nodes[i];
            if(!n||typeof n!=='object')continue;
            const s=(['done','now','next'].includes(n.state))?n.state:'done';
            const tags=Array.isArray(n.tags)?n.tags.map(t=>{
                try{return`<span class="tag ${t.type==='shell'?'sh':t.type==='file'?'fi':'th'}">${escH(String(t.label||''))}</span>`;}
                catch(e){return'';}
            }).join(''):'';
            const isDone=s==='done',isNow=s==='now',isNext=s==='next';
            let acts='';
            if(isDone)acts=`<div class="n-acts"><div class="n-btn" title="Rollback" onclick="rollback(${Number(n.cycle||i)})"><svg viewBox="0 0 24 24"><path d="M13 3c-4.97 0-9 4.03-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42C8.27 19.99 10.51 21 13 21c4.97 0 9-4.03 9-9s-4.03-9-9-9z"/></svg></div></div>`;
            if(isNext)acts=`<div class="n-acts"><div class="n-btn" title="Steer" onclick="openSteer(this)"><svg viewBox="0 0 24 24"><path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/></svg></div></div>`;
            h+=`<div class="node ${s}">
                ${isNow?'<div class="now-badge">NOW</div>':''}${acts}
                <div class="n-time">${escH(String(n.time||''))}</div>
                <div class="n-title">${escH(String(n.title||''))}</div>
                <div class="n-desc">${escH(String(n.desc||''))}</div>
                ${tags?'<div class="n-tags">'+tags+'</div>':''}
                ${isNow?'<div class="prog-track"><div class="prog-bar" style="width:60%"></div></div>':''}
                ${isNext?`<div class="steer-box"><div class="steer-wrap"><input type="text" class="steer-inp" placeholder="Inject direction..." onkeydown="if(event.key==='Enter')submitSteer(this)"><button class="steer-sub" onclick="submitSteer(this.previousElementSibling)">Set</button></div></div>`:''}
            </div>`;
        }catch(e){console.warn('renderPath: skipping bad node',i,e);}
    }
    return h;
}

// ── Render: terminal ────────────────────────────────────────────────────
function renderTerminal(entries){
    if(!entries||entries.length===0)return'<div class="term-empty">No shell commands run yet.</div>';
    let h='';
    for(const e of entries){
        const exitColor=e.exit===0?'var(--green)':'var(--red)';
        const ts=e.ts?new Date(e.ts*1000).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit',second:'2-digit'}):'';
        const outLines=e.out?e.out.split('\n').slice(0,20).join('\n'):'';
        h+=`<div class="term-entry">
            <div class="term-cmd-line">
                <span class="term-prompt">vola@~/workspace$</span>
                <span class="term-cmd">${escH(e.cmd)}</span>
                <span class="term-meta">${ts} <span style="color:${exitColor}">${e.exit===0?'✓':'✗'}</span> ${e.elapsed}s</span>
            </div>
            ${outLines?`<div class="term-out">${escH(outLines)}</div>`:''}
        </div>`;
    }
    return h;
}

// ── Anti-flicker hashes ─────────────────────────────────────────────────
const hashes={path:'',journal:'',horizons:'',activity:'',log:'',workspace:'',terminal:'',cycleCard:''};
function hashStr(s){let h=5381;for(let i=0;i<Math.min(s.length,2000);i++)h=(h*31^s.charCodeAt(i))>>>0;return h.toString(36);}
function isUserTypingInDash(){const a=document.activeElement;return a&&(a.tagName==='INPUT'||a.tagName==='TEXTAREA')&&document.getElementById('dashScroll').contains(a);}

// ── Countdown ───────────────────────────────────────────────────────────
let countdownEnd=null,countdownInterval=null;
function startCountdown(seconds){
    if(countdownInterval)clearInterval(countdownInterval);
    countdownEnd=Date.now()+seconds*1000;
    function tick(){
        const rem=Math.max(0,(countdownEnd-Date.now())/1000);
        const m=Math.floor(rem/60),s=Math.floor(rem%60);
        document.getElementById('sNxt').textContent=rem>0?`${m}m${String(s).padStart(2,'0')}s`:'imm';
        if(rem<=0)clearInterval(countdownInterval);
    }
    tick();countdownInterval=setInterval(tick,1000);
}

// ── Main poll ───────────────────────────────────────────────────────────
async function poll(){
    let d;
    try{const r=await fetch('/api/status');d=await r.json();}
    catch(e){console.error('Poll:',e);return;}
    
    // Validate response has required fields
    if(!d||typeof d!=='object'){console.error('Poll: invalid response');return;}

    // Toolbar
    const dot=document.getElementById('statusDot'),stxt=document.getElementById('statusText');
    const mode=d.exec_mode||d.agent_state||d.status;
    const labels={running:'Running',invoking:'Thinking',waiting:'Waiting',paused:'Paused',stopped:'Stopped',error:'Error',restarting:'Restarting'};
    const colors={running:'var(--blue)',invoking:'var(--cyan)',waiting:'var(--orange)',paused:'var(--yellow)',stopped:'var(--gray)',error:'var(--red)',restarting:'var(--orange)'};
    stxt.textContent=labels[mode]||mode;
    stxt.style.color=colors[mode]||'var(--blue)';
    dot.className='tb-dot';
    if(['paused','stopped','error','waiting','invoking'].includes(mode))dot.classList.add(mode);

    const prevP=isPaused,prevS=isStopped;
    isPaused=d.is_paused;isStopped=d.is_stopped;
    if(isPaused!==prevP||isStopped!==prevS)syncControlUI();

    document.getElementById('sCtx').textContent=d.context_used;
    document.getElementById('sCyc').textContent=d.cycles;
    document.getElementById('chatSub').textContent=d.detail||'Autonomous Agent';
    if(d.tps>0)document.getElementById('sTps').textContent=d.tps;
    if(d.total_cost>0)document.getElementById('sCost').textContent='$'+d.total_cost.toFixed(3);
    if(d.version)document.getElementById('sVer').textContent=d.version;
    if(d.countdown_seconds&&d.countdown_seconds>0){
        startCountdown(d.countdown_seconds);
    }else if(!countdownEnd||(countdownEnd-Date.now())<0){
        document.getElementById('sNxt').textContent=d.next_wake||'—';
    }
    if(d.ctx_breakdown)updateCtxPopover(d.ctx_breakdown);

    // Chat — append only, never replace
    syncChatFromServer(d.messages||[], d.approval);

    // Cycle card
    const cc=d.cycle_card||{};
    const cch=hashStr(JSON.stringify(cc));
    if(cch!==hashes.cycleCard){
        hashes.cycleCard=cch;
        document.getElementById('cycleNum').textContent=cc.cycle?'#'+cc.cycle:'—';
        const body=document.getElementById('cycleCardBody');
        if(cc.now||cc.next){
            let html='<div class="cycle-card">';
            if(cc.now)  html+=`<div class="cc-row"><span class="cc-label">Last</span><span class="cc-text">${escH(cc.now)}</span></div>`;
            if(cc.next) html+=`<div class="cc-row"><span class="cc-label">Up next</span><span class="cc-text">${escH(cc.next)}</span></div>`;
            const meta=[];
            if(cc.action)     meta.push(cc.action);
            if(cc.tool_calls) meta.push(cc.tool_calls+' tool calls');
            if(cc.date)       meta.push(cc.date);
            if(meta.length)   html+=`<div class="cc-meta">${escH(meta.join(' · '))}</div>`;
            html+='</div>';
            body.innerHTML=html;
        } else {
            body.innerHTML='<div style="color:var(--fg3);font-size:12px;padding:4px 0">No cycle yet.</div>';
        }
    }

    // Path
    const ph=hashStr(JSON.stringify(d.path_nodes||[]));
    const hasOpenSteer=document.querySelector('.steer-box[style*="block"]');
    if(ph!==hashes.path&&!hasOpenSteer){
        hashes.path=ph;
        const tl=document.getElementById('timeline');
        tl.innerHTML=renderPath(d.path_nodes||[]);
        const nowNode=tl.querySelector('.node.now');
        if(nowNode){
            const ps=document.getElementById('pathScroll');
            const target=nowNode.offsetTop-ps.clientHeight/2+nowNode.clientHeight/2;
            if(Math.abs(ps.scrollTop-target)>120)ps.scrollTo({top:target,behavior:'smooth'});
        }
    }

    if(isUserTypingInDash())return;

    // Terminal
    const termKey=(d.terminal_entries||[]).map(e=>e.ts).join(',');
    if(termKey!==hashes.terminal){
        hashes.terminal=termKey;
        const tb=document.getElementById('termBox');
        tb.innerHTML=renderTerminal(d.terminal_entries);
        tb.scrollTop=tb.scrollHeight;
    }

    // Journal
    const jh=hashStr(JSON.stringify(d.journal_entries||[]));
    if(jh!==hashes.journal){
        hashes.journal=jh;
        document.getElementById('jrnCt').textContent=d.journal_count;
        let jhtml='';
        for(const j of d.journal_entries||[])jhtml+=`<div class="lr"><div class="lr-t">${j.time}</div><div class="lr-x">${j.text}</div></div>`;
        document.getElementById('jrnBody').innerHTML=jhtml;
    }

    // Horizons
    const hzh=hashStr(d.horizons||'');
    if(hzh!==hashes.horizons){
        hashes.horizons=hzh;
        const hb=document.getElementById('horizonsBody');
        if(d.horizons){
            const lines=d.horizons.split('\n');
            let hhtml='<div class="hz-section">';
            for(const line of lines){
                const t=line.trim();
                if(!t)continue;
                if(t.startsWith('## ')){
                    hhtml+=`<div class="hz-heading">${escH(t.slice(3))}</div>`;
                }else if(t.startsWith('# ')){
                    hhtml+=`<div class="hz-heading">${escH(t.slice(2))}</div>`;
                }else if(t.startsWith('- ')||t.startsWith('* ')){
                    hhtml+=`<div class="hz-item">${escH(t.slice(2))}</div>`;
                }else{
                    hhtml+=`<div class="hz-item" style="padding-left:16px">${escH(t)}</div>`;
                }
            }
            hhtml+='</div>';
            hb.innerHTML=hhtml;
        } else {
            hb.innerHTML='<div class="hz-empty">Not yet written.</div>';
        }
    }

    // Activity
    const ah=hashStr(JSON.stringify((d.activities||[]).slice(0,5)));
    if(ah!==hashes.activity){
        hashes.activity=ah;
        let ahtml='';
        for(const a of d.activities||[])ahtml+=`<div class="ar"><div class="ar-t">${a.time}</div><div class="ar-i">${a.icon}</div><div class="ar-x">${a.title}</div></div>`;
        document.getElementById('actBody').innerHTML=ahtml;
    }

    // Logs
    const logTail=(d.raw_log||'').slice(-200);
    if(logTail!==hashes.log){
        hashes.log=logTail;
        const lb=document.getElementById('logBox');
        const atBottom=lb.scrollHeight-lb.scrollTop-lb.clientHeight<40;
        lb.textContent=d.raw_log||'';
        if(atBottom)lb.scrollTop=lb.scrollHeight;
    }

    // Workspace
    const wh=hashStr(JSON.stringify((d.workspace_files||[]).map(f=>f.name)));
    if(wh!==hashes.workspace){
        hashes.workspace=wh;
        document.getElementById('wsCt').textContent=(d.workspace_files||[]).length;
        let whtml='';
        for(const f of d.workspace_files||[])whtml+=`<div class="ws-i${f.new?' new':''}">${f.icon} ${f.name}</div>`;
        document.getElementById('wsGrid').innerHTML=whtml;
    }
}

// Stream poll
let lastStreamText='';
async function pollStream(){
    try{
        const r=await fetch('/api/stream');
        const d=await r.json();
        const el=document.getElementById('streamText');
        if(d.text!==lastStreamText){
            lastStreamText=d.text;
            el.textContent=d.text.slice(-3000);
            const sb=document.getElementById('streamBox');
            sb.scrollTop=sb.scrollHeight;
        }
        document.getElementById('cursor').style.display=d.done?'none':'inline-block';
        document.getElementById('streamPulse').style.animation=d.done?'none':'pf 1s infinite alternate';
    }catch(e){}
}

// Add ts to messages from server data
const _origSyncChat=syncChatFromServer;

poll();
setInterval(poll,3000);
setInterval(pollStream,800);
</script>

<!-- Update Modal -->
<div id="updateModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.7);z-index:9999;align-items:center;justify-content:center;">
    <div style="background:var(--bg);border:1px solid var(--sep);border-radius:16px;padding:24px;width:360px;max-width:90vw;">
        <div style="font-size:15px;font-weight:600;color:var(--lbl1);margin-bottom:6px;">Update Daemon</div>
        <div style="font-size:12px;color:var(--lbl3);margin-bottom:16px;">Select a vola-vX.X.X.tar.gz file. The daemon will update and restart automatically.</div>
        <div id="updateDropZone" style="border:1.5px dashed var(--sep);border-radius:10px;padding:20px;text-align:center;cursor:pointer;transition:border-color 0.2s;margin-bottom:12px;" onclick="document.getElementById('updateFileInput').click()" ondragover="event.preventDefault();this.style.borderColor='var(--blue)'" ondragleave="this.style.borderColor='var(--sep)'" ondrop="handleUpdateDrop(event)">
            <div style="font-size:24px;margin-bottom:6px;">📦</div>
            <div style="font-size:12px;color:var(--lbl2)">Drop .tar.gz here or click to browse</div>
            <div id="updateFileName" style="font-size:11px;color:var(--blue);margin-top:6px;"></div>
        </div>
        <input type="file" id="updateFileInput" accept=".tar.gz,.tgz" style="display:none" onchange="handleUpdateFile(this.files[0])">
        <div style="display:flex;gap:8px;">
            <button onclick="closeUpdateModal()" style="flex:1;background:var(--fill);border:1px solid var(--sep-s);border-radius:8px;padding:8px;color:var(--lbl2);font-size:13px;cursor:pointer;">Cancel</button>
            <button id="updateBtn" onclick="submitUpdate()" disabled style="flex:2;background:rgba(10,132,255,0.15);border:1px solid rgba(10,132,255,0.3);border-radius:8px;padding:8px;color:var(--blue);font-size:13px;cursor:pointer;opacity:0.5;">Install Update</button>
        </div>
        <div id="updateStatus" style="font-size:11px;color:var(--lbl3);margin-top:10px;text-align:center;"></div>
    </div>
</div>
</body>
</html>'''


if __name__ == "__main__":
    for d in [LOG_DIR, JOURNAL_DIR, STATE_DIR, DASHBOARD_DIR, INBOX_DIR,
              OUTBOX_DIR, WORKSPACE_DIR, CHAT_HISTORY_DIR, SNAPSHOTS_DIR]:
        d.mkdir(parents=True, exist_ok=True)
    app.run(host="127.0.0.1", port=8083, debug=False)
