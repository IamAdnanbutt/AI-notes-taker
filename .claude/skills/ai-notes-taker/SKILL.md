---
name: ai-notes-taker
description: Note-taking agent for ICT (Inner Circle Trader) trading education. Input a YouTube URL or PDF path; output one structured Markdown study document with annotated screenshots, timestamp/page links, and a master summary. Use on "notes: <url|pdf>", "batch: <urls.txt>", "resume", or when the user shares a YouTube URL asking for ICT/video notes.
---

# AI Notes Taker

The full agent specification lives in `CLAUDE.md` at the repository root —
ROLE, COMMANDS, GROUND RULES, VIDEO PIPELINE, PDF PIPELINE, CONTEXT
DISCIPLINE, and QUALITY BAR. Follow it exactly; it is the single source of
truth. Cavemen mode applies: keep chat replies terse, spend tokens on the
notes document.

Supporting material in this folder:

- `references/concept-detection.md` — ICT keyword list for flagging moments
- `references/annotation-legend.md` — color code for `annotate: full` drawn
  boxes
- `references/note-template.md` — long-form note block variant + worked
  example
- `scripts/ict_video.py` — info / transcript / frames helpers (alternative
  to the raw yt-dlp/ffmpeg commands in CLAUDE.md)
- `scripts/annotate.py` — Pillow box/arrow/label drawing for `annotate: full`

`ai_notes_taker.py` at the repo root runs the mechanical part (metadata,
transcript, keyword flagging, frame extraction, scaffold) in one command —
prefer it to keep token use low, then apply CLAUDE.md Steps 4–7 (select and
caption frames, write notes incrementally, summary header, pandoc HTML,
cleanup, library index).
