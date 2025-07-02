from llama_index.llms.ollama import Ollama

class ResponseRewriter:
    def __init__(self):
        self.llm = Ollama(model="qwen2.5:32b", request_timeout=300.0)

    def rewrite(self, question: str, df) -> str:
        # 將查詢結果轉成文字（可簡化或 prettify）
        data_text = df.to_string(index=False)

        prompt = f"""
        你是一位親切的資料解說員。請根據下方使用者的問題與資料表的查詢結果，以口語化、白話文的方式回答問題。

        [問題]
        {question}

        [查詢結果]
        {data_text}

        請用自然語言回答這個問題：
        """

        response = self.llm.complete(prompt=prompt, max_tokens=256)
        return response.text.strip()



class LLMErrorHelper:
    def __init__(self):
        self.llm = Ollama(model="qwen2.5:32b", request_timeout=120.0)

    def transform_error_message(self, user_input: str, error_message: str) -> str:
        prompt = f"""
        你是一個資料庫查詢助手，請將下列 SQL 查詢錯誤訊息轉換為白話文，讓使用者了解發生了什麼問題，並建議可能的解決方式。請用簡短親切的語氣回覆。

        [使用者問題]
        {user_input}

        [錯誤訊息]
        {error_message}

        請用白話文說明這個錯誤可能是什麼原因，並提出建議：
        """.strip()
        response = self.llm.complete(prompt=prompt, max_tokens=200)
        return response.text.strip()
