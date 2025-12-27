# -*- coding: utf-8 -*-
##
# @file src/setting_helper.py
# @brief Path helper utilities derived from setting.csv values.
#
# @if japanese
# setting.csv の各キーからビルドディレクトリやリソースディレクトリ、JSON出力先などのパスを組み立てるユーティリティです。
# 文字列結合のみでロジック変更は行わず、パス算出を集約します。
# @endif
#
# @if english
# Utilities to assemble build, resource, JSON, and HTML paths based on setting.csv entries.
# Performs string concatenation only, centralizing path computations without altering logic.
# @endif
#

import pandas as pd  # [JP] 外部: DataFrame操作 / [EN] External: DataFrame handling
import setting_key as sk  # [JP] 自作: 設定キー定数 / [EN] Local: setting key constants


##
# @brief Build rules directory path / ルールのビルドディレクトリパスを取得
#
# @if japanese
# KEY_BUILD_DIR と KEY_RULES_DIR を結合してルール出力の基点パスを返します。
# @endif
#
# @if english
# Concatenates KEY_BUILD_DIR and KEY_RULES_DIR to return the base rules output path.
# @endif
#
# @param csv [in]  設定DataFrame / Settings DataFrame
# @return str  ルールビルドパス / Rules build path
def rules_path(csv: pd.DataFrame) -> str:
    setting_key = csv.set_index(csv.columns[0])
    setting_val = csv.columns[1]
    return (
        setting_key.at[sk.KEY_BUILD_DIR, setting_val]
        + "/"
        + setting_key.at[sk.KEY_RULES_DIR, setting_val]
    )


##
# @brief Build path including RULES_FILE_DIR / RULES_FILE_DIR を含むパスを取得
#
# @if japanese
# rules_pathにKEY_RULES_FILE_DIRを連結し、Markdownなどの格納ディレクトリパスを返します。
# @endif
#
# @if english
# Appends KEY_RULES_FILE_DIR to rules_path to obtain the directory for Markdown and related files.
# @endif
#
# @param csv [in]  設定DataFrame / Settings DataFrame
# @return str  ルールファイルディレクトリパス / Rules file directory path
def rules_file_dir_path(csv: pd.DataFrame) -> str:
    setting_key = csv.set_index(csv.columns[0])
    setting_val = csv.columns[1]
    return rules_path(csv) + "/" + setting_key.at[sk.KEY_RULES_FILE_DIR, setting_val]


##
# @brief Full path to a file under rules directory / ルールディレクトリ配下のファイルパスを取得
#
# @if japanese
# ビルドディレクトリとRULES_DIRを連結し、指定されたファイル名を付加したフルパスを返します。
# @endif
#
# @if english
# Joins build directory, RULES_DIR, and the given filename to produce a full path.
# @endif
#
# @param csv [in]  設定DataFrame / Settings DataFrame
# @param filename [in]  ファイル名 / Filename
# @return str  フルパス / Full path string
def rules_file_fullpath(csv: pd.DataFrame, filename: str) -> str:
    setting_key = csv.set_index(csv.columns[0])
    setting_val = csv.columns[1]
    return (
        setting_key.at[sk.KEY_BUILD_DIR, setting_val]
        + "/"
        + setting_key.at[sk.KEY_RULES_DIR, setting_val]
        + "/"
        + filename
    )


##
# @brief Resource directory path / リソースディレクトリのパスを取得
#
# @if japanese
# KEY_RESRC_DIR を返します。設定ファイルの親パス解決は行わず、値をそのまま使用します。
# @endif
#
# @if english
# Returns KEY_RESRC_DIR directly without further resolution.
# @endif
#
# @param csv [in]  設定DataFrame / Settings DataFrame
# @return str  リソースパス / Resource path
def resrc_path(csv: pd.DataFrame) -> str:
    setting_key = csv.set_index(csv.columns[0])
    setting_val = csv.columns[1]
    return setting_key.at[sk.KEY_RESRC_DIR, setting_val]


##
# @brief Full path to a resource file / リソースファイルのフルパスを取得
#
# @if japanese
# KEY_RESRC_DIR に指定ファイル名を連結し、リソースファイルのフルパスを返します。
# @endif
#
# @if english
# Appends the filename to KEY_RESRC_DIR to get the full path to a resource file.
# @endif
#
# @param csv [in]  設定DataFrame / Settings DataFrame
# @param filename [in]  ファイル名 / Filename
# @return str  フルパス / Full path string
def resrc_file_fullpath(csv: pd.DataFrame, filename: str) -> str:
    setting_key = csv.set_index(csv.columns[0])
    setting_val = csv.columns[1]
    return setting_key.at[sk.KEY_RESRC_DIR, setting_val] + "/" + filename


##
# @brief Full path to JSON output file / JSON出力ファイルのフルパスを取得
#
# @if japanese
# rules_pathとKEY_JSON_DIRを連結し、指定されたJSONファイル名のパスを返します。
# @endif
#
# @if english
# Combines rules_path with KEY_JSON_DIR and the given filename to return the JSON output path.
# @endif
#
# @param csv [in]  設定DataFrame / Settings DataFrame
# @param filename [in]  JSONファイル名 / JSON filename
# @return str  フルパス / Full path string
def json_file_fullpath(csv: pd.DataFrame, filename: str) -> str:
    setting_key = csv.set_index(csv.columns[0])
    setting_val = csv.columns[1]
    return rules_path(csv) + "/" + setting_key.at[sk.KEY_JSON_DIR, setting_val] + "/" + filename


##
# @brief HTML出力ディレクトリのパスを取得 / Get HTML output directory path
#
# @if japanese
# rules_path と KEY_HTML_DIR を連結し、HTML出力先のディレクトリパスを返します。
# @endif
#
# @if english
# Joins rules_path with KEY_HTML_DIR to return the HTML output directory path.
# @endif
#
# @param csv [in]  設定DataFrame / Settings DataFrame
# @return str  HTMLディレクトリパス / HTML directory path
def rule_html_dirpath(csv: pd.DataFrame) -> str:
    setting_key = csv.set_index(csv.columns[0])
    setting_val = csv.columns[1]
    return rules_path(csv) + "/" + setting_key.at[sk.KEY_HTML_DIR, setting_val]


##
# @brief Full path to an HTML file / HTMLファイルのフルパスを取得
#
# @if japanese
# rule_html_dirpathにファイル名を連結し、HTMLファイルのフルパスを返します。
# @endif
#
# @if english
# Appends the filename to rule_html_dirpath to produce the full HTML file path.
# @endif
#
# @param csv [in]  設定DataFrame / Settings DataFrame
# @param filename [in]  ファイル名 / Filename
# @return str  フルパス / Full path string
def rule_html_fullpath(csv: pd.DataFrame, filename: str) -> str:
    return rule_html_dirpath(csv) + "/" + filename
