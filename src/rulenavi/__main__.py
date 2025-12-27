# -*- coding: utf-8 -*-
##
# @file src/rulenavi/__main__.py
# @brief Module entry point for `python -m rulenavi`.
#
# @if japanese
# `py -m rulenavi ...` 実行時のエントリーポイントです。CLI処理はcli.mainに委譲し、終了コードをSystemExitで返します。
# @endif
#
# @if english
# Entry point when invoking `python -m rulenavi ...`. Delegates CLI handling to cli.main and returns its exit code via SystemExit.
# @endif
#

"""
`py -m rulenavi ...` のときに呼ばれるモジュール。

Python は `-m パッケージ` で実行すると、
該当パッケージの `__main__.py` を探して実行する。

例:
  py -m rulenavi all
  py -m rulenavi step1
"""

# CLI向けのコマンド処理 main() を読込む
from .cli import main

if __name__ == "__main__":
    # main() の戻り値を明示的にSystemExitへ渡すことで、bat側の errorlevel に反映される
    # 0: 成功 / それ以外: 失敗として errorlevel に伝わる
    raise SystemExit(main())
