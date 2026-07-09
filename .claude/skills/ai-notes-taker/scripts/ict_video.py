#!/usr/bin/env python3
"""YouTube helpers for the cavemen skill.

Subcommands:
  info <url>
      Print video title, channel, duration, and upload date as JSON.
  transcript <url> [--lang en]
      Print the caption track (manual if available, else auto-generated)
      as tab-separated lines: HH:MM:SS<TAB>text
  frames <url> --out DIR --at HH:MM:SS [--at HH:MM:SS ...] [--height 1080]
      Download the video once and extract one PNG frame per timestamp
      into DIR as frame_HH-MM-SS.png.

Requires yt-dlp and ffmpeg on PATH.
"""

import argparse
import glob
import json
import os
import re
import subprocess
import sys


def run(cmd, **kwargs):
    result = subprocess.run(cmd, capture_output=True, text=True, **kwargs)
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        raise SystemExit(f"command failed: {' '.join(cmd)}")
    return result.stdout


def cmd_info(args):
    out = run(["yt-dlp", "--skip-download", "--dump-single-json", args.url])
    meta = json.loads(out)
    duration = int(meta.get("duration") or 0)
    print(json.dumps({
        "id": meta.get("id"),
        "title": meta.get("title"),
        "channel": meta.get("channel") or meta.get("uploader"),
        "duration_seconds": duration,
        "duration": f"{duration // 3600:02d}:{duration % 3600 // 60:02d}:{duration % 60:02d}",
        "upload_date": meta.get("upload_date"),
        "url": meta.get("webpage_url") or args.url,
    }, indent=2))


TS_LINE = re.compile(r"^(?:(\d{1,2}):)?(\d{1,2}):(\d{2})\.\d{3}\s+-->")
TAG = re.compile(r"<[^>]+>")


def cmd_transcript(args):
    workdir = args.workdir or "."
    os.makedirs(workdir, exist_ok=True)
    template = os.path.join(workdir, "captions.%(ext)s")
    run([
        "yt-dlp", "--skip-download",
        "--write-subs", "--write-auto-subs",
        "--sub-langs", f"{args.lang}.*,{args.lang}",
        "--sub-format", "vtt",
        "-o", template,
        args.url,
    ])
    vtt_files = sorted(glob.glob(os.path.join(workdir, "captions.*.vtt")))
    if not vtt_files:
        raise SystemExit("no caption track found (tried manual and auto subs)")

    last_text = None
    with open(vtt_files[0], encoding="utf-8") as fh:
        timestamp = None
        for raw in fh:
            line = raw.strip()
            match = TS_LINE.match(line)
            if match:
                hours = int(match.group(1) or 0)
                timestamp = f"{hours:02d}:{int(match.group(2)):02d}:{match.group(3)}"
                continue
            if not line or line in ("WEBVTT",) or line.startswith(("Kind:", "Language:", "NOTE")):
                continue
            if timestamp is None:
                continue
            text = TAG.sub("", line).strip()
            # Auto-generated captions repeat the previous line as it scrolls.
            if text and text != last_text:
                print(f"{timestamp}\t{text}")
                last_text = text
    for path in vtt_files:
        os.remove(path)


def parse_timestamp(value):
    parts = value.split(":")
    if len(parts) == 2:
        parts.insert(0, "0")
    if len(parts) != 3:
        raise SystemExit(f"bad timestamp {value!r}, expected HH:MM:SS or MM:SS")
    hours, minutes, seconds = (int(p) for p in parts)
    return hours * 3600 + minutes * 60 + seconds


def cmd_frames(args):
    os.makedirs(args.out, exist_ok=True)
    video_path = os.path.join(args.out, ".source_video.mp4")
    if not os.path.exists(video_path):
        run([
            "yt-dlp",
            "-f", f"bv*[height<=?{args.height}]/b[height<=?{args.height}]/b",
            "--remux-video", "mp4",
            "-o", video_path,
            args.url,
        ])
    for value in args.at:
        seconds = parse_timestamp(value)
        stamp = f"{seconds // 3600:02d}-{seconds % 3600 // 60:02d}-{seconds % 60:02d}"
        target = os.path.join(args.out, f"frame_{stamp}.png")
        run([
            "ffmpeg", "-y", "-ss", str(seconds), "-i", video_path,
            "-frames:v", "1", target,
        ])
        print(target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_info = sub.add_parser("info")
    p_info.add_argument("url")
    p_info.set_defaults(func=cmd_info)

    p_tr = sub.add_parser("transcript")
    p_tr.add_argument("url")
    p_tr.add_argument("--lang", default="en")
    p_tr.add_argument("--workdir", default=None)
    p_tr.set_defaults(func=cmd_transcript)

    p_fr = sub.add_parser("frames")
    p_fr.add_argument("url")
    p_fr.add_argument("--out", required=True)
    p_fr.add_argument("--at", action="append", required=True,
                      help="timestamp HH:MM:SS or MM:SS (repeatable)")
    p_fr.add_argument("--height", type=int, default=1080)
    p_fr.set_defaults(func=cmd_frames)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
