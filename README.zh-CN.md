[**English**](README.md) | 中文

# video-agent-skills

> video-agent-skills 是一套 Claude Code 多 Agent 技能组，把一个视频选题变成达芬奇 / 剪映可直接导入的时间轴——从调研到发布，一条流水线。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Skills: 11](https://img.shields.io/badge/Skills-11-blue.svg)](.)
[![Platform: Claude Code](https://img.shields.io/badge/Platform-Claude%20Code-blueviolet.svg)](https://claude.ai/code)

## 为什么做这个

制作一条有体系的知识类视频，需要同时处理：调研、写稿、分镜、配音、图片生成、时间轴组装、平台元数据——跨多个工具、彼此缺乏上下文共享。

video-agent-skills 把 11 个专职 Claude Code 技能串成一条协作流水线。每个技能只负责一件事，由制片人统一调度，并在关键节点设置人工审核检查点，确保你始终掌握最终决策权。

最终产出达芬奇 Resolve 项目或剪映草稿——两种目标自选——直接渲染导出。

## 功能

### 流水线技能（10 个技能，顺序执行）

| 技能 | 角色 | 关键产出 |
|------|------|---------|
| `video-agent-producer` | 制片人 / 总调度。接收选题，拆解子任务，按顺序调度所有其他 Agent，管理 4 个人工检查点和断点恢复。 | `project.json` + 完整项目包 |
| `video-agent-operator` | 运营分析师。读取抖音账号 CSV/Excel 导出数据（最多 3 个账号：认知成长 / AI 博主 / Vlog），识别高表现内容特征，给出选题建议。 | 分析报告 + 选题建议 |
| `video-agent-researcher` | 调研员。两种模式：**搜索模式**（网页文章 + YouTube 字幕 → 结构化大纲）和**整理模式**（用户已有素材 → 按视频叙事逻辑重组的详细整理稿）。 | `outline.md` + `materials/sources.json` |
| `video-agent-writer` | 编剧。将大纲展开为逐字稿。支持反常识 / 故事 / 问题 3 种开头模式，280 字/分钟节奏控制，出处标注（供下游 Agent 使用）。 | `script.md` |
| `video-agent-storyboarder` | 分镜师。调用 `generate_storyboard.py`，通过 **Gemini Flash**（`gemini-2.5-flash`）批量生成逐句分镜——每个镜头含画面说明、素材类型、情绪标注。 | `storyboard.json` + `storyboard.md` |
| `video-agent-voice` | 配音师。将逐字稿转为音频和字幕。支持 **MiniMax Speech-02**（中文首选，全球 #1，WER 2.25%）、Edge-TTS（免费草稿）、ElevenLabs（英文）、自录音四种模式。读取分镜情绪标注做情感控制。 | `audio/voiceover.mp3` + `audio/subtitles.srt` |
| `video-agent-visual` | 美术师。读取 `storyboard.json`，调用 `generate_images.py` 通过 **Gemini Image API**（Nano Banana）批量并发生成图片。自动跳过后期制作标记的镜头。支持默认 / 科技 / 知识 三种风格预设。 | `visuals/*.png` + `visual-timeline.json` |
| `video-agent-editor` | 达芬奇剪辑师。通过 **DaVinci Resolve Studio Python API** 直连达芬奇，导入所有素材，构建多轨时间轴（V1 视觉、V2 文字动效、V3 数据动效、A1 配音、A2 BGM 预留、字幕轨），并为后期制作镜头生成占位素材。 | 达芬奇 Resolve 项目 + `editor-report.md` |
| `video-agent-jianying-editor` | 剪映剪辑师。与达芬奇剪辑师共享完全相同的输入文件，通过 **VectCutAPI** 生成剪映草稿文件夹。制片人通过 `output_target` 参数决定调哪个剪辑师（或两个都调）。 | `jianying-draft/` + `jianying-editor-report.md` |
| `video-agent-publisher` | 发布员。为抖音 / B 站 / YouTube 生成各平台发布元数据（标题候选、描述、标签、BGM 推荐、引用出处列表）。 | `publish/metadata.json` + `publish/sources.md` |

### 独立分支技能（1 个技能，独立使用）

| 技能 | 角色 | 关键产出 |
|------|------|---------|
| `live-sharing-writer` | 直播分享撰稿人。用于直播、演讲或录制分享——不是视频流水线。以对话方式挖掘演讲者本人的经历和观点（不查外部资料），写出口语化逐字稿，含互动点和节奏休息标记。 | `script.md`（口语感，可直接上台说） |

> **为什么 `live-sharing-writer` 是独立分支？**
> 视频流水线（调研 → 编剧 → 分镜 → …）预设需要外部调研和视觉制作。直播分享以演讲者为核心：素材全来自演讲者本人，不需要分镜或图片生成。两条分支共用逐字稿格式，但流程完全不同。

## 安装

这是裸 Claude Code 技能集合——每个技能都是一个普通目录，包含一个 `SKILL.md`，Claude Code 读取后作为 Agent 指令运行。

**方式 A — 手动复制**

把你需要的技能目录复制到 Claude Code 的 skills 文件夹（路径取决于你的配置，通常是 `~/.claude/skills/` 或项目级的 `.claude/skills/`）：

```bash
cp -r /path/to/video-agent-skills/video-agent-producer ~/.claude/skills/
cp -r /path/to/video-agent-skills/video-agent-researcher ~/.claude/skills/
# … 按需重复
```

**方式 B — 克隆仓库，在 CLAUDE.md 里引用路径**

```bash
git clone https://github.com/chenyuxiaojin/video-agent-skills.git
```

然后在你的项目 `CLAUDE.md`（或 `~/.claude/CLAUDE.md`）里告诉 Claude Code 在哪里找这些技能。

**没有 marketplace.json 或插件注册表** — 本仓库故意以原始目录形式发布，按需安装即可。

## 使用方式

对 Claude Code 说一句话启动完整流水线：

```
开始制作视频 — 主题：[你的选题]
```

也可以单独触发某个技能：

```
# 只做调研
搜索关于 [主题] 的素材

# 运营分析 + 选题建议
分析数据，下期做什么选题

# 直播分享稿（独立技能）
帮我准备一个直播分享稿
```

制片人技能（`video-agent-producer`）会协调所有流水线步骤，并在 4 个检查点暂停等你确认后再继续。

## 与同类工具对比

| | video-agent-skills | [xiaochen-skills](https://github.com/chenyuxiaojin/xiaochen-skills)（cyxj-ai-weekly-news） | faceless-video / auto-shorts 类生成器 | Anthropic 官方 agent-skills 示例 |
|---|---|---|---|---|
| 主要用途 | 长视频知识内容（6-15 分钟），从调研到时间轴的完整流水线 | AI 周报摘要 → 抖音短视频（只有选题发现 + 写稿，无完整流水线） | 全自动无脸短视频，人工干预极少 | Agent 模式参考实现，不面向生产使用 |
| 人工检查点 | 4 个明确审核节点 | 无（全自动） | 无 | 不适用 |
| 剪辑目标 | 达芬奇 Resolve Studio **或** 剪映 / CapCut（自选） | 不包含 | 平台自动上传 | 不包含 |
| AI 依赖 | Gemini Flash（分镜）+ Gemini Image（视觉素材）+ MiniMax/Edge-TTS/ElevenLabs（配音） | Grok 搜索 + Claude | 因工具而异 | 因工具而异 |
| 重叠说明 | — | `cyxj-ai-weekly-news` 针对 AI 短视频的选题发现；video-agent-skills 处理长内容的完整制作链 | 面向不同受众和时长 | — |

## 常见问题

**一共有几个技能？**
11 个：10 个流水线技能（制片人 → 运营 → 调研 → 编剧 → 分镜 → 配音 → 美术 → 达芬奇剪辑 → 剪映剪辑 → 发布）+ 1 个独立技能（直播分享撰稿人）。

**必须用达芬奇吗？**
不用。可以换成剪映 / CapCut——告诉制片人 `output_target: "jianying"` 即可。也可以两个都生成（`output_target: "both"`）。达芬奇路径要求达芬奇 Resolve Studio 处于运行状态；剪映路径要求 VectCutAPI 在本地运行。

**怎么安装？**
把需要的技能目录复制到你的 Claude Code skills 文件夹（见上方[安装](#安装)说明）。不需要包管理器步骤。

**需要哪些 API？**
| API | 使用技能 | 必须？ |
|-----|---------|-------|
| Gemini Flash（`gemini-2.5-flash`） | 分镜师（via `generate_storyboard.py`） | 分镜生成必须 |
| Gemini Image API | 美术师（via `generate_images.py`） | AI 图片生成必须 |
| MiniMax Speech-02 | 配音师（中文 TTS 首选） | 否——可用免费 Edge-TTS 替代 |
| ElevenLabs | 配音师（英文 TTS） | 否——仅英文项目需要 |
| Edge-TTS | 配音师（免费草稿） | 否——内置，无需 Key |
| VectCutAPI（本地服务） | 剪映剪辑师 | 仅使用剪映输出时需要 |
| DaVinci Resolve Studio Python API | 达芬奇剪辑师 | 仅使用达芬奇输出时需要 |
| 网页搜索 / YouTube 字幕 | 调研员 | 需要 Claude Code 网络工具 |

**可以单独跑某个技能，不走完整流水线吗？**
可以。每个技能都可以用自然语言直接触发（见各技能 `SKILL.md` 里的触发条件）。制片人是可选的，它只是自动化了各技能之间的交接。

## 开源协议

[MIT](LICENSE) © 2026 chenyuxiaojin
