#!/usr/bin/env python3
"""Check what this machine still needs before it can make a video.

    python3 scripts/doctor.py          human-readable checklist
    python3 scripts/doctor.py --json   the same, for an agent to read

Read-only: it runs version commands and `mmx auth status`, and never prints a key.
Each missing item names the setup page that fixes it.
"""

from pathlib import Path
import json
import os
import platform
import re
import shutil
import subprocess
import sys

REPO = Path(__file__).resolve().parent.parent


def out(cmd):
    try:
        r = subprocess.run([shutil.which(cmd[0]) or cmd[0], *cmd[1:]], capture_output=True, text=True, timeout=30)
        return r.returncode, (r.stdout + r.stderr).strip()
    except (OSError, subprocess.TimeoutExpired) as e:
        return 1, str(e)


def version(cmd, pattern=r'(\d+)\.(\d+)'):
    if not shutil.which(cmd[0]):
        return None
    code, text = out(cmd)
    m = re.search(pattern, text)
    return tuple(int(x) for x in m.groups()) if m else ()


def cjk_font():
    system = platform.system()
    if system == 'Darwin':
        return True, 'PingFang SC ships with macOS'
    if system == 'Windows':
        return True, 'Microsoft YaHei ships with Windows'
    if not shutil.which('fc-list'):
        return False, 'fc-list not found; install fontconfig and a CJK font'
    code, text = out(['fc-list', ':lang=zh', 'family'])
    return bool(text.strip()), (text.splitlines()[0] if text.strip() else 'no Chinese font installed')


def main():
    system = platform.system()
    checks = []

    def add(name, ok, detail, fix, required=True):
        checks.append({'name': name, 'ok': bool(ok), 'required': required, 'detail': detail, 'fix': fix})

    add('operating system', system in ('Darwin', 'Linux', 'Windows'),
        f'{system} {platform.release()} ({"tested" if system == "Darwin" else "should work" if system == "Linux" else "not verified yet"})',
        'setup/platforms.md')
    add('git', shutil.which('git'), shutil.which('git') or 'missing', 'setup/02-install.md')
    py = sys.version_info
    add('python >= 3.9', py >= (3, 9), f'{py.major}.{py.minor}.{py.micro}', 'setup/02-install.md#python')
    node = version(['node', '--version'])
    add('node >= 22', node and node >= (22, 0), 'missing' if node is None else 'v' + '.'.join(map(str, node)), 'setup/02-install.md#node')
    add('npm', shutil.which('npm'), shutil.which('npm') or 'missing', 'setup/02-install.md#node')
    ff = version(['ffmpeg', '-version'], r'version n?(\d+)\.(\d+)')
    add('ffmpeg + ffprobe', ff is not None and shutil.which('ffprobe'),
        'missing' if ff is None else 'ffmpeg ' + '.'.join(map(str, ff)), 'setup/02-install.md#ffmpeg')
    ok, detail = cjk_font()
    add('a Chinese font', ok, detail, 'setup/platforms.md#fonts')
    add('gsap (npm install)', (REPO / 'node_modules/gsap/dist/gsap.min.js').exists(),
        'installed' if (REPO / 'node_modules/gsap').exists() else 'run `npm install` in the repo root', 'setup/02-install.md#repo')

    mmx = shutil.which('mmx')
    add('mmx (MiniMax CLI)', mmx, mmx or 'missing', 'setup/02-install.md#mmx')
    if mmx:
        code, text = out(['mmx', 'auth', 'status', '--non-interactive'])
        add('MiniMax signed in', code == 0 and '"method"' in text,
            'signed in' if code == 0 else 'not signed in', 'setup/03-keys.md (account: setup/01-accounts.md#minimax)')
    else:
        add('MiniMax signed in', False, 'needs mmx first', 'setup/03-keys.md (account: setup/01-accounts.md#minimax)')

    agents = [a for a in ('claude', 'codex', 'qwen', 'kimi', 'opencode') if shutil.which(a)]
    add('a coding agent', agents, ', '.join(agents) or 'none found on PATH (fine if you run one elsewhere)',
        'setup/00-agent.md', required=False)
    gem = bool(os.environ.get('GEMINI_API_KEY'))
    if not gem and system == 'Darwin':
        gem = out(['security', 'find-generic-password', '-s', 'apikey/gemini'])[0] == 0
    if not gem and system == 'Linux' and shutil.which('secret-tool'):
        code, text = out(['secret-tool', 'lookup', 'service', 'apikey/gemini'])
        gem = code == 0 and bool(text)
    add('Gemini key (optional, for Lyria music)', gem, 'found' if gem else 'not set; music is optional',
        'setup/01-accounts.md#music-optional', required=False)

    missing = [c for c in checks if c['required'] and not c['ok']]
    if '--json' in sys.argv:
        print(json.dumps({'ready': not missing, 'checks': checks}, ensure_ascii=False, indent=1))
        return
    for c in checks:
        mark = 'ok ' if c['ok'] else ('-- ' if not c['required'] else 'NO ')
        print(f'{mark} {c["name"]}: {c["detail"]}' + ('' if c['ok'] else f'   → {c["fix"]}'))
    print()
    if missing:
        print(f'{len(missing)} required item(s) missing. Fix them in order, then run this again.')
    else:
        py = 'python' if system == 'Windows' else 'python3'
        print(f'Ready. Next: {py} pipeline/make.py new hello, then {py} pipeline/make.py all episodes/hello --placeholder')
    sys.exit(1 if missing else 0)


if __name__ == '__main__':
    main()
