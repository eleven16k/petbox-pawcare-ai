# live 模式（真数据接入）

示例模式（fixtures）是默认。满足以下两个条件才进 live：
1. 环境变量 `PETBOX_API_KEY` 已设置（小程序「我的 → Agent 接入」生成，`pbk_live_` 前缀，仅生成时明文一次，丢了吊销重发）；
2. 后端 `/open/agent/*` 端点已上线（未上线时 api_call.py 会 404，退回示例模式）。

## 接入码保存与调用

家长路径（二选一）：

```bash
# 路径 A（推荐，家长贴给 agent 的一句话）：
python3 scripts/api_call.py save-key pbk_live_xxx   # 存到 ~/.petbox/api_key（权限 600）
# 路径 B（技术用户）：
export PETBOX_API_KEY=pbk_live_xxx                  # 环境变量优先于配置文件
```

调用（key 读取顺序：环境变量 → ~/.petbox/api_key；响应 JSON 原样存盘即可作 render_html.py 的 --data）：

```bash
python3 scripts/api_call.py get /open/agent/profiles > /tmp/profiles.json
python3 scripts/api_call.py get "/open/agent/records?petId=1&type=weight" > /tmp/records.json
python3 scripts/validate_spec.py spec.json --data /tmp/records.json
python3 scripts/render_html.py spec.json --data /tmp/records.json --live --out preview.html
```

## 端点表（2026-10-20 修复：api_call.py 自动补 `/app-api` 前缀，短路径可直接用；直连 curl 需写全路径）

| 端点 | 用途 | 配额 |
|---|---|---|
| GET /app-api/open/agent/catalog | 块目录与版本（live 模式渲染前校验） | 只读，不计次 |
| GET /app-api/open/agent/profiles | 宠物档案列表 | 只读日池 |
| GET /app-api/open/agent/records | 体重/便便/饮水历史（?petId=&type=weight\|poo\|water） | 只读日池 |
| GET /app-api/open/agent/reports/verify | 验算报告存档（≤20 条，无大快照） | 只读日池 |
| GET /app-api/open/agent/foods/search | 食材库检索（?keyword=，含每 100g 营养面） | 只读日池 |
| GET /app-api/open/agent/triage | 急症判定（服务端同源词表） | **不计次，永不限量（信任层）** |
| POST /app-api/open/agent/recipe/plan | 食谱选材方案（服务端 DER+AI 选材，Jev 全门） | **每会员每月限次（当前未分级阶段统一 30 次/月；会员分级上线后按档位区分）** |
| POST /app-api/open/agent/records/draft | **起草**记录（weight/poo/water） | 只产生草稿；只读日池计次 |

## 写通道语义（records/draft，红线级）

1. 调用后**没有任何数据写入**健康记录——只生成 PENDING 草稿，家长在小程序「Agent 接入 → 待确认草稿」确认后才生效。
2. **对家长的话术红线**：只能说「已帮你起草，待你在小程序确认」，**严禁**说「已记录/已打卡」。
3. payload 数据关（服务端校验，不过即 1_004_003_130）：
   - weight：`{"weight": 5.3}`（kg，>0）
   - poo：`{"shape": 3, "color": 2, "smell": 1}`（形状 0-6 / 颜色 0-7 / 气味 0-4，序数刻度）
   - water：`{"drunk": 58}`（ml，>0）
   - 可选 `note`（给家长的一句话）、recordTime 缺省补今天。
4. 确认落库时 poo 的 source 强制 `ai_confirmed`（AI 起草、家长背书）。
5. **scope 门禁**：draft 端点需接入码为 `read_write` 档（家长生成接入码时自选，默认仅读取）。
   403（1_004_003_131）时如实说明"当前接入码未开放写入"，引导家长回小程序吊销重发并选「读取+起草」，**禁止**反复重试。

```bash
python3 scripts/api_call.py post /open/agent/records/draft --body \
  '{"petId":1,"type":"weight","payload":{"weight":5.3},"note":"刚称的体重，请确认"}'
```

## recipe/plan 调用约定（2026-10-19 上线）

1. 先 `GET /profiles` 拿宠物档案（选 petId），再 `GET /foods/search?keyword=…` 收集可用食材 `[{id,name,categoryName}]`（≥8 种为宜）。
2. `POST /recipe/plan` body：`{"petId":1,"availableFoods":[{"id":101,"name":"鸡胸肉","categoryName":"白肉"}],"concern":"减重"}`。
   档案与 DER/喂食量全部**服务端组装计算**（与小程序同公式），家长不可编造体重/疾病信息。
3. 响应 `plan`（DER/喂食量区间/档案快照/**portions**）+ `selection`（recipeName/description/categories/supplementAdvice/alignment/toxicGuard）。
   **portions = 服务端 GA 配重的每种食材克数（生重）**：`recipe:[{foodId,name,amount(克)}]`、
   `groups:[{name,percent,g,items}]`、`totalWeight/totalKcal/kcalAccuracy`。卡片展示分食材克重时
   一律 $ref 指向 portions，禁止自行按比例拆分总量；口径标注「生重（未烹饪）」。
   渲染纪律不变：数值 $ref 指向本响应；`selection.alignment.confirm` 项须在卡片中透明标注。
4. **验算与落库（2026-10-20 上线）**：响应含 `verification{reportId, verifyFinal, report}`——
   服务端已对方案做确定性 + NRC 全量复核并落库存档（回小程序「验算存档」可查）。
   `verifyFinal=fail`（如单一食材方案缺肝脏营养）时**如实告知不达标**，建议补充食材类别重新生成；
   禁止把 fail 方案说成"营养均衡"，也禁止美化结论。
5. 超限（1_004_003_127）：如实告知"本月生成次数已用完"，**禁止**用 fixtures 冒充本月真数据重试。

响应 JSON 原样存盘后即可作为 render_html.py 的 `--data`：

```bash
python3 scripts/api_call.py get /open/agent/records > /tmp/records.json
python3 scripts/validate_spec.py spec.json --data /tmp/records.json
python3 scripts/render_html.py spec.json --data /tmp/records.json --live --out preview.html
```

## 端点与配额（上线后以 /open/agent/catalog 实际返回为准）

| 端点 | 用途 | 配额 |
|---|---|---|
| GET /app-api/open/agent/catalog | 块目录与版本（live-mode 版本校验） | 只读，宽配额 |
| GET /app-api/open/agent/profiles | 宠物档案 | 只读 |
| GET /app-api/open/agent/records | 体重/便便/饮水历史 | 只读 |
| GET /app-api/open/agent/reports/verify | 验算报告存档 | 只读 |
| GET /app-api/open/agent/foods/search | 食材库检索 | 只读 |
| GET /app-api/open/agent/triage | 急症判定（服务端同源词表） | **不计次，永不限量（信任层）** |
| POST /app-api/open/agent/recipe/plan | 食谱生成（服务端 GA+营养引擎+Jev） | **与小程序共享同一配额池** |

## 降级链（任何失败不阻塞对话）

1. 401 → 接入码失效：提示用户回小程序重新生成；本轮降级示例模式并标注「示例数据」。
2. 429 → 配额到顶：说明"生成次数用完/会员到期"，本轮降级示例模式并标注；**禁止**换渠道重试绕配额。
3. 网络/超时 → 重试 ≤2 次（间隔递增），仍失败降级示例模式。
4. API 返回成功但字段缺失 → 相应块被渲染器剔除（宁缺毋错），向用户说明哪段缺数据。

## 隐私与安全红线（在 示例模式红线之上追加）

- `PETBOX_API_KEY` 只进 `Authorization` header 与环境变量；**禁止**写进 spec.json / preview.html / 任何产出文件 / 对话回复。渲染完成后可全文检索 preview.html 确认无 `pbk_` 字样。
- live 数值的每个 `$ref` 必须指向 **API 响应 JSON** 的路径；API 失败剔块降级，**禁止用 fixtures 数值冒充真数据**（这就是徽标存在的意义：示例模式必须标「示例数据」，live 必须加 `--live`）。
- 验算报告只读展示，不重算、不自行修改结论。
