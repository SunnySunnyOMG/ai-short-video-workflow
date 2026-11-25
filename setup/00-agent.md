# 0. Get an agent running

Everything after this page can be done by a coding agent: a program that runs on your computer, reads and writes files, runs commands and talks to a large model. This page is the only part a person may have to do by hand. If you already have one of these agents working, skip to the last section.

Facts on this page were checked on 2026-11-26. Prices and plan names change; follow the links.

## Pick a route

| | Global route | China route (no VPN) |
| --- | --- | --- |
| Who | Your network reaches Anthropic or OpenAI, and you are in a country they serve | Mainland China, or you would rather pay a domestic provider |
| Agent | Claude Code with a Claude plan, or Codex with a ChatGPT plan | Claude Code connected to a domestic model, or a domestic agent CLI |
| Details | Below | [china.md](china.md) |

Both routes use the same pipeline. Only the model behind the agent and the optional music source differ.

## Global route

### Claude Code (what this repo was built with)

1. A plan that includes Claude Code: Pro, Max or higher, or an Anthropic Console (API) account. The free plan does not include it. Pricing: <https://claude.com/pricing>. Anthropic serves only the countries on <https://www.anthropic.com/supported-countries> (mainland China and Hong Kong are not on it).
2. Install (docs: <https://code.claude.com/docs/en/setup>):

   macOS, Linux, WSL:
   ```bash
   curl -fsSL https://claude.ai/install.sh | bash
   ```
   Windows PowerShell:
   ```powershell
   irm https://claude.ai/install.ps1 | iex
   ```
   Or `brew install --cask claude-code`, or `winget install Anthropic.ClaudeCode`.
3. In a terminal, go to this repo's folder and run `claude`. The first run opens the browser to sign in.

### Codex

1. A ChatGPT plan that includes Codex, or an OpenAI API key. Plan details: <https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan>.
2. Install (<https://github.com/openai/codex>): `npm install -g @openai/codex` (needs Node, see [02-install.md](02-install.md#node)), or `brew install --cask codex`.
3. Run `codex` in this repo's folder and sign in.

## Once the agent runs

Open the agent in this repo's folder and say (in any language):

> Read AGENTS.md and set up this machine to make videos. Ask me before installing anything, and tell me exactly what I need to sign up for.

The agent reads [AGENTS.md](../AGENTS.md), runs `scripts/doctor.py`, and walks you through the rest: [accounts](01-accounts.md), [installs](02-install.md), [keys](03-keys.md), and a test video.

If you use an agent this repo does not name, it only needs to be able to read files and run commands in this folder. Point it at `AGENTS.md`.
