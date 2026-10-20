#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
api_call.py — petbox live 模式 REST 客户端（零依赖 Python 3 标准库）。

用法：
  export PETBOX_API_KEY=pbk_live_xxx        # 小程序「我的 → Agent 接入」生成，仅生成时明文一次
  python3 scripts/api_call.py save-key pbk_live_xxx   # 家长路径：把接入码存到 ~/.petbox/api_key（0600）
  python3 scripts/api_call.py get  /open/agent/profiles
  python3 scripts/api_call.py post /open/agent/recipe/plan --body '{"petId":1,"goal":"weight-loss"}'

key 读取顺序：环境变量 PETBOX_API_KEY → ~/.petbox/api_key 文件。
红线：key 只进 Authorization header；禁止写进 spec / preview.html / 任何产出文件。
错误人话：401=接入码失效（回小程序重新生成）；429=配额到顶/到期（见 references/live-mode.md 降级规则）。
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_BASE = "https://api.tahe.pet"
KEY_FILE = os.path.join(os.path.expanduser("~"), ".petbox", "api_key")


def load_key():
    env = os.environ.get("PETBOX_API_KEY", "").strip()
    if env:
        return env
    try:
        with open(KEY_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return ""


def save_key(raw):
    raw = (raw or "").strip()
    if not raw.startswith("pbk_live_") or len(raw) <= len("pbk_live_"):
        print("❌ 接入码格式不对：应以 pbk_live_ 开头（小程序「我的 → Agent 接入」生成）")
        sys.exit(2)
    os.makedirs(os.path.dirname(KEY_FILE), mode=0o700, exist_ok=True)
    with open(KEY_FILE, "w", encoding="utf-8") as f:
        f.write(raw + "\n")
    os.chmod(KEY_FILE, 0o600)
    print("✅ 接入码已保存到 " + KEY_FILE + "（权限 600，不会进任何产出文件）")
    print("   现在可以直接说：「帮我看看我家猫最近的体重，生成一份减脂食谱」")


def main():
    # 家长子命令先行处理（不走 REST 参数解析）
    if len(sys.argv) > 2 and sys.argv[1] == "save-key":
        save_key(sys.argv[2])
        return

    ap = argparse.ArgumentParser(description="petbox live API 客户端")
    ap.add_argument("method", choices=["get", "post"])
    ap.add_argument("path", help="API 路径，如 /open/agent/profiles")
    ap.add_argument("--body", help="POST JSON 体（字符串）")
    ap.add_argument("--base", default=os.environ.get("PETBOX_API_BASE", DEFAULT_BASE))
    args = ap.parse_args()

    key = load_key()
    if not key:
        print("❌ 未设置 PETBOX_API_KEY 环境变量——小程序「我的 → Agent 接入」生成后再试；"
              "或直接使用 demo 模式（fixtures 数据，输出须标注「示例数据」）")
        sys.exit(2)

    # yudao 网关前缀：业务路径缺 /app-api 时自动补齐（2026-10-20 修复：此前裸拼导致
    # /open/agent/* 落在 nginx 静态首页返回 HTML，被误判为"接口未上线"）
    path = args.path
    if not path.startswith("/app-api"):
        path = "/app-api" + path
    # 中文关键词等非 ASCII 必须 URL 编码（2026-10-20 修复：foods/search?keyword=鸡胸 崩溃）
    parts = urllib.parse.urlsplit(args.base.rstrip("/") + path)
    url = urllib.parse.urlunsplit((
        parts.scheme, parts.netloc,
        urllib.parse.quote(parts.path, safe="/"),
        urllib.parse.quote(parts.query, safe="=&"),
        ""))
    req = urllib.request.Request(url, method=args.method.upper())
    req.add_header("Authorization", "Bearer " + key)
    req.add_header("Accept", "application/json")
    if args.method == "post":
        req.add_header("Content-Type", "application/json")
        req.data = (args.body or "{}").encode("utf-8")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print("❌ 401：API KEY 无效或已被吊销——回小程序「Agent 接入」页重新生成（旧码即刻失效）")
        elif e.code == 429:
            print("❌ 429：配额到顶或会员到期——生成类与小程序共享同一配额池；"
                  "降级规则见 references/live-mode.md（可用 demo 数据但必须标注「示例数据」）")
        elif e.code == 403:
            print("❌ 403：当前会员等级无此端点权限（生成类端点需对应档位）")
        else:
            print(f"❌ HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:300]}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"❌ 网络异常：{e.reason}——live 数据拿不到时降级 demo（必须标注「示例数据」），不要空等重试超过 2 次")
        sys.exit(1)

    try:
        print(json.dumps(json.loads(body), ensure_ascii=False, indent=2))
    except json.JSONDecodeError:
        print(body)


if __name__ == "__main__":
    main()
