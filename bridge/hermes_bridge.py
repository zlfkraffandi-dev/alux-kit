#!/usr/bin/env python3
"""hermes-bridge — run ExtendScript in the open Premiere Pro through the Hermes Bridge CEP panel.

    hermes-bridge status                 # panel alive? + project / sequence summary
    hermes-bridge ping                   # panel heartbeat only (no Premiere call)
    hermes-bridge eval "app.version"     # evaluate an ExtendScript expression
    hermes-bridge run file.jsx           # run a .jsx file   (or: ... run -  to read stdin)
    options: --timeout N (default 180 s)

Panel: com.hermes.bridge  (%APPDATA%\\Adobe\\CEP\\extensions\\com.hermes.bridge)
Queue: %LOCALAPPDATA%\\hermes\\bridge\\premiere\\{inbox,outbox,heartbeat.json}
The value of the script's last expression is returned; errors come back as "ERR: ... (line N)".
Exit codes: 0 ok, 1 script error, 2 panel not alive, 3 timeout, 64 usage.
"""
import json
import os
import sys
import time
from pathlib import Path

if os.name == "nt":
    ROOT = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "hermes" / "bridge" / "premiere"
else:
    ROOT = Path.home() / "Library" / "Application Support" / "hermes" / "bridge" / "premiere"
INBOX, OUTBOX, HEARTBEAT = ROOT / "inbox", ROOT / "outbox", ROOT / "heartbeat.json"

STATUS_JSX = r"""
(function () {
    var r = ["premiere " + app.version];
    if (!app.project || !app.project.path) { r.push("no project open"); return r.join("\n"); }
    r.push("project  " + app.project.path);
    var n = app.project.sequences.numSequences, names = [];
    for (var i = 0; i < n; i++) names.push(app.project.sequences[i].name);
    r.push("sequences(" + n + ") " + names.join(" | "));
    var s = app.project.activeSequence;
    if (s) {
        var fps = Math.round(254016000000 / Number(s.timebase) * 1000) / 1000;
        r.push("active   " + s.name + "  " + s.frameSizeHorizontal + "x" + s.frameSizeVertical + " @" + fps +
               "fps  V" + s.videoTracks.numTracks + "/A" + s.audioTracks.numTracks +
               "  markers " + s.markers.numMarkers + "  playhead " + s.getPlayerPosition().seconds.toFixed(2) + "s");
    } else {
        r.push("active   none");
    }
    return r.join("\n");
})();
"""


def heartbeat():
    try:
        return json.loads(HEARTBEAT.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def alive(max_age=3.0):
    hb = heartbeat()
    return bool(hb) and time.time() * 1000 - hb.get("t", 0) < max_age * 1000


def run(code, timeout=180):
    if not alive():
        print("ERR: Hermes Bridge not alive - open Premiere, then Window > Extensions > Hermes Bridge", file=sys.stderr)
        sys.exit(2)
    INBOX.mkdir(parents=True, exist_ok=True)
    job = f"job_{int(time.time() * 1000)}_{os.getpid()}"
    tmp = INBOX / f".{job}.tmp"
    tmp.write_text(code, encoding="utf-8")
    tmp.rename(INBOX / f"{job}.jsx")               # atomic: the panel never reads a half-written file
    answer = OUTBOX / f"{job}.txt"
    deadline = time.time() + timeout
    while time.time() < deadline:
        if answer.exists():
            try:
                text = answer.read_text(encoding="utf-8")
                answer.unlink(missing_ok=True)
                return text
            except PermissionError:
                time.sleep(0.05)
                continue
        time.sleep(0.05)
    (INBOX / f"{job}.jsx").unlink(missing_ok=True)
    hb = heartbeat() or {}
    why = f"panel busy with {hb.get('job')} for {hb.get('busy_ms', 0) // 1000}s" if hb.get("busy") else \
          "panel closed, or a modal dialog is open in Premiere"
    print(f"TIMEOUT: Hermes Bridge did not answer ({why})", file=sys.stderr)
    sys.exit(3)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    timeout = 180
    if "--timeout" in args:
        i = args.index("--timeout")
        timeout = int(args[i + 1])
        del args[i:i + 2]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return
    cmd = args[0]
    if cmd == "ping":
        hb = heartbeat()
        ok = alive()
        print(("alive " if ok else "NOT alive ") + json.dumps(hb))
        sys.exit(0 if ok else 2)
    if cmd == "status":
        code = STATUS_JSX
    elif cmd == "eval" and len(args) > 1:
        code = " ".join(args[1:])
    elif cmd == "run" and len(args) > 1:
        code = sys.stdin.read() if args[1] == "-" else Path(args[1]).read_text(encoding="utf-8")
    else:
        print(__doc__)
        sys.exit(64)
    out = run(code, timeout)
    print(out)
    sys.exit(1 if out.startswith("ERR:") else 0)


if __name__ == "__main__":
    main()
