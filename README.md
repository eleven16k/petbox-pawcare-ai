# 它盒 AI 科养助手 · PetBox AI PawCare

> 宠物健康 Agent 技能包 —— 猫狗鲜食食谱生成、营养分析、急症分诊三大能力，
> 以「**数值永不来自 LLM**」的可溯源架构，渲染宠物信箱风格的生成式界面卡片。
> 遵循 Agent Skills 开放标准：**WorkBuddy / Qoder / Claude Code / 任何能读文件的 agent** 通吃。

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

---

## 这是什么

一个面向零基础养宠家长的 Agent 技能包。装进你的 agent 后，它负责三件事：

| 能力 | 说明 |
|---|---|
| 🍚 **鲜食食谱生成** | 对话收集宠物档案 → AI 选材（毒性剔除 + 实体对齐 + 关注点筛查）→ 遗传算法配比克重 → NRC 标准复核 |
| 🔬 **食谱/营养分析** | 拆解食材构成，对照 NRC/AAFCO 推荐区间给出缺口/超标结论 |
| 🚑 **健康咨询分诊** | 规则化急症关键词命中 → 只输出就医建议卡，**绝不在线诊断** |

所有结果渲染为**宠物信箱风格的单文件 HTML 卡片**（明信片形制、航空斜纹边框、To. 宠物主信头），
双击即开，无需任何运行时与网络依赖。

## 核心纪律（为什么值得信任）

宠物健康 AI 最常被质疑的是"黑箱编数"。本技能用可审计的机制回应：

1. **数值永不来自 LLM** —— 每个数字必须通过 `$ref` 溯源到结构化数据（内置合成数据或后端 API 响应），
   `validate_spec.py` 零 LLM 三层校验（结构/引用/值形），不过不渲染；
2. **急症优先，绝不诊断** —— 急症关键词命中即只输出就医建议卡（词表与兽医公开标准同源），不做任何病情判断；
3. **demo 强制标注** —— 无后端接入码时使用合成示例数据，渲染卡片加盖「示例数据」戳，永不冒充真实建议；
4. **隐私裁剪** —— 数据面只含宠物与记录，永不含手机号等身份信息。

完整纪律见 [`references/blocks.md`](references/blocks.md)（含 8 条负面清单）与 [`SKILL.md`](SKILL.md)。

## 快速开始

**WorkBuddy**：
```bash
git clone https://github.com/eleven16k/petbox-pawcare-ai.git ~/.workbuddy/skills/petbox-pawcare-ai
```
然后对 WorkBuddy 说：「帮我看看我家猫最近的体重，生成一份减脂食谱」

**Qoder / Claude Code**：将文件夹放入各自技能目录（Claude Code `~/.claude/skills/`）。

**纯文件兜底（任何 agent）**：把本仓库路径贴给 agent——「读 SKILL.md 照做」。

**开箱即 demo 模式**：内置 4 份合成数据（猫减脂/犬通用/营养分析/健康记录），渲染卡片加盖「示例数据」戳。

## 接入真实数据（它盒小程序）

想看自家宠物的真实档案与 GA 配重克重？

1. 打开**它盒 PetBox 小程序** → 「我的 → Agent 接入」→ 选择开放范围（仅读取 / 读取+起草）→ 生成接入码（仅显示一次）；
2. 将接入码保存到本机：`python3 scripts/api_call.py save-key pbk_live_xxx`；
3. 对 agent 说：「列出我所有宠物」——从此渲染的就是**实时数据**卡片（加盖「实时数据」戳）。

> 真实数据通道由它盒服务端提供：接入码鉴权、每日/每月配额、全量访问审计、写入走"家长确认"草稿制。
> 服务端营养引擎（遗传算法配重 + NRC 全量复核 60+ 项）同样零 LLM，确定性可复算。

详细约定见 [`references/live-mode.md`](references/live-mode.md)。

## 目录结构

```
SKILL.md            主指令（红线 + 三业务入口 + 标准流程）
references/         blocks 负面清单 / 三业务流水线 / ui-style / live-mode
schemas/            catalog.v1.json（块目录）+ spec.schema.json
scripts/            validate_spec.py（三层校验）/ render_html.py（渲染）
                    api_call.py（live 客户端 + save-key）/ package.sh（打包）
fixtures/           4 份合成示例数据（严禁放真实用户数据）
templates/          preview.template.html（宠物信箱明信片，离线单文件）
```

## 使用条款与免责

- 本技能输出的健康管理建议**不构成医疗诊断**；急症场景请立即联系宠物医院；
- live 模式需它盒小程序接入码，使用受配额与公平使用约束；接入码只读宠物数据，
  不含、不返回手机号等身份信息；
- 请保留急症就医卡纪律与「示例数据」标注机制——它们是本技能存在的理由。

## License

[Apache-2.0](LICENSE) © 2026 它盒 PetBox
