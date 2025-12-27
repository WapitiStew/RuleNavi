# src/sitegen/cli.py
from __future__ import annotations

import argparse
from pathlib import Path

# 既存の各step処理を import して呼ぶ想定（後で実装を寄せる）
# 例：from sitegen.pages import build_site など


def main() -> None:
    parser = argparse.ArgumentParser(prog="rulenavi")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_all = sub.add_parser("all", help="Run STEP1+STEP2 pipeline")
    p_all.add_argument("--log-level", default="INFO")

    p_site = sub.add_parser("site", help="Generate static site (HTML/CSS/JS)")
    p_site.add_argument("--log-level", default="INFO")

    args = parser.parse_args()

    # ここは後で “既存scriptsを内部関数化” して呼ぶように寄せるのが理想
    if args.cmd == "all":
        print("[TODO] call pipeline runner")
    elif args.cmd == "site":
        print("[TODO] call site generator")


if __name__ == "__main__":
    main()
