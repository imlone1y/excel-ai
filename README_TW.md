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
1. 執行 `mssql` 將工廠即時數據輸出成 csv 檔，並放置到 `files` 資料夾下。
2. 為避免使用錯誤的名稱搜尋試算表，讀出所有試算表名稱、各列欄位名稱，初始化模型 prompt。
3. 利用 `streamlit` 部署對話介面。
4. 將 `custom_terms.txt` (也可在 `sreamlit` 網頁中修改) 內容一併加入 prompt。
5. 使用第一層模型判斷用戶問題類型
> 5-1. 若用戶問題非查詢，則直接用第一層模型回覆用戶
> 5-2. 若問題類型為查詢相關，則需由第一層模型生成 `duckdb sql` 輸出查詢結果，再由第二層模型將用戶問題及查詢結果合併後轉換為白話文回覆用戶。
>> 5-2-1. 若查詢失敗，則會將錯誤訊息由第二層模型轉換為白話文方便 debug。

