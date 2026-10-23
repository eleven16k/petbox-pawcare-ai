# petbox-pawcare-ai 技能包

它盒 PetBox 生成式界面技能（Agent Skills 开放标准 / SKILL.md），三端通用：
WorkBuddy（`~/.workbuddy/skills/`）、Qoder、Claude Code，以及"把文件夹贴给任何 agent"的纯文件兜底。

设计来源与纪律：仓库根目录《跨Agent生成式界面Skill方案-WorkBuddy与Qoder.md》（2026-09-23）
与《Skill化接入方案-APIKEY与MCP-20261008.md》。AI 给出本目录时，读 `SKILL.md` 照做即可。

## 目录

```
SKILL.md                 主指令（红线 + 三业务入口 + 标准流程）
references/              blocks 负面清单 / 三业务 / ui-style / live-mode
schemas/                 catalog.v1.json（后端只读拷贝）+ spec.schema.json
scripts/                 validate_spec.py / render_html.py / api_call.py / sync-catalog.sh
fixtures/                四份合成示例数据（形状=后端 DTO，严禁放真实用户数据）
templates/               preview.template.html（ToThereOn 浅色玻璃，MP 端镜像）
```

## 安装

- WorkBuddy：`cp -r petbox-pawcare-ai ~/.workbuddy/skills/`；对话触发（"给我家猫生成减脂食谱并展示"）。
- Qoder / Claude Code：拷入各自技能目录。
- 纯文件兜底：把本目录路径贴给 agent，"读 SKILL.md 照做"。

## 本机自测

```bash
# 正例：三业务各一条（fixture 数据）
python3 scripts/validate_spec.py spec.json --data fixtures/cat-weight-loss.json
python3 scripts/render_html.py spec.json --data fixtures/cat-weight-loss.json --out preview.html
# 负例自检：数字字面量必须被拒；坏 $ref 必须被剔块
```

## 单源同步（开发机）

后端改了块目录：`bash scripts/sync-catalog.sh`（catalog 单向拷入，禁止手改包内拷贝）。
后端急症词表变更时同步更新 `references/business-consult.md`（来源 EmergencyGuard.java）。

## 状态

- 示例模式：可用（本包自包含）。
- live 模式：**待后端 P2**（`/open/agent/*` 端点组 + API KEY，见 10-08 方案）；`api_call.py` 已就绪。
- 连接器（MCP）形态：另行规划（官方连接器 = MCP Server + 本技能的精简版）。
