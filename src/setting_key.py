# -*- coding: utf-8 -*-
##
# @file src/setting_key.py
# @brief Constants for setting.csv keys.
#
# @if japanese
# setting.csv で使用するキー名を集約した定数定義モジュールです。各値は文字列のみでロジック変更はありません。
# コメントにより役割を補足し、他モジュールからのキー参照を一元化します。
# @endif
#
# @if english
# Centralized string constants representing keys used in setting.csv. Values remain unchanged; comments clarify their roles.
# Provides a single source of truth for key names across modules.
# @endif
#

from typing import Final  # [JP] 標準: イミュータブル定数用ヒント / [EN] Standard: type hint for immutable constants

# 基本パス系 / Base directories
KEY_RESRC_DIR: Final[str] = "RESRC_DIR"  # 入力ディレクトリ / resource directory
KEY_BUILD_DIR: Final[str] = "BUILD_DIR"  # 出力ディレクトリ / build output directory
KEY_SRC_EXCEL: Final[str] = "DB_SRC_EXCEL"  # Excel ファイル名（必要なら変更可） / source Excel name
KEY_DB_NAME: Final[str] = "DB_NAME"  # 作成されるSQLite ファイル / SQLite database filename

# ルールファイル出力パス / Rule file paths
KEY_RULES_DIR: Final[str] = "RULES_DIR"  # ルール保存ディレクトリ / rules directory
KEY_RULES_FILE_DIR: Final[str] = "RULES_FILE_DIR"  # ルールファイル保存サブディレクトリ / rule file subdir

# JSON/HTML/MD関連 / JSON, HTML, Markdown
KEY_JSON_DIR: Final[str] = "JSON_DIR"  # JSON出力ディレクトリ / JSON output directory
KEY_JSON_MAIN_TREE: Final[str] = "JSON_MAIN_TREE"  # ルールツリーJSONファイル名 / tree JSON filename
KEY_JSON_MAIN_INDEX: Final[str] = "JSON_MAIN_INDEX"  # ルールインデックスJSONファイル名 / index JSON filename
KEY_MD_RULE_FILENAME: Final[str] = "MD_RULE_FILENAME"  # ルールMDファイル名 / rule markdown filename
KEY_TSV_MANIFEST_RULE_CAP: Final[str] = "TSV_MANIFEST_RULE_CAP"  # ルールマニフェストTSV / manifest TSV
KEY_HTML_DIR: Final[str] = "HTML_DIR"  # HTML出力ディレクトリ / HTML output directory
KEY_HTML_MAIN: Final[str] = "HTML_MAIN"  # ルールツリーHTMLファイル名 / main HTML filename
KEY_SITE_DIR: Final[str] = "SITE_DIR"  # site output dir under BUILD_DIR
KEY_SITE_TITLE: Final[str] = "SITE_TITLE"  # title shown in header
KEY_SITE_INDEX_HTML: Final[str] = "SITE_INDEX_HTML"  # entry html name
KEY_SITE_APP_JS: Final[str] = "SITE_APP_JS"  # app js name
KEY_MD_BODY_FILENAME: Final[str] = "MD_BODY_FILENAME"  # markdown body filename in each rule dir

# カテゴリ系テーブル / Category tables
KEY_TBL_CAT_TYPE: Final[str] = "TBL_CAT_TYPE"  # 基準類テーブル / category type table
KEY_ITM_CAT_TYPE_PKEY: Final[str] = "ITM_CAT_TYPE_PKEY"  # キー大分類キー / type primary key
KEY_ITM_CAT_TYPE_TITLE_JP: Final[str] = "ITM_CAT_TYPE_TITLE_JP"  # 日本語名称 / type title JP
KEY_ITM_CAT_TYPE_TITLE_EN: Final[str] = "ITM_CAT_TYPE_TITLE_EN"  # 英語名称 / type title EN
KEY_ITM_CAT_TYPE_PATH: Final[str] = "ITM_CAT_TYPE_PATH"  # 保存用フォルダのパス / type path

KEY_TBL_CAT_MAJOR: Final[str] = "TBL_CAT_MAJOR"  # 基準大分類テーブル / major category table
KEY_ITM_CAT_MAJOR_PKEY: Final[str] = "ITM_CAT_MAJOR_PKEY"  # 中分類キー / major key
KEY_ITM_CAT_MAJOR_TITLE_JP: Final[str] = "ITM_CAT_MAJOR_TITLE_JP"  # 日本語名称 / major title JP
KEY_ITM_CAT_MAJOR_TITLE_EN: Final[str] = "ITM_CAT_MAJOR_TITLE_EN"  # 英語名称 / major title EN
KEY_ITM_CAT_MAJOR_FKEY_CAT_TYPE: Final[str] = "ITM_CAT_MAJOR_FKEY_CAT_TYPE"  # 対応する大分類key_cat_type / FK to type
KEY_ITM_CAT_MAJOR_PATH: Final[str] = "ITM_CAT_MAJOR_PATH"  # 保存用フォルダのパス / major path

KEY_TBL_CAT_SUB: Final[str] = "TBL_CAT_SUB"  # 基準小分類テーブル / sub category table
KEY_ITM_CAT_SUB_PKEY: Final[str] = "ITM_CAT_SUB_PKEY"  # 小分類キー / sub key
KEY_ITM_CAT_SUB_TITLE_JP: Final[str] = "ITM_CAT_SUB_TITLE_JP"  # 日本語名称 / sub title JP
KEY_ITM_CAT_SUB_TITLE_EN: Final[str] = "ITM_CAT_SUB_TITLE_EN"  # 英語名称 / sub title EN
KEY_ITM_CAT_SUB_FKEY_CAT_MAJOR: Final[str] = "ITM_CAT_SUB_FKEY_CAT_MAJOR"  # 対応する中分類key_cat_major / FK to major
KEY_ITM_CAT_SUB_PATH: Final[str] = "ITM_CAT_SUB_PATH"  # 保存用フォルダのパス / sub path

KEY_TBL_CAT_STATE: Final[str] = "TBL_CAT_STATE"  # 状態テーブル / state table
KEY_ITM_CAT_STATE_PKEY: Final[str] = "ITM_CAT_STATE_PKEY"  # 状態ID / state ID
KEY_ITM_CAT_STATE_TITLE_JP: Final[str] = "ITM_CAT_STATE_TITLE_JP"  # 日本語名称 / state title JP
KEY_ITM_CAT_STATE_TITLE_EN: Final[str] = "ITM_CAT_STATE_TITLE_EN"  # 英語名称 / state title EN

# ルールテーブル / Rule table
KEY_TBL_RULES: Final[str] = "TBL_RULES"  # ルールテーブル / rules table
KEY_ITM_RULES_PKEY: Final[str] = "ITM_RULES_PKEY"  # ルール通し番号 / primary key
KEY_ITM_RULES_ID_RULE: Final[str] = "ITM_RULES_ID_RULE"  # ルールID / rule identifier
KEY_ITM_RULES_NAME_RULE: Final[str] = "ITM_RULES_NAME_RULE"  # ルール名 / rule name
KEY_ITM_RULES_FKEY_CAT_SUB: Final[str] = "ITM_RULES_FKEY_CAT_SUB"  # 小分類キー / FK to sub
KEY_ITM_RULES_LINK: Final[str] = "ITM_RULES_LINK"  # 関連URL / link URL
KEY_ITM_RULES_FKEY_CAT_STATE: Final[str] = "ITM_RULES_FKEY_CAT_STATE"  # 状態ID / FK to state
KEY_ITM_RULES_CREATED_DATE: Final[str] = "ITM_RULES_CREATED_DATE"  # 制定日 / created date
KEY_ITM_RULES_UPDATE_DATE: Final[str] = "ITM_RULES_UPDATE_DATE"  # 改訂日 / updated date

# 設計領域カテゴリ / Request categories
KEY_TBL_CAT_REQUEST: Final[str] = "TBL_CAT_REQUEST"  # 設計領域テーブル / request category table
KEY_ITM_CAT_REQUEST_PKEY: Final[str] = "ITM_CAT_REQUEST_PKEY"  # 設計領域ID / request ID
KEY_ITM_CAT_REQUEST_TITLE_JP: Final[str] = "ITM_CAT_REQUEST_TITLE_JP"  # 日本語名称 / request title JP
KEY_ITM_CAT_REQUEST_TITLE_EN: Final[str] = "ITM_CAT_REQUEST_TITLE_EN"  # 英語名称 / request title EN
KEY_ITM_CAT_REQUEST_KEY_CAT_REQ_TYPE: Final[str] = "ITM_CAT_REQUEST_KEY_CAT_REQ_TYPE"  # 要件種類ID / request type key
KEY_ITM_CAT_REQUEST_REQ_TYPE: Final[str] = "ITM_CAT_REQUEST_REQ_TYPE"  # 要件種類 / request type

# フェーズカテゴリ / Phase categories
KEY_TBL_CAT_PHASE: Final[str] = "TBL_CAT_PHASE"  # 設計領域テーブル / phase table
KEY_ITM_CAT_PHASE_PKEY: Final[str] = "ITM_CAT_PHASE_PKEY"  # 設計領域ID / phase ID
KEY_ITM_CAT_PHASE_TITLE_JP: Final[str] = "ITM_CAT_PHASE_TITLE_JP"  # 日本語名称 / phase title JP
KEY_ITM_CAT_PHASE_TITLE_EN: Final[str] = "ITM_CAT_PHASE_TITLE_EN"  # 英語名称 / phase title EN

# スコープカテゴリ / Scope categories
KEY_TBL_SCP_SALES_REGION: Final[str] = "TBL_SCP_SALES_REGION"  # 要件類テーブル / sales region table
KEY_ITM_SCP_SALES_REGION_PKEY: Final[str] = "ITM_SCP_SALES_REGION_PKEY"  # 販売地域ID / sales region ID
KEY_ITM_SCP_SALES_REGION_TITLE_JP: Final[str] = "ITM_SCP_SALES_REGION_TITLE_JP"  # 日本語名称 / sales region title JP
KEY_ITM_SCP_SALES_REGION_TITLE_EN: Final[str] = "ITM_SCP_SALES_REGION_TITLE_EN"  # 英語名称 / sales region title EN
KEY_ITM_SCP_SALES_REGION_COUNTRY_CODE_2: Final[str] = (
    "ITM_SCP_SALES_REGION_COUNTRY_CODE_2"  # 国コード2桁 / ISO 3166-1 alpha-2
)
KEY_ITM_SCP_SALES_REGION_COUNTRY_CODE_3: Final[str] = (
    "ITM_SCP_SALES_REGION_COUNTRY_CODE_3"  # 国コード3桁 / ISO 3166-1 alpha-3
)

KEY_TBL_SCP_PRODUCT_GENRE: Final[str] = "TBL_SCP_PRODUCT_GENRE"  # 製品ジャンルテーブル / product genre
KEY_ITM_SCP_PRODUCT_GENRE_PKEY: Final[str] = "ITM_SCP_PRODUCT_GENRE_PKEY"  # 製品ジャンルID / product genre ID
KEY_ITM_SCP_PRODUCT_GENRE_TITLE_JP: Final[str] = "ITM_SCP_PRODUCT_GENRE_TITLE_JP"  # 日本語名称 / product genre title JP
KEY_ITM_SCP_PRODUCT_GENRE_TITLE_EN: Final[str] = "ITM_SCP_PRODUCT_GENRE_TITLE_EN"  # 英語名称 / product genre title EN
KEY_ITM_SCP_PRODUCT_GENRE_HS_CODE: Final[str] = "ITM_SCP_PRODUCT_GENRE_HS_CODE"  # HSコード / HS code

KEY_TBL_SCP_SERVICE_GENRE: Final[str] = "TBL_SCP_SERVICE_GENRE"  # サービスジャンルテーブル / service genre
KEY_ITM_SCP_SERVICE_GENRE_PKEY: Final[str] = "ITM_SCP_SERVICE_GENRE_PKEY"  # 製品ジャンルID / service genre ID
KEY_ITM_SCP_SERVICE_GENRE_TITLE_JP: Final[str] = "ITM_SCP_SERVICE_GENRE_TITLE_JP"  # 日本語名称 / service genre title JP
KEY_ITM_SCP_SERVICE_GENRE_TITLE_EN: Final[str] = "ITM_SCP_SERVICE_GENRE_TITLE_EN"  # 英語名称 / service genre title EN

KEY_TBL_SCP_EQUIPMENT: Final[str] = "TBL_SCP_EQUIPMENT"  # 設備テーブル / equipment table
KEY_ITM_SCP_EQUIPMENT_PKEY: Final[str] = "ITM_SCP_EQUIPMENT_PKEY"  # 設備ID / equipment ID
KEY_ITM_SCP_EQUIPMENT_TITLE_JP: Final[str] = "ITM_SCP_EQUIPMENT_TITLE_JP"  # 日本語名称 / equipment title JP
KEY_ITM_SCP_EQUIPMENT_TITLE_EN: Final[str] = "ITM_SCP_EQUIPMENT_TITLE_EN"  # 英語名称 / equipment title EN

KEY_TBL_SCP_PII: Final[str] = "TBL_SCP_PII"  # 個人情報テーブル / PII table
KEY_ITM_SCP_PII_PKEY: Final[str] = "ITM_SCP_PII_PKEY"  # 個人情報ID / PII ID
KEY_ITM_SCP_PII_TITLE_JP: Final[str] = "ITM_SCP_PII_TITLE_JP"  # 日本語名称 / PII title JP
KEY_ITM_SCP_PII_TITLE_EN: Final[str] = "ITM_SCP_PII_TITLE_EN"  # 英語名称 / PII title EN

KEY_TBL_SCP_DESIGN_DOMAIN: Final[str] = "TBL_SCP_DESIGN_DOMAIN"  # 設計領域テーブル / design domain table
KEY_ITM_SCP_DESIGN_DOMAIN_PKEY: Final[str] = "ITM_SCP_DESIGN_DOMAIN_PKEY"  # 設計領域ID / design domain ID
KEY_ITM_SCP_DESIGN_DOMAIN_TITLE_JP: Final[str] = "ITM_SCP_DESIGN_DOMAIN_TITLE_JP"  # 日本語名称 / design domain title JP
KEY_ITM_SCP_DESIGN_DOMAIN_TITLE_EN: Final[str] = "ITM_SCP_DESIGN_DOMAIN_TITLE_EN"  # 英語名称 / design domain title EN

# 要件テーブル / Request table
KEY_TBL_REQUEST: Final[str] = "TBL_REQUEST"  # 要件テーブル / request table
KEY_ITM_REQUEST_PKEY: Final[str] = "ITM_REQUEST_PKEY"  # 要件キー / request PK
KEY_ITM_REQUEST_KEY_RULE: Final[str] = "ITM_REQUEST_KEY_RULE"  # 基準キー / FK to rule
KEY_ITM_REQUEST_ID_CAP: Final[str] = "ITM_REQUEST_ID_CAP"  # 章名称 / chapter ID
KEY_ITM_REQUEST_FTITLE_CAPTER: Final[str] = "ITM_REQUEST_FTITLE_CAPTER"  # 節名称 / chapter title
KEY_ITM_REQUEST_TITLE_SECTION: Final[str] = "ITM_REQUEST_TITLE_SECTION"  # 本文タイトル / section title
KEY_ITM_REQUEST_FTOP_BODY: Final[str] = "ITM_REQUEST_FTOP_BODY"  # 本文上段 / top body
KEY_ITM_REQUEST_LOW_BODY: Final[str] = "ITM_REQUEST_LOW_BODY"  # 本文下段 / low body
KEY_ITM_REQUEST_TOP_TBL: Final[str] = "ITM_REQUEST_TOP_TBL"  # 表(上) / top table
KEY_ITM_REQUEST_TOP_FIG: Final[str] = "ITM_REQUEST_TOP_FIG"  # 図(上) / top figure
KEY_ITM_REQUEST_LOW_TBL: Final[str] = "ITM_REQUEST_LOW_TBL"  # 表(下) / low table
KEY_ITM_REQUEST_LOW_FIG: Final[str] = "ITM_REQUEST_LOW_FIG"  # 図(下) / low figure
KEY_ITM_REQUEST_LEAD_TIME: Final[str] = "ITM_REQUEST_LEAD_TIME"  # リードタイム / lead time
KEY_ITM_REQUEST_REFERENCE: Final[str] = "ITM_REQUEST_REFERENCE"  # 参考 / reference
KEY_ITM_REQUEST_CREATED_DATE: Final[str] = "ITM_REQUEST_CREATED_DATE"  # 制定日など / created date
KEY_ITM_REQUEST_FUPDATE_DATE: Final[str] = "ITM_REQUEST_FUPDATE_DATE"  # 改訂日など / updated date
KEY_ITM_REQUEST_FKEY_CAT_REQUEST: Final[str] = "ITM_REQUEST_FKEY_CAT_REQUEST"  # 要求カテゴリID / FK to request cat
KEY_ITM_REQUEST_FKEY_CAT_PHASE: Final[str] = "ITM_REQUEST_FKEY_CAT_PHASE"  # 対応フェーズID / FK to phase
KEY_ITM_REQUEST_FSCOPE_PRODUCT_GENRE: Final[str] = (
    "ITM_REQUEST_FSCOPE_PRODUCT_GENRE"  # 製品ジャンル(複数持ち可 中間テーブル初回生成用) / product genre scope
)
KEY_ITM_REQUEST_FSCOPE_SERVICE_GENRE: Final[str] = (
    "ITM_REQUEST_FSCOPE_SERVICE_GENRE"  # サービスジャンル(複数持ち可 中間テーブル初回生成用) / service genre scope
)
KEY_ITM_REQUEST_FSCOPE_EQUIPMENT: Final[str] = (
    "ITM_REQUEST_FSCOPE_EQUIPMENT"  # 設備(複数持ち可 中間テーブル初回生成用) / equipment scope
)
KEY_ITM_REQUEST_FSCOPE_PII: Final[str] = (
    "ITM_REQUEST_FSCOPE_PII"  # 個人情報(複数持ち可 中間テーブル初回生成用) / PII scope
)
KEY_ITM_REQUEST_FSCOPE_DESIGN_DOMAIN: Final[str] = (
    "ITM_REQUEST_FSCOPE_DESIGN_DOMAIN"  # 設計領域(複数持ち可 中間テーブル初回生成用) / design domain scope
)
KEY_ITM_REQUEST_UNIQUE_SEARCH: Final[str] = (
    "ITM_REQUEST_UNIQUE_SEARCH"  # 固有条件(複数持ち可 中間テーブル初回生成用) / unique search key
)
