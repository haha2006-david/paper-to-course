# 论文补给站 · Paper to Course

**把论文变成易理解的阅读页：概念 → 方法链 → 原图与证据 → 自测 → 复习卡。**

适合跨专业读论文、刚进入新方向的研究生。配合支持 Agent Skills 的 AI 助手使用，生成可离线打开的 HTML。

![暗金阅读器界面示意](docs/preview.svg)

## 你会得到什么

|读懂|自测|复习卡|
|---|---|---|
|讲清概念、创新和方法，对照论文原图理解证据与局限|用易混淆选项检查理解，答后看解析|留下问题、方法、证据和边界，支持保存图片|

## 安装

在终端运行，选择你使用的 Agent：

```bash
npx skills add haha2006-david/paper-to-course --skill paper-to-course -g
```

通过 [Skills CLI](https://github.com/vercel-labs/skills) 安装到 Claude Code、Codex、Cursor、Gemini CLI、OpenCode、GitHub Copilot、Windsurf、Trae 等 Agent。需要 Node.js；无 Node 或自定义 Agent 可用 [ZIP / Python 安装方式](docs/install.md)。

完整阅读页需要 Agent 能读取 PDF、运行 Python、生成文件。安装兼容性与各宿主的解读效果分开验证，见[安装与验证范围](docs/install.md)。

## 使用

上传 PDF，发送：

```text
请使用 paper-to-course 帮我理解这篇论文。
```

也可按所用 Agent 的技能调用方式启动。

**批量上传 n 篇，就能从这 n 篇里选择阅读。** 各批次分开保存，每篇都有独立自测记录。

解读使用宿主 AI 的模型能力与额度；脚本负责排版。材料缺失会注明，正式引用与复现仍需核对原文。

---

[详细说明](docs/guide.md) · [下载文字演示](https://github.com/haha2006-david/paper-to-course/raw/refs/heads/main/demo/deep-compression.html) · [反馈问题](https://github.com/haha2006-david/paper-to-course/issues) · [MIT License](LICENSE)
