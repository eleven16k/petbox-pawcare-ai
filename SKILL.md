---
name: petbox-pawcare-ai
display_name: 它盒猫狗AI科养助手
display_name_en: PetBox AI PawCare
description: 它盒 PetBox 生成式界面技能——为宠物食谱生成、食谱分析、健康咨询三大业务生成结构化界面卡片（spec JSON）并渲染为可直接打开的 preview.html。当用户要求生成/展示宠物食谱、分析食谱营养、或咨询宠物健康问题并希望以卡片界面呈现结果时使用。
description_zh: 它盒 PetBox 生成式界面技能：为宠物食谱生成、食谱分析、健康咨询三大业务生成结构化界面卡片（spec JSON）并渲染为可直接打开的 preview.html。当用户要求生成/展示宠物食谱、分析食谱营养、或就宠物健康问题生成卡片式解答时使用。
description_en: PetBox generative-UI skill — builds structured UI cards (spec JSON) for three workflows (pet recipe generation, recipe/nutrition analysis, health consultation) and renders a self-contained preview.html. Use when the user asks to create or show a pet recipe, analyze recipe nutrition, or wants a card-style answer to a pet health question.
version: 1.3.0
author: 它盒 PetBox
---

# 功能总览（用户能做什么）

| # | 能力 | 用户怎么说 | 数据 |
|---|---|---|---|
| 1 | 鲜食食谱生成（含每种食材克重 + NRC 复核结论） | 「帮我看看我家猫最近的体重，生成一份减脂食谱」 | 示例数据 / live |
| 2 | 食谱/营养分析（缺口与超标结论） | 「这份狗粮配方营养达标吗？」 | 示例数据 / live |
| 3 | 健康咨询 + 急症分诊（急症只出就医卡） | 「狗后腿站不起来呼吸快」 | 规则判定，不计次 |
| 4 | 查询真实档案与记录（live） | 「列出我所有宠物」「皮皮最近便便怎么样」 | 需接入码 |
| 5 | 起草记录（体重/便便/饮水，家长确认后生效） | 「帮我把今天便便记一下」 | 需接入码 + read_write 档 |

三业务的详细流程见下方「三业务入口」；每能力的红线与调用约定见对应 references 文档。

# 红线（先读这个，违反任何一条 = 重做）

1. **数值永不编造**：stat-grid.value / bar-row.current·target / trend-lite.points
   必须写 `{"$ref":"data.<路径>"}`；数据只来自 `fixtures/`（示例模式）或 live API 响应。
2. **急症优先**：用户消息命中急症关键词表（references/business-consult.md）
   → 只输出一个 danger callout 就医卡，不装其他卡、不做诊断、不做食谱。
3. **示例数据强制标注**：用 fixtures 数据时徽标保持「示例数据」；live 数据才加 `--live`。
   档位型（序数）数据展示必须带方向图例。
4. **不过校验不渲染**：组装完必须跑
   `python3 scripts/validate_spec.py spec.json --data <数据文件>`，通过才进渲染。
5. **key 永不入产物**（live 模式）：PETBOX_API_KEY 只进环境变量与 Authorization
   header，禁止写进 spec / preview.html / 任何产出文件。

# 工作目录约定

把当前工作目录的文件路径用于命令（spec.json 存在当前目录即可）。
脚本路径相对技能包根目录（本文件所在目录）。

# 三业务入口（判断用户意图后只读对应一篇）

- 生成/调整食谱 → references/business-recipe.md
- 分析食谱/营养盘点 → references/business-analysis.md
- 健康问题咨询（先分诊！）→ references/business-consult.md
- 块目录与负面清单（组装前必读）→ references/blocks.md
- 视觉调性（一般不用改）→ references/ui-style.md
- live 真数据（有 PETBOX_API_KEY 时）→ references/live-mode.md

# 标准流程

```
① 分诊（咨询类必做）：急症 → danger callout，结束。
② 收集输入：食谱类收集档案（缺什么问什么）；分析类拿食谱清单；咨询类判断行动型/咨询型。
③ 选数据源：
   有 PETBOX_API_KEY 且端点在线 → live（references/live-mode.md）；
   否则 → 示例模式：从 fixtures/ 选最贴近的一份（cat-weight-loss / dog-generic /
   analysis-sample / consult-records）。
④ 组装 spec.json：version=1、title≤12字、blocks≤14、11 块白名单、数值全 $ref
   （语法与限制见 schemas/spec.schema.json 与 schemas/catalog.v1.json）。
⑤ 硬门：python3 scripts/validate_spec.py spec.json --data <数据文件>
   失败 → 按报错修正，重试 ≤2 次。
⑥ 渲染：python3 scripts/render_html.py spec.json --data <数据文件> --out preview.html
   （live 数据追加 --live）
   注意剔除报告：被剔块 = 数据缺失，向用户说明，不要试图用编造数据补齐。
⑦ 打开 preview.html 展示给用户；配一句人话总结（结论必须能在数据里指认）。
⑧ 校验/渲染失败 ≥3 次 → 放弃卡片，纯文字回答（同样遵守红线 1：数值只引数据）。
```

# 降级纪律（任何失败不阻塞对话）

校验重试 ≤2 次 → 剔块 → 纯文字。live 拿不到数据 → 示例模式兜底但必须标「示例数据」；
禁止用示例数据冒充真数据；禁止绕配额重试。

# 依赖

Python 3 标准库（零第三方依赖）。preview.html 是离线单文件，任何环境"打开文件"即见。
