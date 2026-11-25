# 1. Accounts and what to buy

What a working setup needs, checked on 2026-11-26. Prices and plan names change: follow the links and read the current page before paying.

| What | Needed? | What it does | Global route | China route |
| --- | --- | --- | --- | --- |
| A computer | Yes | Runs everything locally | macOS (tested), Linux, Windows (not verified). 8 GB RAM and 10 GB free disk are comfortable. | Same |
| Agent plan | Yes | The model your agent thinks with | Claude Pro/Max, or a ChatGPT plan with Codex ([00-agent.md](00-agent.md)) | MiniMax M Plan, GLM Coding Plan, Kimi Code or DeepSeek ([china.md](china.md)) |
| MiniMax | Yes | Voice (text to speech) and transcription for timing and checks | <https://platform.minimax.io> | <https://platform.minimaxi.com> |
| Music | No | A music bed under the voice | Gemini API key for Lyria | Add music in the Douyin app when posting, or a domestic API ([china.md](china.md#配乐)) |
| Douyin account | To post | You post the video yourself | | |

## MiniMax

The pipeline calls MiniMax through its official CLI, `mmx` (<https://github.com/MiniMax-AI/cli>). One account covers both speech synthesis and transcription.

Naming you will meet: the China site lives at both `minimaxi.com` and `minimax.cn` (both official; one redirects to the other). The subscription is called **M Plan** on the sales pages and **Token Plan** in some docs and in `mmx` help; it is the same thing. Its keys start with `sk-cp` and are not interchangeable with pay-as-you-go keys (`sk-api`).

1. Sign up: mainland China <https://platform.minimaxi.com>, elsewhere <https://platform.minimax.io>. The two are separate accounts; pick one and use the matching region when signing in (`--region=cn` or `--region=global`).
2. Pay for usage, either way works:
   - **Pay as you go.** On the China site on 2026-11-26, `speech-2.8-hd` cost ¥3.50 per 10,000 characters. A two-minute video is roughly 600 characters, so a few re-takes cost well under ¥1. Pricing: <https://platform.minimax.cn/docs/guides/pricing>; global: <https://platform.minimax.io/docs/guides/pricing-paygo>.
   - **M Plan** (subscription; tiers Go, Explore, Build). Every tier includes speech, and the same plan can also power your agent on the China route. China: <https://www.minimax.cn/m-plan>; global: <https://www.minimax.io/m-plan>.
3. Sign in on this machine: see [03-keys.md](03-keys.md#minimax-voice-and-transcription-sign-in-with-the-browser).

The voice the example uses is `Chinese (Mandarin)_Sincere_Adult`. List others with `mmx speech voices` and set yours in `config/video.json`.

MiniMax's pricing page says its music model stopped serving new users on 2026-08-20 (<https://platform.minimax.cn/docs/guides/pricing>), so this pipeline does not use MiniMax for music.

## Music (optional)

The pipeline runs without music. Options:

- **Douyin's own library.** Post the voice-only video and pick a track in the Douyin app. No account or cost, and the track is licensed for use on Douyin. Simplest on any route.
- **Google Lyria RealTime** (global route). Needs a Gemini API key from <https://aistudio.google.com/apikey>; Google AI Studio is not available in mainland China or Hong Kong. The model (`lyria-realtime-exp`) is experimental and not listed on the pricing page; the batch Lyria models cost from $0.04 per 30-second clip with no free tier (<https://aistudio.google.com/docs/pricing>). Generate a bed with `.venv/bin/python pipeline/music_lyria.py --prompt "<describe the music>"` (setup in [02-install.md](02-install.md#python)), then set `music.file` in the config. Store the key as in [03-keys.md](03-keys.md#gemini-optional-for-lyria-music).
- **Domestic music APIs**: see [china.md](china.md#配乐). Not built into the pipeline yet; your agent can add an adapter.
- **Your own file**: any instrumental track you are licensed to use. Put it in the episode folder and set `music.file`.
