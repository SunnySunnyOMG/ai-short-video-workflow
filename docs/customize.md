# Customize

Three places, from least to most effort. Change the first one that can do what you want.

| What you want | Where |
| --- | --- |
| A different voice, speed, colour, font size, caption position, music level or loudness | `config/video.json` (all episodes) or `episodes/<slug>/episode.json` (one episode) |
| Rules about writing, wording, what must never appear, words the voice misreads | `rules/rules.md` (the agent reads it before every episode) |
| A new kind of page, a different TTS provider, a progress bar, a logo | `pipeline/make.py` |

After any change, rebuild from the earliest step it touches: script or voice settings → `voice`; look → `build`; loudness → `finish`. Then run the example episode once (`--placeholder` is enough for looks) to check nothing else broke.

## config/video.json

An episode's `episode.json` only needs the keys it changes; nested objects merge. For example:

```json
{ "title": "my-episode", "tts": { "speed": 1.1 }, "palette": { "accent": "#2950E6" } }
```

| Key | Meaning |
| --- | --- |
| `hyperframes` | Pinned HyperFrames CLI version. Change it deliberately and re-run the example. |
| `width`, `height`, `fps` | 1080 × 1920 at 30 fps for Douyin. |
| `tts.provider`, `model`, `voice`, `speed`, `language` | Speech synthesis. List MiniMax voices with `mmx speech voices`. |
| `tts.chars_per_second` | Only for `--placeholder` timing. |
| `asr.provider`, `language` | Speech recognition used to align captions and check the final audio. |
| `speak_replacements` | `[{"pattern": "<regex>", "replace": "<text>"}]` applied to what the voice reads, never to captions. Use it for words the voice gets wrong. |
| `pause_after_page`, `pauses` | Silence after each page, in seconds; `pauses` overrides it per page id. |
| `lead_in`, `end_hold` | Silence before the first word, and the minimum hold after the last page. |
| `music.file` | A music bed (path relative to the episode folder or the repo). Empty means voice only. |
| `music.level_lufs`, `music.duck` | Bed loudness, and whether it dips under speech. |
| `voice_level_lufs` | Voice loudness inside the mix, before the final normalisation. |
| `loudness.target_lufs`, `true_peak`, `lra` | The delivered file's loudness. |
| `palette` | `ground` background, `paper` cards, `ink` text, `muted` secondary text, `accent` decoration, `accent_text` highlighted words (keep it readable on `ground`). |
| `fonts.regular`, `fonts.bold` | Installed font names, tried in order. See `setup/platforms.md#fonts`. |
| `text.*` | Font sizes in pixels. Keep everything at or above `min_size`. |
| `captions.top`, `size`, `max_width_chars` | Caption position and size. Keep captions clear of Douyin's own buttons and text at the bottom and right. |
| `cover_at` | Second of the video used for `output/cover.png`. |
| `output_name` | File name for the delivered video; defaults to the episode folder name. |

## Layouts

Each line of `script.tsv` picks one:

- `title`: the first caption large, the rest as smaller lines under it. On the first page, the title is on screen from frame 0 (it becomes the thumbnail).
- `points`: one numbered card per caption, appearing as it is spoken; earlier cards dim.
- `keyword`: each caption as a large line; `[[keywords]]` turn into highlighted blocks when spoken.

In every layout, `[[keyword]]` changes colour at the moment it is heard.

To add a layout, add a branch in `page_html()` in `pipeline/make.py`, add its name to `LAYOUTS`, and use only the times in `scene['cues']` and `kw_time()` so the page still follows the voice. Ask your agent to do it: describe the page you want and point it at this section.

## Another TTS or ASR provider

`TTS` and `ASR` in `pipeline/make.py` map a provider name to a function. A TTS function writes an MP3 for a piece of text; an ASR function returns `(text, start, end)` per word. Add yours next to the MiniMax ones and set `tts.provider` / `asr.provider`. Keep MiniMax's function as the reference for retries and error messages.
