# -*- coding: utf-8 -*-
##
# @file src/rulenavi/__init__.py
# @brief Package marker for rulenavi.
#
# @if japanese
# rulenaviフォルダをPythonパッケージとして認識させるための空モジュールです。
# 現状は公開シンボルを持たず、将来のバージョン情報やエクスポート制御のための場所として利用できます。
# @endif
#
# @if english
# Minimal module to mark the rulenavi directory as a Python package.
# Currently exposes no symbols; serves as a placeholder for future version or export controls.
# @endif
#

"""
rulenavi パッケージの入口。

- このファイルがあることで、Python はこのフォルダを「パッケージ」として扱う。
- 今は特に機能は持たせていないが、バージョン情報などを置くことはある。
"""

# 外部に公開する名前を制御する。from rulenavi import * などを使ったときの対象。
__all__ = []
