import pyodbc
import pandas as pd
from datetime import datetime
from sql import return_sql

conn_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=YOUR_SERVER_IP;"
    "DATABASE=YOUR_SERVER_DATABASE;"
    "UID=YOUR_DATABASE_LOGIN;"
    "PWD=YOUR_DATABASE_PASSWORD"
)


def output_csv():
    conn   = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    sql = return_sql() 
    cursor.execute(sql)

    last_columns, last_rows = None, None
    while True:
        if cursor.description:
            last_columns = [c[0] for c in cursor.description]
            last_rows    = [tuple(row) for row in cursor.fetchall()]
        if not cursor.nextset():
            break

    if last_columns is None:
        raise RuntimeError("此批 SQL 沒有任何 SELECT 結果集。")

    df = pd.DataFrame(last_rows, columns=last_columns)

    ts = datetime.now().strftime("%Y%m%d_%H%M")
    fn = f"./files/production_summary_{ts}.csv"
    df.to_csv(fn, index=False, encoding="utf-8-sig")

    # print(f"✅ 已輸出：{fn}")
    # print(df.head())

