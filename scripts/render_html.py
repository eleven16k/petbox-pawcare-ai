#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render_html.py — spec + 数据 → 单文件 preview.html（零依赖 Python 3 标准库）。

流水线（对齐后端 GenerativeUiService）：
  解析 $ref（路径不通整块剔除，宁缺毋错）
  → 字符串内嵌模板 {ref:'data.x'} / {$ref:"data.x"} 替换（任一路径不通剔块）
  → 值形后校验（bar-row 标量 / trend-lite 数值数组 / stat-grid 标量，违规剔块/剔项）
  → 套 ToThereOn 浅色玻璃模板输出静态 DOM（无框架/无 CDN/无构建），
    文件内嵌原始 spec JSON 供检查对照。

用法：
  python3 scripts/render_html.py spec.json --data fixtures/xxx.json [--out preview.html]
输出渲染报告：成功 N/M 块；被剔块连原因列出（对照红线排查）。
"""
import argparse
import html
import json
import math
import re
import sys
from pathlib import Path

REF_TEMPLATE_RE = re.compile(r"\{+\$?ref\s*:\s*['\"]([^'\"]+)['\"]\}")
POO_COLOR_SCALE = ["#ECECEC", "#E6C84A", "#C89B3C", "#8B5A2B", "#5C3A1E", "#6B8E23", "#2B2B2B", "#C0392B"]
DROPPED = []


def fmt(n):
    """数值格式化（MP 同源）：保留 1 位小数，整数不带小数点；非有限数 → —"""
    if not isinstance(n, (int, float)) or isinstance(n, bool) or not math.isfinite(n):
        return "—"
    r = round(n * 10) / 10
    return str(int(r)) if r == int(r) else f"{r:.1f}"


def esc(s):
    return html.escape(str(s), quote=True)


def lookup(data_root, path):
    if not isinstance(path, str) or not path.startswith("data."):
        return None
    node = data_root
    for seg in path[5:].split("."):
        if isinstance(node, dict):
            node = node.get(seg)
        elif isinstance(node, list):
            if not seg.isdigit() or int(seg) >= len(node):
                return None
            node = node[int(seg)]
        else:
            return None
        if node is None:
            return None
    return node


def resolve_templates(text, data):
    """字符串内嵌模板替换；任一路径不可解析返回 None（剔块）。"""
    if not isinstance(text, str) or "ref" not in text:
        return text

    def repl(m):
        v = lookup(data, m.group(1).strip())
        if v is None or (isinstance(v, str) and not v.strip()) or v == []:
            return "\x00DROP"
        return fmt(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else str(v)

    out = REF_TEMPLATE_RE.sub(repl, text)
    return None if "\x00DROP" in out else out


def resolve_props(props, data, i, btype):
    """返回解析后的 props；不可解析返回 None（剔块）。逐项剔除仅 stat-grid。"""
    out = {}
    for key, value in props.items():
        if isinstance(value, dict) and "$ref" in value:
            v = lookup(data, value.get("$ref"))
            if v is None or (isinstance(v, str) and not v.strip()) or v == []:
                DROPPED.append(f"blocks[{i}]({btype}) 剔除：{key} 引用不可解析 {value.get('$ref')}")
                return None
            out[key] = v
        elif isinstance(value, list):
            items = []
            bad = False
            for item in value:
                if isinstance(item, dict) and "$ref" in item:
                    v = lookup(data, item.get("$ref"))
                    if v is None:
                        DROPPED.append(f"blocks[{i}]({btype}) 剔除：{key} 内 $ref 不可解析")
                        bad = True
                        break
                    items.append(v)
                elif isinstance(item, dict):
                    # 内层对象的字段级 $ref（stat-grid.items[].value / kv-list.rows[].value）
                    ritem = {}
                    for k2, v2 in item.items():
                        if isinstance(v2, dict) and "$ref" in v2:
                            rv = lookup(data, v2["$ref"])
                            if rv is None:
                                DROPPED.append(f"blocks[{i}]({btype}) 剔除：{key}[].{k2} 引用不可解析 {v2.get('$ref')}")
                                bad = True
                                break
                            ritem[k2] = rv
                        else:
                            ritem[k2] = v2
                    if bad:
                        break
                    items.append(ritem)
                else:
                    items.append(item)
            if bad:
                return None
            out[key] = items
        elif isinstance(value, str):
            resolved = resolve_templates(value, data)
            if resolved is None:
                DROPPED.append(f"blocks[{i}]({btype}) 剔除：{key} 内嵌模板引用不可解析")
                return None
            out[key] = resolved
        else:
            out[key] = value
    return out


def enforce_semantics(props, i, btype):
    """值形后校验（注入后）：bar-row 标量 / trend-lite 数值数组 / stat-grid 标量。违规剔块或剔项。"""
    if btype == "bar-row":
        if not (isinstance(props.get("current"), (int, float)) and isinstance(props.get("target"), (int, float))):
            DROPPED.append(f"blocks[{i}](bar-row) 剔除：current/target 非标量数值")
            return None
    elif btype == "trend-lite":
        pts = props.get("points")
        if not (isinstance(pts, list) and pts and all(isinstance(p, (int, float)) and not isinstance(p, bool) for p in pts)):
            DROPPED.append(f"blocks[{i}](trend-lite) 剔除：points 非非空数值数组")
            return None
    elif btype == "stat-grid":
        valid = [it for it in props.get("items", [])
                 if isinstance(it, dict) and isinstance(it.get("value"), (int, float)) and not isinstance(it.get("value"), bool)]
        if len(valid) != len(props.get("items", [])):
            DROPPED.append(f"blocks[{i}](stat-grid) 剔除非数值 value 项 {len(props.get('items', [])) - len(valid)} 个")
        if not valid:
            DROPPED.append(f"blocks[{i}](stat-grid) 剔除：无有效数值项")
            return None
        props["items"] = valid
    return props


def trend_bar_color(label, value):
    """柱色（MP 同源）：便便颜色走真实色阶、形状按距 3、气味阈值，其余默认灰。"""
    label = label or ""
    if "颜色" in label or "color" in label.lower():
        idx = max(0, min(int(value), len(POO_COLOR_SCALE) - 1))
        return POO_COLOR_SCALE[idx]
    if "形状" in label or "shape" in label.lower():
        dist = abs(value - 3)
        return "#4CAF50" if dist <= 1 else ("#FF9800" if dist == 2 else "#F44336")
    if "气味" in label or "臭" in label or "smell" in label.lower():
        return "#4CAF50" if value <= 1 else ("#FF9800" if value == 2 else "#F44336")
    return "#BDBDBD"


def render_block(block, i):
    btype, props = block["type"], block["props"]
    if btype == "section-title":
        return f'<div class="blk blk__title">{esc(props["text"])}</div>'
    if btype == "stat-grid":
        cells = "".join(
            f'<div class="stat"><div class="stat__num">{esc(fmt(it["value"]))}'
            f'<span class="stat__unit">{esc(it.get("unit", ""))}</span></div>'
            f'<div class="stat__label">{esc(it["label"])}</div></div>'
            for it in props["items"])
        return f'<div class="blk stat-grid">{cells}</div>'
    if btype == "kv-list":
        rows = "".join(
            f'<div class="kv"><span class="kv__key">{esc(r["key"])}</span>'
            f'<span class="kv__val">{esc(fmt(r["value"]) if isinstance(r["value"], (int, float)) else r["value"])}</span></div>'
            for r in props["rows"])
        return f'<div class="blk kv-list">{rows}</div>'
    if btype == "bar-row":
        cur, tgt = props["current"], props["target"]
        pct = min(100, max(2, round(cur / tgt * 100))) if tgt else 2
        return (f'<div class="blk bar-row"><div class="bar__top"><span>{esc(props["label"])}</span>'
                f'<span>{esc(fmt(cur))}/{esc(fmt(tgt))}{esc(props.get("unit", ""))}</span></div>'
                f'<div class="bar__track"><div class="bar__fill" style="width:{pct}%"></div></div></div>')
    if btype == "trend-lite":
        pts = props["points"][:14]
        lo, hi = min(pts), max(pts)
        span = (hi - lo) or 1
        bars = "".join(
            f'<div class="trend__col"><div class="trend__bar" style="height:{12 + (p - lo) / span * 88:.0f}%;'
            f'background:{trend_bar_color(props.get("label"), p)}" title="{esc(fmt(p))}"></div></div>'
            for p in pts)
        legend = f'<div class="blk__legend">{esc(props["label"])}</div>' if props.get("label") else ""
        return f'<div class="blk trend">{legend}<div class="trend__bars">{bars}</div></div>'
    if btype == "callout":
        return f'<div class="blk callout callout--{esc(props["tone"])}">{esc(props["text"])}</div>'
    if btype == "food-chip":
        chips = "".join(f'<span class="chip">{esc(it["name"])}</span>' for it in props["items"])
        return f'<div class="blk chips">{chips}</div>'
    if btype == "cite-list":
        rows = "".join(
            f'<div class="cite">{esc(it["title"])}'
            + (f'<span class="cite__src">{esc(it["source"])}</span>' if it.get("source") else "")
            + "</div>"
            for it in props["items"])
        return f'<div class="blk cites">{rows}</div>'
    if btype == "text-block":
        return f'<div class="blk tb">{esc(props["text"]).replace(chr(10), "<br>")}</div>'
    if btype == "quiz-lite":
        opts = "".join(
            f'<button class="quiz__opt" data-quiz="q{i}" data-correct="{k == props["answerIndex"]}">{esc(o)}</button>'
            for k, o in enumerate(props["options"]))
        expl = f'<div class="quiz__explain" data-explain="q{i}">{esc(props.get("explanation", ""))}</div>' if props.get("explanation") else ""
        return (f'<div class="blk quiz" data-quiz-block="q{i}"><div class="quiz__q">{esc(props["question"])}</div>'
                f'{opts}{expl}</div>')
    if btype == "divider":
        return '<div class="blk divider"></div>'
    return ""


def main():
    ap = argparse.ArgumentParser(description="spec + 数据 → preview.html")
    ap.add_argument("spec")
    ap.add_argument("--data", required=True, help="数据文档（fixtures 或 live API 响应）")
    ap.add_argument("--out", default="preview.html")
    ap.add_argument("--live", action="store_true", help="live 数据模式：徽标与脚注标「实时数据」而非「示例数据」")
    ap.add_argument("--template", default=str(Path(__file__).resolve().parent.parent / "templates" / "preview.template.html"))
    args = ap.parse_args()

    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    data = json.loads(Path(args.data).read_text(encoding="utf-8"))
    template = Path(args.template).read_text(encoding="utf-8")

    rendered, kept = [], []
    for i, block in enumerate(spec.get("blocks", [])):
        btype = block.get("type", "?")
        props = resolve_props(block.get("props", {}), data, i, btype)
        if props is None:
            continue
        props = enforce_semantics(props, i, btype)
        if props is None:
            continue
        kept.append({"type": btype, "props": props})
        rendered.append(render_block({"type": btype, "props": props}, i))

    spec_json = json.dumps(spec, ensure_ascii=False).replace("</", "<\\/")
    pet_name = lookup(data, "data.pet.name")
    to_line = "To. " + (f"{pet_name}的铲屎官" if pet_name else esc(spec.get("title", "它盒卡片")))
    html_out = (template
                .replace("__TITLE__", esc(spec.get("title", "它盒卡片")))
                .replace("__TO_LINE__", to_line)
                .replace("__BODY__", "\n".join(rendered))
                .replace("__SPEC_JSON__", spec_json)
                .replace("__DEMO_BADGE__", "实时数据" if args.live else "示例数据")
                .replace("__FOOT_NOTE__", ""))

    Path(args.out).write_text(html_out, encoding="utf-8")
    total = len(spec.get("blocks", []))
    print(f"✅ 已生成 {args.out}：渲染 {len(kept)}/{total} 块")
    for d in DROPPED:
        print(f"  ⚠ {d}")
    if not kept:
        print("❌ 无可渲染块——检查数据路径（宁缺毋错，不渲染空壳）")
        sys.exit(1)


if __name__ == "__main__":
    main()
