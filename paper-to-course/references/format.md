# 单文件讲义格式

把 JSON 作为 UTF-8 文件交给 `scripts/build.py`。所有内容字段不写HTML；可写LaTeX数学定界符，显示时由内置KaTeX排版。新讲义使用 `schema_version: 2`；生成器兼容旧版 1。下面展示基础字段；v2 的额外要求在末尾，不能省略。

```json
{
  "schema_version": 1,
  "paper": {
    "id": "stable-paper-id-version",
    "title": "真实题名",
    "subtitle": "面向读者的一句话学习目标",
    "url": "https://example.org/paper",
    "coverage": "全文 / 摘要 / 已读章节；写清版本及缺失内容",
    "audience": "跨专业研究生"
  },
  "intro": "论文解决什么、作者关键动作、结果与适用范围。",
  "prerequisites": [
    {"term": "术语（English）", "explanation": "背景知识：定义与小例子。"}
  ],
  "lessons": [
    {
      "id": "mechanism",
      "title": "作者到底改了什么",
      "body": "解释因果链或论证链。",
      "example": "教学例子，非论文实验：具体输入、操作、输出。",
      "caution": "这个例子或类比省略了什么。",
      "source_ids": ["s1"]
    }
  ],
  "sources": [
    {"id": "s1", "label": "方法", "locator": "§3.2 / PDF p.4 / Eq.1",
     "url": "https://example.org/paper#section3", "note": "该位置支持的要点，用自己的话简述。"}
  ],
  "evidence": [
    {"claim": "一个结论", "observation": "实际观察及比较条件",
     "boundary": "不能外推什么；标清作者报告还是读者推断。", "source_ids": ["s1"]}
  ],
  "questions": [
    {"id": "q1", "prompt": "理解题", "choices": ["选项甲", "选项乙", "选项丙"],
     "answer": 0, "explanation": "为何正确，以及常见错因。", "source_ids": ["s1"]}
  ],
  "teach_back": {"prompt": "请用自己的话解释……", "checkpoints": ["要点一", "要点二"]},
  "recap": {"problem": "问题", "move": "关键动作", "evidence": "最强证据", "boundary": "边界", "tomorrow": "明天先回忆这个问题"}
}
```

数组数量服从重点覆盖，不能为控制长度遗漏主要任务、核心结果或重要负结果。所有 `source_ids` 必须解析；对尚未核验的背景明确用空数组。`answer` 为从 0 开始的下标。只允许 http/https 来源链接；本地 PDF 路径写在 coverage，url 可为空。生成器不验证链接可达性或事实真实性。

当前阅读顺序是核心定位 → 必要概念卡 → 方法/例子/对应原图 → 结果证据与边界。概念卡同时显示explanation与role，紧贴首次使用；lessons.example现在实际显示，不再是被渲染器忽略的字段。无需例子时可省略example或使用空字符串，不能每个段落硬凑例子。构造的例子在文字中标“教学例子，非论文实验”；直接取自论文的例子标原文位置。

lesson可选增加`steps: [{"label": "输入", "text": "实际输入什么"}, {"label": "关键操作", "text": "改变什么、输出什么"}]`，至少两步；用于讲清信息流或对照，别与body重复。可选`formula`、`formula_note`让必需公式与符号解释显示在该lesson内。公式与overview只放一处，不重复。

分支并行时加`step_layout: "parallel"`（默认sequence），并用可选`output`短句写明如何汇合、得到什么。输出实际进入正文、字数核查与Markdown导出；不要用装饰箭头暗示不存在的先后关系。默认深炭灰/暗金界面，装饰图案仅作背景，不承载科学含义。完整来源的paper.coverage留在内部数据和导出记录；access非full时在页头显示资料缺口。

`intro` 与 `paper.subtitle` 同样需要人工回看原文。背景知识、教学例子、读者推断均在文字中显式标识。`source.note` 是简短释义，不复制受版权保护的大段原文。不要分发原 PDF，除非有相应授权。

## schema v2 新增的必填字段

设置 `schema_version: 2`，保留上述基础结构，额外加入：

```json
{
  "paper": {"access": "full"},
  "conclusions": [{"text": "可独立阅读的核心结论；保留限定条件", "source_ids": ["s1"]}],
  "coverage_audit": [
    {"topic": "problem", "status": "covered", "note": "讲义交代了哪些重点及缺口", "source_ids": ["s1"]},
    {"topic": "method", "status": "covered", "note": "方法全流程与核心变化", "source_ids": ["s1"]},
    {"topic": "results", "status": "partial", "note": "缺少原图，影响哪些结论", "source_ids": ["s1"]},
    {"topic": "robustness", "status": "unavailable", "note": "未取得附件", "source_ids": []},
    {"topic": "conclusions", "status": "covered", "note": "核心结论与推断区分", "source_ids": ["s1"]},
    {"topic": "limitations", "status": "partial", "note": "作者局限与读者推断", "source_ids": ["s1"]},
    {"topic": "use", "status": "covered", "note": "用途与回原文位置", "source_ids": ["s1"]}
  ],
  "return_to_original": ["复现时看 §5 的配置与预处理；引用结果时核对 Table 2 的条件。"]
}
```

注意：以上 `paper` 只是新增字段示意，实际对象必须同时保留基础字段。access 为 full / partial / abstract。coverage_audit 七个 topic 各一次，状态为 covered / partial / unavailable / not_applicable，后两者须写原因；不是七项都强行写已覆盖，更不输出整体正确率。

每个 source 额外含 `kind: primary|background` 及 `authority`（来源书名/作者/机构或原论文；不是笼统“权威来源”）。每个 prerequisite 额外含 `role`（本文作用）、`source_ids` 及 `verification: verified|paper_defined|unverified`。verified 表示该解释已对照所列外部来源，paper_defined 仅表示所列原论文本身有此定义；unverified 必须清楚标注并用空 source_ids，不能伪造引用。

复用已有`source_map.json`时，source可选加`block_ids: ["S021"]`与`pdf_pages: [7]`。后者是正整数PDF页序号，不是印刷页码；没有可靠页码则省略。用`audit_brief.py --source-map`检查锚点连接，不把这些元数据当成事实核查；具体流程见[quality.md](quality.md)。旧讲义不必为此补造source map。

背景解释用准确短句讲定义，role说明本文作用；必要才加例子。lessons只保留建立理解所需的方法和实验设置，避免扩成术语百科；evidence覆盖所有主要结果、关键消融和反证。来源与数字冲突须显式放入相应body/observation/boundary。

## 可选的图解（兼容 schema v2）

顶层增加 `figures` 数组，每张图包含 `id,title,kind,image,alt,caption,reading,boundary,source_ids`。kind 为 original（原文图/表）、teaching（教学示意）或 redrawn_data（按原始数值重绘）。image 必须为完整 `data:image/png;base64,...`；不接收远程地址、SVG 或模型虚构的文件路径。caption 写清出处/教学性质与条件，reading 解释读图顺序，boundary 交代简化和推断边界。原图和重绘数据图须引用 primary 来源。

在相应 lesson 或 evidence 加 `figure_ids: ["图id"]`，每张图必须有位置。单图上限约 9MB 编码前数据，总图像数据最多20MB，宽高各不超过10000、总像素不超过3500万。渲染器检查格式与定位，不证明图像内容准确；制作时必须实际查看。默认无需生成图；需要时从原 PDF 提取或制作后内嵌，不让语言模型输出大段臆造 base64。

`collapsed`仅保留旧数据兼容，当前阅读器直接显示原图／原表，支持放大与保存。

## 默认简版与公式

新讲义保留顶层`overview`，含`question,method,result,boundary,source_ids`。question写一句核心问题/判断，result用短句说明本篇核心新意；method为内部兼容字段，真正的方法需在lesson中讲懂；boundary为结尾适用限制。整篇实际文字通常约400–700中文字，包含概念、例子、步骤、公式释义与图导读；按理解难度调整，不用密集摘要或隐藏长文凑预算。原图在对应lesson/evidence出现一次；overview中的figure引用仅作兼容。必要公式可放lesson内，旧overview.formula仍显示；short_reading写简短读图顺序和关键对照。无折叠正文，无网站介绍/使用教程/泛泛评价。

数学以纯文本中的 `\(...\)` 或 `\[...\]` 标记；JSON文件中每个反斜杠写成两个反斜杠。例如公式值为 `"\\[c_t=f_t\\odot c_{t-1}+i_t\\odot\\tilde c_t\\]"`。多行公式可用aligned环境，矩阵可用bmatrix；不要输出未封闭的定界符。HTML正文始终转义，KaTeX设置trust=false，不允许借公式执行脚本或加载远程内容。数学库与字体随单文件导出；Math字体/引擎的MIT许可见assets/math/LICENSE。

内嵌数学字体每个family/style/weight组合必须各自放在独立`@font-face`块中，不能合并多个font-family和src声明；否则公式虽能通过语法检查，仍会回退字体并造成上下标、根号、重音错位。复习卡只保留短标签；return_to_original默认在复习卡下方的details中关闭，可点击查看。这不折叠读懂正文。

修改说明文字或排版时保留现有题目和作答。生成器以题目身份保存记录，覆写同一路径时会迁移旧版兼容的存储键；题目或核对提示改变时使用新记录，避免把旧答案算成新题答案。

## 可选的多篇选择

一次上传n篇后，只为本次指定论文创建一份JSON数组清单，每项为`{"lesson":"相对清单位置的lesson.json路径","file":"本地阅读页.html"}`，然后运行`python scripts/build_library.py batch.json --out dist/batches/本批唯一名称`。每批清单与输出目录独立，禁止扫描历史dist或复用全局样稿清单来填充选择列表；n=1也有效。它在每页右上角提供“选择论文”，弹窗仅显示本批内容，标出正在读的论文；部分原文导读明确标注。只连接已生成的解读，不把上传PDF误称为已完成解读；不可读文件保留在批次记录，有限导读只写实际可读范围。

目录内所有阅读页内嵌同一清单，通过相对HTML链接切换；不需要服务器、网络请求或账号。保留原输出文件名与兼容的作答存储键，各篇作答互不混用。单独重建原阅读页会保留已有选择清单；新增/删除论文后重新运行build_library.py。复制单个HTML仍能阅读本篇，多篇切换需要相邻HTML文件一同保留。
