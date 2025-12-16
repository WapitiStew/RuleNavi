from pathlib import Path
from typing import List, Tuple
import sqlite3
import pandas as pd
import re

import utility.read_setting as rs
import setting_key as sk

# Excelシートを「1行目をヘッダとして」「余計な列を削った」形で読み込む
def load_sheet_clean( excel_path: Path, sheet_name: str) -> pd.DataFrame:

    print(f"Exxcel file: {excel_path}   /   Sheet: {sheet_name}")

    # header=None で「全部データ」として読み込む
    df_raw = pd.read_excel(excel_path, sheet_name=sheet_name, header=None)

    # 1行目をヘッダ行として取り出す
    header = df_raw.iloc[0]
    df = df_raw.iloc[1:].copy()   # 2行目以降がデータ
    df.columns = header           # ヘッダを列名としてセット

    # 見出しが NaN（空）の列は削除
    df = df.loc[:, ~df.columns.isna()]

    # 見出しが重複している列は「最初の1個だけ残す」
    df = df.loc[:, ~df.columns.duplicated()]

    # 文字列列の前後の空白をトリム
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace({"": None, "nan": None})

    return df


def quote_ident(name: str) -> str:
    # 安全のため、許可する名前を制限（必要なら緩めてOK）
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        raise ValueError(f"Invalid table name: {name}")
    return f'"{name}"'  # SQLiteの識別子クォート


def build_create_table_sql(table_name: str, col_defs: List[Tuple[str, str, str]]) -> str:
    """列定義から CREATE TABLE 文を生成する。"""
    lines = []
    n = len(col_defs)

    for i, (col, typ, remark) in enumerate(col_defs):
        line = f'    {quote_ident(col)} {typ}'

        # ★カンマはコメントより前に付ける
        if i < n - 1:
            line += ','

        if remark and str(remark).strip() and str(remark).strip().lower() != "nan":
            r = str(remark).strip()
            # もし "--" が付いてなければ付ける（好みで）
            if not r.startswith("--"):
                r = "-- " + r
            line += f'  {r}'

        lines.append(line)

    body = "\n".join(lines)
    return f'CREATE TABLE {quote_ident(table_name)} (\n{body}\n);\n'


# SQLite に明示的なスキーマを作る
def create_tables(csv: pd.DataFrame, conn: sqlite3.Connection) -> None:
    cur = conn.cursor()

    tbl_rules     = rs.get_setting_value(csv, sk.KEY_TBL_RULES)
    tbl_cat_type  = rs.get_setting_value(csv, sk.KEY_TBL_CAT_TYPE)
    tbl_cat_major = rs.get_setting_value(csv, sk.KEY_TBL_CAT_MAJOR)
    tbl_cat_sub   = rs.get_setting_value(csv, sk.KEY_TBL_CAT_SUB)
    tbl_cat_state = rs.get_setting_value(csv, sk.KEY_TBL_CAT_STATE)

    table_names = {
        "RULES":     tbl_rules,
        "CAT_TYPE":  tbl_cat_type,
        "CAT_MAJOR": tbl_cat_major,
        "CAT_SUB":   tbl_cat_sub,
        "CAT_STATE": tbl_cat_state,
    }

    # Drop
    drop_script = "\n".join(
        f"DROP TABLE IF EXISTS {quote_ident(name)};" for name in table_names.values()
    )
    print("SQL::DROP")
    print(drop_script)
    cur.executescript(drop_script)

    # Column definitions (ITM_***)
    groups = list(table_names.keys())
    item_defs = rs.get_setting_sql_table_item(csv, groups)

    # Create
    create_script = ""
    for group, tbl_name in table_names.items():
        create_script += build_create_table_sql(tbl_name, item_defs[group])
    print("SQL::CREATE")
    print(create_script)
    cur.executescript(create_script)
    conn.commit()


def main():

    setting_csv = rs.load_setting_csv()  # sub.py から見た data/sample.csv を読む
    print(setting_csv)

    DB_PATH     = Path( rs.get_setting_value( setting_csv, sk.KEY_DB_NAME ) )              # 作成される SQLite ファイル
    EXCEL_PATH  = Path(rs.get_setting_value( setting_csv, sk.KEY_SRC_EXCEL ) )   # Excel ファイル名（必要なら変更）

    if not EXCEL_PATH.exists():
        print(f"Excel file not found: {EXCEL_PATH}")
        return

    # 既存DBを削除して作り直す（初期開発フェーズなので割り切り）
    if DB_PATH.exists():
        print(f"Delete DB file: {DB_PATH}")
        DB_PATH.unlink()

    sql_file = sqlite3.connect( DB_PATH)

    # スキーマ作成（カラム名・型をここで固定）
    create_tables(setting_csv, sql_file)

    # 各シートを読み込む
    rules_df                = load_sheet_clean( EXCEL_PATH, rs.get_setting_value( setting_csv, sk.KEY_TBL_RULES      ) )
    cat_key_type_df         = load_sheet_clean( EXCEL_PATH, rs.get_setting_value( setting_csv, sk.KEY_TBL_CAT_TYPE   ) )
    cat_major_df            = load_sheet_clean( EXCEL_PATH, rs.get_setting_value( setting_csv, sk.KEY_TBL_CAT_MAJOR  ) )
    cat_sub_df              = load_sheet_clean( EXCEL_PATH, rs.get_setting_value( setting_csv, sk.KEY_TBL_CAT_SUB    ) )
    state_df                = load_sheet_clean( EXCEL_PATH, rs.get_setting_value( setting_csv, sk.KEY_TBL_CAT_STATE  ) )
    cat_request_df          = load_sheet_clean( EXCEL_PATH, rs.get_setting_value( setting_csv, sk.KEY_TBL_CAT_REQUEST         ) )
    cat_phase_df            = load_sheet_clean( EXCEL_PATH, rs.get_setting_value( setting_csv, sk.KEY_TBL_CAT_PHASE           ) )
    scp_sales_region_df     = load_sheet_clean( EXCEL_PATH, rs.get_setting_value( setting_csv, sk.KEY_TBL_SCP_SALES_REGION    ) )
    scp_product_genre_df    = load_sheet_clean( EXCEL_PATH, rs.get_setting_value( setting_csv, sk.KEY_TBL_SCP_PRODUCT_GENRE   ) )
    scp_service_genre_df    = load_sheet_clean( EXCEL_PATH, rs.get_setting_value( setting_csv, sk.KEY_TBL_SCP_SERVICE_GENRE   ) )
    scp_equipment_df        = load_sheet_clean( EXCEL_PATH, rs.get_setting_value( setting_csv, sk.KEY_TBL_SCP_EQUIPMENT       ) )
    scp_pii_df              = load_sheet_clean( EXCEL_PATH, rs.get_setting_value( setting_csv, sk.KEY_TBL_SCP_PII             ) )
    scp_design_domain_df    = load_sheet_clean( EXCEL_PATH, rs.get_setting_value( setting_csv, sk.KEY_TBL_SCP_DESIGN_DOMAIN   ) )
    request_df              = load_sheet_clean( EXCEL_PATH, rs.get_setting_value( setting_csv, sk.KEY_TBL_REQUEST             ) )
   

    # --- 重要ポイント ---
    # DataFrame の列を「テーブルに実際に存在する列だけ」に絞る
    # （Excel側に余分な列があってもここで無視できる）
    rules_df = rules_df[[
          rs.get_setting_value( setting_csv, sk.KEY_ITM_RULES_PKEY           )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_RULES_ID_RULE        )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_RULES_NAME_RULE      )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_RULES_FKEY_CAT_SUB   )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_RULES_LINK           )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_RULES_FKEY_CAT_STATE )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_RULES_CREATED_DATE   )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_RULES_UPDATE_DATE    )
    ]]

    cat_key_type_df = cat_key_type_df[[
          rs.get_setting_value( setting_csv, sk.KEY_ITM_CAT_TYPE_PKEY     )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_CAT_TYPE_TITLE_JP )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_CAT_TYPE_TITLE_EN )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_CAT_TYPE_PATH     )
    ]]

    cat_major_df = cat_major_df[[
          rs.get_setting_value( setting_csv, sk.KEY_ITM_CAT_MAJOR_PKEY          )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_CAT_MAJOR_TITLE_JP      )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_CAT_MAJOR_TITLE_EN      )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_CAT_MAJOR_FKEY_CAT_TYPE )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_CAT_MAJOR_PATH          )
    ]]

    cat_sub_df = cat_sub_df[[
          rs.get_setting_value( setting_csv, sk.KEY_ITM_CAT_SUB_PKEY           )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_CAT_SUB_TITLE_JP       )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_CAT_SUB_TITLE_EN       )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_CAT_SUB_FKEY_CAT_MAJOR )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_CAT_SUB_PATH           )
    ]]

    state_df = state_df[[
          rs.get_setting_value( setting_csv, sk.KEY_ITM_CAT_STATE_PKEY     )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_CAT_STATE_TITLE_JP )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_CAT_STATE_TITLE_EN )
    ]]

    cat_request_df = cat_request_df[[
          rs.get_setting_value( setting_csv, sk.KEY_ITM_CAT_REQUEST_PKEY     )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_CAT_REQUEST_TITLE_JP )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_CAT_REQUEST_TITLE_EN )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_CAT_REQUEST_KEY_CAT_REQ_TYPE )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_CAT_REQUEST_REQ_TYPE )
    ]]

    cat_phase_df = cat_phase_df[[
          rs.get_setting_value( setting_csv, sk.KEY_ITM_CAT_PHASE_PKEY     )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_CAT_PHASE_TITLE_JP )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_CAT_PHASE_TITLE_EN )
    ]]

    scp_sales_region_df = scp_sales_region_df[[
          rs.get_setting_value( setting_csv, sk.KEY_ITM_SCP_SALES_REGION_PKEY     )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_SCP_SALES_REGION_TITLE_JP )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_SCP_SALES_REGION_TITLE_EN )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_SCP_SALES_REGION_COUNTRY_CODE_2 )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_SCP_SALES_REGION_COUNTRY_CODE_3 )
    ]]

    scp_product_genre_df = scp_product_genre_df[[
          rs.get_setting_value( setting_csv, sk.KEY_ITM_SCP_PRODUCT_GENRE_PKEY      )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_SCP_PRODUCT_GENRE_TITLE_JP  )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_SCP_PRODUCT_GENRE_TITLE_EN  )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_SCP_PRODUCT_GENRE_HS_CODE   )
    ]]

    scp_service_genre_df = scp_service_genre_df[[
          rs.get_setting_value( setting_csv, sk.KEY_ITM_SCP_SERVICE_GENRE_PKEY      )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_SCP_SERVICE_GENRE_TITLE_JP  )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_SCP_SERVICE_GENRE_TITLE_EN  )
    ]]

    scp_equipment_df = scp_equipment_df[[
          rs.get_setting_value( setting_csv, sk.KEY_ITM_SCP_EQUIPMENT_PKEY      )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_SCP_EQUIPMENT_TITLE_JP  )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_SCP_EQUIPMENT_TITLE_EN  )
    ]]

    scp_pii_df = scp_pii_df[[
          rs.get_setting_value( setting_csv, sk.KEY_ITM_SCP_PII_PKEY      )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_SCP_PII_TITLE_JP  )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_SCP_PII_TITLE_EN  )
    ]]

    scp_design_domain_df = scp_design_domain_df[[
          rs.get_setting_value( setting_csv, sk.KEY_ITM_SCP_DESIGN_DOMAIN_PKEY     )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_SCP_DESIGN_DOMAIN_TITLE_JP )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_SCP_DESIGN_DOMAIN_TITLE_EN )
    ]]

    request_df = request_df[[
          rs.get_setting_value( setting_csv, sk.KEY_ITM_REQUEST_PKEY                  )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_REQUEST_KEY_RULE              )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_REQUEST_ID_CAP                )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_REQUEST_FTITLE_CAPTER         )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_REQUEST_TITLE_SECTION         )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_REQUEST_FTOP_BODY             )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_REQUEST_LOW_BODY              )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_REQUEST_TOP_TBL               )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_REQUEST_TOP_FIG               )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_REQUEST_LOW_TBL               )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_REQUEST_LOW_FIG               )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_REQUEST_LEAD_TIME             )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_REQUEST_REFERENCE             )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_REQUEST_CREATED_DATE          )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_REQUEST_FUPDATE_DATE          )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_REQUEST_FKEY_CAT_REQUEST      )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_REQUEST_FKEY_CAT_PHASE        )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_REQUEST_FSCOPE_PRODUCT_GENRE  )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_REQUEST_FSCOPE_SERVICE_GENRE  )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_REQUEST_FSCOPE_EQUIPMENT      )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_REQUEST_FSCOPE_PII            )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_REQUEST_FSCOPE_DESIGN_DOMAIN  )
        , rs.get_setting_value( setting_csv, sk.KEY_ITM_REQUEST_UNIQUE_SEARCH         )
    ]]

    '''
    '''
    # DataFrame → 既に定義済みのテーブルに INSERT
    rules_df                .to_sql (  rs.get_setting_value( setting_csv, sk.KEY_TBL_RULES               ), sql_file, if_exists="append", index=False)
    cat_key_type_df         .to_sql (  rs.get_setting_value( setting_csv, sk.KEY_TBL_CAT_TYPE            ), sql_file, if_exists="append", index=False)
    cat_major_df            .to_sql (  rs.get_setting_value( setting_csv, sk.KEY_TBL_CAT_MAJOR           ), sql_file, if_exists="append", index=False)
    cat_sub_df              .to_sql (  rs.get_setting_value( setting_csv, sk.KEY_TBL_CAT_SUB             ), sql_file, if_exists="append", index=False)
    state_df                .to_sql (  rs.get_setting_value( setting_csv, sk.KEY_TBL_CAT_STATE           ), sql_file, if_exists="append", index=False)
    cat_request_df          .to_sql (  rs.get_setting_value( setting_csv, sk.KEY_TBL_CAT_REQUEST         ), sql_file, if_exists="append", index=False)
    cat_phase_df            .to_sql (  rs.get_setting_value( setting_csv, sk.KEY_TBL_CAT_PHASE           ), sql_file, if_exists="append", index=False)
    scp_sales_region_df     .to_sql (  rs.get_setting_value( setting_csv, sk.KEY_TBL_SCP_SALES_REGION    ), sql_file, if_exists="append", index=False)
    scp_product_genre_df    .to_sql (  rs.get_setting_value( setting_csv, sk.KEY_TBL_SCP_PRODUCT_GENRE   ), sql_file, if_exists="append", index=False)
    scp_service_genre_df    .to_sql (  rs.get_setting_value( setting_csv, sk.KEY_TBL_SCP_SERVICE_GENRE   ), sql_file, if_exists="append", index=False)
    scp_equipment_df        .to_sql (  rs.get_setting_value( setting_csv, sk.KEY_TBL_SCP_EQUIPMENT       ), sql_file, if_exists="append", index=False)
    scp_pii_df              .to_sql (  rs.get_setting_value( setting_csv, sk.KEY_TBL_SCP_PII             ), sql_file, if_exists="append", index=False)
    scp_design_domain_df    .to_sql (  rs.get_setting_value( setting_csv, sk.KEY_TBL_SCP_DESIGN_DOMAIN   ), sql_file, if_exists="append", index=False)
    request_df              .to_sql (  rs.get_setting_value( setting_csv, sk.KEY_TBL_REQUEST             ), sql_file, if_exists="append", index=False)
 
    sql_file.close()
    print("Done. SQLite DB created:", DB_PATH)

if __name__ == "__main__":
    main()
