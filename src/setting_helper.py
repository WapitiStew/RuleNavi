import pandas as pd
import setting_key as sk

##
# @brief \jp CSVに記載されているビルドパスを取得する  \en Get the build path from CSV
# @return \jp ビルドパス \en Build path
# @param csv \jp 読み込んだCSVデータ（DataFrame） \en Loaded CSV data (DataFrame)
##
def rules_path( csv : pd.DataFrame ) -> str:

    setting_key = csv.set_index(csv.columns[0])
    setting_val = csv.columns[1]
    return setting_key.at[ sk.KEY_BUILD_DIR, setting_val ] + "/" + setting_key.at[ sk.KEY_RULES_DIR, setting_val ]

##
# @brief \jp CSVに記載されているビルドパスを取得する  \en Get the build path from CSV
# @return \jp ビルドパス \en Build path
# @param csv \jp 読み込んだCSVデータ（DataFrame） \en Loaded CSV data (DataFrame)
##
def rules_file_dir_path( csv : pd.DataFrame ) -> str:

    setting_key = csv.set_index(csv.columns[0])
    setting_val = csv.columns[1]
    return rules_path( csv ) + "/" + setting_key.at[ sk.KEY_RULES_FILE_DIR, setting_val ]


##
# @brief \jp CSVに記載されているビルドパスを取得する  \en Get the build path from CSV
# @return \jp リソースパス \en Resource path
# @param csv \jp 読み込んだCSVデータ（DataFrame） \en Loaded CSV data (DataFrame)
# @param filename \jp ファイル名 \en Filename
##
def rules_file_fullpath( csv : pd.DataFrame, filename: str ) -> str:

    setting_key = csv.set_index(csv.columns[0])
    setting_val = csv.columns[1]
    return setting_key.at[ sk.KEY_BUILD_DIR, setting_val ] + "/" + setting_key.at[ sk.KEY_RULES_DIR, setting_val ] + "/" + filename


##
# @brief \jp CSVに記載されているリソースパスを取得する  \en Get the resource path from CSV
# @return \jp リソースパス \en Resource path
# @param csv \jp 読み込んだCSVデータ（DataFrame） \en Loaded CSV data (DataFrame)
##
def resrc_path( csv : pd.DataFrame ) -> str:

    setting_key = csv.set_index(csv.columns[0])
    setting_val = csv.columns[1]
    return setting_key.at[ sk.KEY_RESRC_DIR, setting_val ]


##
# @brief \jp CSVに記載されているリソースパスを取得する  \en Get the resource path from CSV
# @return \jp リソースパス \en Resource path
# @param csv \jp 読み込んだCSVデータ（DataFrame） \en Loaded CSV data (DataFrame)
# @param filename \jp ファイル名 \en Filename
##
def resrc_file_fullpath( csv : pd.DataFrame, filename: str ) -> str:

    setting_key = csv.set_index(csv.columns[0])
    setting_val = csv.columns[1]
    return setting_key.at[ sk.KEY_RESRC_DIR, setting_val ] + "/" + filename

##
# @brief \jp CSVに記載されているリソースパスを取得する  \en Get the resource path from CSV
# @return \jp リソースパス \en Resource path
# @param csv \jp 読み込んだCSVデータ（DataFrame） \en Loaded CSV data (DataFrame)
# @param filename \jp ファイル名 \en Filename
##
def json_file_fullpath( csv : pd.DataFrame, filename: str ) -> str:
    setting_key = csv.set_index(csv.columns[0])
    setting_val = csv.columns[1]
    return rules_path( csv ) + "/" + setting_key.at[ sk.KEY_JSON_DIR, setting_val ] + "/" + filename


##
# @brief \jp CSVに記載されているリソースパスを取得する  \en Get the resource path from CSV
# @return \jp リソースパス \en Resource path
# @param csv \jp 読み込んだCSVデータ（DataFrame） \en Loaded CSV data (DataFrame)
# @param filename \jp ファイル名 \en Filename
##
def rule_html_dirpath( csv : pd.DataFrame ) -> str:
    setting_key = csv.set_index(csv.columns[0])
    setting_val = csv.columns[1]
    return rules_path( csv ) + "/" + setting_key.at[ sk.KEY_HTML_DIR, setting_val ]

##
# @brief \jp CSVに記載されているリソースパスを取得する  \en Get the resource path from CSV
# @return \jp リソースパス \en Resource path
# @param csv \jp 読み込んだCSVデータ（DataFrame） \en Loaded CSV data (DataFrame)
# @param filename \jp ファイル名 \en Filename
##
def rule_html_fullpath( csv : pd.DataFrame, filename: str ) -> str:
    return rule_html_dirpath( csv ) + "/" + filename