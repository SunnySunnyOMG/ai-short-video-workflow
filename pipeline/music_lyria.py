#!/usr/bin/env python3
"""Generate an instrumental music bed with Google Lyria RealTime (optional; needs a Gemini API key).

    pip install google-genai          (once, ideally in a virtualenv)
    python3 pipeline/music_lyria.py --seconds 90 --out music/bed.m4a \
        --prompt "calm electronic underscore, soft synth arpeggio, warm pads, light percussion, no vocals"

Then set "music": {"file": "music/bed.m4a"} in config/video.json or an episode.json.

The key is read from GEMINI_API_KEY, else from the macOS Keychain item "apikey/gemini",
else from Linux secret-tool (service apikey/gemini). It is never printed.
The live stream sometimes drops after 20–70 s, so the bed is generated in parts and joined with crossfades.
"""

from pathlib import Path
import argparse
import asyncio
import os
import platform
import subprocess
import sys
import tempfile
import wave

RATE, CHANNELS, WIDTH = 48000, 2, 2


def api_key():
    if os.environ.get('GEMINI_API_KEY'):
        return os.environ['GEMINI_API_KEY']
    cmds = {'Darwin': ['security', 'find-generic-password', '-s', 'apikey/gemini', '-w'],
            'Linux': ['secret-tool', 'lookup', 'service', 'apikey/gemini']}
    cmd = cmds.get(platform.system())
    if cmd:
        try:
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode == 0 and r.stdout.strip():
                return r.stdout.strip()
        except OSError:
            pass
    sys.exit('No Gemini key: set GEMINI_API_KEY or store it as "apikey/gemini" (see setup/03-keys.md)')


async def part(client, types, args, seconds):
    buf, target = bytearray(), int(seconds * RATE * CHANNELS * WIDTH)
    cfg = types.LiveMusicGenerationConfig(bpm=args.bpm, density=args.density, brightness=args.brightness, temperature=1.0)
    try:
        async with client.aio.live.music.connect(model='models/lyria-realtime-exp') as session:
            await session.set_weighted_prompts(prompts=[types.WeightedPrompt(text=args.prompt, weight=1.0)])
            await session.set_music_generation_config(config=cfg)
            await session.play()

            async def collect():
                while len(buf) < target:
                    async for msg in session.receive():
                        sc = msg.server_content
                        for chunk in (sc.audio_chunks if sc and sc.audio_chunks else []):
                            buf.extend(chunk.data)
                            if len(buf) >= target:
                                return
            await asyncio.wait_for(collect(), timeout=seconds * 2 + 20)
    except Exception as e:  # the stream drops often; keep what arrived
        print(f'  stream ended early ({type(e).__name__}); keeping {len(buf) / (RATE * CHANNELS * WIDTH):.1f}s', file=sys.stderr)
    return bytes(buf[:target])


async def generate(args):
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        sys.exit('google-genai is not installed: pip install google-genai')
    client = genai.Client(api_key=api_key(), http_options={'api_version': 'v1alpha'})
    parts, have = [], 0.0
    while have < args.seconds and len(parts) < 12:
        want = min(60, args.seconds - have + 3)
        pcm = await part(client, types, args, want)
        got = len(pcm) / (RATE * CHANNELS * WIDTH)
        print(f'  part {len(parts) + 1}: {got:.1f}s', flush=True)
        if got >= 8:
            parts.append(pcm)
            have += got - (3 if len(parts) > 1 else 0)
    if not parts:
        sys.exit('Lyria returned no audio; check the key, region and quota')
    return parts


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--prompt', required=True)
    ap.add_argument('--seconds', type=float, default=90)
    ap.add_argument('--bpm', type=int, default=108)
    ap.add_argument('--density', type=float, default=0.4)
    ap.add_argument('--brightness', type=float, default=0.65)
    ap.add_argument('--out', default='music/bed.m4a')
    args = ap.parse_args()
    parts = asyncio.run(generate(args))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        files = []
        for i, pcm in enumerate(parts):
            f = Path(tmp) / f'p{i}.wav'
            with wave.open(str(f), 'wb') as w:
                w.setnchannels(CHANNELS)
                w.setsampwidth(WIDTH)
                w.setframerate(RATE)
                w.writeframes(pcm)
            files.append(f)
        inputs = sum((['-i', str(f)] for f in files), [])
        chain, last = [], '[0:a]'
        for i in range(1, len(files)):
            chain.append(f'{last}[{i}:a]acrossfade=d=3[x{i}]')
            last = f'[x{i}]'
        graph = ';'.join(chain + [f'{last}atrim=0:{args.seconds},loudnorm=I=-18:TP=-2:LRA=8[out]'])
        subprocess.run(['ffmpeg', '-v', 'error', '-y', *inputs, '-filter_complex', graph, '-map', '[out]',
                        '-c:a', 'aac', '-b:a', '192k', str(out)], check=True)
    (out.parent / (out.stem + '-SOURCE.txt')).write_text(
        f'Google Lyria RealTime (models/lyria-realtime-exp) via the Gemini API\nprompt\t{args.prompt}\n'
        f'bpm\t{args.bpm}\ndensity\t{args.density}\nbrightness\t{args.brightness}\nparts\t{len(parts)}, 3 s crossfades, loudnorm -18 LUFS\n')
    print(f'music: {out}')


if __name__ == '__main__':
    main()
