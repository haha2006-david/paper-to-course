# 论文补给站 · Paper to Course

**把论文变成易理解的阅读页：概念 → 方法链 → 原图与证据 → 自测 → 复习卡。**

适合跨专业读论文、刚进入新方向的研究生。配合支持 Agent Skills 的 AI 助手使用，生成可离线打开的 HTML。

![暗金阅读器界面示意](docs/preview.svg)

## 你会得到什么

|读懂|自测|复习卡|
|---|---|---|
|讲清概念、创新和方法，对照论文原图理解证据与局限|用易混淆选项检查理解，答后看解析|留下问题、方法、证据和边界，支持保存图片|

## 安装

[下载 ZIP](https://github.com/haha2006-david/paper-to-course/raw/refs/heads/main/downloads/paper-to-course.zip)，解压后将完整的 `paper-to-course` 文件夹放入对应目录：

|工具|用户级 skills 目录|
|---|---|
|[Codex](https://learn.chatgpt.com/docs/build-skills)|`~/.agents/skills/`|
|[Claude Code](https://code.claude.com/docs/en/skills)|`~/.claude/skills/`|
|[Cursor](https://cursor.com/help/customization/skills)|`~/.cursor/skills/`|

目前主要在 Codex 中验证；Claude Code、Cursor 官方支持该技能格式，本项目完整流程仍待实测。宿主需具备 PDF 读取、Python 执行和文件生成能力。

## 使用

上传 PDF，发送：

```text
请使用 paper-to-course 帮我理解这篇论文。
```

也可直接调用：Codex 用 `$paper-to-course`，Claude Code / Cursor 用 `/paper-to-course`。

**批量上传 n 篇，就能从这 n 篇里选择阅读。** 各批次分开保存，每篇都有独立自测记录。

解读使用宿主 AI 的模型能力与额度；脚本负责排版。材料缺失会注明，正式引用与复现仍需核对原文。

---

[详细说明](docs/guide.md) · [下载文字演示](https://github.com/haha2006-david/paper-to-course/raw/refs/heads/main/demo/deep-compression.html) · [反馈问题](https://github.com/haha2006-david/paper-to-course/issues) · [MIT License](LICENSE)
