# 跨 Agent 使用

本 skill 的核心入口是 `SKILL.md`，配套脚本使用 Python 标准库，阅读器是离线 HTML。没有专属模型 API、宿主 SDK、固定 MCP 服务或必须存在的 Codex 工具名。`agents/openai.yaml` 只提供可选界面元数据。

## 用当前宿主的工具完成相同动作

|动作|接入要求|
|---|---|
|加载规范|读取当前安装位置的SKILL.md及其相对参考文件，不依赖某种命令前缀|
|读论文与原图|使用宿主实际可用的PDF/文本和图像读取工具；内容不可见时说明范围|
|生成阅读页|能运行Python并写出文件；从当前skill根目录调用scripts/build.py|
|公式检查|有Node.js则运行check_math.py；没有时记录语法检查未执行，保留LaTeX，不伪称已检查|
|打开结果|有页面打开工具就使用；否则给出生成文件路径，让用户自行打开|

不要把 `$paper-to-course`、`/paper-to-course` 或某个品牌工具名当成唯一调用方式。它们只是不同客户端的入口。使用相对资源时，先确定当前 skill 安装根目录；执行命令时正确引用含空格的路径。

## 无原生 Skills 加载器的 Agent

将完整文件夹保存在该Agent能访问的位置，请它先读 `paper-to-course/SKILL.md`，再按需要读references和运行scripts。自定义Agent可将该文件设为按需任务指令，继续使用相同资源，不必复制成另一套提示词。只有纯聊天、不能访问文件/运行工具的环境，无法仅靠安装包获得完整HTML生成能力；此时按正文规则交付有限文字版。

安装目录由宿主决定。解压包内可运行 `python scripts/install.py --to "目标skills目录"`，把完整skill复制到目标；已有安装默认保留，显式`--replace`会先备份。该脚本不替用户修改其他全局配置，也不购买或配置模型API。
