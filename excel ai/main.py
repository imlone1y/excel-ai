import os
import re
import time
import hashlib
import pandas as pd
import streamlit as st
from datetime import datetime
from duckdb_handler import DuckDBHandler
from llm_handler import LLMHandler
from prompt_template import generate_table_schema
from db_search import output_csv
from response_rewriter import ResponseRewriter, LLMErrorHelper

# 每位使用者一組 session_id
def get_user_id():
    ctx = st.runtime.scriptrunner.get_script_run_ctx()
    session_id = ctx.session_id if ctx else "unknown"
    return hashlib.md5(session_id.encode()).hexdigest()

# 組合上下文 prompt（最多保留 N 輪）
def build_chat_prompt(messages: list, system_instruction: str = "", max_rounds: int = 5) -> str:
    rounds = []
    current_pair = []
    for msg in messages:
        if msg["role"] == "user":
            current_pair = [f"使用者：{msg['content']}"]
        elif msg["role"] == "assistant" and current_pair:
            current_pair.append(f"助手：{msg['content']}")
            rounds.append(current_pair)
            current_pair = []
    recent = rounds[-max_rounds:]
    prompt = [system_instruction] if system_instruction else []
    for pair in recent:
        prompt.extend(pair)
    if messages and messages[-1]["role"] == "user":
        prompt.append(f"使用者：{messages[-1]['content']}")
    prompt.append("助手：")
    return "\n".join(prompt)

# 初始化元件
db = DuckDBHandler()
llm = LLMHandler()
rewriter = ResponseRewriter()
error_helper = LLMErrorHelper()

# 每次查詢前保留最新 CSV
def retain_latest_production_csvs(folder: str = "./files", keep: int = 1):
    files = [f for f in os.listdir(folder) if f.startswith("production_summary") and f.endswith(".csv")]
    files = sorted(files, key=lambda f: os.path.getmtime(os.path.join(folder, f)), reverse=True)
    for file in files[keep:]:
        try:
            os.remove(os.path.join(folder, file))
        except:
            pass

# 載入 CSV 並註冊進 DuckDB
def prepare_duckdb():
    output_csv()
    retain_latest_production_csvs()

# Streamlit UI
st.set_page_config(page_title="資料查詢助手", layout="wide")
st.title("資料查詢聊天機器人")

# 📊 開關是否自動更新資料
auto_update = st.toggle("📈 啟用自動更新資料（每次對話都更新最新 CSV）", value=True)

# 🔧 特殊用語設定（共用全域）
st.markdown("### 🔧 特殊用語設定（所有人共用）")

with open("custom_terms.txt", "r", encoding="utf-8") as f:
    current_terms = f.read()

# 顯示可編輯欄位
edited_terms = st.text_area("✏️ 編輯特殊用法（可影響所有查詢結果）", value=current_terms, height=150)

# 儲存變更按鈕
if st.button("💾 儲存特殊用法"):
    with open("custom_terms.txt", "w", encoding="utf-8") as f:
        f.write(edited_terms)
    st.success("✅ 已成功儲存特殊用法設定")


# 批量上傳 CSV
st.subheader("📄 上傳 CSV 檔案")
uploaded_files = st.file_uploader("請選擇一個或多個 CSV 檔案", type=["csv"], accept_multiple_files=True)
if uploaded_files:
    for uploaded_file in uploaded_files:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{uploaded_file.name}"
        save_path = os.path.join("./files", filename)
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"已儲存：{uploaded_file.name} → `{filename}`")

# 多人對話隔離
uid = get_user_id()
if "user_states" not in st.session_state:
    st.session_state.user_states = {}

if uid not in st.session_state.user_states:
    st.session_state.user_states[uid] = {"messages": []}

user_state = st.session_state.user_states[uid]

# 顯示歷史對話
for msg in user_state["messages"]:
    with st.chat_message("user" if msg["role"] == "user" else "assistant"):
        st.markdown(msg["content"])

# 對話輸入處理
user_input = st.chat_input("請輸入問題或閒聊訊息...")
if user_input:
    user_state["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        try:
            if auto_update:
                prepare_duckdb()
            db.clear()
            csv_folder = "./files"
            for file in os.listdir(csv_folder):
                if file.endswith(".csv"):
                    try:
                        df = pd.read_csv(os.path.join(csv_folder, file))
                        table_name = file.replace(".csv", "")
                        db.register(table_name, df)
                    except Exception as e:
                        st.warning(f"⚠️ 無法載入 {file}：{e}")
            tables = db.list_tables()
            schema = generate_table_schema(tables, db, sample_rows=1)
            table_columns = {table: db.get_column_names(table) for table in tables}

            if not llm.is_query(user_input):
                chat_prompt = build_chat_prompt(
                    user_state["messages"],
                    system_instruction="你是一個親切且知識豐富的助理，請自然地延續對話，請用繁體中文回覆",
                    max_rounds=5
                )
                response = llm.llm.complete(prompt=chat_prompt, max_tokens=200).text.strip()
                st.markdown(response)
                user_state["messages"].append({"role": "assistant", "content": response})
            else:
                sql = llm.generate_sql(user_input, schema)
                sql = sql.replace("```sql", "").replace("```", "").strip()
                sql = llm.correct_table_names(sql)
                sql = llm.correct_column_names(sql, table_columns)

                # st.code(sql, language="sql")
                # print("🔍 LLM 查詢語句：", sql)
                result = db.query(sql)
                st.subheader("🔍 查詢結果")
                st.dataframe(result)
                explanation = rewriter.rewrite(user_input, result)
                st.markdown(f"{explanation}")
                user_state["messages"].append({"role": "assistant", "content": explanation})
        except Exception as e:
            error_msg = str(e)
            explanation = error_helper.transform_error_message(user_input, error_msg)
            st.error("查詢失敗")
            st.markdown(f"{explanation}")
            user_state["messages"].append({"role": "assistant", "content": explanation})
