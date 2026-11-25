# AI Short Video Workflow

**中文说明 → [README.zh-CN.md](README.zh-CN.md)**

Turn a script into a finished Douyin vertical video (1080×1920, 30 fps) on your own computer: synthetic voice, code-rendered animation, captions timed to the spoken word, automatic checks, loudness-normalised delivery. You talk to a coding agent; the agent runs the pipeline.

<img src="docs/img/example-frames.jpg" alt="Three frames of the example video: a title page, a numbered list, and a closing line with a highlighted keyword" width="620">

The repo is built so that a person or an agent can read it and set everything up on a bare machine: which accounts to open, what to buy, what to install, where keys go, and a test video to prove it works. Mainland China users get a route that needs no VPN.

## Start here

**If you are an agent**, read [AGENTS.md](AGENTS.md).

**If you are a person**:

1. Get a coding agent running on your computer: [setup/00-agent.md](setup/00-agent.md) (in mainland China: [setup/china.md](setup/china.md)).
2. Clone this repo, open the agent in its folder, and say: *"Read AGENTS.md and set up this machine to make videos. Ask me before installing anything."*
3. The agent checks the machine, tells you which accounts to create, installs the tools, and renders a test video.

After that, give the agent a topic. It follows [skills/douyin-video/SKILL.md](skills/douyin-video/SKILL.md): sources, script, voice, visuals, checks, delivery. You approve the script, review the video, and post it yourself.

## What you need

| | |
| --- | --- |
| A computer | macOS (tested), Linux (should work), Windows (not verified; see [setup/platforms.md](setup/platforms.md)) |
| An agent plan | Claude or ChatGPT, or a Chinese provider such as MiniMax, GLM, Kimi or DeepSeek ([setup/00-agent.md](setup/00-agent.md)) |
| A MiniMax account | Voice and transcription; pay as you go is enough ([setup/01-accounts.md](setup/01-accounts.md)) |
| Music (optional) | Google Lyria, a Chinese music API, your own file, or a track picked in the Douyin app when posting |

## How it works

```
script.tsv ──voice──▶ narration + timing ──align──▶ word-level timing ──build──▶ HTML pages
                                                                                    │
output/*.mp4 ◀──finish── renders/master.mp4 ◀──render── check (lint + a frame per page)
```

- **The voice is the clock.** Each page is synthesised with MiniMax, then transcribed back; captions and `[[keywords]]` appear at the second they are spoken. Change a sentence and rebuild: everything after it moves with it.
- **Visuals are code.** Pages are HTML + GSAP rendered frame by frame with [HyperFrames](https://github.com/heygen-com/hyperframes), so the same input gives the same video every time.
- **Every build is checked.** The HyperFrames checker runs, the agent looks at a frame from each page, loudness is normalised to −14 LUFS in two passes, and the final audio is transcribed and compared with the script.

One command runs it all: `python3 pipeline/make.py all episodes/<name>`. Add `--placeholder` for a silent preview that needs no accounts.

## Make it yours

The repo contains the procedure and the tools, and no style rules. Yours go in your fork:

- [config/video.json](config/video.json): voice, speed, colours, fonts, caption position, music level, loudness. See [docs/customize.md](docs/customize.md).
- `rules/rules.md`: your rules about writing, wording, looks and what must never appear on screen. It starts from an empty [template](rules/rules.template.md); the agent reads it before every episode and adds to it after you approve one.
- [pipeline/make.py](pipeline/make.py): page layouts and providers, for when the config is not enough. Ask your agent to change it.

## What's inside

```
AGENTS.md                 instructions for any agent (CLAUDE.md, GEMINI.md, QWEN.md point here)
setup/                    agent, accounts, installs, keys, operating systems, China route
skills/douyin-video/      the per-episode procedure
pipeline/make.py          script → video, one file, Python standard library only
pipeline/music_lyria.py   optional music bed from Google Lyria
scripts/doctor.py         what this machine is still missing
config/video.json         defaults for every episode
rules/rules.template.md   empty rules file for your own style
examples/hello/           a 20-second example script
docs/customize.md         every setting and how to extend the pipeline
```

## Not included

- Publishing. The pipeline never logs in to or posts on any platform.
- Style advice. Keep yours in `rules/rules.md`.

## Credits

[HyperFrames](https://github.com/heygen-com/hyperframes) (Apache-2.0) renders the video. [GSAP](https://gsap.com) animates the pages under its own no-charge licence and is installed by `npm install`, not bundled. Voice and transcription by [MiniMax](https://github.com/MiniMax-AI/cli). Optional music by Google Lyria.

## License

[MIT](LICENSE)
