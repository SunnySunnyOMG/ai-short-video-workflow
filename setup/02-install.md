# 2. Install the tools

The pipeline needs Python 3.9+, Node.js 22+, ffmpeg, the MiniMax CLI and this repo's one npm package. HyperFrames, the renderer, runs through `npx` and downloads itself and a headless Chrome on first use. `python3 scripts/doctor.py` shows what is still missing.

Agents: ask the owner before installing system-wide packages, and say which ones.

On a mainland China network, set the mirrors in [china.md](china.md#镜像) first.

## macOS

With Homebrew (<https://brew.sh>):

```bash
brew install python node ffmpeg
```

## Linux (Ubuntu/Debian)

Ubuntu's own `nodejs` package is usually older than 22. Install Node from <https://nodejs.org/en/download> (nvm or NodeSource), then:

```bash
sudo apt install python3 python3-venv ffmpeg fonts-noto-cjk
```

## Windows (not verified)

```powershell
winget install Python.Python.3.14
winget install OpenJS.NodeJS.LTS
winget install Gyan.FFmpeg
```

Open a new terminal afterwards. See [platforms.md](platforms.md#windows) for known differences.

## <a id="python"></a>Python

Check with `python3 --version` (Windows: `python --version`). The pipeline uses only the standard library. The optional Lyria music script needs `google-genai`; install it in a virtual environment:

```bash
python3 -m venv .venv
.venv/bin/pip install google-genai
```

## <a id="node"></a>Node.js

Check with `node --version`: it must be 22 or newer (HyperFrames and Claude Code both require it).

## <a id="ffmpeg"></a>ffmpeg

Check with `ffmpeg -version` and `ffprobe -version`.

## <a id="mmx"></a>MiniMax CLI

```bash
npm install -g mmx-cli
mmx --version
```

Then sign in: [03-keys.md](03-keys.md#minimax-voice-and-transcription-sign-in-with-the-browser).

## <a id="repo"></a>This repo

```bash
git clone https://github.com/SunnySunnyOMG/ai-short-video-workflow.git
cd ai-short-video-workflow
npm install
python3 scripts/doctor.py
```

`npm install` fetches GSAP, the animation library the generated pages use (its own no-charge licence: <https://gsap.com/standard-license>).

HyperFrames is pinned in `config/video.json` (`"hyperframes": "0.9.43"`, the version this repo was tested with). To check the renderer on a new machine: `npx --yes hyperframes@0.9.43 doctor`. To upgrade, change the version, then run the example episode and look at its frames before using it for real work.

## Test

```bash
python3 pipeline/make.py new hello
python3 pipeline/make.py all episodes/hello --placeholder
```

This renders a silent 20-second video without any account. With MiniMax signed in, run the same command without `--placeholder` for the real thing; the report at the end should show about −14 LUFS and a readback match above 95 %.
