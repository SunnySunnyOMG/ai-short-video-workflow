# 中国大陆路线（不需要翻墙）

本页列出需要翻墙的环节和对应的国产替代，2026-11-26 核实。价格和模型名经常变，付钱之前打开链接看当天的页面。

| 环节 | 海外路线 | 大陆路线（推荐） | 备选 |
| --- | --- | --- | --- |
| Agent 背后的模型 | Claude / ChatGPT 订阅 | Claude Code 接 MiniMax（M Plan），和配音共用一个账号 | 智谱 GLM Coding Plan、Kimi Code、DeepSeek 按量付费 |
| Agent 程序本身 | Claude Code / Codex | Claude Code（从 npm 国内镜像安装） | Qwen Code、Kimi Code CLI、腾讯 CodeBuddy Code |
| 配音、转写 | MiniMax 国际站 | MiniMax 国内站，本来就是国产 | — |
| 配乐 | Google Lyria | 发布时在抖音里选曲库音乐 | 火山引擎「生成纯音乐」、Mureka |
| 安装包下载 | 官方源 | 国内镜像（见下文） | — |
| 渲染用的浏览器 | HyperFrames 自动下载 Chrome | 先自己装好 Chrome 或 Edge | — |

## <a id="镜像"></a>1. 先换镜像

npm（Node 的包）：

```bash
npm config set registry https://registry.npmmirror.com
```

Homebrew（macOS）：按中科大镜像的说明设置，<https://mirrors.ustc.edu.cn/help/brew.git.html>。

GitHub：`git clone` 卡住时，在仓库页面点 Code → Download ZIP 下载解压，效果一样。

## 2. 先装好浏览器

渲染视频用的 HyperFrames 要用 Chrome。电脑上已经有 Chrome 或 Edge，它会自己找到；没有的话，它会去谷歌的服务器下载，在国内通常下不动。所以先装一个：

- Chrome：<https://www.google.cn/chrome/>
- 或 Edge（Windows 自带）：<https://www.microsoft.com/edge>

如果渲染时仍然提示找不到浏览器（`chrome_not_found`），把浏览器程序的完整路径设到环境变量 `HYPERFRAMES_BROWSER_PATH`。macOS 上 Chrome 的路径是 `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`。这一步还没有在国内网络下实测过，遇到问题让 Agent 把解决办法记进 `rules/rules.md`。

## 3. 推荐：Claude Code + MiniMax

好处是一个 MiniMax 账号同时管 Agent 的模型和视频配音，只开一个账号、付一份钱。

1. 在 <https://platform.minimaxi.com> 注册，开通 M Plan（<https://www.minimax.cn/m-plan>，每档都含语音），或者先按量充值。
2. 装 Node 22 以上（见 [02-install.md](02-install.md#node)），然后从国内镜像装 Claude Code 和 MiniMax 命令行：

   ```bash
   npm install -g @anthropic-ai/claude-code mmx-cli
   ```

3. 把 Claude Code 接到 MiniMax 的模型上。照 MiniMax 官方说明做：<https://platform.minimaxi.com/docs/m-plan/claude-code.md>。做法是由你自己打开用户目录下的 `~/.claude/settings.json`，在 `env` 里填三样东西：`ANTHROPIC_BASE_URL`（国内站是 `https://api.minimax.cn/anthropic`）、`ANTHROPIC_AUTH_TOKEN`（你的 MiniMax key）和官方说明里写的模型名。key 只写在这个文件里，不要发给 Agent，也不要放进本仓库。订阅（M Plan）的 key 以 `sk-cp` 开头，和按量付费的 key 不通用。

   MiniMax 命令行也有一个自动配置命令 `mmx agent setup --agent claude-code --region cn`。它在没给 key 时会沿用已有的配置、不一定提示你输入，所以第一次配置建议按上面的官方说明手动填。

4. 登录配音用的命令行（同一个账号）：

   ```bash
   mmx auth login --recommend --region=cn
   ```

5. 进入本仓库文件夹，运行 `claude`，对它说：「读 AGENTS.md，帮我把这台电脑配置好，装东西之前先问我。」

注意：接国产模型的 Claude Code 不经过 Anthropic，Anthropic 账号相关的功能（例如远程控制）不可用，做视频用不到这些。

## 4. 其他可选模型

都可以接 Claude Code，做法相同：在 `~/.claude/settings.json` 的 `env` 里填对方给的地址、key 和模型名。各家都有一页「在 Claude Code 中使用」的官方说明，按它填。

| 厂商 | 接入地址（`ANTHROPIC_BASE_URL`） | 官方说明 | 购买 |
| --- | --- | --- | --- |
| 智谱 GLM | `https://open.bigmodel.cn/api/anthropic` | <https://docs.bigmodel.cn/cn/coding-plan/tool/claude> | GLM Coding Plan：<https://www.bigmodel.cn/glm-coding> |
| Kimi（会员） | `https://api.kimi.com/coding/` | <https://www.kimi.com/code/docs/third-party-tools/claude-code.html> | Kimi Code 会员：<https://www.kimi.com/resources/coding-plan> |
| Kimi（按量） | `https://api.moonshot.cn/anthropic` | <https://platform.kimi.com/docs/guide/claude-code-kimi.md> | <https://platform.kimi.com/console/api-keys> |
| DeepSeek（按量） | `https://api.deepseek.com/anthropic` | <https://api-docs.deepseek.com/quick_start/agent_integrations/claude_code> | <https://api-docs.deepseek.com/quick_start/pricing> |
| 阿里百炼 Coding Plan | `https://coding.dashscope.aliyuncs.com/apps/anthropic` | <https://help.aliyun.com/zh/model-studio/coding-plan-overview> | 同左 |

选了这些模型，配音仍然要单独开一个 MiniMax 账号（按量付费就够）。

## 5. 不用 Claude Code 也行

本仓库对 Agent 只有一个要求：能读写这个文件夹里的文件、能运行命令。国产的命令行 Agent 都满足：

- Qwen Code：<https://github.com/QwenLM/qwen-code>，`npm install -g @qwen-code/qwen-code@latest`，启动后用 `/auth` 登录。它默认读 `QWEN.md`，本仓库的 `QWEN.md` 会让它去读 `AGENTS.md`。
- Kimi Code CLI：<https://www.kimi.com/code/docs/en/>，`npm install -g @moonshot-ai/kimi-code`，登录方式见官方文档。
- 腾讯 CodeBuddy Code：<https://www.codebuddy.cn/docs/cli/installation>，`npm install -g @tencent-ai/codebuddy-code`。

这些 Agent 没有在本仓库里完整跑过一遍。它们读到 `AGENTS.md` 后应该能照做；遇到不一样的地方，让它把改动记进 `rules/rules.md`。

## <a id="配乐"></a>6. 配乐

- **推荐：发布时在抖音里选音乐。** 流水线默认只出人声版，你在抖音发布页从曲库里挑一首，平台已经处理好版权，不花钱。
- **火山引擎「生成纯音乐」（GenBGM）**：据官方文档，只出纯音乐，单段 30 到 120 秒，按秒计费，免费试用只面向企业。文档 <https://docs.volcengine.com/docs/84992/2100970>。需要火山引擎账号和实名认证。流水线里还没有对接，需要时让 Agent 参照 `pipeline/music_lyria.py` 写一个，生成的文件填进 `music.file`。
- **Mureka（昆仑万维）**：有公开 API 和纯音乐接口，<https://platform.mureka.ai/docs/>。价格和国内站情况没有核实。
- 不推荐：MiniMax 的音乐模型，据其价格页 2026-08-20 起不再对新用户开放（<https://platform.minimax.cn/docs/guides/pricing>）；阿里百炼的 Fun-Music，据其文档目前是邀测（<https://help.aliyun.com/zh/model-studio/fun-music-api>）。
