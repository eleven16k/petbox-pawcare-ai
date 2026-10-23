# 业务二：食谱分析

示例数据：`fixtures/analysis-sample.json`。

## 流程

1. **确定输入**：用户给食谱（口述食材清单 / 包装标签 / 照片转述）。live → `POST /open/agent/foods/search` 查食材库再算（未上线前用 fixtures 样例演示）；示例模式 → 直接用 fixtures。
2. **块组合模板**：

```
food-chip   食材构成（data.recipe.foods 展开为 name）
kv-list     关键占比（data.recipe.foods.0.pct 等，值 ≤16 字格式化）
stat-grid   每日热量/蛋白/脂肪（data.plan.*）
bar-row     蛋白 vs 推荐区间（current=data.nutrients.0.intake, target=data.nutrients.0.recommend）
bar-row     脂肪 vs 推荐区间
bar-row     钙磷比（若有）
trend-lite  体重曲线（data.weights.points，有历史才出）
callout     缺口/超标结论（status=high→warn，low→info 或 warn 视程度）
```

3. **status 字段语义**：`ok` 达标 / `low` 偏低 / `lowerRec` 低于推荐但未缺 / `high` 超标。结论句必须引用具体数字对照（一致性自检）。

## 档位型数据纪律（红线 3 的展开）

便便形状（1 水样 → 4 干硬）、颜色（0 白 → 7 红）、气味（0 无 → 4 刺鼻）是**序数刻度**，不是分数：

- 展示均值或趋势时**必须带方向图例**（用 trend-lite 的 label 写清："近 7 次便便形状（1水样 2糊 3成型 4干硬）"）。
- 柱色渲染器已按 label 关键词自动着色（形状按距 3 红绿灯、颜色走真实色阶、气味阈值），不要自己造颜色规则。
- 禁止把序数均值说成"得分 2.5 分"——说"多数偏软"。

## 示例片段

```json
{"type": "bar-row", "props": {"label": "粗脂肪 vs 推荐", "current": {"$ref": "data.nutrients.1.intake"}, "target": {"$ref": "data.nutrients.1.recommend"}, "unit": "g"}}
{"type": "trend-lite", "props": {"label": {"$ref": "data.pooShape.label"}, "points": {"$ref": "data.pooShape.points"}}}
```

label 也可以是 $ref（fixtures 里带了方向说明的完整 label）。

## 纪律

- "超标"结论必须能指认 intake 与 upper 的对比；区间缺失（upper=null）就说"无明确上限，按推荐值参考"。
- 减脂/处方诉求转业务一流程；出现急症关键词立刻转业务三分诊。
