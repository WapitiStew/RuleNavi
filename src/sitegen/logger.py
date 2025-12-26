# -*- coding: utf-8 -*-
from __future__ import annotations

import time


def now_ts() -> str:
    return time.strftime("%H:%M:%S")


class Logger:
    def __init__(self, verbose: bool = True) -> None:
        self.verbose = verbose

    def info(self, msg: str) -> None:
        print(f"[{now_ts()}] {msg}")

    def debug(self, msg: str) -> None:
        if self.verbose:
            print(f"[{now_ts()}] [DBG] {msg}")

    def warn(self, msg: str) -> None:
        print(f"[{now_ts()}] [WRN] {msg}")
