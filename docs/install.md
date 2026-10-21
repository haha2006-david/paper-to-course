# 跨 Agent 安装

## 一条命令安装

安装 Node.js 后，在终端运行：

```bash
npx skills add haha2006-david/paper-to-course --skill paper-to-course -g
```

选择你使用的 Agent，按提示完成安装，再让 Agent 使用 `paper-to-course` 处理 PDF。如果暂未发现新技能，按宿主的方式刷新技能或重新打开会话。

安装使用开源 [Skills CLI](https://github.com/vercel-labs/skills)。支持的 Agent 和安装路径由其维护，见[完整名单](https://github.com/vercel-labs/skills/blob/main/docs/agents.md)。技能本身不绑定模型服务商。

指定 Agent 示例：

```bash
npx skills add haha2006-david/paper-to-course --skill paper-to-course -g --agent claude-code cursor codex
```

安装到 CLI 支持的全部 Agent：

```bash
npx skills add haha2006-david/paper-to-course --skill paper-to-course -g --agent '*'
```

去掉 `-g` 可安装到当前项目；加上 `--copy` 可使用文件副本代替符号链接。更多选项见[官方命令说明](https://github.com/vercel-labs/skills/blob/main/docs/commands.md)。

## 不用 Node / 指定安装目录

[下载 ZIP](https://github.com/haha2006-david/paper-to-course/raw/refs/heads/main/downloads/paper-to-course.zip)，解压后把完整的 `paper-to-course` 文件夹放进 Agent 的 skills 目录即可。目录中应保留 `SKILL.md`、`scripts`、`references`、`templates` 等全部文件。

也可在解压后的上级目录运行（需要 Python 3.10+）：

```bash
python paper-to-course/scripts/install.py --to "/path/to/agent/skills"
```

将 `/path/to/agent/skills` 替换为你的真实 skills 目录。脚本会创建其中的 `paper-to-course` 文件夹。已有安装默认不覆盖；加 `--replace` 会先将旧版保留为旁边的备份目录。`--dry-run` 只显示目标，不写文件。

## 自定义 Agent / 没有原生 Skills 入口

把完整文件夹放在 Agent 可访问的位置，然后发送（替换为实际路径）：

```text
先读取 /path/to/paper-to-course/SKILL.md，
按其中的工作流与相对参考文件，帮我理解上传的论文。
用当前环境可用的工具读取 PDF、查看原图、运行脚本并生成阅读页。
```

开发者可将 `SKILL.md` 作为按需加载的任务指令入口。工具映射见[宿主接入说明](../paper-to-course/references/portability.md)，无需为每个 Agent 改写一套解读方法。

## 环境与验证范围

完整 HTML 输出需要 Agent 能访问 PDF/原图、执行 Python 3.10+ 并写出文件；公式语法检查使用 Node.js。无需单独配置模型 API，解读使用 Agent 自身的模型能力与额度。纯聊天且没有文件与执行工具的环境，只能交付有限文字版。

2026-10-21 的安装验证：使用 Skills CLI 1.7.4 在隔离项目中向 Claude Code、Cursor、Codex、Gemini CLI、OpenCode、GitHub Copilot、Windsurf、Trae 的目录安装，核对完整技能文件。Python 自定义目录安装另有复制完整性、备份、预览与防止自身复制测试。

上述验证检查的是安装与文件完整性。实际论文解读和阅读页目前主要在 Codex 中使用与检查，其他 Agent 尚未逐一运行完整论文任务；内容质量仍取决于宿主模型及可用工具。
