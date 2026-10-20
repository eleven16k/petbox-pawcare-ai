# 块目录与负面清单（组装前必读）

块目录单一事实源：`schemas/catalog.v1.json`（后端只读拷贝）。技能可用 **11 块**（action-button 是小程序页面跳转专用，外部无意义，禁用）。

## 11 块速查

| 块 | 用途 | 数值槽（必须 $ref） | 关键限制 |
|---|---|---|---|
| section-title | 分节标题 | — | text ≤30 字，可带 emoji |
| stat-grid | 核心数字宫格 | items[].value | 2-3 项，value 标量 |
| kv-list | 档案式键值对 | rows[].value（二选一：字符串≤16字或 $ref） | ≤8 行，key ≤8 字 |
| bar-row | 单条进度（当前 vs 目标） | current、target | 都必须是数值 |
| trend-lite | 7 点迷你趋势（纯 CSS 柱） | points | 数值数组 ≤14 点，时间正序 |
| callout | 提示条 info/warn/danger | — | text ≤120 字；danger 仅就医级 |
| food-chip | 食材标签组 | — | ≤8 项 |
| cite-list | 引用来源 | — | ≤5 项 |
| text-block | 大白话段落 | 文案内可嵌 `{ref:'data.x'}` | ≤200 字，支持换行 |
| quiz-lite | 单选小测（自动翻牌） | — | options 2-4 项，answerIndex 指正确项 |
| divider | 分隔线 | — | 无 props |

`layer` 可选 0（默认大白话，独立成卡）/1（进阶）/2（专业）：1/2 层是补充，0 层必须自己完整可读。

## 组装模板（默认骨架）

`section-title` → `kv-list`（档案速览）→ 数据主块（stat-grid / bar-row / trend-lite）→ `callout`（提示收尾）。有建议用 callout 收尾；danger 只用于就医级。

## 负面清单（8 条，真机教训，违反任何一条 = 重写）

1. **$ref 嵌进字符串字面量泄漏**：数值槽必须整体 `{"$ref":"data.x"}`，不要写 `"5.2kg"` 之类的硬编码字符串冒充数据。
2. **数组塞数值槽**：stat-grid.value / bar-row.current·target 是标量，不要把数组塞进去（要趋势用 trend-lite）。
3. **时间样式字符串收进数值键**：`"08:30"`、`"2025-07-21"` 不是数值，禁止喂给任何数值槽。
4. **日期数字织进文案**：不要在 text 里拼 `{"$ref"}` 日期当统计值；日期放 kv-list。
5. **趋势数组不用 trend-lite**：多个时间点的数值必须用 trend-lite，不要拆成多个 stat-grid。
6. **档位均值无方向**：便便形状 1-3 / 颜色 0-7 / 气味 0-4 是序数不是分数——展示均值必须带方向图例（"越低越稀"/"3 最健康"）。
7. **知识问答硬装卡**：纯知识问答不装卡，text-block + cite-list 回答即可（J-UI1 纪律）。
8. **空数据块不剔除**：引用路径解析不了的块会被渲染器整块剔除（宁缺毋错）——不要指望空壳块占位。

## 转述一致性自检（J-UI2 移植）

文案中的每个比较/趋势结论，必须能在数据里指认出原始数值；指认不了就删掉那句。禁止"明显改善""大幅超出"这类无数据支撑的程度词。
