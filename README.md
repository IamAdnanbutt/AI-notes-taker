# AI Notes Taker

An agentic AI note-taking toolkit for YouTube trading videos, built as a
[Claude Code skill](https://code.claude.com/docs/en/skills).

## Cavemen — YouTube ICT Video Note-Taker

The `cavemen` skill (`.claude/skills/cavemen/`) turns Claude Code into an
autonomous ICT (Inner Circle Trader) video study agent. Give it a YouTube
link and it:

1. Extracts the video metadata and full transcript with timestamps
2. Flags every key teaching moment (chart examples, trade setups,
   ICT concepts, presenter cues)
3. Captures the exact video frame at each flagged timestamp
4. Annotates each screenshot with ICT labels — FVGs, Order Blocks,
   liquidity sweeps, MSS, PO3, Kill Zones, entry/SL/TP levels
5. Writes a structured note block under each screenshot (model, concept,
   timeframe, session, playbook rule, trade setup, key lesson)
6. Exports a formatted study document with a master summary, table of
   contents, and clickable timestamp links

### Usage

In Claude Code, from this repository:

```
Make notes for this video: https://www.youtube.com/watch?v=...
```

or invoke the skill directly with `/cavemen`.

### Requirements

- `yt-dlp` — video, metadata, and caption download
- `ffmpeg` — frame extraction
- Python 3 with `Pillow` — screenshot annotation

```bash
pip install yt-dlp Pillow
```

### Layout

```
.claude/skills/cavemen/
├── SKILL.md                        # the agent workflow
├── references/
│   ├── concept-detection.md        # ICT concepts that trigger a screenshot
│   ├── annotation-legend.md        # mandatory annotation color code
│   └── note-template.md            # note block structure + worked example
└── scripts/
    ├── ict_video.py                # info / transcript / frames helpers
    └── annotate.py                 # draws ICT labels on screenshots
```

Generated study documents land in `notes/<video-slug>/NOTES.md` with
annotated screenshots in `notes/<video-slug>/screenshots/`.
