# 业务一：食谱生成

demo 数据：`fixtures/cat-weight-loss.json`（猫减脂）、`fixtures/dog-generic.json`（犬通用）。
live 模式（有 PETBOX_API_KEY 且后端端点已上线）：见 `live-mode.md`。

## 流程

1. **对话收集档案**（缺什么问什么，别一次问一堆）：
   物种 → 年龄/生命周期阶段 → 当前体重与目标体重 → 体态评分（BCS 1-9，不知道就问"肋骨摸不摸得到"）→ 绝育 → 活动量 → 健康标签（过敏/肾病/孕期等）。
2. **选数据源**：live → `POST /open/agent/recipe/plan`（服务端 GA 配比 + 营养引擎 + Jev 门，agent 不算任何营养值）；demo → 选对应 fixtures 文件。
3. **组装 spec**（数值一律 `{"$ref":"data.<路径>"}`）：

```
section-title「减脂食谱」
kv-list     档案速览（data.pet.*：品种/年龄/体重/体态/绝育）
food-chip   推荐食材（data.recipe.categories 展开为 name）
stat-grid   每日热量/蛋白/脂肪（data.plan.energy / .protein / .fat）
bar-row     蛋白质达标（current=data.nutrients.0.intake, target=data.nutrients.0.recommend）
bar-row     体重进度（current=data.pet.weight, target=data.pet.expectWeight）
trend-lite  近期体重趋势（data.weights.points，有 ≥2 个点才出）
callout     喂养提示/禁忌（info 或 warn）
text-block  过渡换粮说明
```

4. **校验**：`python3 scripts/validate_spec.py spec.json --data fixtures/cat-weight-loss.json`
5. **渲染**：`python3 scripts/render_html.py spec.json --data fixtures/cat-weight-loss.json --out preview.html`
   live 数据加 `--live`（徽标变「实时数据」）。
6. 打开 preview.html 展示；有块被剔除时向用户说明哪段缺数据。

## 示例片段（节选，完整骨架见上）

```json
{"type": "stat-grid", "props": {"items": [
  {"label": "每日热量", "value": {"$ref": "data.plan.energy"}, "unit": "kcal"},
  {"label": "蛋白质", "value": {"$ref": "data.plan.protein"}, "unit": "g"},
  {"label": "脂肪", "value": {"$ref": "data.plan.fat"}, "unit": "g"}
]}}
```

## 纪律

- agent **永不算营养数**：热量/蛋白/克数全部来自 fixtures 或 API 响应。
- 涉及肾病/糖尿病/孕期的"食谱"属于医疗边界：给一般原则 + 建议就医定制，不做处方。
- 用户催数时宁可说"需要先确认档案"，也不要现编。
