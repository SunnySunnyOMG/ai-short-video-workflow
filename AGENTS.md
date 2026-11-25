# Instructions for agents

You are helping the owner of this repo make Douyin vertical videos with an automated pipeline. Speak to the owner in their language (usually Chinese). There are two jobs:

1. **Setup**: the machine is not ready yet. Follow the setup protocol below.
2. **An episode**: the machine is ready. Follow `skills/douyin-video/SKILL.md`.

Run `python3 scripts/doctor.py` (or `python scripts/doctor.py` on Windows) to tell which job you are in. If Python itself is missing, start at `setup/02-install.md#python`.

## Setup protocol

Goal: from a bare machine to a rendered example video, with the owner doing only what a person must do.

1. **Route.** Ask the owner one question: can this machine reach Anthropic, OpenAI and Google services (outside mainland China, or with a working proxy)? Yes → global route. No or unsure → China route (`setup/china.md`). The route decides which agent model and which music option to use; everything else is the same.
2. **Check.** Run the doctor. Fix missing items in the order it prints them, using the page each item points to.
3. **Split the work.**
   - You do: installing packages and CLIs, running `npm install`, writing config, running the pipeline. Before installing anything system-wide, tell the owner what and why, and get a yes.
   - The owner does: creating accounts, paying, signing in, and typing or pasting keys into the secure prompt of the tool that stores them (`setup/03-keys.md`). Give the exact link and the exact button or menu; then wait.
   - Never ask the owner to paste a key, password or token into the chat. Never print a key. Never write one into this repo.
4. **Prove it works, cheapest first.**
   - `python3 pipeline/make.py new hello` then `python3 pipeline/make.py all episodes/hello --placeholder`: a silent video with no accounts needed. It tests Node, ffmpeg, fonts and rendering.
   - When MiniMax is signed in: `python3 pipeline/make.py all episodes/hello`. It should end with a report showing about −14 LUFS and a readback match above 95 %. Show the owner `episodes/hello/output/hello.mp4`.
5. **Hand over.** Copy `rules/rules.template.md` to `rules/rules.md`. Ask the owner whether they want to set a default voice, colours or music now (see `docs/customize.md`); empty is fine. Tell them the next step is to give you a topic.

Record anything you had to do differently on this machine (a different command, a missing font, a Windows path fix) in `rules/rules.md` under "Pipeline changes", so the next session does not rediscover it.

## Operating systems

macOS is the tested platform. Linux should work by following the same steps. Windows has not been verified. On Windows, adapt as you go: read `setup/platforms.md#windows` for the known differences, make the smallest change that works, run the example episode to prove it, and record what you changed. If a change belongs in the repo for everyone, tell the owner; do not open pull requests on their behalf.

## Working rules

- The owner decides the topic, the angle, what goes on screen and whether a video is done. Ask; do not assume.
- Read `rules/rules.md` before every episode. It overrides your defaults and this repo's examples.
- Never publish to Douyin or any other platform.
- Change `config/`, the script, or `pipeline/`; never hand-edit generated files (`index.html`, `compositions/`).
- When a step fails, read the message, fix the cause, and re-run only that step. Steps are cached and idempotent.
