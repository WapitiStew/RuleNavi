"""
`py -m rulenavi ...` のときに実行されるファイル。

Python は `-m パッケージ名` で実行すると、
そのパッケージの `__main__.py` を探して実行する仕組みになっている。

例:
  py -m rulenavi all
  py -m rulenavi step1
"""

# CLI（コマンドライン）本体の main() を読み込む
from .cli import main

if __name__ == "__main__":
    # main() の戻り値（終了コード）でプロセスを終了する
    # 0: 成功 / それ以外: 失敗（bat 側の errorlevel に伝わる）
    raise SystemExit(main())
