# -*- coding: utf-8 -*-
##
# @file src/sitegen/page_builders/__init__.py
# @brief Export page writer entry points for site generation.
#
# @if japanese
# 各ページ用writer関数をまとめて公開するモジュールです。ページビルダー内の実装には手を入れず、エントリのみを再エクスポートします。
# 入出力はwriter関数に委ね、ここでは依存関係を集約するだけです。
# @endif
#
# @if english
# Module that re-exports page writer functions for site generation without altering their implementations.
# It centralizes dependencies while delegating all I/O and logic to the individual writer functions.
# @endif
#
from sitegen.page_builders.page_top import write as write_top  # [JP] 自作: TOPページ生成 / [EN] Local: write TOP page
from sitegen.page_builders.page_rules import write as write_rules  # [JP] 自作: 基準一覧ページ生成 / [EN] Local: write rules page
from sitegen.page_builders.page_products import write as write_products  # [JP] 自作: 製品ページ生成 / [EN] Local: write products page
from sitegen.page_builders.page_services import write as write_services  # [JP] 自作: サービスページ生成 / [EN] Local: write services page
from sitegen.page_builders.page_search import write as write_search  # [JP] 自作: 検索ページ生成 / [EN] Local: write search page
from sitegen.page_builders.page_wiki import write as write_wiki  # [JP] 自作: wikiページ生成 / [EN] Local: write wiki page
from sitegen.page_builders.page_howto import write as write_howto  # [JP] 自作: HowToページ生成 / [EN] Local: write how-to page

# [JP] 公開するwriter一覧 / [EN] List of exported writers
__all__ = [
    "write_top",
    "write_rules",
    "write_products",
    "write_services",
    "write_search",
    "write_wiki",
    "write_howto",
]