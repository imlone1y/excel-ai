import re

def generate_table_schema(tables: list, db_handler, sample_rows: int = 1) -> str:
    schema_descriptions = []
    for table in tables:
        date_hint = re.findall(r"\d{8}", table)
        date_str = f"（這是 {date_hint[0][:4]} 年 {date_hint[0][4:6]} 月 {date_hint[0][6:]} 號的資料）" if date_hint else ""

        columns = db_handler.get_column_names(table)
        col_list = ", ".join([f'"{col}"' for col in columns])

        # 加入範例資料
        try:
            sample = db_handler.query(f"SELECT * FROM {table} LIMIT {sample_rows}")
            sample_text = sample.to_dict(orient="records")[0]  # 第一筆
            example = "\n  範例：" + ", ".join([f"{k} = {v}" for k, v in sample_text.items()])
        except:
            example = ""

        schema_descriptions.append(f"{table} {date_str}\n  欄位: {col_list}{example}")

    return "\n\n".join(schema_descriptions)
