# 中国大陆路线（不需要翻墙）

本页列出需要翻墙的环节和对应的国产替代，2026-11-26 核实。价格和模型名经常变，付钱之前打开链接看当天的页面。

| 环节 | 海外路线 | 大陆路线（推荐） | 备选 |
| --- | --- | --- | --- |
| Agent 背后的模型 | Claude / ChatGPT 订阅 | Claude Code 接 MiniMax（M Plan），和配音共用一个账号 | 智谱 GLM Coding Plan、Kimi Code、DeepSeek 按量付费 |
| Agent 程序本身 | Claude Code / Codex | Claude Code（从 npm 国内镜像安装） | Qwen Code、Kimi Code CLI、腾讯 CodeBuddy Code |
| 配音、转写 | MiniMax 国际站 | MiniMax 国内站，本来就是国产 | — |
| 配乐 | Google Lyria | 发布时在抖音里选曲库音乐 | 火山引擎「生成纯音乐」、Mureka |
| 安装包下载 | 官方源 | 国内镜像（见下文） | — |

## <a id="镜像"></a>1. 先换镜像

npm（Node 的包）：

```bash
npm config set registry https://registry.npmmirror.com
```

pip（只有可选的配乐脚本需要）：

```bash
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

Homebrew（macOS）：按中科大镜像的说明设置，<https://mirrors.ustc.edu.cn/help/brew.git.html>。

## 2. 推荐：Claude Code + MiniMax

好处是一个 MiniMax 账号同时管 Agent 的模型和视频配音，只开一个账号、付一份钱。

1. 在 <https://platform.minimaxi.com> 注册，开通 M Plan（<https://www.minimax.cn/m-plan>，每档都含语音），或者先按量充值。
2. 装 Node 22 以上（见 [02-install.md](02-install.md#node)），然后从国内镜像装 Claude Code 和 MiniMax 命令行：

   ```bash
   npm install -g @anthropic-ai/claude-code mmx-cli
   ```

3. 让 MiniMax 命令行替你把 Claude Code 接到 MiniMax 的模型上。下面这条由你自己在终端里运行，按提示填 MiniMax 的 API key。key 只填在终端提示里，不要发给 Agent。注意订阅（M Plan）的 key 和按量付费的 key 不通用，用你买的那种：

   ```bash
   mmx agent setup --agent claude-code --region cn
   ```

   如果它没有提示你输入 key，或者你想手动配置，看 MiniMax 官方说明：<https://platform.minimaxi.com/docs/m-plan/claude-code.md>。原理是在 `~/.claude/settings.json` 的 `env` 里设置 `ANTHROPIC_BASE_URL`（国内站为 `https://api.minimax.cn/anthropic`）、`ANTHROPIC_AUTH_TOKEN` 和模型名。

4. 登录配音用的命令行（同一个账号）：

   ```bash
   mmx auth login --recommend --region=cn
   ```

5. 进入本仓库文件夹，运行 `claude`，对它说：「读 AGENTS.md，帮我把这台电脑配置好，装东西之前先问我。」

注意：接国产模型的 Claude Code 不经过 Anthropic，Anthropic 账号相关的功能（例如远程控制）不可用，做视频用不到这些。

## 3. 其他可选模型

都可以接 Claude Code，做法相同：在 `~/.claude/settings.json` 的 `env` 里填对方给的地址、key 和模型名。各家都有一页「在 Claude Code 中使用」的官方说明，按它填。

| 厂商 | 接入地址（`ANTHROPIC_BASE_URL`） | 官方说明 | 购买 |
| --- | --- | --- | --- |
| 智谱 GLM | `https://open.bigmodel.cn/api/anthropic` | <https://docs.bigmodel.cn/cn/coding-plan/tool/claude> | GLM Coding Plan：<https://www.bigmodel.cn/glm-coding> |
| Kimi（会员） | `https://api.kimi.com/coding/` | <https://www.kimi.com/code/docs/third-party-tools/claude-code.html> | Kimi Code 会员：<https://www.kimi.com/resources/coding-plan> |
| Kimi（按量） | `https://api.moonshot.cn/anthropic` | <https://platform.kimi.com/docs/guide/claude-code-kimi.md> | <https://platform.kimi.com/console/api-keys> |
| DeepSeek（按量） | `https://api.deepseek.com/anthropic` | <https://api-docs.deepseek.com/quick_start/agent_integrations/claude_code> | <https://api-docs.deepseek.com/quick_start/pricing> |
| 阿里百炼 Coding Plan | `https://coding.dashscope.aliyuncs.com/apps/anthropic` | <https://help.aliyun.com/zh/model-studio/coding-plan-overview> | 同左 |

选了这些模型，配音仍然要单独开一个 MiniMax 账号（按量付费就够）。

## 4. 不用 Claude Code 也行

本仓库对 Agent 只有一个要求：能读写这个文件夹里的文件、能运行命令。国产的命令行 Agent 都满足：

- Qwen Code：<https://github.com/QwenLM/qwen-code>，`npm install -g @qwen-code/qwen-code@latest`，启动后用 `/auth` 登录。它默认读 `QWEN.md`，本仓库的 `QWEN.md` 会让它去读 `AGENTS.md`。
- Kimi Code CLI：<https://www.kimi.com/code/docs/en/>，`npm install -g @moonshot-ai/kimi-code`，启动后用 `/login` 登录。会读 `AGENTS.md`。
- 腾讯 CodeBuddy Code：<https://www.codebuddy.cn/docs/cli/installation>，`npm install -g @tencent-ai/codebuddy-code`。

这些 Agent 没有在本仓库里完整跑过一遍。它们读到 `AGENTS.md` 后应该能照做；遇到不一样的地方，让它把改动记进 `rules/rules.md`。

## <a id="配乐"></a>5. 配乐

- **推荐：发布时在抖音里选音乐。** 流水线默认只出人声版，你在抖音发布页从曲库里挑一首，平台已经处理好版权，不花钱。
- **火山引擎「生成纯音乐」（GenBGM）**：只出纯音乐，30 到 120 秒，按秒计费。文档 <https://docs.volcengine.com/docs/84992/2100970>。需要火山引擎账号和实名认证，个人用户没有免费试用。流水线里还没有对接，需要时让 Agent 参照 `pipeline/music_lyria.py` 写一个，生成的文件填进 `music.file`。
- **Mureka（昆仑万维）**：有公开 API 和纯音乐接口，<https://platform.mureka.ai/docs/>。价格和国内站情况没有核实。
- MiniMax 的音乐模型 2026-08-20 起不再对新用户开放，阿里百炼的 Fun-Music 目前是邀测，这两个都不推荐。
