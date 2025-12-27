# -*- coding: utf-8 -*-
##
# @file src/rulenavi/cli.py
# @brief Command runner for RuleNavi scripts.
#
# @if japanese
# RuleNavi配下のscripts/にあるstep*.pyをまとめて実行したり、個別に実行するためのCLIユーティリティです。
# リポジトリルート検出、ログ表示、サブコマンド(all/step1/step2/run)のディスパッチを行います。
# ロジックはサブプロセス呼び出しと環境変数設定のみで、ビジネスデータには触れません。
# @endif
#
# @if english
# CLI utility to run RuleNavi step scripts under scripts/ either in batch or individually.
# Handles repository root discovery, logging, and dispatch for subcommands (all/step1/step2/run).
# Only manages subprocess execution and environment setup without touching business data.
# @endif
#

from __future__ import annotations

import argparse  # [JP] 標準: CLI引数処理 / [EN] Standard: CLI argument parsing
import os  # [JP] 標準: 環境変数操作 / [EN] Standard: environment handling
import subprocess  # [JP] 標準: 外部プロセス実行 / [EN] Standard: subprocess execution
import sys  # [JP] 標準: 実行中Pythonの情報 / [EN] Standard: interpreter info
import time  # [JP] 標準: 時刻取得 / [EN] Standard: timestamp utilities
from pathlib import Path  # [JP] 標準: パス操作 / [EN] Standard: path utilities

# ------------------------------------------------------------
# コマンド文字列（サブコマンド名）
# ------------------------------------------------------------

CMD_ALL = "all"
CMD_STEP1 = "step1"
CMD_STEP2 = "step2"
CMD_RUN = "run"


# ------------------------------------------------------------
# ログ表示用の小さなユーティリティ
# ------------------------------------------------------------

##
# @brief Get current time string HH:MM:SS / 現在時刻をHH:MM:SSで返す
#
# @if japanese
# ログ表示用に時刻文字列を返します。処理ロジックは単純なstrftimeのみです。
# @endif
#
# @if english
# Returns the current time as HH:MM:SS for log prefixing; uses strftime without side effects.
# @endif
#
# @return str  時刻文字列 / Time string
def _ts() -> str:
    """
    現在時刻を"HH:MM:SS" 形式で返す。
    ログの見た目を揃えるために使う。
    """
    return time.strftime("%H:%M:%S")


##
# @brief Print a log line with timestamp / タイムスタンプ付きでログを出力
#
# @if japanese
# 標準出力に簡易ログを表示します。フォーマットは [_ts()] msg で固定です。
# @endif
#
# @if english
# Prints a simple log line to stdout, formatting as [_ts()] msg.
# @endif
#
# @param msg [in]  出力するメッセージ / Message to log
def log(msg: str) -> None:
    """
    どこでも同じ見た目でログを出すための関数。
    """
    print(f"[{_ts()}] {msg}")


# ------------------------------------------------------------
# リポジトリルート（RuleNaviの最上位）を見つける処理
# ------------------------------------------------------------

##
# @brief Find repository root containing .rulenavi_root / .rulenavi_root を含むリポジトリルートを探す
#
# @if japanese
# 指定ディレクトリから親方向に最大20階層辿り、.rulenavi_root が見つかった場所をルートとして返します。
# 見つからない場合は開始ディレクトリを返し、ファイルI/Oや環境変更は行いません。
# @endif
#
# @if english
# Walks up to 20 parent levels from the given start path to locate .rulenavi_root and returns that directory.
# Falls back to the starting path if not found; performs no I/O beyond existence checks.
# @endif
#
# @param start [in]  探索開始パス / Starting path for search
# @return Path  ルート推定パス / Resolved repository root path
def find_repo_root(start: Path) -> Path:
    """
    リポジトリルートを探索する。

    RuleNavi では、ルート直下に `.rulenavi_root` が置いてある前提なので、
    それが見つかるまで上のフォルダへたどる。

    こうすることで、どこでコマンドを実行しても"ROOT" が一定になる。
    （例えば tools/ や scripts/ から呼んでもOKにしたい）
    """
    p = start.resolve()

    # [JP] 上へ最大20階層まで探索（無限ループ防止） / [EN] Traverse up to 20 levels to avoid infinite loops
    for _ in range(20):
        if (p / ".rulenavi_root").exists():
            return p
        if p.parent == p:  # ルート到達
            break
        p = p.parent

    # [JP] 見つからない場合は開始位置を返す / [EN] Return start path if not found
    return start.resolve()


# ------------------------------------------------------------
# scripts/ 以下の step*.py を呼び出すための関数
# ------------------------------------------------------------

##
# @brief Run a script under scripts/ with provided args / scripts/配下のスクリプトを引数付きで実行する
#
# @if japanese
# repo_root/scripts 配下のPythonスクリプトをサブプロセスで起動します。CWDをrepo_rootに固定し、
# PYTHONPATHにsrcを追加してプロジェクト内モジュールをインポート可能にします。
# @endif
#
# @if english
# Launches a Python script under repo_root/scripts as a subprocess, fixing CWD to repo_root
# and augmenting PYTHONPATH with src to ensure project modules are importable.
# @endif
#
# @param repo_root [in]  リポジトリルートパス / Repository root path
# @param script_name [in]  実行するスクリプト名 / Script filename under scripts/
# @param script_args [in]  スクリプトへ渡す引数リスト / Arguments to pass to the script
# @return int  終了コード(0成功) / Exit code (0 on success)
# @details
# @if japanese
# - スクリプトファイルの存在をチェックする。
# - sys.executableを使い現在のPython環境で実行する。
# - 環境変数PYTHONPATHにsrcを追加する。
# - 実行結果のreturncodeをそのまま返す。
# @endif
# @if english
# - Verify script file existence.
# - Use sys.executable to run with current Python environment.
# - Prepend src to PYTHONPATH in the child environment.
# - Return the subprocess exit code unchanged.
# @endif
#
def run_script(repo_root: Path, script_name: str, script_args: list[str]) -> int:
    """
    RuleNavi/scripts の中にある Python スクリプトを本実行する。

    - repo_root: リポジトリのルートフォルダ
    - script_name: scripts フォルダにあるファイル名（例: step2_p01_dump_category_tree.py）
    - script_args: そのスクリプトに渡す引数（例: ["--out", "xxx"]）

    戻り値:
      - 0: 成功
      - それ以外: 失敗（bat 側の errorlevel に伝わる）
    """
    scripts_dir = repo_root / "scripts"
    script_path = scripts_dir / script_name

    # [JP] スクリプト存在チェック / [EN] Verify script existence
    if not script_path.exists():
        log(f"[ERR] not found: {script_path}")
        return 2

    # [JP] 実行コマンド組み立て / [EN] Build command line
    cmd = [sys.executable, str(script_path), *script_args]

    # [JP] CWDとPYTHONPATHを設定 / [EN] Configure CWD and PYTHONPATH
    env = os.environ.copy()
    src_dir = str(repo_root / "src")
    env["PYTHONPATH"] = src_dir + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")

    # [JP] 実行ログ / [EN] Log execution
    log("----------------------------------------")
    log(f"[RUN] {script_name} {' '.join(script_args)}".rstrip())
    log("----------------------------------------")

    # [JP] サブプロセス実行 / [EN] Run subprocess
    r = subprocess.run(cmd, cwd=str(repo_root), env=env)

    # [JP] 非ゼロ終了時にログ / [EN] Log on non-zero exit
    if r.returncode != 0:
        log(f"[ERR] failed: {script_name} (exit={r.returncode})")

    return int(r.returncode)


# ------------------------------------------------------------
# 「まとめ実行」コマンド群
# ------------------------------------------------------------

##
# @brief Run STEP1 and STEP2 scripts sequentially / STEP1とSTEP2を順に実行する
#
# @if japanese
# step1_p00〜step2_p05までを順番に呼び、途中で失敗した場合はそのコードで停止します。
# @endif
#
# @if english
# Executes step1_p00 through step2_p05 in order, stopping at the first non-zero exit code.
# @endif
#
# @param repo_root [in]  リポジトリルート / Repository root
# @return int  終了コード / Exit code
# @details
# @if japanese
# - 固定リストstepsを走査しrun_scriptで実行。
# - いずれかが非0なら即return。
# - 全て成功なら0。
# @endif
# @if english
# - Iterate fixed steps list and call run_script.
# - Return immediately on non-zero exit.
# - Return 0 when all succeed.
# @endif
#
def cmd_all(repo_root: Path) -> int:
    """
    STEP1 + STEP2 を全部実行する。
    """
    steps: list[str] = [
        "step1_p00_check_excel.py",
        "step1_p01_import_excel_to_sqlite.py",
        "step1_p02_check_db.py",
        "step2_p00_make_directory_rules.py",
        "step2_p01_dump_category_tree.py",
        "step2_p02_export_tree_json.py",
        "step2_p03_export_rules_index.py",
        "step2_p04_export_markdown_rules.py",
        "step2_p05_make_site_stub.py",
    ]

    # [JP] 各ステップを順次実行 / [EN] Run each step sequentially
    for s in steps:
        ec = run_script(repo_root, s, [])
        if ec != 0:
            return ec
    return 0


##
# @brief Run only STEP1 scripts / STEP1のみ実行する
#
# @if japanese
# STEP1の3スクリプトを順に実行し、途中で失敗したらそのコードで終了します。
# @endif
#
# @if english
# Runs the three STEP1 scripts sequentially, returning the first non-zero exit code if any.
# @endif
#
# @param repo_root [in]  リポジトリルート / Repository root
# @return int  終了コード / Exit code
def cmd_step1(repo_root: Path) -> int:
    """
    STEP1 だけ実行する。
    """
    steps: list[str] = [
        "step1_p00_check_excel.py",
        "step1_p01_import_excel_to_sqlite.py",
        "step1_p02_check_db.py",
    ]
    for s in steps:
        ec = run_script(repo_root, s, [])
        if ec != 0:
            return ec
    return 0


##
# @brief Run only STEP2 scripts / STEP2のみ実行する
#
# @if japanese
# STEP2の6スクリプトを順番に実行し、失敗時はそのコードを返します。
# @endif
#
# @if english
# Runs the six STEP2 scripts in order, returning the exit code of the first failure.
# @endif
#
# @param repo_root [in]  リポジトリルート / Repository root
# @return int  終了コード / Exit code
def cmd_step2(repo_root: Path) -> int:
    """
    STEP2 だけ実行する。
    """
    steps: list[str] = [
        "step2_p00_make_directory_rules.py",
        "step2_p01_dump_category_tree.py",
        "step2_p02_export_tree_json.py",
        "step2_p03_export_rules_index.py",
        "step2_p04_export_markdown_rules.py",
        "step2_p05_make_site_stub.py",
    ]
    for s in steps:
        ec = run_script(repo_root, s, [])
        if ec != 0:
            return ec
    return 0


##
# @brief Run arbitrary script under scripts/ / 任意のscripts配下スクリプトを実行
#
# @if japanese
# runサブコマンド用のディスパッチで、渡されたスクリプト名と引数をそのままrun_scriptに委譲します。
# @endif
#
# @if english
# Dispatcher for the run subcommand; forwards script name and args to run_script.
# @endif
#
# @param repo_root [in]  リポジトリルート / Repository root
# @param script_name [in]  スクリプト名 / Script filename
# @param script_args [in]  スクリプト引数 / Script arguments
# @return int  終了コード / Exit code
def cmd_run(repo_root: Path, script_name: str, script_args: list[str]) -> int:
    """
    任意スクリプト実行用。

    例:
      rulenavi run step2_p01_dump_category_tree.py -- --out out.txt --log-level DEBUG

    ポイント:
      - `--` 以降を「スクリプト側の引数」としてそのまま渡す
      - これにより rulenavi 自身の引数解析と衝突しない
    """
    return run_script(repo_root, script_name, script_args)


# ------------------------------------------------------------
# CLI（コマンド）としての入口
# ------------------------------------------------------------

##
# @brief CLI main entry point / CLIエントリーポイント
#
# @if japanese
# argparseでサブコマンドを解析し、all/step1/step2/runに応じて処理を分岐します。
# スクリプト実行時の引数は`--`以降をスクリプト側へそのまま渡します。
# @endif
#
# @if english
# Parses subcommands with argparse and dispatches to all/step1/step2/run handlers.
# Passes arguments after `--` directly to the target script.
# @endif
#
# @param argv [in]  解析対象の引数リスト（省略時はsys.argv） / Arguments to parse (defaults to sys.argv)
# @return int  終了コード / Exit code
# @details
# @if japanese
# - argparseでサブコマンドと引数を設定。
# - repo_rootをfind_repo_rootで解決しログ出力。
# - サブコマンドに応じてcmd_*関数を呼ぶ。runの場合は先頭の"--"を除去して渡す。
# - 想定外のcmdでは2を返す。
# @endif
# @if english
# - Configure argparse subcommands and options.
# - Resolve repo_root via find_repo_root and log it.
# - Invoke cmd_* functions based on parsed command; strip leading "--" for run args.
# - Return 2 for unexpected command values.
# @endif
#
def main(argv: list[str] | None = None) -> int:
    """
    `rulenavi ...` / `py -m rulenavi ...` の入口関数。

    argparse でコマンドを解析して、
    実行したい処理を All / step1 / step2 / run に振り分ける。
    """
    ap = argparse.ArgumentParser(
        prog="rulenavi",
        description=(
            "RuleNavi command runner.\n"
            "Tips: pass script args after `--`.\n"
            "  rulenavi run step2_p01_dump_category_tree.py -- --out out.txt"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )

    sub = ap.add_subparsers(dest="cmd", required=True)

    # [JP] まとめ実行 / [EN] Batch execution
    sub.add_parser("all", help="run STEP1 + STEP2")
    sub.add_parser("step1", help="run STEP1 only")
    sub.add_parser("step2", help="run STEP2 only")

    # [JP] 任意スクリプト実行 / [EN] Arbitrary script execution
    p_run = sub.add_parser("run", help="run any script under scripts/")
    p_run.add_argument("script", help="script file name in scripts/ (e.g. step2_p01_dump_category_tree.py)")
    p_run.add_argument(
        "script_args",
        nargs=argparse.REMAINDER,
        help="arguments for the script (recommended to put after `--`)",
    )

    args = ap.parse_args(argv)

    # [JP] どこで実行してもルートを見つける / [EN] Resolve repo root regardless of CWD
    repo_root = find_repo_root(Path.cwd())
    log(f"repo_root : {repo_root}")

    # [JP] サブコマンドごとに処理を分岐 / [EN] Dispatch based on subcommand
    if args.cmd == CMD_ALL:
        return cmd_all(repo_root)
    if args.cmd == CMD_STEP1:
        return cmd_step1(repo_root)
    if args.cmd == CMD_STEP2:
        return cmd_step2(repo_root)
    if args.cmd == CMD_RUN:
        # [JP] 先頭の"--"を除去してスクリプトに渡す / [EN] Strip leading "--" before forwarding
        script_args = list(args.script_args)
        if script_args[:1] == ["--"]:
            script_args = script_args[1:]
        return cmd_run(repo_root, args.script, script_args)

    # [JP] 想定外のcmdはエラーコード2 / [EN] Unexpected command fallback
    return 2
