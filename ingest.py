"""ALUX ingest: picks -> download -> rename -> ffprobe -> import into Premiere (match by MARKING NAME, never timecode).
  uv run --with websockets python ingest.py --picks DIR [--dry-run]      footage (V4 B###->V1, V5 A###->V2)
  uv run --with websockets python ingest.py --graphics DIR [--dry-run]    renders named EP005-###*.mp4/mov -> V3 at V6 marking
  python ingest.py --undo                                                 remove what the last run placed (ingest_manifest.json)
Needs: Chrome with --remote-debugging-port=9222 logged in to Envato, Hermes Bridge panel open, ffprobe/ffmpeg.
Refuses to overwrite a non-empty target track range. Report: ingest_report.json. Never ship keys; none used.
"""
import argparse, glob, json, os, re, shutil, subprocess, sys, tempfile, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
LA = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
BRIDGE = os.environ.get("HERMES_BRIDGE", os.path.join(LA, "hermes", "bridge", "hermes_bridge.py"))
CDP = "http://127.0.0.1:9222"
UA = "AluxResearch/1.0 (editor footage pick; contact: alux editors)"
TPS = 254016000000
IMG = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".gif", ".bmp"}
TR = {"V1": 0, "V2": 1, "V3": 2, "V4": 3, "V5": 4, "V6": 5}


def wp(p):
    # git-bash "/d/x" -> "D:/x" (abspath alone would make D:/d/x)
    m = re.match(r"^/([a-zA-Z])/(.*)", p or "")
    return os.path.abspath((m.group(1).upper() + ":/" + m.group(2)) if m else p)


def tool(n):
    p = os.environ.get(n.upper()) or shutil.which(n)
    if not p:
        for g in glob.glob(os.path.join(LA, "hermes", "tools", "ffmpeg*", "bin", n + ".exe")):
            p = g
    if not p:
        sys.exit("%s tidak ditemukan (pasang ffmpeg atau set env %s)" % (n, n.upper()))
    return p


# ---------- Premiere (ExtendScript through Hermes Bridge) ----------
PRE = r'''
var seq = app.project.activeSequence;
function findItem(b, n) { for (var i = 0; i < b.children.numItems; i++) { var c = b.children[i]; if (c.name === n) return c; if (c.type === 2) { var r = findItem(c, n); if (r) return r; } } return null; }
function findBin(b, n) { for (var i = 0; i < b.children.numItems; i++) { var c = b.children[i]; if (c.type === 2) { if (c.name === n) return c; var r = findBin(c, n); if (r) return r; } } return null; }
function cnt() { return seq.videoTracks[3].clips.numItems + "/" + seq.videoTracks[4].clips.numItems + "/" + seq.videoTracks[5].clips.numItems; }
function tk(t) { var x = new Time(); x.ticks = String(t); return x; }
function mk(tr, code) { var t = seq.videoTracks[tr]; for (var i = 0; i < t.clips.numItems; i++) { var c = t.clips[i]; if (c.name.indexOf(code + " :") === 0) return c; } return null; }
function busy(tr, s, e) { var t = seq.videoTracks[tr]; for (var i = 0; i < t.clips.numItems; i++) { var c = t.clips[i]; if (c.start.seconds < e - 0.001 && c.end.seconds > s + 0.001) return c.name; } return null; }
function motion(cl) { for (var i = 0; i < cl.components.numItems; i++) if (cl.components[i].displayName === "Motion") return cl.components[i]; return null; }
function prop(m, n) { for (var i = 0; i < m.properties.numItems; i++) if (m.properties[i].displayName === n) return m.properties[i]; return null; }
'''

SCAN = PRE + r'''(function () {
  if (!seq) return "ERR no active sequence";
  var out = ["SEQ|" + seq.name + "|" + seq.frameSizeHorizontal + "|" + seq.frameSizeVertical];
  for (var tr = 3; tr <= 5; tr++) { var t = seq.videoTracks[tr];
    for (var i = 0; i < t.clips.numItems; i++) { var c = t.clips[i], m = c.name.match(/^((?:EP\d+-\d+[A-Z]?)|[AB]\d{3}) :/);
      if (m) out.push(m[1] + "|V" + (tr + 1) + "|" + c.start.ticks + "|" + c.end.ticks); } }
  return out.join("\n");
})();'''

PLACE = PRE + r'''(function () {
  if (!seq) return "ERR no active sequence";
  var m = mk(__MTR__, "__CODE__"); if (!m) return "ERR marking __CODE__ not on V__MTRN__";
  var s = m.start.seconds, e = m.end.seconds, st = Number(m.start.ticks), et = Number(m.end.ticks), dur = et - st;
  var b = busy(__TTR__, s, e); if (b) return (b === new File("__PATH__").name) ? "OK ALREADY " + b : "ERR target V__TTRN__ busy: " + b;
  var f = new File("__PATH__"); if (!f.exists) return "ERR file missing";
  var it = findItem(app.project.rootItem, f.name);
  if (!it) { app.project.importFiles([f.fsName], true, findBin(app.project.rootItem, "footage") || app.project.rootItem, false); it = findItem(app.project.rootItem, f.name); }
  if (!it) return "ERR import failed";
  var src = __SRC__, place = dur, c0 = cnt();
  if (src > 0) { var sd = Math.round(src * 254016000000); if (sd < dur) place = sd; }
  it.setInPoint("0", 4); it.setOutPoint(String(place), 4);
  var tr = seq.videoTracks[__TTR__]; tr.overwriteClip(it, tk(st));
  if (cnt() !== c0) return "ERR MARKINGS CHANGED " + c0 + " -> " + cnt() + " (stop, check master)";
  var cl = null;
  for (var i = 0; i < tr.clips.numItems; i++) if (Math.abs(tr.clips[i].start.seconds - s) < 0.01 && tr.clips[i].name === f.name) cl = tr.clips[i];
  if (!cl) return "ERR placed clip not found";
  cl.end = tk(String(st + place));
  var mo = motion(cl), sc = mo ? prop(mo, "Scale") : null; if (!sc) return "ERR no Scale prop (clip placed)";
  if (__KB__) { sc.setTimeVarying(true); sc.addKey(cl.inPoint); sc.setValueAtKey(cl.inPoint, __PCT__, true); sc.addKey(cl.outPoint); sc.setValueAtKey(cl.outPoint, __PCT__ * 1.05, true); }
  else sc.setValue(__PCT__, true);
  var after = __KB__ ? sc.getValueAtTime(cl.inPoint) + ">" + sc.getValueAtTime(cl.outPoint) : sc.getValue();
  return "OK " + cl.name + " " + cl.start.seconds.toFixed(3) + "-" + cl.end.seconds.toFixed(3) + " frames " + Math.round((cl.end.seconds - cl.start.seconds) * 24) + " scale " + after + (place < dur ? " SHORT(" + (place / TPSX).toFixed(2) + "s<" + (dur / TPSX).toFixed(2) + "s)" : "");
})();'''.replace("TPSX", str(TPS))

FLIP = PRE + r'''(function () {
  if (!seq) return "ERR no active sequence";
  var o = mk(4, "__OLD__"); if (!o) return "ERR __OLD__ not on V5";
  var s = o.start.seconds, e = o.end.seconds, st = o.start.ticks, et = o.end.ticks, nm = o.name;
  var b = busy(3, s, e); if (b) return "ERR V4 busy: " + b;
  var it = findItem(app.project.rootItem, "ADJUSTMENT ENVATO"); if (!it) return "ERR no ADJUSTMENT ENVATO item";
  var v4 = seq.videoTracks[3], c0 = cnt(), oi = it.getInPoint().ticks, oo = it.getOutPoint().ticks;
  it.setInPoint("0", 4); it.setOutPoint(String(Number(et) - Number(st)), 4);
  v4.overwriteClip(it, tk(st));
  it.setInPoint(oi, 4); it.setOutPoint(oo, 4);
  var n = null; for (var i = 0; i < v4.clips.numItems; i++) if (Math.abs(v4.clips[i].start.seconds - s) < 0.01) n = v4.clips[i];
  if (!n) return "ERR new V4 marking not found";
  n.end = tk(et); n.name = "__NEW__" + nm.substring("__OLD__".length);
  o.remove(false, false);
  var p = c0.split("/"); if (seq.videoTracks[3].clips.numItems !== Number(p[0]) + 1 || seq.videoTracks[4].clips.numItems !== Number(p[1]) - 1) return "ERR MARKINGS CHANGED " + c0 + " -> " + cnt();
  return "OK " + n.name.substring(0, 20) + " " + n.start.seconds.toFixed(3) + "-" + n.end.seconds.toFixed(3) + "|" + st + "|" + et + "|" + nm;
})();'''

UNDO_CLIP = PRE + r'''(function () {
  var t = seq.videoTracks[__TTR__], n = 0;
  for (var i = t.clips.numItems - 1; i >= 0; i--) if (t.clips[i].name === "__NAME__" && Math.abs(t.clips[i].start.ticks - __ST__) < 1000000) { t.clips[i].remove(false, false); n++; }
  return "removed " + n;
})();'''

UNDO_FLIP = PRE + r'''(function () {
  var n = mk(3, "__NEW__"); if (!n) return "ERR new marking not found";
  var it = findItem(app.project.rootItem, "ADJUSTMENT ARCHIVE"); if (!it) return "ERR no ADJUSTMENT ARCHIVE item";
  var v5 = seq.videoTracks[4], oi = it.getInPoint().ticks, oo = it.getOutPoint().ticks;
  it.setInPoint("0", 4); it.setOutPoint(String(__ET__ - __ST__), 4); v5.overwriteClip(it, tk("__ST__")); it.setInPoint(oi, 4); it.setOutPoint(oo, 4);
  var o = null; for (var i = 0; i < v5.clips.numItems; i++) if (Math.abs(v5.clips[i].start.ticks - __ST__) < 1000000) o = v5.clips[i];
  if (!o) return "ERR restore failed (V4 marking kept)";
  o.end = tk("__ET__"); o.name = "__OLDNAME__"; n.remove(false, false);
  return "restored " + o.name.substring(0, 12);
})();'''


def wait_alive(maxs=40):
    for _ in range(maxs // 2):
        r = subprocess.run([sys.executable, BRIDGE, "ping"], capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.stdout.startswith("alive"): return True
        time.sleep(2)
    return False


def bridge(code, timeout=150):
    # ponytail: no retry after `run` (placing is not idempotent); only wait for the panel BEFORE sending.
    if not wait_alive(): return "ERR: Hermes Bridge not alive - open Premiere, then Window > Extensions > Hermes Bridge"
    fd, p = tempfile.mkstemp(suffix=".jsx", dir=os.environ.get("TMPDIR"))
    os.write(fd, code.encode("utf-8")); os.close(fd)
    try:
        r = subprocess.run([sys.executable, BRIDGE, "run", p, "--timeout", str(timeout)], capture_output=True, text=True, encoding="utf-8", errors="replace")
    finally:
        os.remove(p)
    return (r.stdout + r.stderr).strip()


def fill(t, **kw):
    for k, v in kw.items():
        t = t.replace("__%s__" % k, str(v))
    return t


def scan():
    o = bridge(SCAN)
    if o.startswith("ERR") or "|" not in o:
        sys.exit("scan gagal: " + o[:300])
    L = o.splitlines(); _, name, w, h = L[0].split("|")
    mk = {}
    for l in L[1:]:
        c, tr, s, e = l.split("|"); mk[c] = (tr, int(s), int(e))
    return name, int(w), int(h), mk


# ---------- download ----------
def probe(path):
    r = subprocess.run([tool("ffprobe"), "-v", "error", "-show_streams", "-show_format", "-of", "json", path], capture_output=True, text=True)
    d = json.loads(r.stdout or "{}")
    v = next((s for s in d.get("streams", []) if s.get("codec_type") == "video" and s.get("width")), None)
    if not v:
        return None
    w, h = v["width"], v["height"]
    rot = 0
    for sd in v.get("side_data_list", []) or []:
        rot = abs(int(sd.get("rotation", 0)))
    if rot in (90, 270):
        w, h = h, w
    dur = float(d.get("format", {}).get("duration", 0) or 0)
    still = os.path.splitext(path)[1].lower() in IMG
    return dict(w=w, h=h, dur=0 if still else dur, still=still, pix=v.get("pix_fmt"), audio=any(s.get("codec_type") == "audio" for s in d["streams"]), codec=v.get("codec_name"))


def envato_dl(url, tmp, timeout=240):
    import asyncio, websockets
    async def run():
        tabs = json.load(urllib.request.urlopen(CDP + "/json/list"))
        tab = next((t for t in tabs if t["type"] == "page" and "envato.com" in t["url"]), None)
        if not tab:
            raise RuntimeError("tab Envato tidak ada di Chrome 9222")
        async with websockets.connect(tab["webSocketDebuggerUrl"], max_size=None) as ws:
            n = 0
            async def send(m, p=None):
                nonlocal n; n += 1; i = n
                await ws.send(json.dumps({"id": i, "method": m, "params": p or {}}))
                while True:
                    d = json.loads(await ws.recv())
                    if d.get("id") == i: return d.get("result", d)
            async def ev(e):
                r = await send("Runtime.evaluate", {"expression": e, "returnByValue": True})
                return r.get("result", {}).get("value")
            os.makedirs(tmp, exist_ok=True)
            await send("Browser.setDownloadBehavior", {"behavior": "allow", "downloadPath": os.path.abspath(tmp)})
            before = set(os.listdir(tmp))
            await send("Page.navigate", {"url": url})
            sel = 'button[data-cy="idp-download-button"]'
            for _ in range(30):
                await asyncio.sleep(1)
                if await ev("!!document.querySelector('%s')" % sel): break
            else:
                raise RuntimeError("tombol Download tidak muncul (login Envato? item hilang?)")
            await ev("document.querySelector('%s').click()" % sel)
            last = {}
            t0 = time.time()
            while time.time() - t0 < timeout:
                await asyncio.sleep(2)
                new = [f for f in os.listdir(tmp) if f not in before]
                done = [f for f in new if not f.endswith(".crdownload")]
                if done:
                    p = os.path.join(tmp, done[0]); s = os.path.getsize(p)
                    if last.get(p) == s: return p
                    last[p] = s
            dlg = await ev("[...document.querySelectorAll('[role=dialog],dialog,[aria-modal=true]')].filter(d=>d.offsetParent||d.open).map(d=>d.innerText.split(String.fromCharCode(10)).join(' | ').slice(0,300)).join(' // ')")
            raise RuntimeError("download timeout; dialog di Envato: %s" % (dlg or "tidak ada (cek login/lisensi/kuota)"))
    return asyncio.run(run())


def commons_dl(fid, tmp):
    title = fid if fid.startswith("File:") else "File:" + fid
    q = urllib.parse.urlencode(dict(action="query", titles=title, prop="imageinfo", iiprop="url|size|mime", iiurlwidth=3840, format="json"))
    req = urllib.request.Request("https://commons.wikimedia.org/w/api.php?" + q, headers={"User-Agent": UA})
    info = next(iter(json.load(urllib.request.urlopen(req, timeout=30))["query"]["pages"].values()))["imageinfo"][0]
    url = info.get("thumburl") or info["url"]
    ext = os.path.splitext(urllib.parse.urlparse(url).path)[1] or ".jpg"
    os.makedirs(tmp, exist_ok=True)
    p = os.path.join(tmp, "dl" + ext)
    time.sleep(2)  # Commons 429 mitigation
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=120) as r, open(p, "wb") as f:
        shutil.copyfileobj(r, f)
    return p


def normalise(src, dst_noext):
    """reject vertical video, strip audio, force yuv420p. Returns (path, probe, notes)."""
    pr = probe(src); notes = []
    if not pr:
        return None, None, ["ffprobe: tidak ada stream video/gambar"]
    ext = os.path.splitext(src)[1].lower()
    if not pr["still"]:
        if pr["h"] > pr["w"]:
            return None, pr, ["VERTIKAL %dx%d ditolak" % (pr["w"], pr["h"])]
        if pr["audio"] or pr["pix"] != "yuv420p":
            out = dst_noext + ".mp4"
            cmd = [tool("ffmpeg"), "-y", "-v", "error", "-i", src, "-an", "-pix_fmt", "yuv420p"] + (["-c:v", "copy"] if pr["pix"] == "yuv420p" and pr["codec"] == "h264" else ["-c:v", "libx264", "-crf", "16"]) + [out]
            if subprocess.run(cmd).returncode: return None, pr, ["ffmpeg gagal"]
            notes.append("remux/transcode (audio=%s pix=%s)" % (pr["audio"], pr["pix"]))
            return out, probe(out), notes
    if pr["still"] and pr["w"] < 1920: notes.append("LOWRES %dx%d" % (pr["w"], pr["h"]))
    if pr["still"] and pr["h"] > pr["w"]: notes.append("PORTRAIT: cover akan memotong, cek manual")
    out = dst_noext + ext
    shutil.move(src, out)
    return out, pr, notes


def cover(sw, sh, pw, ph):
    return round(max(sw / pw, sh / ph) * 100, 3)


# ---------- main ----------
def load_picks(d):
    P, who = {}, {}
    for f in sorted(glob.glob(os.path.join(d, "pilihan_*.json"))):
        ed = os.path.basename(f)[8:-5]
        for k, v in json.load(open(f, encoding="utf-8")).items():
            if v in (None, "", "NONE"): continue
            if k in P and P[k] != v: print("KONFLIK %s: %s (%s) vs %s (%s) -> dilewati" % (k, P[k], who[k], v, ed)); P[k] = "__CONFLICT__"; continue
            P[k], who[k] = v, ed
    return {k: v for k, v in P.items() if v != "__CONFLICT__"}, who


def footage(a):
    cf = a.catalog or os.path.join(a.picks, "full_catalog.json")  # catalog ships inside the editor's pick zip, not in the public kit
    if not os.path.isfile(cf): sys.exit("ERR: full_catalog.json tidak ada di %s. Pakai folder dari zip EP005_PILIH_FOOTAGE_<NAMA>." % a.picks)
    cat = {s["code"]: s for s in json.load(open(cf, encoding="utf-8"))}
    picks, who = load_picks(a.picks)
    seqname, W, H, mk = scan()
    print("sequence %s %dx%d, %d marking terbaca, %d pilihan" % (seqname, W, H, len(mk), len(picks)))
    nextb = max([int(c[1:]) for c in mk if re.fullmatch(r"B\d{3}", c)] + [0]) + 1
    man = json.load(open(a.manifest)) if os.path.exists(a.manifest) and not a.dry_run else {"placed": [], "flips": []}
    rep = {}
    todo = sorted((k for k in picks if k in cat), key=lambda k: mk.get(k, ("", 0, 0))[1])
    for k in picks:
        if k not in cat: rep[k] = "SKIP kode tidak ada di katalog"
    for code in todo:
        s = cat[code]; pid = picks[code]
        if s["type"] == "GRAPHIC": rep[code] = "SKIP grafis (pakai --graphics)"; continue
        opt = next((o for o in s["options"] if o["id"] == pid), None)
        if not opt: rep[code] = "ERR id pilihan tidak ada di opsi"; continue
        if code not in mk: rep[code] = "ERR marking tidak ada di timeline"; continue
        tr, st, et = mk[code]; want = "V4" if s["type"] == "ENVATO" else "V5"
        flip = tr != want
        if flip and not (tr == "V5" and want == "V4"): rep[code] = "ERR marking di %s, diharapkan %s" % (tr, want); continue
        newcode = ("B%03d" % nextb) if flip else code
        if a.dry_run:
            rep[code] = "PLAN %s%s -> V%s, %.2fs" % (s["type"], " FLIP %s->%s" % (code, newcode) if flip else "", "1" if want == "V4" else "2", (et - st) / TPS); 
            if flip: nextb += 1
            continue
        tmp = os.path.join(a.out, "_tmp_" + code)
        try:
            raw = envato_dl(opt["url"], tmp) if s["type"] == "ENVATO" else commons_dl(opt["id"], tmp)
        except Exception as ex:
            rep[code] = "ERR download: %s" % ex; continue
        sub = "ENVATO" if s["type"] == "ENVATO" else "ARCHIVE"
        os.makedirs(os.path.join(a.out, sub), exist_ok=True)
        # a re-run reuses nothing: raw is always a fresh download, final name = code
        path, pr, notes = normalise(raw, os.path.join(a.out, sub, newcode))
        shutil.rmtree(tmp, ignore_errors=True)
        if not path: rep[code] = "ERR file: " + "; ".join(notes); continue
        if flip:
            o = bridge(fill(FLIP, OLD=code, NEW=newcode))
            if not o.startswith("OK"): rep[code] = "ERR flip: " + o[:200]; continue
            _, ost, oet, onm = o.split("|", 3)
            man["flips"].append(dict(new=newcode, st=ost, et=oet, oldname=onm)); nextb += 1
            mcode, mtr = newcode, 3
        else:
            mcode, mtr = code, 3 if want == "V4" else 4
        ttr = 0 if want == "V4" else 1
        pct = cover(W, H, pr["w"], pr["h"])
        o = bridge(fill(PLACE, MTR=mtr, MTRN=mtr + 1, TTR=ttr, TTRN=ttr + 1, CODE=mcode, PATH=path.replace("\\", "/"), SRC=pr["dur"], PCT=pct, KB="true" if pr["still"] else "false"))
        if o.startswith("OK"):
            if "ALREADY" not in o: man["placed"].append(dict(track=ttr, name=os.path.basename(path), st=mk[code][1]))
            rep[code] = ("WARN " if ("SHORT" in o or notes) else "") + o + (" | " + "; ".join(notes) if notes else "")
        else:
            rep[code] = "ERR place: " + o[:200] + " (file ada di " + path + ")"
        json.dump(man, open(a.manifest, "w"), indent=1)
    return rep


def graphics(a):
    seqname, W, H, mk = scan()
    rep, man = {}, json.load(open(a.manifest)) if os.path.exists(a.manifest) and not a.dry_run else {"placed": [], "flips": []}
    for f in sorted(glob.glob(os.path.join(a.graphics, "*"))):
        m = re.match(r"(EP\d+-\d+[A-Z]?)(?![0-9A-Z])", os.path.basename(f))
        if not m or os.path.splitext(f)[1].lower() not in (".mp4", ".mov", ".png"): continue
        code = m.group(1)
        if code not in mk or mk[code][0] != "V6": rep[code] = "ERR tidak ada marking V6 dengan kode ini"; continue
        pr = probe(f)
        if not pr: rep[code] = "ERR ffprobe"; continue
        _, st, et = mk[code]
        if a.dry_run: rep[code] = "PLAN V3 %.2fs file %dx%d %.2fs" % ((et - st) / TPS, pr["w"], pr["h"], pr["dur"]); continue
        pct = 100 if (pr["w"], pr["h"]) == (W, H) else cover(W, H, pr["w"], pr["h"])
        o = bridge(fill(PLACE, MTR=5, MTRN=6, TTR=2, TTRN=3, CODE=code, PATH=f.replace("\\", "/"), SRC=pr["dur"], PCT=pct, KB="false"))
        rep[code] = o[:240]
        if o.startswith("OK ") and "ALREADY" not in o: man["placed"].append(dict(track=2, name=os.path.basename(f), st=st))
        json.dump(man, open(a.manifest, "w"), indent=1)
    return rep


def undo(a):
    man = json.load(open(a.manifest)); out = []
    for p in man["placed"]:
        out.append(bridge(fill(UNDO_CLIP, TTR=p["track"], NAME=p["name"], ST=p["st"])))
    for fl in man["flips"]:
        out.append(bridge(fill(UNDO_FLIP, NEW=fl["new"], ST=fl["st"], ET=fl["et"], OLDNAME=fl["oldname"].replace('"', '\\"'))))
    os.rename(a.manifest, a.manifest + ".undone")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--picks"); ap.add_argument("--graphics"); ap.add_argument("--undo", action="store_true"); ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--catalog"); ap.add_argument("--out", default=os.path.join(os.getcwd(), "FOOTAGE"))
    ap.add_argument("--manifest", default=os.path.join(os.getcwd(), "ingest_manifest.json"))
    a = ap.parse_args()
    for k in ("picks", "graphics", "catalog", "out", "manifest"):
        if getattr(a, k): setattr(a, k, wp(getattr(a, k)))
    if a.undo: res = undo(a)
    elif a.graphics: res = graphics(a)
    elif a.picks: res = footage(a)
    else: sys.exit(__doc__)
    json.dump(res, open(os.path.join(os.getcwd(), "ingest_report.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    for k, v in (res.items() if isinstance(res, dict) else enumerate(res)): print(k, "->", v)
