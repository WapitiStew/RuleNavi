# -*- coding: utf-8 -*-
##
# @file src/sitegen/logger.py
# @brief Minimal logging helper with timestamp.
#
# @if japanese
# 簡易的なタイムスタンプ付きロガーを提供するモジュールです。標準出力にINFO/DEBUG/WARNを出し分けるのみで、副作用はありません。
# @endif
#
# @if english
# Minimal timestamped logger that prints INFO/DEBUG/WARN messages to stdout. No side effects beyond console output.
# @endif
#

from __future__ import annotations

import time  # [JP] 標準: 時刻取得 / [EN] Standard: time utilities


##
# @brief Current timestamp string HH:MM:SS / 現在時刻をHH:MM:SS形式で返す
#
# @if japanese
# ログ出力用の時刻文字列を返します。処理はtime.strftimeのみで、状態は保持しません。
# @endif
#
# @if english
# Returns a HH:MM:SS timestamp string for logging; relies solely on time.strftime and holds no state.
# @endif
#
# @return str  時刻文字列 / Timestamp string
def now_ts() -> str:
    return time.strftime("%H:%M:%S")


class Logger:
    """
    Simple stdout logger with optional verbosity.
    """

    ##
    # @brief Initialize Logger / Loggerを初期化する
    #
    # @if japanese
    # verboseフラグを保持し、DEBUG出力を制御します。
    # @endif
    #
    # @if english
    # Stores the verbose flag to control DEBUG outputs.
    # @endif
    #
    # @param verbose [in]  DEBUGを出すかどうか / Whether to emit DEBUG logs
    def __init__(self, verbose: bool = True) -> None:
        self.verbose = verbose

    ##
    # @brief Print info log / INFOログを出力
    #
    # @if japanese
    # タイムスタンプ付きでINFOレベルのメッセージを標準出力へ表示します。
    # @endif
    #
    # @if english
    # Prints an INFO-level message with timestamp to stdout.
    # @endif
    #
    # @param msg [in]  ログメッセージ / Log message
    def info(self, msg: str) -> None:
        print(f"[{now_ts()}] {msg}")

    ##
    # @brief Print debug log if verbose / verbose時にDEBUGログを出力
    #
    # @if japanese
    # verboseがTrueの場合にのみDEBUGメッセージを出力します。
    # @endif
    #
    # @if english
    # Emits DEBUG messages only when verbose is True.
    # @endif
    #
    # @param msg [in]  ログメッセージ / Log message
    def debug(self, msg: str) -> None:
        if self.verbose:
            print(f"[{now_ts()}] [DBG] {msg}")

    ##
    # @brief Print warning log / 警告ログを出力
    #
    # @if japanese
    # WARNレベルのメッセージをタイムスタンプ付きで出力します。
    # @endif
    #
    # @if english
    # Prints a WARN-level message with timestamp.
    # @endif
    #
    # @param msg [in]  ログメッセージ / Log message
    def warn(self, msg: str) -> None:
        print(f"[{now_ts()}] [WRN] {msg}")
