# AI Notes Taker

Agentic AI note-taker for YouTube ICT (Inner Circle Trader) videos.
Give it a link — it extracts the transcript, flags every key teaching
moment, captures and annotates chart screenshots, and builds a structured
study document.

The agent specification lives in [`CLAUDE.md`](CLAUDE.md) — Claude Code
loads it automatically in this folder. Commands: `notes: <url|pdf>`,
`batch: <urls.txt>`, `resume`, `annotate: full`. It handles PDFs as well
as videos, keeps per-job `state.json` for resumability, and exports
`notes.md` + self-contained `notes.html` (pandoc). Optionally add your
`PLAYBOOK.md` for model tagging.

Ships two ways to run it:

## 1. One-command pipeline (token-cheap "cavemen mode")

```bash
pip install yt-dlp Pillow   # plus ffmpeg on PATH
python3 ai_notes_taker.py "https://www.youtube.com/watch?v=..."
```

Mechanically does the heavy lifting without burning AI tokens:

1. Fetches metadata + full transcript with timestamps
2. Auto-flags every ICT keyword moment (FVG, OB, sweeps, MSS, PO3,
   Kill Zones, entries/SL/TP, presenter cues...)
3. Extracts a video frame per flagged moment
4. Writes `notes/<video-slug>/NOTES.md` — a scaffold with a prefilled
   note block and clickable timestamp link under every screenshot

Then annotate the screenshots and fill the TODO analysis fields —
yourself, or with the skill below.

## 2. Claude Code skill (`ai-notes-taker`)

`.claude/skills/ai-notes-taker/` turns Claude Code into the full
autonomous study agent from the master prompt. In this repo say:

```
Make notes for this video: https://www.youtube.com/watch?v=...
```

Claude runs the pipeline, reviews each frame, draws the color-coded ICT
annotations (`scripts/annotate.py`), completes every note block, and adds
the master summary (top 5 lessons, model mapping, study score).

### Layout

```
ai_notes_taker.py                   # one-command pipeline
.claude/skills/ai-notes-taker/
├── SKILL.md                        # agent workflow
├── references/
│   ├── concept-detection.md        # ICT concepts that trigger a screenshot
│   ├── annotation-legend.md        # annotation color code
│   └── note-template.md            # note block structure + example
└── scripts/
    ├── ict_video.py                # info / transcript / frames helpers
    └── annotate.py                 # draws ICT labels on screenshots
notes/<video-slug>/                 # generated: NOTES.md + screenshots/
```
