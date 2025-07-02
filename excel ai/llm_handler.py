import re
import os
from llama_index.llms.ollama import Ollama

class LLMHandler:
    def __init__(self, csv_folder="./files"):
        self.llm = Ollama(model="qwen2.5:32b", request_timeout=300.0)
        self.csv_folder = csv_folder
    
    def is_query(self, text: str) -> bool:
        prompt = f"""
        你是一個分類助手。請判斷下列句子是否為「針對資料的查詢問題」。
        如果是請回答 YES，如果不是請回答 NO。

        句子：
        {text}
        """
        response = self.llm.complete(prompt=prompt, max_tokens=5)
        return "YES" in response.text.strip().upper()


    def generate_sql(self, question: str, schema: str) -> str:
        # 讀取 prompt 檔案
        with open("prompt.txt", "r", encoding="utf-8") as f:
            prompt_template = f.read()
        
        with open("custom_terms.txt", "r", encoding="utf-8") as f:
            custom_terms = f.read()

        # 套用格式
        prompt = prompt_template.format(
            question=question,
            schema=schema,
            custom_terms=custom_terms
        )
        # 呼叫模型
        response = self.llm.complete(prompt=prompt, max_tokens=512)
        sql = response.text.strip()

        # 修正欄位名稱雙引號處理
        column_names = [
            "Line Name", "Style", "Start Time", "Check Quantity",
            "Defect Quantity", "Net Good Quantity", "People",
            "IE Seconds", "Work Seconds", "Defect Rate %",
            "Line Good Ratio %", "Efficiency %"
        ]
        for col in column_names:
            sql = re.sub(rf'(?<!")\b{re.escape(col)}\b(?!")', f'"{col}"', sql)
            if '"' in col:
                parts = col.split('"')
                if len(parts) == 2:
                    broken = f'"{parts[0]}" {parts[1]}'
                    sql = sql.replace(broken, f'"{col}"')
        sql = sql.replace('"Efficiency" %', '"Efficiency %"')
        return sql


    def correct_table_names(self, sql: str) -> str:
        import difflib

        all_csvs = [f.replace(".csv", "") for f in os.listdir(self.csv_folder) if f.endswith(".csv")]

        # 找出 SQL 中出現的所有 FROM 表格名稱
        matches = re.findall(r'\bFROM\s+([^\s;]+)', sql, re.IGNORECASE)
        for name in matches:
            if name not in all_csvs:
                best_match = difflib.get_close_matches(name, all_csvs, n=1, cutoff=0.5)
                if best_match:
                    sql = sql.replace(name, best_match[0])
        return sql

    def correct_column_names(self, sql: str, table_columns: dict) -> str:
        import difflib

        # 針對每張表格處理對應欄位
        for table, columns in table_columns.items():
            for col in re.findall(rf'"([^"]+)"', sql):
                if col not in columns:
                    best_match = difflib.get_close_matches(col, columns, n=1, cutoff=0.6)
                    if best_match:
                        sql = re.sub(rf'"{re.escape(col)}"', f'"{best_match[0]}"', sql)
        return sql


def get_latest_csv_name(folder: str = "./files") -> str:
    csv_files = [f for f in os.listdir(folder) if f.endswith(".csv") and "production_summary" in f]
    if not csv_files:
        raise FileNotFoundError("找不到任何 production_summary 開頭的 csv 檔案")
    
    latest_file = max(csv_files, key=lambda f: os.path.getmtime(os.path.join(folder, f)))
    return latest_file.replace(".csv", "")
