

**English** | [中文文档](README.zh-CN.md)

# video-agent-skills

> video-agent-skills is a multi-agent team of Claude Code skills that turns a video topic into a DaVinci/CapCut-ready timeline — from research to publish.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Skills: 11](https://img.shields.io/badge/Skills-11-blue.svg)](.)
[![Platform: Claude Code](https://img.shields.io/badge/Platform-Claude%20Code-blueviolet.svg)](https://claude.ai/code)

## Why

Creating a structured knowledge video from scratch requires juggling research, scriptwriting, storyboarding, voice-over, image generation, timeline assembly, and platform metadata — across many tools with no shared context.

video-agent-skills wires up 11 specialized Claude Code skills into a coordinated pipeline. Each skill owns a single role; the producer orchestrates the whole sequence, with human-review checkpoints so you stay in control at every critical decision.

The pipeline outputs a DaVinci Resolve project or a CapCut/JianYing draft — your choice — ready to render.

## Features

### Pipeline skills (10 skills — run in sequence)

| Skill | Role | Key output |
|-------|------|-----------|
| `video-agent-producer` | Director / orchestrator. Accepts a topic, breaks it into sub-tasks, dispatches all other agents in order, manages 4 human checkpoints and checkpoint recovery. | `project.json` + final deliverable package |
| `video-agent-operator` | Analytics strategist. Reads Douyin account CSV/Excel exports (up to 3 accounts: growth, AI, vlog), identifies high-performing content patterns, and suggests topics. | Analytics report + topic recommendations |
| `video-agent-researcher` | Research lead. Two modes: **search mode** (web articles + YouTube transcripts → structured outline) and **organize mode** (user-supplied material → narrative-restructured outline). | `outline.md` + `materials/sources.json` |
| `video-agent-writer` | Screenwriter. Turns the outline into a word-for-word narration script. Supports 3 opening patterns (counter-intuitive / story / question), 280 chars/min pacing, and citation tagging for downstream agents. | `script.md` |
| `video-agent-storyboarder` | Storyboard designer. Calls `generate_storyboard.py` which sends the script to **Gemini Flash** (`gemini-2.5-flash`) and returns a shot-by-shot storyboard with visual descriptions, asset type, and mood per shot. | `storyboard.json` + `storyboard.md` |
| `video-agent-voice` | Voice producer. Converts the script to audio and subtitles. Supports **MiniMax Speech-02** (Chinese, recommended), Edge-TTS (free draft), ElevenLabs (English), and manual recording mode. Reads storyboard mood annotations for emotion control. | `audio/voiceover.mp3` + `audio/subtitles.srt` |
| `video-agent-visual` | Art director. Reads `storyboard.json` and calls `generate_images.py` to batch-generate images via **Gemini Image API** (Nano Banana). Skips shots flagged as post-production. Supports style presets (default / tech / knowledge). | `visuals/*.png` + `visual-timeline.json` |
| `video-agent-editor` | DaVinci editor. Imports all assets into **DaVinci Resolve Studio** via the Python API. Builds a multi-track timeline (V1 visuals, V2 text effects, V3 data effects, A1 voice-over, A2 BGM placeholder, subtitle track). Generates placeholder clips for post-production shots. | DaVinci Resolve project + `editor-report.md` |
| `video-agent-jianying-editor` | CapCut/JianYing editor. Shares the exact same inputs as the DaVinci editor but outputs a **JianYing draft folder** via **VectCutAPI**. The producer dispatches one or both editors via the `output_target` parameter. | `jianying-draft/` + `jianying-editor-report.md` |
| `video-agent-publisher` | Publishing coordinator. Generates platform-specific metadata (title candidates, description, hashtags, BGM suggestions, citation list) for Douyin, Bilibili, and YouTube. | `publish/metadata.json` + `publish/sources.md` |

### Independent skill (1 skill — standalone branch)

| Skill | Role | Key output |
|-------|------|-----------|
| `live-sharing-writer` | Live / presentation scriptwriter. For livestreams, talks, or recorded speeches — not videos. Works by interviewing the presenter (no external research), extracts personal stories and viewpoints, and writes a spoken-word script with interaction cues and pacing markers. | `script.md` (conversational, speaker-ready) |

> **Why is `live-sharing-writer` separate?**
> The video pipeline (researcher → writer → storyboarder → …) assumes external research and visual production. Live sharing is presenter-first: all material comes from the speaker, no storyboard or image generation is needed. The two branches share a script format but nothing else.

## Install

These are bare Claude Code skills — plain directories, each containing a `SKILL.md` that Claude Code reads as agent instructions.

**Option A — Copy manually**

Copy each skill directory into your Claude Code skills folder (the path depends on how you configured Claude Code; typically `~/.claude/skills/` or a project-level `.claude/skills/`):

```bash
cp -r /path/to/video-agent-skills/video-agent-producer ~/.claude/skills/
cp -r /path/to/video-agent-skills/video-agent-researcher ~/.claude/skills/
# … repeat for each skill you need
```

**Option B — Clone the repo next to your project and add to your CLAUDE.md**

```bash
git clone https://github.com/chenyuxiaojin/video-agent-skills.git
```

Then in your project's `CLAUDE.md` (or `~/.claude/CLAUDE.md`) reference the cloned path so Claude Code can find the skills.

**No marketplace.json or plugin registry** — this repo ships raw skill directories intentionally. Install only what you need.

## Usage

Start the full pipeline by telling Claude Code:

```
开始制作视频 — 主题：[your topic]
```

Or trigger individual skills directly:

```
# Topic research only
搜索关于 [主题] 的素材

# Analytics + topic suggestion
分析数据，下期做什么选题

# Live sharing script (independent)
帮我准备一个直播分享稿
```

The producer skill (`video-agent-producer`) orchestrates all pipeline steps and pauses at 4 checkpoints for your review before proceeding.

## Compared to alternatives

| | video-agent-skills | [xiaochen-skills](https://github.com/chenyuxiaojin/xiaochen-skills) (cyxj-ai-weekly-news) | faceless-video / auto-shorts generators | Anthropic official agent-skills examples |
|---|---|---|---|---|
| Primary use | Long-form knowledge video (6–15 min), full pipeline from research to timeline | AI weekly news digest → Douyin short clip (topic discovery + script only, no full pipeline) | Fully automated faceless short videos, minimal human control | Reference implementations for agent patterns, not production-ready |
| Human checkpoints | 4 explicit review gates | None (automated) | None | N/A |
| Editor target | DaVinci Resolve Studio **or** CapCut/JianYing (your choice) | Not included | Platform-specific auto-upload | Not included |
| AI dependencies | Gemini Flash (storyboard) + Gemini Image (visuals) + MiniMax/Edge-TTS/ElevenLabs (voice) | Grok search + Claude | Varies by tool | Varies |
| Overlap note | — | `cyxj-ai-weekly-news` covers AI topic discovery for short clips; video-agent-skills handles the full production chain for longer content | Different audience and length target | — |

## FAQ

**How many skills are there?**
11 total: 10 pipeline skills (producer → operator → researcher → writer → storyboarder → voice → visual → editor → jianying-editor → publisher) plus 1 independent skill (live-sharing-writer).

**Do I have to use DaVinci Resolve?**
No. The default is DaVinci (`output_target: "resolve"`). You can use CapCut/JianYing instead — just tell the producer `output_target: "jianying"`. You can also generate both (`output_target: "both"`). The DaVinci path requires DaVinci Resolve Studio to be running; the JianYing path requires VectCutAPI running locally.

**How do I install these skills?**
Copy the skill directories you need into your Claude Code skills folder (see [Install](#install) above). There is no package manager step.

**What APIs do I need?**
| API | Used by | Required? |
|-----|---------|-----------|
| Gemini Flash (`gemini-2.5-flash`) | storyboarder (via `generate_storyboard.py`) | Yes for storyboard generation |
| Gemini Image API | visual (via `generate_images.py`) | Yes for AI image generation |
| MiniMax Speech-02 | voice (Chinese TTS, recommended) | No — Edge-TTS is free alternative |
| ElevenLabs | voice (English TTS) | No — only for English projects |
| Edge-TTS | voice (free draft) | No — bundled, no key needed |
| VectCutAPI (local) | jianying-editor | Only if using CapCut/JianYing output |
| DaVinci Resolve Studio Python API | editor | Only if using DaVinci output |
| Web search / YouTube transcripts | researcher | Requires Claude Code web tools |

**Can I run a single skill without the full pipeline?**
Yes. Every skill can be triggered independently with a natural-language phrase (see each skill's trigger conditions in its `SKILL.md`). The producer is optional — it just automates the hand-offs.

## License

[MIT](LICENSE) © 2026 chenyuxiaojin
