# 3. Keys and sign-ins

Rule for agents: the owner types or pastes secrets only into the tool that stores them, in their own terminal or browser. Never into the chat, never into a file in this repo, never as a command-line argument you run (it lands in shell history and process lists).

## MiniMax (voice and transcription): sign in with the browser

The owner runs this in their own terminal:

```bash
mmx auth login --recommend --region=cn
```

Use `--region=global` for an international (minimax.io) account. A browser window opens; after approving, `mmx` keeps the session in its own config (`~/.mmx/`). Check with:

```bash
mmx auth status
```

If the owner prefers an API key over browser sign-in, they run `mmx auth login` and choose the API-key option at the prompt. Do not suggest `mmx auth login --api-key <key>`: the key would be saved in shell history.

## The agent's model key (only for the China route)

Some routes in `setup/china.md` give Claude Code a domestic model through environment variables. The owner puts the key in their own shell profile or in the agent's settings file in their home folder (for Claude Code, `~/.claude/settings.json` under `"env"`), never in this repo. The page for each provider shows where.

## Gemini (optional, for Lyria music)

`pipeline/music_lyria.py` looks for the key in this order:

1. the environment variable `GEMINI_API_KEY`;
2. macOS Keychain, item `apikey/gemini`;
3. Linux Secret Service (`secret-tool`), service `apikey/gemini`.

macOS, owner runs (it prompts for the key without echoing it):

```bash
security add-generic-password -a "$USER" -s apikey/gemini -w
```

Linux with a desktop keyring:

```bash
secret-tool store --label="Gemini API key" service apikey/gemini
```

Windows (not verified): set a user environment variable `GEMINI_API_KEY` in System Properties → Environment Variables, then open a new terminal.

## What never goes in the repo

`.env` files, keys, tokens, cookies, account names, and screenshots that show any of them. `.gitignore` blocks `.env` and `*.key`, but check `git status` before every commit anyway.
