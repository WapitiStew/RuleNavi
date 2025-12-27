from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

# ------------------------------------------------------------
# コマンド文字列
# ------------------------------------------------------------

CMD_ALL   = "all"
CMD_STEP1 = "step1"
CMD_STEP2 = "step2"
CMD_RUN   = "run"


# ------------------------------------------------------------
# ログ表示用の小さなユーティリティ
# ------------------------------------------------------------

def _ts() -> str:
    """
    現在時刻を "HH:MM:SS" 形式で返す。
    ログの見た目を揃えるために使う。
    """
    return time.strftime("%H:%M:%S")


def log(msg: str) -> None:
    """
    いつでも同じ見た目でログを出すための関数。
    """
    print(f"[{_ts()}] {msg}")


# ------------------------------------------------------------
# リポジトリルート（RuleNaviの最上位）を見つける処理
# ------------------------------------------------------------

def find_repo_root(start: Path) -> Path:
    """
    リポジトリルートを探索する。

    RuleNavi では、ルート直下に `.rulenavi_root` が置いてある前提なので、
    それが見つかるまで上のフォルダへたどる。

    こうすることで、どこでコマンドを実行しても "ROOT" が一定になる。
    （例えば tools/ 内や scripts/ 内から呼んでもOKにしたい）
    """
    p = start.resolve()

    # 上へ最大20階層まで探索（念のため無限ループ防止）
    for _ in range(20):
        if (p / ".rulenavi_root").exists():
            return p
        if p.parent == p:  # もうこれ以上上へ行けない（ドライブのルート等）
            break
        p = p.parent

    # 見つからない場合は start を返す（最低限動かす）
    return start.resolve()


# ------------------------------------------------------------
# scripts/ 以下の step*.py を呼び出すための関数
# ------------------------------------------------------------

def run_script(repo_root: Path, script_name: str, script_args: list[str]) -> int:
    """
    RuleNavi/scripts の中にある Python スクリプトを1本実行する。

    - repo_root: リポジトリのルートフォルダ
    - script_name: scripts フォルダにあるファイル名（例: step2_p01_dump_category_tree.py）
    - script_args: そのスクリプトに渡す引数（例: ["--out", "xxx"]）

    戻り値:
      - 0: 成功
      - それ以外: 失敗（bat 側の errorlevel に伝わる）
    """
    scripts_dir = repo_root / "scripts"
    script_path = scripts_dir / script_name

    # ファイルが存在するかチェック
    if not script_path.exists():
        log(f"[ERR] not found: {script_path}")
        return 2

    # 実行コマンドを作る
    # sys.executable を使うと、今動いている Python（venv も含む）で実行できる
    cmd = [sys.executable, str(script_path), *script_args]

    # 実行環境を調整する（重要）
    # 1) CWD（カレントディレクトリ）を repo_root に固定する
    #    → スクリプト内の相対パス処理が安定する
    #
    # 2) PYTHONPATH に repo_root/src を追加する
    #    → scripts から src のモジュール（sitegen等）が import できるようになる
    env = os.environ.copy()
    src_dir = str(repo_root / "src")
    env["PYTHONPATH"] = src_dir + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")

    # 実行ログ
    log("----------------------------------------")
    log(f"[RUN] {script_name} {' '.join(script_args)}".rstrip())
    log("----------------------------------------")

    # 実行（subprocess.run は外部コマンドを呼ぶための標準手段）
    r = subprocess.run(cmd, cwd=str(repo_root), env=env)

    # 失敗時はログを出す
    if r.returncode != 0:
        log(f"[ERR] failed: {script_name} (exit={r.returncode})")

    return int(r.returncode)


# ------------------------------------------------------------
# 「まとめ実行」コマンド群
# ------------------------------------------------------------

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

    for s in steps:
        ec = run_script(repo_root, s, [])
        if ec != 0:
            # どれか1つでも失敗したらそこで止める
            return ec
    return 0


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

def main(argv: list[str] | None = None) -> int:
    """
    `rulenavi ...` / `py -m rulenavi ...` の入口関数。

    argparse でコマンドを解析して、
    実行したい処理（all / step1 / step2 / run）へ振り分ける。
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

    # まとめ実行
    sub.add_parser("all", help="run STEP1 + STEP2")
    sub.add_parser("step1", help="run STEP1 only")
    sub.add_parser("step2", help="run STEP2 only")

    # 任意スクリプト実行
    # `argparse.REMAINDER` を使うと、残りの引数を「そのまま」受け取れる。
    # ただし混乱を避けるため、利用者には `--` を挟む運用を推奨する。
    p_run = sub.add_parser("run", help="run any script under scripts/")
    p_run.add_argument("script", help="script file name in scripts/ (e.g. step2_p01_dump_category_tree.py)")
    p_run.add_argument(
        "script_args",
        nargs=argparse.REMAINDER,
        help="arguments for the script (recommended to put after `--`)",
    )

    args = ap.parse_args(argv)

    # どこで実行してもルートを見つける
    repo_root = find_repo_root(Path.cwd())
    log(f"repo_root : {repo_root}")

    # 実行するコマンドを分岐
    if args.cmd == CMD_ALL:
        return cmd_all(repo_root)
    if args.cmd == CMD_STEP1:
        return cmd_step1(repo_root)
    if args.cmd == CMD_STEP2:
        return cmd_step2(repo_root)
    if args.cmd == CMD_RUN:
        # script_args は ["--", "--out", "xxx"] のように入る場合があるので、
        # 先頭が "--" なら取り除いてスクリプトへ渡す（見た目をきれいにする）
        script_args = list(args.script_args)
        if script_args[:1] == ["--"]:
            script_args = script_args[1:]
        return cmd_run(repo_root, args.script, script_args)

    # 通常ここには来ない（念のため）
    return 2
