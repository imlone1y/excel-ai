# 大型試算表項目查詢機器人

繁體中文 | [English](README.md)

本項目為振大環球股份有限公司所外包之軟體系統，未經授權禁止使用、販售。

## 項目介紹

為處理**極大型**試算表檔案，利用 `duckdb` 將大型的試算表模擬成資料庫進行查詢。也擁有即時從工廠資料庫中導出數據，確保每次查詢均為最新資料之功能。

## 項目結構
```
.
├── custom_terms.txt                           # 工廠特殊用語設定
├── db_search.py                               # 工廠即時資料查詢
├── duckdb_handler.py                          # duckdb 查詢
├── files                                      # 試算表放置處
│   └── production_summary_20250702_1403.csv
├── llm_handler.py                             # 判斷是否為查詢相關問題 / 生成、處理查詢 sql
├── main.py                                    # 主程式、streamlit 架構
├── prompt_template.py                         # 試算表名稱格式轉換
├── prompt.txt                                 # ollama 模型 prompt
├── response_rewriter.py                       # 將查詢出的結果轉換為白話文
└── sql.py                                     # 工廠資料即時查詢 sql
```
## 項目詳細處理流程
1. 執行 mssql 將工廠即時數據輸出成 csv 檔，並放置到 `files` 資料夾下
