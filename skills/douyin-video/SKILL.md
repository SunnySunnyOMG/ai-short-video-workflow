---
name: douyin-video
description: Make one Douyin vertical video (1080×1920, 30 fps) with this repo's pipeline, from a topic to a checked, loudness-normalised MP4 with cover and captions. Use when the owner asks to make, script, voice, rebuild, check or deliver an episode, or to change how videos look or sound. The owner's own style rules live in rules/rules.md; this skill only holds the procedure.
---

# Douyin video

This skill is the procedure. It carries no style advice on purpose: how to write, what to avoid and what the owner likes all live in the owner's rules file, `rules/rules.md`, which grows after every episode. Read it before anything else and let it override your defaults.

If the machine is not set up yet, stop and follow `AGENTS.md` (setup) first.

## Boundaries

- Never publish, upload or log in to Douyin. The owner posts the video.
- Never put a key, token, password, account name, local path or other person's name on screen or in a committed file.
- Every fact in the narration needs a source the owner can open, or an experiment whose record is saved in the episode folder. If neither exists, rephrase it as an opinion or drop it.
- Third-party footage, images or music only with a licence that allows it; note the source in the episode folder.

## 0. Start

1. Read `rules/rules.md`. If it does not exist, copy `rules/rules.template.md` to it and tell the owner it is empty for now.
2. Create the episode: `python3 pipeline/make.py new <slug>` → `episodes/<slug>/`.
3. Settings come from `config/video.json`; anything that differs for this episode goes in `episodes/<slug>/episode.json`.

## 1. Topic and sources

- Agree with the owner on one sentence: what this episode says and what the viewer can do afterwards.
- Collect sources into `episodes/<slug>/sources.md` (link, date checked, the exact sentence you rely on).
- Offer the owner two or three directions when the angle is open; the owner chooses.

## 2. Script

Write `episodes/<slug>/script.tsv`, one page per line:

```
page-id<TAB>layout<TAB>narration with / between captions and [[keywords]]
```

- `layout` is `title`, `points` or `keyword` (see `docs/customize.md` for what each draws, and how to add layouts).
- `/` splits a page into captions; each caption appears when its first word is spoken.
- `[[word]]` lights up on screen the moment the word is spoken. It must appear in the narration exactly as written.
- Show the full narration to the owner and wait for approval before spending on voice.

Optional: `python3 pipeline/make.py voice episodes/<slug> --placeholder` then `build` and `check` gives a silent preview with estimated timing, at no cost.

## 3. Voice and timing

```
python3 pipeline/make.py voice episodes/<slug>
python3 pipeline/make.py align episodes/<slug>
```

- `voice` synthesises each page (cached by text and settings, so re-runs only pay for changed pages) and mixes the music bed if one is configured.
- Words the voice gets wrong are fixed with `speak_replacements` in the config (the caption keeps the original text). Add the rule to `rules/rules.md` too, so it is not lost.
- `align` transcribes the voice and moves captions and keywords onto the spoken words. Below 85 % match it stops: listen to `work/voice-only.mp3` and find the misread.

## 4. Build and check

```
python3 pipeline/make.py build episodes/<slug>
python3 pipeline/make.py check episodes/<slug>
```

- `check` runs the HyperFrames checker and saves a frame from the middle and the end of every page in `work/review/`. Errors must be zero. Read each warning and either fix it or say why it is fine.
- Open every frame in `work/review/` and look at it: overlapping text, a caption covering content, a line broken in the middle of a word, anything private on screen. The checker samples only some moments, so the frames are the real test.
- Never hand-edit `index.html` or `compositions/`: change the script, the config or `pipeline/make.py`, then rebuild.

## 5. Render and finish

```
python3 pipeline/make.py render episodes/<slug>
python3 pipeline/make.py finish episodes/<slug>
```

`finish` normalises loudness in two passes, writes `output/<name>.mp4`, `output/cover.png`, `output/<name>.srt` and `output/report.md`, and transcribes the final audio back to compare with the script. Report to the owner: duration, loudness, check result, readback match and every difference it lists, what you did not verify (for example, how it looks on a phone), and what needs the owner's decision.

## 6. Owner review

The owner watches the video and gives notes. Apply them, rebuild from the earliest step the change touches (script → voice; config look → build), and deliver again.

## 7. After the owner signs off: update the rules file

Ask the owner what from this episode should become a rule, and add it to `rules/rules.md` with the episode name and the reason. Also add mechanical fixes you made along the way (a word the voice misreads, a layout limit). Something that happened once and may not recur goes under "notes", not "rules". The next episode starts by reading this file.

If the owner asked for a change in how the pipeline itself works (a new layout, a different voice provider), make it in `pipeline/` or `config/`, run the example episode again to prove nothing else broke, and record the change in `rules/rules.md` under "pipeline changes".
