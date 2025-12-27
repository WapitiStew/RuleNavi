# -*- coding: utf-8 -*-
##
# @file src/sitegen/cli.py
# @brief CLI stub for site generation.
#
# @if japanese
# サイト生成用のCLIエントリを用意するスタブです。現状は全体パイプラインやサイト生成の呼び出し部分がTODOのままです。
# argparseでサブコマンドを定義し、処理は簡易な標準出力に留めています。
# @endif
#
# @if english
# Stub CLI entry for site generation. Currently leaves pipeline and site-generation calls as TODOs while defining subcommands via argparse.
# Behavior is limited to simple stdout messages without side effects.
# @endif
#

from __future__ import annotations

import argparse  # [JP] 標準: CLI引数処理 / [EN] Standard: CLI argument parsing
from pathlib import Path  # [JP] 標準: パス型ヒント用 / [EN] Standard: path type hint (placeholder)

# 循環import対策のため、実処理モジュールのimportは未実装 / Actual processing imports are TODO to avoid circular dependencies for now


##
# @brief CLI main for sitegen / sitegen向けCLIのメイン
#
# @if japanese
# all と site のサブコマンドを定義し、現時点ではTODOメッセージを表示するのみです。
# 将来的にパイプライン実行や静的サイト生成ロジックをここから呼び出す想定です。
# @endif
#
# @if english
# Defines subcommands all and site, currently printing TODO placeholders only.
# Intended to later dispatch to pipeline and static site generation routines.
# @endif
#
# @return None  終了コード無し / No explicit exit code
def main() -> None:
    parser = argparse.ArgumentParser(prog="rulenavi")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # [JP] STEP1+STEP2パイプライン用のサブコマンド / [EN] Subcommand for full pipeline
    p_all = sub.add_parser("all", help="Run STEP1+STEP2 pipeline")
    p_all.add_argument("--log-level", default="INFO")

    # [JP] サイト生成用のサブコマンド / [EN] Subcommand for static site generation
    p_site = sub.add_parser("site", help="Generate static site (HTML/CSS/JS)")
    p_site.add_argument("--log-level", default="INFO")

    args = parser.parse_args()

    # [JP] 現在はTODOメッセージのみ / [EN] Currently print TODO placeholders
    if args.cmd == "all":
        print("[TODO] call pipeline runner")
    elif args.cmd == "site":
        print("[TODO] call site generator")


if __name__ == "__main__":
    main()
