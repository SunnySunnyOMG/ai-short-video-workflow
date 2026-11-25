#!/usr/bin/env python3
"""Turn an episode's script.tsv into a finished vertical video.

    python3 pipeline/make.py new <slug>                 copy examples/hello into episodes/<slug>/
    python3 pipeline/make.py all <episode-dir>          voice → align → build → check → render → finish
    python3 pipeline/make.py <step> <episode-dir>       run one step: voice, align, build, check, render, finish
    add --placeholder to voice/all to use silent, estimated timing (no accounts needed)

The voice is the clock: every caption and every [[keyword]] appears at the second it is spoken.
Settings come from config/video.json, overridden by <episode-dir>/episode.json. See docs/customize.md.
"""

from array import array
from concurrent.futures import ThreadPoolExecutor
from difflib import SequenceMatcher
from hashlib import sha256
from html import escape
from pathlib import Path
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
import time
import wave

REPO = Path(__file__).resolve().parent.parent
RATE = 48000
LAYOUTS = ('title', 'points', 'keyword')


# ---------------------------------------------------------------- config and script

def merge(base, over):
    out = dict(base)
    for k, v in over.items():
        out[k] = merge(base[k], v) if isinstance(v, dict) and isinstance(base.get(k), dict) else v
    return out


def read_json(path):
    try:
        return json.loads(path.read_text(encoding='utf-8-sig'))
    except json.JSONDecodeError as e:
        sys.exit(f'{path.name} is not valid JSON: {e}')


def load_config(ep):
    cfg = read_json(REPO / 'config/video.json')
    own = ep / 'episode.json'
    cfg = merge(cfg, read_json(own)) if own.exists() else cfg
    small = {k: v for k, v in cfg['text'].items() if k != 'min_size' and v < cfg['text']['min_size']}
    if cfg['captions']['size'] < cfg['text']['min_size']:
        small['captions.size'] = cfg['captions']['size']
    if small:
        sys.exit(f'font sizes below text.min_size ({cfg["text"]["min_size"]}px): {small}')
    return cfg


def timing_of(ep):
    path = ep / 'work/timing.json'
    if not path.exists():
        sys.exit('no work/timing.json yet: run the voice step first')
    return json.loads(path.read_text(encoding='utf-8'))


def read_script(ep):
    """script.tsv: one page per line, `page<TAB>layout<TAB>text`; cues split by `/`; [[word]] marks a keyword."""
    pages = []
    for n, line in enumerate((ep / 'script.tsv').read_text(encoding='utf-8-sig').splitlines(), 1):
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        cols = line.split('\t')
        if len(cols) != 3:
            sys.exit(f'script.tsv line {n}: expected 3 tab-separated columns (page, layout, text), got {len(cols)}')
        pid, layout, text = (c.strip() for c in cols)
        if not re.fullmatch(r'[a-z][a-z0-9-]*', pid) or pid in {p['id'] for p in pages}:
            sys.exit(f'script.tsv line {n}: page id {pid!r} must be unique, lowercase, start with a letter')
        if layout not in LAYOUTS:
            sys.exit(f'script.tsv line {n}: layout {layout!r} is not one of {", ".join(LAYOUTS)}')
        if text.count('[[') != text.count(']]') or '[[]]' in text or re.search(r'\[\[[^\]]*/', text):
            sys.exit(f'script.tsv line {n}: each [[keyword]] needs both brackets, some text, and no "/" inside')
        cues = [c.strip() for c in text.split('/') if plain(c).strip(' 。，,.')]
        if not cues:
            sys.exit(f'script.tsv line {n}: page {pid!r} has no narration')
        if layout == 'points' and len(cues) > 6:
            sys.exit(f'script.tsv line {n}: a points page holds at most 6 cues; split it into two pages')
        pages.append({'id': pid, 'layout': layout, 'cues': cues})
    if not pages:
        sys.exit('script.tsv is empty')
    return pages


def plain(text):
    return text.replace('[[', '').replace(']]', '')


def keywords(text):
    return re.findall(r'\[\[(.+?)\]\]', text)


def canonical(text):
    return re.sub(r'[^\w]', '', text.lower()).replace('_', '')


def spoken(text, cfg):
    """What the voice reads. Captions keep the original text; rewrites come from speak_replacements."""
    out = plain(text)
    for rule in cfg['speak_replacements']:
        out = re.sub(rule['pattern'], rule['replace'], out)
    return out


# ---------------------------------------------------------------- audio helpers

def exe(name):
    """Full path of a command, so npm-installed .cmd shims also run on Windows."""
    return shutil.which(name) or name


def ffmpeg(*args):
    r = subprocess.run([exe('ffmpeg'), '-v', 'error', '-y', *map(str, args)], capture_output=True)
    if r.returncode:
        sys.exit(f'ffmpeg failed: {r.stderr.decode("utf-8", "replace").strip()[-1500:]}')
    return r.stdout


def wav(path, pcm):
    with wave.open(str(path), 'wb') as f:
        f.setparams((1, 2, RATE, 0, 'NONE', ''))
        f.writeframes(pcm)


def weight(text):
    return sum(len(w) * .42 for w in re.findall('[A-Za-z]+', text)) + sum(
        1 if '\u4e00' <= c <= '\u9fff' else .4 if c.isdigit() else .55 if c in '，,：；;、' else 0 for c in text)


def run(cmd, cwd=None, check=True):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if check and r.returncode:
        sys.exit(f'failed: {" ".join(map(str, cmd))}\n{r.stderr.strip() or r.stdout.strip()}')
    return r


# ---------------------------------------------------------------- providers

def tts_minimax(text, out, cfg):
    t = cfg['tts']
    cmd = [exe('mmx'), 'speech', 'synthesize', '--non-interactive', '--quiet', '--model', t['model'], '--voice', t['voice'],
           '--speed', str(t['speed']), '--language', t['language'], '--text-normalization', '--text-file', '-', '--out', str(out)]
    for delay in (0, 13, 24, 38):
        time.sleep(delay)
        r = subprocess.run(cmd, input=text, capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode == 0:
            return
        if 'rate limit' not in (r.stderr + r.stdout).lower():
            sys.exit(f'MiniMax speech failed: {r.stderr.strip() or r.stdout.strip()}\nIs mmx logged in? Run: mmx auth status')
    sys.exit('MiniMax rate limit persisted; wait a minute and run the voice step again')


def asr_minimax(audio, out, cfg):
    run([exe('mmx'), 'speech', 'transcribe', '--non-interactive', '--file', str(audio), '--language', cfg['asr']['language'],
         '--response-format', 'verbose_json', '--timestamp-level', 'word', '--out', str(out)])
    data = json.loads(out.read_text(encoding='utf-8'))
    return [(s['text'], s['start'], s['end']) for s in data['segments']]


TTS = {'minimax': tts_minimax}
ASR = {'minimax': asr_minimax}


# ---------------------------------------------------------------- step: voice

def synth_page(page, ep, cfg, placeholder):
    text = spoken(''.join(page['cues']), cfg)
    if placeholder:
        seconds = max(1.0, weight(text) / cfg['tts']['chars_per_second'])
        return bytes(2 * round(seconds * RATE))
    t = cfg['tts']
    tag = sha256(json.dumps([t, text], ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]
    out = ep / 'work/narration' / f'{page["id"]}-{tag}.mp3'
    out.parent.mkdir(parents=True, exist_ok=True)
    if not out.exists():
        tmp = out.with_name(out.stem + '.partial.mp3')
        TTS[t['provider']](text, tmp, cfg)
        tmp.replace(out)
    pcm = ffmpeg('-i', out, '-af',
                 'silenceremove=start_periods=1:start_duration=0.008:start_threshold=-62dB,areverse,'
                 'silenceremove=start_periods=1:start_duration=0.008:start_threshold=-62dB,areverse',
                 '-ar', RATE, '-ac', 1, '-f', 's16le', '-')
    print(f'  {page["id"]}: {len(pcm) / (2 * RATE):.2f}s', flush=True)
    return pcm


def cue_cuts(pcm, cues):
    """First guess of where each cue starts: proportional to text weight, nudged into quiet gaps."""
    samples = array('h', pcm)
    duration = len(samples) / RATE
    win = RATE // 100
    env = [max((abs(s) for s in samples[i:i + win]), default=0) for i in range(0, len(samples), win)] or [0]
    ws = [max(weight(plain(c)), .5) for c in cues]
    total, cuts, acc = sum(ws), [0.0], 0
    for i, w in enumerate(ws[:-1]):
        acc += w
        target = round(duration * acc / total * 100)
        lo = max(round(cuts[-1] * 100) + 30, target - 29)
        hi = min(len(env) - (len(cues) - i - 1) * 30, target + 29)
        cut = min(range(lo, hi + 1), key=lambda j: sum(env[max(0, j - 3):j + 3]) / 8000 + abs(j - target) * .12,
                  default=target)
        cuts.append(cut / 100)
    return cuts + [duration]


def estimate_chars(scene):
    chars = []
    for cue in scene['cues']:
        c = canonical(plain(cue['text']))
        span = cue['end'] - cue['start']
        chars += [[ch, round(cue['start'] + span * (i + .5) / max(1, len(c)), 3)] for i, ch in enumerate(c)]
    return chars


def resolve_music(ep, cfg):
    f = cfg['music']['file']
    if not f:
        return None
    for base in (ep, REPO):
        if (base / f).exists():
            return base / f
    sys.exit(f'music file not found: {f} (looked in the episode folder and the repo root)')


def step_voice(ep, cfg, placeholder=False):
    pages = read_script(ep)
    with ThreadPoolExecutor(max_workers=3) as pool:
        recs = list(pool.map(lambda p: synth_page(p, ep, cfg, placeholder), pages))
    pcm = bytearray(2 * round(cfg['lead_in'] * RATE))
    scenes = []
    for page, rec in zip(pages, recs):
        start = len(pcm) / (2 * RATE)
        pts = cue_cuts(rec, page['cues'])
        cues = [{'start': round(start + a, 4), 'end': round(start + b, 4), 'text': t}
                for a, b, t in zip(pts, pts[1:], page['cues'])]
        pcm.extend(rec)
        pause = cfg['pauses'].get(page['id'], cfg['pause_after_page'])
        pcm.extend(bytes(2 * round((max(pause, cfg['end_hold']) if page is pages[-1] else pause) * RATE)))
        scenes.append({'id': page['id'], 'layout': page['layout'], 'start': round(start, 4),
                       'end': round(len(pcm) / (2 * RATE), 4), 'cues': cues})
    fps = cfg['fps']
    duration = math.ceil(len(pcm) / (2 * RATE) * fps) / fps
    for a, b in zip(scenes, scenes[1:]):
        a['end'] = b['start'] = round((a['cues'][-1]['end'] + b['cues'][0]['start']) / 2, 4)
    scenes[0]['start'], scenes[-1]['end'] = 0, duration
    for s in scenes:
        s['chars'] = estimate_chars(s)

    audio = ep / 'assets/audio'
    audio.mkdir(parents=True, exist_ok=True)
    music = resolve_music(ep, cfg)
    with tempfile.TemporaryDirectory() as tmp:
        voice = Path(tmp) / 'voice.wav'
        wav(voice, bytes(pcm))
        ffmpeg('-i', voice, '-c:a', 'libmp3lame', '-b:a', '128k', ep / 'work/voice-only.mp3')
        vl = cfg['voice_level_lufs']
        if placeholder and not music:
            ffmpeg('-i', voice, '-ac', 2, '-t', duration, '-c:a', 'aac', '-b:a', '128k', audio / 'mix.m4a')
        elif not music:
            ffmpeg('-i', voice, '-af', f'loudnorm=I={vl}:TP=-2:LRA=7,aresample={RATE},pan=stereo|c0=c0|c1=c0',
                   '-t', duration, '-c:a', 'aac', '-b:a', '192k', audio / 'mix.m4a')
        else:
            m = cfg['music']
            duck = '[m][k]sidechaincompress=threshold=0.035:ratio=6:attack=20:release=300[bed];' if m['duck'] else '[m]anull[bed];[k]anullsink;'
            ffmpeg('-i', voice, '-stream_loop', -1, '-i', music, '-filter_complex',
                   f'[0:a]loudnorm=I={vl}:TP=-2:LRA=7,aresample={RATE},asplit=2[v][k];'
                   f'[1:a]loudnorm=I={m["level_lufs"]}:TP=-8:LRA=6,aresample={RATE},afade=t=in:d=0.8,'
                   f'afade=t=out:st={max(0, duration - 1.6)}:d=1.6[m];{duck}'
                   '[v]pan=stereo|c0=c0|c1=c0[n];[n][bed]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.92[out]',
                   '-map', '[out]', '-t', duration, '-ar', RATE, '-c:a', 'aac', '-b:a', '192k', audio / 'mix.m4a')
    timing = {'duration': duration, 'placeholder': placeholder, 'aligned': False, 'scenes': scenes}
    (ep / 'work/timing.json').write_text(json.dumps(timing, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'voice: {duration:.2f}s, {len(scenes)} pages{" (placeholder: silent, estimated timing)" if placeholder else ""}')


# ---------------------------------------------------------------- step: align

def match_ratio(script_text, heard_text):
    return SequenceMatcher(None, canonical(script_text), canonical(heard_text), autojunk=False).ratio()


def step_align(ep, cfg):
    path = ep / 'work/timing.json'
    timing = timing_of(ep)
    if timing['placeholder']:
        print('align: skipped (placeholder voice has nothing to transcribe)')
        return
    words = ASR[cfg['asr']['provider']](ep / 'work/voice-only.mp3', ep / 'work/readback-voice.json', cfg)
    words = [(canonical(w), a, b) for w, a, b in words]
    htxt = ''.join(w for w, _, _ in words)
    htimes = [a + (b - a) * i / max(1, len(w)) for w, a, b in words for i in range(len(w))]
    script = ''.join(canonical(plain(c['text'])) for s in timing['scenes'] for c in s['cues'])
    m = SequenceMatcher(None, script, htxt, autojunk=False)
    score = m.ratio()
    if score < .85:
        sys.exit(f'align: the transcript matches the script only {score:.1%}; listen to work/voice-only.mp3')
    mapping = {i + n: j + n for i, j, size in m.get_matching_blocks() for n in range(size)}
    t_of = [htimes[mapping[i]] if i in mapping else None for i in range(len(script))]
    for i in range(len(script)):
        if t_of[i] is None:
            prev = next(((k, t_of[k]) for k in range(i - 1, -1, -1) if t_of[k] is not None), None)
            nxt = next(((k, t_of[k]) for k in range(i + 1, len(script)) if t_of[k] is not None), None)
            if prev and nxt:
                t_of[i] = prev[1] + (nxt[1] - prev[1]) * (i - prev[0]) / (nxt[0] - prev[0])
            else:
                t_of[i] = (prev or nxt)[1]
    k, moved = 0, 0
    for scene in timing['scenes']:
        scene['chars'] = []
        for ci, cue in enumerate(scene['cues']):
            c = canonical(plain(cue['text']))
            if ci and c and k in mapping:
                seen = round(t_of[k] - .05, 4)
                if abs(seen - cue['start']) < 1.8 and scene['cues'][ci - 1]['start'] + .4 < seen:
                    cue['start'] = scene['cues'][ci - 1]['end'] = seen
                    moved += 1
            scene['chars'] += [[ch, round(t_of[k + n], 3)] for n, ch in enumerate(c)]
            k += len(c)
    timing['aligned'] = True
    timing['voice_match'] = round(score, 4)
    path.write_text(json.dumps(timing, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'align: transcript matches the script {score:.1%}; moved {moved} caption starts onto the spoken word')


# ---------------------------------------------------------------- step: build

def esc(s):
    return escape(str(s), quote=True)


def font_css(cfg):
    def face(names, w):
        return f"@font-face{{font-family:Body;src:{','.join(f'local({json.dumps(n)})' for n in names)};font-weight:{w}}}"
    return face(cfg['fonts']['regular'], 400) + face(cfg['fonts']['bold'], 700)


def styles(cfg):
    p, t = cfg['palette'], cfg['text']
    return f"""{font_css(cfg)}
#root{{position:absolute;inset:0;background:{p['ground']};color:{p['ink']};font-family:Body,sans-serif;overflow:hidden}}
#root *{{box-sizing:border-box}}
.stack{{position:absolute;left:60px;right:60px;top:260px;display:flex;flex-direction:column;gap:34px}}
.title{{font-size:{t['title_size']}px;font-weight:700;line-height:1.18;text-align:center;margin-top:160px}}
.bar{{width:120px;height:12px;background:{p['accent']};align-self:center}}
.sub{{font-size:{t['point_size']}px;font-weight:400;line-height:1.35;text-align:center;color:{p['muted']}}}
.row{{display:flex;gap:26px;align-items:flex-start;background:{p['paper']};border:5px solid {p['ink']};box-shadow:10px 10px 0 {p['ink']};padding:24px 28px}}
.num{{flex:none;width:72px;height:72px;background:{p['ink']};color:{p['paper']};font-size:44px;font-weight:700;display:flex;align-items:center;justify-content:center}}
.row .txt{{font-size:{t['point_size']}px;font-weight:700;line-height:1.3}}
.big{{font-size:{t['keyword_size']}px;font-weight:700;line-height:1.3;text-align:center}}
.big:first-child{{margin-top:140px}}
.kw{{color:{p['ink']}}}
.big .kw{{padding:0 .12em}}

"""


def kw_time(scene, word, after):
    text = ''.join(c for c, _ in scene['chars'])
    i = text.find(canonical(word), after)
    if i < 0:
        i = text.find(canonical(word))
    if i < 0:
        sys.exit(f'build: keyword {word!r} not found on page {scene["id"]}')
    return scene['chars'][i][1], i + 1


def marked(text, ids):
    """Caption text with [[keywords]] wrapped in spans that light up when spoken."""
    text = text.rstrip('。，；：,.;: ')
    out, pos = [], 0
    for m in re.finditer(r'\[\[(.+?)\]\]', text):
        out.append(esc(text[pos:m.start()]))
        out.append(f'<span class="kw" id="{ids.pop(0)}">{esc(m.group(1))}</span>')
        pos = m.end()
    out.append(esc(text[pos:]))
    return ''.join(out)


def width(text):
    return sum(1 if ord(c) > 127 else .55 for c in plain(text))


def split_at_comma(text, limit):
    """Break a long line at the comma nearest its middle, so a big line never leaves one character alone."""
    t = text.rstrip('。，；：,.;:')
    if width(t) <= limit:
        return [t]
    pts = [m.end() for m in re.finditer(r'[，、；：,;:]', t)]
    if not pts:
        return [t]
    cut = min(pts, key=lambda i: abs(width(t[:i]) - width(t) / 2))
    return split_at_comma(t[:cut], limit) + split_at_comma(t[cut:], limit)


def big_lines(text, size, ids, cfg):
    limit = (cfg['width'] - 120) / size - .5
    return '<br>'.join(marked(part, ids) for part in split_at_comma(text, limit))


def page_html(scene, cfg):
    start, accent_text = scene['start'], cfg['palette']['accent_text']
    cues = scene['cues']
    words = [w for c in cues for w in keywords(c['text'])]
    ids, times, after = [f'k{i}' for i in range(len(words))], [], 0
    for w in words:
        t, after = kw_time(scene, w, after)
        times.append(round(t - start, 3))
    local = [round(c['start'] - start, 3) for c in cues]
    tw, slots = [], list(ids)

    def fin(sel, t, y=26):
        tw.append(f'tl.fromTo("{sel}",{{opacity:0,y:{y}}},{{opacity:1,y:0,duration:.42,ease:"power2.out"}},{max(0, t - .08):.3f});')

    if scene['layout'] == 'title':
        opening = start == 0
        body = f'<div class="title" id="c0" style="opacity:{1 if opening else 0}">{big_lines(cues[0]["text"], cfg["text"]["title_size"], slots, cfg)}</div>'
        body += f'<div class="bar" id="bar" style="opacity:{1 if opening else 0}"></div>'
        body += ''.join(f'<div class="sub" id="c{i}" style="opacity:0">{marked(c["text"], slots)}</div>' for i, c in enumerate(cues[1:], 1))
        for i, t in enumerate(local):
            if not (i == 0 and opening):
                fin(f'#c{i}', max(.05, t) if i == 0 else t)
            if i == 0 and not opening:
                fin('#bar', max(.05, t))
    elif scene['layout'] == 'points':
        body = ''.join(f'<div class="row" id="c{i}" style="opacity:0"><div class="num">{i + 1}</div><div class="txt">{marked(c["text"], slots)}</div></div>'
                       for i, c in enumerate(cues))
        for i, t in enumerate(local):
            fin(f'#c{i}', t, 30)
            if i:
                tw.append(f'tl.to("#c{i - 1}",{{opacity:.45,duration:.3}},{t:.3f});')
    else:
        body = ''.join(f'<div class="big" id="c{i}" style="opacity:0">{big_lines(c["text"], cfg["text"]["keyword_size"], slots, cfg)}</div>' for i, c in enumerate(cues))
        for i, t in enumerate(local):
            fin(f'#c{i}', max(.05, t) if i == 0 else t)
        p = cfg['palette']
        for i, t in zip(ids, times):
            tw.append(f'tl.to("#{i}",{{backgroundColor:"{p["ink"]}",color:"{p["paper"]}",duration:.22,ease:"power2.out"}},{max(0, t - .06):.3f});')
        ids = []
    for i, t in zip(ids, times):
        tw.append(f'tl.to("#{i}",{{color:"{accent_text}",duration:.22,ease:"power2.out"}},{max(0, t - .06):.3f});')
    return f'<div class="stack">{body}</div>', tw


def caption_lines(text, cfg):
    limit = cfg['captions']['max_width_chars']
    lines = split_at_comma(plain(text), limit)
    if len(lines) > 3 or any(width(l) > limit * 1.2 for l in lines):
        sys.exit(f'caption too long to fit: {plain(text)!r}. Add a "/" in script.tsv to split it into two captions')
    return [l.strip('，、；：,;: ') for l in lines]


def srt_time(x):
    ms = round(x * 1000)
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'


def template(cid, css, body, tweens, duration, cfg):
    return f'''<template>
<style>{css}</style>
<div id="root" data-composition-id="{cid}" data-width="{cfg['width']}" data-height="{cfg['height']}" data-duration="{duration:.3f}">
{body}
</div>
<script>
(() => {{
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(tweens)}
window.__timelines = window.__timelines || {{}};
window.__timelines["{cid}"] = tl;
}})();
</script>
</template>
'''


def ensure_gsap(ep):
    dst = ep / 'assets/vendor/gsap.min.js'
    if dst.exists():
        return
    src = REPO / 'node_modules/gsap/dist/gsap.min.js'
    if not src.exists():
        print('build: installing gsap with npm (once)')
        run([exe('npm'), 'install', '--no-audit', '--no-fund'], cwd=REPO)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(src, dst)


def step_build(ep, cfg):
    if not (ep / 'work/timing.json').exists():
        sys.exit('no work/timing.json yet: run the voice step first')
    timing = timing_of(ep)
    dur, W, H, p = timing['duration'], cfg['width'], cfg['height'], cfg['palette']
    ensure_gsap(ep)
    comp = ep / 'compositions'
    if comp.exists():
        shutil.rmtree(comp)
    comp.mkdir()
    css, hosts = styles(cfg), []
    for n, s in enumerate(timing['scenes']):
        body, tw = page_html(s, cfg)
        d = s['end'] - s['start']
        (comp / f'{s["id"]}.html').write_text(template(s['id'], css, body, tw, d, cfg), encoding='utf-8')
        hosts.append(f'<div id="h-{s["id"]}" class="clip" data-composition-id="{s["id"]}" data-composition-src="compositions/{s["id"]}.html" '
                     f'data-start="{s["start"]:.3f}" data-duration="{d:.3f}" data-track-index="{1 + n % 2}" data-track-kind="graphics" '
                     f'data-width="{W}" data-height="{H}"></div>')
    cues = [c for s in timing['scenes'] for c in s['cues']]
    caps, srt = [], []
    for i, c in enumerate(cues):
        end = min(cues[i + 1]['start'] if i + 1 < len(cues) else dur, c['end'] + .45)
        lines = caption_lines(c['text'], cfg)
        caps.append(f'<div id="cap{i}" class="clip cap" data-start="{c["start"]:.3f}" data-duration="{end - c["start"]:.3f}" data-track-index="1">'
                    f'<span>{"".join(f"<b>{esc(l)}</b>" for l in lines)}</span></div>')
        srt.append(f'{i + 1}\n{srt_time(c["start"])} --> {srt_time(end)}\n' + '\n'.join(lines) + '\n')
    cc = cfg['captions']
    ccss = (f'{font_css(cfg)}#root{{position:absolute;inset:0;pointer-events:none}}'
            f'.cap{{position:absolute;left:0;right:0;top:{cc["top"]}px;text-align:center}}'
            f'.cap span{{display:inline-block;background:{p["ink"]};color:{p["paper"]};font-family:Body,sans-serif;font-weight:700;'
            f'font-size:{cc["size"]}px;padding:12px 26px;line-height:1.3}} .cap b{{display:block;font-weight:700;white-space:nowrap}}')
    (comp / 'captions.html').write_text(f'''<template>
<style>{ccss}</style>
<div id="root" data-composition-id="captions" data-width="{W}" data-height="{H}" data-duration="{dur:.3f}">
{chr(10).join(caps)}
</div>
</template>
''', encoding='utf-8')
    (ep / 'captions.srt').write_text('\n'.join(srt), encoding='utf-8')
    title = cfg.get('title') or ep.name
    (ep / 'index.html').write_text(f'''<!doctype html>
<html lang="zh-CN" data-resolution="portrait">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width={W}, height={H}" />
<title>{esc(title)}</title>
<script src="assets/vendor/gsap.min.js"></script>
<style>*{{margin:0;padding:0;box-sizing:border-box}} html,body{{width:{W}px;height:{H}px;overflow:hidden;background:{p["ground"]}}} #main{{position:absolute;inset:0;background:{p["ground"]}}}</style>
</head>
<body>
<!-- Generated by pipeline/make.py from script.tsv and work/timing.json. Edit the script or the config, not this file. -->
<div id="main" data-composition-id="main" data-start="0" data-duration="{dur:.3f}" data-width="{W}" data-height="{H}">
{chr(10).join(hosts)}
<div id="h-captions" class="clip" data-composition-id="captions" data-composition-src="compositions/captions.html" data-start="0" data-duration="{dur:.3f}" data-track-index="4" data-track-kind="captions" data-width="{W}" data-height="{H}" style="z-index:50"></div>
<audio id="mix" class="clip" src="assets/audio/mix.m4a" data-start="0" data-duration="{dur:.3f}" data-track-index="5" data-volume="1"></audio>
</div>
<script>window.__timelines = window.__timelines || {{}}; window.__timelines["main"] = gsap.timeline({{ paused: true }});</script>
</body>
</html>
''', encoding='utf-8')
    (ep / 'hyperframes.json').write_text(json.dumps({'paths': {'blocks': 'compositions', 'assets': 'assets'}}, indent=2) + '\n', encoding='utf-8')
    (ep / 'meta.json').write_text(json.dumps({'id': ep.name, 'name': ep.name}, indent=2) + '\n', encoding='utf-8')
    print(f'build: {len(timing["scenes"])} pages, {len(cues)} captions, {dur:.2f}s')


# ---------------------------------------------------------------- steps: check, render, finish

def hf(cfg):
    return [exe('npx'), '--yes', f'hyperframes@{cfg["hyperframes"]}']


def step_check(ep, cfg):
    r = run([*hf(cfg), 'check', '--json'], cwd=ep, check=False)
    try:
        report = json.loads(r.stdout[r.stdout.find('{'):])
    except ValueError:
        sys.exit(f'check: could not read the report\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}')
    (ep / 'work/check.json').write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding='utf-8')
    found = []

    def walk(x):
        if isinstance(x, dict):
            if x.get('severity') in ('error', 'warning') and (x.get('code') or x.get('rule') or x.get('message')):
                found.append(x)
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(report)
    errors = [f for f in found if f['severity'] == 'error']
    for f in found:
        print(f"  {f['severity']}: {f.get('code') or f.get('rule')}: {f.get('message', '')[:200]}")
    timing = timing_of(ep)
    shots = sorted({round((s['start'] + s['end']) / 2, 2) for s in timing['scenes']} |
                   {round(s['end'] - .35, 2) for s in timing['scenes']})
    out = ep / 'work/review'
    run([*hf(cfg), 'snapshot', '--at', ','.join(map(str, shots)), '--no-end', '-o', str(out)], cwd=ep)
    print(f'check: {len(errors)} errors, {len(found) - len(errors)} warnings; {len(shots)} frames in work/review/ (look at every one)')
    if errors:
        sys.exit(1)


def step_render(ep, cfg):
    (ep / 'renders').mkdir(exist_ok=True)
    run([*hf(cfg), 'render', '--workers', '1', '--fps', str(cfg['fps']), '-o', 'renders/master.mp4'], cwd=ep)
    print('render: renders/master.mp4')


def loudness(path):
    r = subprocess.run([exe('ffmpeg'), '-hide_banner', '-nostats', '-i', str(path), '-af', 'ebur128=peak=true', '-f', 'null', '-'],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    tail = r.stderr[r.stderr.rfind('Summary:'):]
    lufs = re.search(r'I:\s+(-?[\d.]+) LUFS', tail)
    peak = re.search(r'Peak:\s+(-?[\d.]+) dBFS', tail)
    return float(lufs.group(1)), float(peak.group(1)) if peak else None


def step_finish(ep, cfg):
    L = cfg['loudness']
    src, out = ep / 'renders/master.mp4', ep / 'output'
    if not src.exists():
        sys.exit('no renders/master.mp4 yet: run the render step first')
    out.mkdir(exist_ok=True)
    name = cfg.get('output_name') or ep.name
    final = out / f'{name}.mp4'
    timing = timing_of(ep)
    first = f'loudnorm=I={L["target_lufs"]}:TP={L["true_peak"]}:LRA={L["lra"]}'
    if timing['placeholder']:
        ffmpeg('-i', src, '-c:v', 'libx264', '-crf', 18, '-preset', 'slow', '-pix_fmt', 'yuv420p',
               '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', final)
    else:
        loudnorm(src, final, first)
    lufs, peak = loudness(final) if not timing['placeholder'] else ('n/a (silent)', 'n/a')
    finish_rest(ep, cfg, final, name, out, timing, lufs, peak)


def loudnorm(src, final, first):
    r = subprocess.run([exe('ffmpeg'), '-hide_banner', '-nostats', '-i', str(src), '-af', first + ':print_format=json', '-f', 'null', '-'],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    m = json.loads(r.stderr[r.stderr.rfind('{'):r.stderr.rfind('}') + 1])
    second = (f'{first}:measured_I={m["input_i"]}:measured_TP={m["input_tp"]}:measured_LRA={m["input_lra"]}'
              f':measured_thresh={m["input_thresh"]}:offset={m["target_offset"]}:linear=true')
    ffmpeg('-i', src, '-af', second, '-ar', RATE, '-c:v', 'libx264', '-crf', 18, '-preset', 'slow', '-pix_fmt', 'yuv420p',
           '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', final)


def finish_rest(ep, cfg, final, name, out, timing, lufs, peak):
    L = cfg['loudness']
    shutil.copy(ep / 'captions.srt', out / f'{name}.srt')
    cover = out / 'cover.png'
    with tempfile.TemporaryDirectory() as tmp:
        run([*hf(cfg), 'snapshot', '--at', str(cfg['cover_at']), '--no-end', '--keep', '-o', tmp], cwd=ep)
        shutil.copy(next(Path(tmp).glob('*.png')), cover)
    timing = timing_of(ep)
    probe = json.loads(run([exe('ffprobe'), '-v', 'error', '-show_entries', 'stream=width,height,r_frame_rate:format=duration', '-of', 'json', str(final)]).stdout)
    v = next(s for s in probe['streams'] if 'width' in s)
    lines = [f'# {name}', '', f'- file: output/{final.name} ({final.stat().st_size / 1e6:.1f} MB)',
             f'- {v["width"]}×{v["height"]}, {v["r_frame_rate"]} fps, {float(probe["format"]["duration"]):.1f} s',
             f'- loudness {lufs} LUFS, true peak {peak} dBFS (target {L["target_lufs"]})']
    if timing['placeholder']:
        lines.append('- placeholder voice: silent, timing estimated. Run the voice step without --placeholder for a real cut.')
    else:
        ffmpeg('-i', final, '-vn', '-c:a', 'libmp3lame', '-b:a', '128k', ep / 'work/final-audio.mp3')
        heard = ASR[cfg['asr']['provider']](ep / 'work/final-audio.mp3', ep / 'work/readback-final.json', cfg)
        script = ''.join(plain(c['text']) for s in timing['scenes'] for c in s['cues'])
        heard_text = ''.join(w for w, _, _ in heard)
        ratio = match_ratio(script, heard_text)
        lines.append(f'- readback: the final audio transcribes {ratio:.1%} the same as the script (work/readback-final.json)')
        sm = SequenceMatcher(None, canonical(script), canonical(heard_text), autojunk=False)
        a, b = canonical(script), canonical(heard_text)
        diffs = [f'  - script 「{a[i1:i2]}」 → heard 「{b[j1:j2]}」' for op, i1, i2, j1, j2 in sm.get_opcodes() if op != 'equal'][:30]
        if diffs:
            lines += ['- differences to listen to (homophones are usually fine; misreadings are not):', *diffs]
    lines += ['- cover: output/cover.png', f'- captions: output/{name}.srt', '',
              'Not checked by this script: how it looks on a phone, and whether anything private is on screen.']
    (out / 'report.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('\n'.join(lines))


# ---------------------------------------------------------------- entry

def new_episode(slug):
    if not re.fullmatch(r'[\w\-\u4e00-\u9fff]+', slug):
        sys.exit('episode name: letters, digits, Chinese characters, - and _ only')
    dst = REPO / 'episodes' / slug
    if dst.exists():
        sys.exit(f'{dst} already exists')
    dst.mkdir(parents=True)
    shutil.copy(REPO / 'examples/hello/script.tsv', dst / 'script.tsv')
    (dst / 'episode.json').write_text('{\n  "title": "' + slug + '"\n}\n', encoding='utf-8')
    print(f'created episodes/{slug}/ — edit script.tsv, then: python3 pipeline/make.py all episodes/{slug}')


STEPS = {'voice': step_voice, 'align': step_align, 'build': step_build, 'check': step_check,
         'render': step_render, 'finish': step_finish}


def main(argv):
    flags = {a for a in argv if a.startswith('--')}
    args = [a for a in argv if not a.startswith('--')]
    if flags - {'--placeholder'}:
        sys.exit(f'unknown option {", ".join(sorted(flags - {"--placeholder"}))}; the only option is --placeholder')
    if '--placeholder' in flags and args and args[0] not in ('voice', 'all'):
        sys.exit('--placeholder only applies to the voice and all steps')
    if len(args) != 2 or args[0] not in (*STEPS, 'all', 'new'):
        sys.exit(__doc__)
    if args[0] == 'new':
        return new_episode(args[1])
    ep = Path(args[1]).resolve()
    if not (ep / 'script.tsv').exists():
        sys.exit(f'no script.tsv in {ep}')
    (ep / 'work').mkdir(exist_ok=True)
    cfg = load_config(ep)
    placeholder = '--placeholder' in flags
    for name in (STEPS if args[0] == 'all' else [args[0]]):
        print(f'== {name}', flush=True)
        STEPS[name](ep, cfg, placeholder) if name == 'voice' else STEPS[name](ep, cfg)


if __name__ == '__main__':
    main(sys.argv[1:])
