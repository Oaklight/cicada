import sqlite3
import logging
from sqlite3 import Connection

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class CodeCache:
    def __init__(self, db_file="code-generator.db"):
        self.db_file = db_file
        self.connection_pool = []
        self.initialize_database()

    def _get_connection(self) -> Connection:
        if len(self.connection_pool) == 0:
            return sqlite3.connect(self.db_file)
        return self.connection_pool.pop()

    def _return_connection(self, conn: Connection):
        if conn:
            self.connection_pool.append(conn)

    def initialize_database(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions_table (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS codes_table (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                timestamp DATETIME DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW')),
                description TEXT,
                code TEXT,
                FOREIGN KEY(session_id) REFERENCES sessions_table(id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS execution_table (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code_id INTEGER,
                success BOOLEAN,
                error_message TEXT,
                output TEXT,
                FOREIGN KEY(code_id) REFERENCES codes_table(id)
            )
            """
        )

        conn.commit()
        self._return_connection(conn)
        logging.info("Database tables initialized.")

    def insert_session(self, description):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id FROM sessions_table WHERE description = ?
            """,
            (description,),
        )
        session_id = cursor.fetchone()
        if session_id:
            logging.info(f"Session already exists with ID: {session_id[0]}")
            return session_id[0]
        else:
            cursor.execute(
                """
                INSERT INTO sessions_table (description)
                VALUES (?)
                """,
                (description,),
            )
        conn.commit()
        logging.info(f"Session inserted with ID: {cursor.lastrowid}")
        session_id = cursor.lastrowid
        self._return_connection(conn)
        return session_id

    def insert_code(self, session_id, description, code):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO codes_table (session_id, description, code)
            VALUES (?, ?, ?)
            """,
            (session_id, description, code),
        )
        conn.commit()
        code_id = cursor.lastrowid
        logging.info(f"Code inserted with ID: {code_id}")
        self._return_connection(conn)
        return code_id

    def insert_execution_result(
        self, code_id, success, error_message=None, output=None
    ):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO execution_table (code_id, success, error_message, output)
            VALUES (?, ?, ?, ?)
            """,
            (code_id, success, error_message, output),
        )
        conn.commit()
        logging.info(f"Execution result inserted for code ID: {code_id}")
        self._return_connection(conn)

    def get_code_by_id(self, code_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT code FROM codes_table WHERE id = ?
            """,
            (code_id,),
        )
        result = cursor.fetchone()
        self._return_connection(conn)
        if result:
            return result[0]
        else:
            logging.warning(f"No code found with ID: {code_id}")
            return None

    def get_all_codes(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, description, code FROM codes_table
            """
        )
        codes = cursor.fetchall()
        self._return_connection(conn)
        return codes

    def get_everything_by_session(self, session_id, order_by="DESC"):
        order_map = {"descending": "DESC", "ascending": "ASC"}
        order_by = order_map.get(order_by.lower(), "DESC")
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT id, timestamp, description, code FROM codes_table
            WHERE session_id = ?
            ORDER BY timestamp {order_by}
            """,
            (session_id,),
        )
        session_codes = cursor.fetchall()
        self._return_connection(conn)
        return session_codes

    def get_execution_results_by_code_id(self, code_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT success, error_message, output FROM execution_table WHERE code_id = ?
            """,
            (code_id,),
        )
        execution_results = cursor.fetchall()
        self._return_connection(conn)
        return execution_results

    def close(self):
        for conn in self.connection_pool:
            if conn:
                conn.close()
        self.connection_pool.clear()
        logging.info("All database connections closed and cleaned up.")


# Usage example
if __name__ == "__main__":
    # Create an instance of CodeCache
    code_cache = CodeCache()

    # Insert a new session
    session_id_1 = code_cache.insert_session("First Test Session")
    logging.info(f"Created session with ID: {session_id_1}")

    # Insert code snippets for the first session
    code_id_1 = code_cache.insert_code(
        session_id_1, "Print Hello World", 'print("Hello, World!")'
    )
    code_id_2 = code_cache.insert_code(
        session_id_1, "Print Goodbye", 'print("Goodbye!")'
    )

    # Simulate execution of the code snippets
    code_cache.insert_execution_result(code_id_1, True, output="Hello, World!")
    code_cache.insert_execution_result(code_id_2, True, output="Goodbye!")

    # Insert another session
    session_id_2 = code_cache.insert_session("Second Test Session")
    logging.info(f"Created session with ID: {session_id_2}")

    # Insert code snippet for the second session
    code_id_3 = code_cache.insert_code(
        session_id_2, "Print Another Message", 'print("Another Message!")'
    )

    # Simulate execution of the code snippet
    code_cache.insert_execution_result(code_id_3, True, output="Another Message!")

    # Retrieve and print all codes for the first session
    codes_in_session_1 = code_cache.get_everything_by_session(session_id_1)
    logging.info(f"Codes in session {session_id_1}: {codes_in_session_1}")

    # Retrieve and print all codes for the second session
    codes_in_session_2 = code_cache.get_everything_by_session(session_id_2)
    logging.info(f"Codes in session {session_id_2}: {codes_in_session_2}")

    # Retrieve and print all execution results for the first code ID
    execution_results_code_1 = code_cache.get_execution_results_by_code_id(code_id_1)
    logging.info(
        f"Execution results for code ID {code_id_1}: {execution_results_code_1}"
    )

    # Retrieve and print all execution results for the second code ID
    execution_results_code_2 = code_cache.get_execution_results_by_code_id(code_id_2)
    logging.info(
        f"Execution results for code ID {code_id_2}: {execution_results_code_2}"
    )

    # Retrieve and print all execution results for the third code ID
    execution_results_code_3 = code_cache.get_execution_results_by_code_id(code_id_3)
    logging.info(
        f"Execution results for code ID {code_id_3}: {execution_results_code_3}"
    )

    # Clean up resources
    code_cache.close()
