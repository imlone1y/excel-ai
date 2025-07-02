import duckdb

class DuckDBHandler:
    def __init__(self):
        self.conn = duckdb.connect(database=":memory:")
        self.tables = []

    def register_dataframe(self, name: str, df):
        self.conn.register(name, df)

    def list_tables(self) -> list:
        result = self.conn.execute("SHOW TABLES").fetchall()
        return [row[0] for row in result]

    def get_column_names(self, table: str) -> list:
        result = self.conn.execute(f"DESCRIBE {table}").fetchall()
        return [row[0] for row in result]

    def query(self, sql: str):
        return self.conn.execute(sql).df()

    def clear(self):
        for table in self.tables:
            self.conn.unregister(table)
        self.tables = []
        
    def register(self, table_name: str, df):
        self.conn.register(table_name, df)
        self.tables.append(table_name)