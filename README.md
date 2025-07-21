# Large Spreadsheet Query Bot

[繁體中文](README_TW.md) | English

This project is a commissioned software system for Zhen Da Global Co., Ltd. Unauthorized use or resale is strictly prohibited.

## Project Overview

To handle **extremely large** spreadsheet files, this system uses `duckdb` to simulate spreadsheets as a database for efficient querying. It also supports real-time data export from the factory database to ensure all queries are based on the most up-to-date information.

## Project Structure

```
.
├── custom_terms.txt                           # Custom factory terminology
├── db_search.py                               # Real-time factory data queries
├── duckdb_handler.py                          # DuckDB query handler
├── files                                      # Folder for spreadsheet files
│   └── production_summary_20250702_1403.csv
├── llm_handler.py                             # Determines if query-related / Generates and processes SQL
├── main.py                                    # Main program using Streamlit
├── prompt_template.py                         # Template for spreadsheet name normalization
├── prompt.txt                                 # Prompt for Ollama model
├── response_rewriter.py                       # Converts query results into natural language
└── sql.py                                     # Real-time factory query SQL
```

## Detailed Workflow

1. Use `mssql` to export real-time factory data into a CSV file and place it in the `files` folder.
2. To avoid incorrect spreadsheet name references, read all spreadsheet and column names to initialize the model prompt.
3. Deploy the chatbot interface using `streamlit`.
4. Include the contents of `custom_terms.txt` (editable via the `streamlit` interface) in the prompt.
5. Use a first-stage model to classify the user query type:

> 5-1. If the query is **not** related to data retrieval, the first-stage model will respond directly.

> 5-2. If the query **is** data-related, the first-stage model will generate a `duckdb SQL` query to retrieve data. The second-stage model will then merge the original question and query result, and return a natural language answer.
>
> > 5-2-1. If the query fails, the error message will be rewritten by the second-stage model into a user-friendly explanation for debugging.
