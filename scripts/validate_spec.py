#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_spec.py — petbox-pawcare-ai spec 三层校验（零 LLM，零依赖 Python 3 标准库）。

与后端 SpecValidator.java / GenerativeUiService.java 对齐（2026-10-19 移植）：
  ① 结构：version=1、title≤12字、blocks 1-14、type 白名单（11 块可移植子集，
     action-button 禁用）、每块必填 props 与长度、layer 0-2
  ② 引用：数值槽位必须 {"$ref":"data.<路径>"}；给 --data 时校验路径可解析、
     文案内嵌模板 {ref:'data.x'} / {$ref:"data.x"} 可解析
  ③ 值形：bar-row current/target 标量、trend-lite.points 非空数值数组、
     stat-grid value 标量（非数值项报错令其剔除）

用法：
  python3 scripts/validate_spec.py spec.json [--data fixtures/xxx.json]
不过校验不渲染（红线 4）。退出码 0=通过，1=有错误。
"""
import argparse
import json
import re
import sys
from pathlib import Path

MAX_BLOCKS = 14
# 可移植子集（9-23 方案 §三）：12 块剔除 action-button
BLOCK_TYPES = {
    "section-title", "stat-grid", "kv-list", "bar-row", "trend-lite", "callout",
    "food-chip", "cite-list", "text-block", "quiz-lite", "divider",
}
TONES = {"info", "warn", "danger"}
REF_PATH_RE = re.compile(r"^data\..+")
# 字符串内嵌模板（真机修复二）：{ref:'data.x'} / {$ref:"data.x"} / 多花括号均命中
REF_TEMPLATE_RE = re.compile(r"\{+\$?ref\s*:\s*['\"]([^'\"]+)['\"]\}")

errors = []


def err(block_i, btype, msg):
    errors.append(f"blocks[{block_i}]({btype}): {msg}")


def is_ref(value):
    return (isinstance(value, dict) and "$ref" in value
            and isinstance(value["$ref"], str) and REF_PATH_RE.match(value["$ref"]))


def lookup(data_root, path):
    """按 . 分段取路径；数组段接受纯数字下标；任一段不可用返回 None。"""
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


def check_str(props, key, btype, i, required, max_len):
    v = props.get(key)
    if required and (not isinstance(v, str) or not v.strip()):
        err(i, btype, f"{key} 必填且非空")
        return
    if isinstance(v, str) and max_len and len(v) > max_len:
        err(i, btype, f"{key} 超 {max_len} 字（现 {len(v)} 字）")


def check_numeric_ref(props, key, btype, i, data):
    v = props.get(key)
    if not is_ref(v):
        err(i, btype, f"{key} 必须写 {{\"$ref\":\"data.<路径>\"}}，禁止数字字面量")
        return
    if data is not None:
        resolved = lookup(data, v["$ref"])
        if resolved is None:
            err(i, btype, f"{key} 路径不可解析: {v['$ref']}（路径用点分段，数组下标写数字段：data.list.0.field）")
        elif not isinstance(resolved, (int, float)) or isinstance(resolved, bool):
            err(i, btype, f"{key} 引用到的值不是数值（值形层）: {v['$ref']}")


def check_string_template(text, btype, i, key, data):
    if not isinstance(text, str) or "ref" not in text:
        return
    for m in REF_TEMPLATE_RE.finditer(text):
        path = m.group(1).strip()
        if data is not None and lookup(data, path) is None:
            err(i, btype, f"{key} 内嵌模板引用不可解析: {path}")


def validate_block(i, block, data):
    if not isinstance(block, dict):
        err(i, "?", "块必须是对象")
        return
    btype = block.get("type")
    if btype == "action-button":
        err(i, "action-button", "小程序专用块（route 白名单外部无意义），技能 spec 禁用——请剔除")
        return
    if btype not in BLOCK_TYPES:
        err(i, str(btype), f"未知块类型，白名单: {sorted(BLOCK_TYPES)}")
        return
    if not isinstance(block.get("props"), dict):
        err(i, btype, "props 必须是对象")
        return
    layer = block.get("layer", 0)
    if not isinstance(layer, int) or isinstance(layer, bool) or not 0 <= layer <= 2:
        err(i, btype, f"layer 越界: {layer}")
    props = block["props"]

    if btype == "section-title":
        check_str(props, "text", btype, i, True, 30)
        check_string_template(props.get("text"), btype, i, "text", data)
    elif btype == "stat-grid":
        items = props.get("items")
        if not isinstance(items, list) or not 2 <= len(items) <= 3:
            err(i, btype, "items 必须是 2-3 项数组")
        else:
            for k, item in enumerate(items):
                if not isinstance(item, dict) or not item.get("label"):
                    err(i, btype, f"items[{k}].label 必填")
                if not is_ref(item.get("value")):
                    err(i, btype, f"items[{k}].value 必须 $ref，禁止数字字面量")
                elif data is not None:
                    resolved = lookup(data, item["value"]["$ref"])
                    if resolved is None:
                        err(i, btype, f"items[{k}].value 路径不可解析: {item['value']['$ref']}")
                    elif not isinstance(resolved, (int, float)) or isinstance(resolved, bool):
                        err(i, btype, f"items[{k}].value 引用值不是数值: {item['value']['$ref']}")
    elif btype == "kv-list":
        rows = props.get("rows")
        if not isinstance(rows, list) or not 1 <= len(rows) <= 8:
            err(i, btype, "rows 必须是 1-8 项数组")
        else:
            for k, row in enumerate(rows):
                if not isinstance(row, dict):
                    err(i, btype, f"rows[{k}] 必须是对象")
                    continue
                if not isinstance(row.get("key"), str) or not row.get("key").strip():
                    err(i, btype, f"rows[{k}].key 必填")
                elif len(row["key"]) > 8:
                    err(i, btype, f"rows[{k}].key 超 8 字")
                v = row.get("value")
                if isinstance(v, str):
                    if len(v) > 16:
                        err(i, btype, f"rows[{k}].value 超 16 字（超长请用 text-block）")
                elif not is_ref(v):
                    err(i, btype, f"rows[{k}].value 须字符串或 $ref")
                elif data is not None and lookup(data, v["$ref"]) is None:
                    err(i, btype, f"rows[{k}].value 路径不可解析: {v['$ref']}（路径用点分段，数组下标写数字段：data.list.0.field）")
    elif btype == "bar-row":
        check_str(props, "label", btype, i, True, None)
        check_numeric_ref(props, "current", btype, i, data)
        check_numeric_ref(props, "target", btype, i, data)
    elif btype == "trend-lite":
        v = props.get("points")
        if not is_ref(v):
            err(i, btype, "points 必须 $ref 指向数值数组，禁止字面量")
        elif data is not None:
            resolved = lookup(data, v["$ref"])
            if not isinstance(resolved, list) or not resolved:
                err(i, btype, f"points 引用值须非空数组: {v['$ref']}")
            elif not all(isinstance(p, (int, float)) and not isinstance(p, bool) for p in resolved):
                err(i, btype, f"points 引用值须全为数值: {v['$ref']}")
            elif len(resolved) > 14:
                err(i, btype, "points 超过 14 个点（取最近 ≤14）")
    elif btype == "callout":
        if props.get("tone") not in TONES:
            err(i, btype, "tone 必须是 info|warn|danger")
        check_str(props, "text", btype, i, True, 120)
        check_string_template(props.get("text"), btype, i, "text", data)
    elif btype == "food-chip":
        items = props.get("items")
        if not isinstance(items, list) or not 1 <= len(items) <= 8:
            err(i, btype, "items 必须是 1-8 项数组")
        else:
            for k, item in enumerate(items):
                if not isinstance(item, dict) or not item.get("name"):
                    err(i, btype, f"items[{k}].name 必填")
    elif btype == "cite-list":
        items = props.get("items")
        if not isinstance(items, list) or not 1 <= len(items) <= 5:
            err(i, btype, "items 必须是 1-5 项数组")
        else:
            for k, item in enumerate(items):
                if not isinstance(item, dict) or not item.get("title"):
                    err(i, btype, f"items[{k}].title 必填")
    elif btype == "text-block":
        check_str(props, "text", btype, i, True, 200)
        check_string_template(props.get("text"), btype, i, "text", data)
    elif btype == "quiz-lite":
        check_str(props, "question", btype, i, True, 60)
        options = props.get("options")
        if not isinstance(options, list) or not 2 <= len(options) <= 4:
            err(i, btype, "options 必须是 2-4 项字符串数组")
        idx = props.get("answerIndex")
        if not isinstance(idx, int) or isinstance(idx, bool) or not (0 <= idx < (len(options) if isinstance(options, list) else 0)):
            err(i, btype, "answerIndex 必须是 options 范围内的整数")
        check_str(props, "explanation", btype, i, False, 60)
    # divider：无 props 校验


def main():
    ap = argparse.ArgumentParser(description="petbox-pawcare-ai spec 三层校验")
    ap.add_argument("spec", help="spec JSON 文件路径")
    ap.add_argument("--data", help="数据文档（fixtures 或 live API 响应 JSON），给全路径才能做引用/值形校验")
    args = ap.parse_args()

    try:
        spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    except Exception as e:
        print(f"❌ spec 文件读取/解析失败: {e}", file=sys.stderr)
        sys.exit(1)
    data = None
    if args.data:
        try:
            data = json.loads(Path(args.data).read_text(encoding="utf-8"))
        except Exception as e:
            print(f"❌ data 文件读取/解析失败: {e}", file=sys.stderr)
            sys.exit(1)

    if spec.get("version") != 1:
        errors.append("version 必须为 1")
    title = spec.get("title")
    if not isinstance(title, str) or not title.strip():
        errors.append("title 必填")
    elif len(title) > 12:
        errors.append(f"title 超 12 字（现 {len(title)} 字）")
    blocks = spec.get("blocks")
    if not isinstance(blocks, list) or not blocks:
        errors.append("blocks 为空")
    elif len(blocks) > MAX_BLOCKS:
        errors.append(f"blocks 超上限 {MAX_BLOCKS}")
    else:
        for i, block in enumerate(blocks):
            validate_block(i, block, data)

    if errors:
        print(f"❌ 校验未通过（{len(errors)} 处）：")
        for e in errors:
            print(f"  - {e}")
        print("红线：不过校验不渲染。修正后重跑。")
        sys.exit(1)
    mode = "含值形校验" if data is not None else "仅结构+引用语法（未给 --data，路径存在性未验）"
    print(f"✅ 校验通过，{len(blocks)} 块（{mode}）")


if __name__ == "__main__":
    main()
