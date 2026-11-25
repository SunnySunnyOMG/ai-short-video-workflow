# Operating systems

| System | Status |
| --- | --- |
| macOS (Apple silicon) | Tested end to end: setup, the example episode, real episodes. |
| Linux (Ubuntu/Debian) | Not tested end to end yet. Every tool used here supports Linux; follow the same steps with the commands in `02-install.md`. |
| Windows 10/11 | Not verified. The tools support Windows, and the scripts avoid shell-specific syntax, but nobody has run the whole pipeline there yet. |

An agent can adapt the pipeline to an untested system: make the smallest change that works, prove it with the example episode, and write what it changed into `rules/rules.md` under "Pipeline changes". The known differences are below.

## Fonts

The video uses installed fonts, listed in `config/video.json` under `fonts` and tried in order:

- macOS: PingFang SC, built in.
- Windows: Microsoft YaHei, built in.
- Linux: install a Chinese font, for example `sudo apt install fonts-noto-cjk`, then `fc-list :lang=zh family` should list "Noto Sans CJK SC".

The HyperFrames checker warns `font_face_local_only` for every installed font. That is expected: it means the video uses this machine's copy. If you render on another machine, make sure it has one of the listed fonts, or put a font file you are licensed to use into the episode's `assets/fonts/` and change the `@font-face` in `pipeline/make.py`.

## Linux

- Headless Chrome, which HyperFrames uses to render, needs some system libraries. If rendering fails with a missing `.so`, install the libraries the error names (on Ubuntu, `libnss3`, `libatk-bridge2.0-0`, `libgbm1`, `libasound2` and friends cover most cases).
- Keys for optional services use `secret-tool` (package `libsecret-tools`) or an environment variable. See `03-keys.md`.

## Windows

Known differences for an agent to handle:

- Python is usually `python` or `py`, not `python3`. Use whichever `python --version` answers with 3.9 or newer.
- Commands installed by npm (`npx`, `mmx`) are `.cmd` shims. The pipeline resolves them with `shutil.which`; if a step still says a command is not found, check it runs in a new terminal first.
- Install tools with `winget` (see `02-install.md`). Open a new terminal afterwards so `PATH` updates.
- There is no Keychain; optional keys go in user environment variables (`03-keys.md`).
- Long paths or paths with spaces can break ffmpeg filters. Keep the repo in a short path such as `C:\video\`.
- Rendering needs a few GB of free disk space; `render` already uses one worker to keep memory and disk use low.
