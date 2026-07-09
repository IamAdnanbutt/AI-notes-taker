#!/usr/bin/env python3
"""AI Notes Taker — YouTube ICT video -> study-notes scaffold.

One command does the token-cheap part of the pipeline mechanically:
fetch metadata + transcript, auto-flag every ICT teaching moment by
keyword, extract a frame per flagged moment, and write a NOTES.md
scaffold with a prefilled note block under each screenshot. Claude (or
you) then annotates the screenshots and completes the analysis fields.

Usage:
  python3 ai_notes_taker.py <youtube-url> [--out notes] [--gap 30] [--height 1080]

Requires: yt-dlp, ffmpeg (see .claude/skills/ai-notes-taker/scripts/).
"""

import argparse
import json
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.abspath(__file__))
ICT_VIDEO = os.path.join(REPO, ".claude/skills/ai-notes-taker/scripts/ict_video.py")

# Keyword -> canonical concept, from references/concept-detection.md
CONCEPTS = {
    r"fair value gap|fvg|ifvg|inversion": "FVG",
    r"breaker": "Breaker Block",
    r"order block": "Order Block",
    r"mitigation": "Mitigation Block",
    r"balanced price range|bpr": "BPR",
    r"rejection block": "Rejection Block",
    r"propulsion": "Propulsion Block",
    r"vacuum|void": "Vacuum / Void",
    r"buy.?side|bsl": "BSL",
    r"sell.?side|ssl": "SSL",
    r"liquidity|sweep|swept|raid": "Liquidity Sweep",
    r"equal highs|equal lows": "Equal Highs/Lows",
    r"previous day (high|low)": "Previous Day High/Low",
    r"market structure|mss": "MSS",
    r"change of character|choch": "CHoCH",
    r"premium|discount|equilibrium": "Premium/Discount",
    r"optimal trade entry|\bote\b": "OTE",
    r"silver bullet": "Silver Bullet",
    r"kill.?zone": "Kill Zone",
    r"asian (range|session)|asia session": "Asian Range",
    r"power of (3|three)|po3": "PO3",
    r"accumulation|manipulation|distribution": "PO3 (AMD)",
    r"midnight open|true day open": "Midnight/True Day Open",
    r"entry|trigger": "Entry",
    r"stop.?loss": "Stop Loss",
    r"take.?profit|target": "Target",
    r"partial|scale out": "Partial Close",
    r"\bdol\b|objective level": "DOL",
    r"\badr\b|daily range": "ADR",
    r"risk.?reward|\brr\b": "Risk:Reward",
    r"backtest": "Backtest Example",
    r"look at this|here you can see|notice|this is important": "Presenter Cue",
}
PATTERNS = [(re.compile(pat, re.I), name) for pat, name in CONCEPTS.items()]


def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        raise SystemExit(f"command failed: {' '.join(cmd)}")
    return result.stdout


def hms_to_seconds(hms):
    hours, minutes, seconds = (int(p) for p in hms.split(":"))
    return hours * 3600 + minutes * 60 + seconds


def seconds_to_hms(total):
    return f"{total // 3600:02d}:{total % 3600 // 60:02d}:{total % 60:02d}"


def slugify(title):
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug[:60] or "video"


def flag_moments(transcript_lines, gap):
    """Group keyword hits within `gap` seconds into one flagged moment."""
    moments = []
    for line in transcript_lines:
        if "\t" not in line:
            continue
        stamp, text = line.split("\t", 1)
        hits = {name for pattern, name in PATTERNS if pattern.search(text)}
        if not hits:
            continue
        seconds = hms_to_seconds(stamp)
        if moments and seconds - moments[-1]["seconds"] <= gap:
            moments[-1]["concepts"] |= hits
            moments[-1]["text"] += " " + text
        else:
            moments.append({"seconds": seconds, "concepts": hits, "text": text})
    return moments


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("--out", default=os.path.join(REPO, "notes"))
    parser.add_argument("--gap", type=int, default=30,
                        help="merge keyword hits within N seconds (default 30)")
    parser.add_argument("--height", type=int, default=1080)
    args = parser.parse_args()

    print("[1/4] metadata...")
    info = json.loads(run([sys.executable, ICT_VIDEO, "info", args.url]))
    slug = slugify(info["title"])
    workdir = os.path.join(args.out, slug)
    shots = os.path.join(workdir, "screenshots")
    os.makedirs(shots, exist_ok=True)

    print("[2/4] transcript...")
    transcript = run([sys.executable, ICT_VIDEO, "transcript", args.url,
                      "--workdir", workdir])
    with open(os.path.join(workdir, "transcript.tsv"), "w", encoding="utf-8") as fh:
        fh.write(transcript)

    moments = flag_moments(transcript.splitlines(), args.gap)
    print(f"[3/4] {len(moments)} moments flagged, extracting frames...")
    if moments:
        cmd = [sys.executable, ICT_VIDEO, "frames", args.url, "--out", shots,
               "--height", str(args.height)]
        for moment in moments:
            cmd += ["--at", seconds_to_hms(moment["seconds"])]
        run(cmd)

    print("[4/4] writing NOTES.md scaffold...")
    url = info.get("url", args.url)
    sep = "&" if "?" in url else "?"
    concepts_all = sorted({c for m in moments for c in m["concepts"]})
    lines = [
        f"# {info['title']}",
        "",
        "## Summary",
        "",
        f"- **Channel:** {info.get('channel')}",
        f"- **Duration:** {info.get('duration')}",
        f"- **Uploaded:** {info.get('upload_date')}",
        f"- **Source:** {url}",
        f"- **Screenshots captured:** {len(moments)}",
        f"- **ICT concepts covered:** {', '.join(concepts_all) or 'TODO'}",
        "- **Top 5 key lessons:** TODO",
        "- **Most relevant of the 7 ICT models:** TODO",
        "- **Study score (1-10):** TODO",
        "",
        "## Notes",
        "",
    ]
    for index, moment in enumerate(moments, 1):
        stamp = seconds_to_hms(moment["seconds"])
        fname = f"frame_{stamp.replace(':', '-')}.png"
        lines += [
            f"### Screenshot {index} — [{stamp}]({url}{sep}t={moment['seconds']})",
            "",
            f"![{stamp}](screenshots/{fname})",
            "",
            "```",
            f"TIMESTAMP: {stamp} | LINK: {url}{sep}t={moment['seconds']}",
            "ICT MODEL: TODO (which of the 7 models)",
            f"CONCEPT: {', '.join(sorted(moment['concepts']))}",
            "TIMEFRAME: TODO | INSTRUMENT: TODO | SESSION: TODO",
            "",
            "WHAT IS HAPPENING:",
            f"TODO — transcript: \"{moment['text'][:300]}\"",
            "",
            "ICT PLAYBOOK RULE APPLIED:",
            "TODO",
            "",
            "TRADE SETUP (if applicable):",
            "- Bias / Entry / SL / Target / RR: TODO",
            "",
            "KEY LESSON:",
            "TODO",
            "```",
            "",
        ]
    notes_path = os.path.join(workdir, "NOTES.md")
    with open(notes_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print(f"done: {notes_path}")
    print(f"screenshots: {shots}")
    print("next: annotate screenshots (scripts/annotate.py) and fill the TODOs")


if __name__ == "__main__":
    main()
