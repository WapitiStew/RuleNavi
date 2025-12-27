# -*- coding: utf-8 -*-
##
# @file src/textio.py
# @brief UTF-8 text I/O helpers for consistent encoding handling.
#
# @if japanese
# UTF-8(BOMなし)での書き込みと、UTF-8 → UTF-8-SIG → CP932 の順で読み込む関数を提供します。
# file:// 配信時の文字化け防止と、既存資産の互換読み込みを両立させるための共通ヘルパーです。
# @endif
#
# @if english
# Provides helpers to write UTF-8 (no BOM) and to read text trying UTF-8, UTF-8-SIG, then CP932.
# Centralized helpers prevent encoding drift and keep compatibility with existing assets.
# @endif
#

from __future__ import annotations

from pathlib import Path  # [JP] 標準: パス操作 / [EN] Standard: path utilities
from typing import Iterable  # [JP] 標準: 型ヒント / [EN] Standard: type hints


##
# @brief Write text as UTF-8 without BOM / UTF-8(BOMなし)でテキストを書き込む
#
# @if japanese
# 親ディレクトリを作成し、改行コードを指定した上でUTF-8(BOMなし)で保存します。
# @endif
#
# @if english
# Ensures parent directory exists, then saves text as UTF-8 (no BOM) with the specified newline.
# @endif
#
# @param path [in]  出力パス / Target path
# @param text [in]  書き込むテキスト / Text to write
# @param newline [in]  改行コード / Newline characters to use
def write_text_utf8(path: Path | str, text: str, *, newline: str = "\n") -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8", newline=newline)


##
# @brief Read text with fallback encodings / 複数エンコーディングで読み込む
#
# @if japanese
# UTF-8 → UTF-8-SIG → CP932 の順で読み込みを試み、最初に成功した内容を返します。
# すべて失敗した場合は最後の例外を送出します。
# @endif
#
# @if english
# Tries UTF-8, UTF-8-SIG, then CP932 and returns the first successfully decoded content.
# Raises the last exception if all attempts fail.
# @endif
#
# @param path [in]  入力パス / Path to read
# @param encodings [in]  試行するエンコーディング順 / Encoding order to try
# @return str  読み込んだテキスト / Read text content
def read_text_auto(
    path: Path | str, encodings: Iterable[str] = ("utf-8", "utf-8-sig", "cp932")
) -> str:
    p = Path(path)
    last_err: Exception | None = None
    for enc in encodings:
        try:
            return p.read_text(encoding=enc)
        except Exception as e:  # pragma: no cover - fallback path
            last_err = e
    if last_err is not None:
        raise last_err
    raise FileNotFoundError(p)

