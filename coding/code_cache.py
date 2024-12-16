import json
import logging
import sqlite3
from sqlite3 import Connection

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class CodeCache:
    def __init__(self, db_file="coding.db"):
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
            CREATE TABLE IF NOT EXISTS session (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                design_goal TEXT NOT NULL,
                parent_session_id INTEGER,
                coding_plan TEXT,
                created_at TIMESTAMP DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW')),
                FOREIGN KEY (parent_session_id) REFERENCES session(id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS iteration (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                code TEXT NOT NULL,
                feedback TEXT,
                created_at TIMESTAMP DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW')),
                FOREIGN KEY (session_id) REFERENCES session(id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS error (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                iteration_id INTEGER NOT NULL,
                error_type TEXT CHECK(error_type IN ('syntax', 'runtime')),
                error_message TEXT,
                error_line INTEGER,
                created_at TIMESTAMP DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW')),
                FOREIGN KEY (iteration_id) REFERENCES iteration(id)
            )
            """
        )

        conn.commit()
        self._return_connection(conn)
        logging.info("Database tables initialized.")

    # Session API

    def get_session(self, session_id, fields=None):
        conn = self._get_connection()
        cursor = conn.cursor()
        if fields is None:
            fields = "*"
        else:
            fields = ", ".join(fields)
        cursor.execute(
            f"""
            SELECT {fields} FROM session WHERE id = ?
            """,
            (session_id,),
        )
        result = cursor.fetchone()
        self._return_connection(conn)
        if result:
            return dict(
                zip([description[0] for description in cursor.description], result)
            )
        else:
            logging.warning(f"No session found with ID: {session_id}")
            return None

    def insert_session(
        self, design_goal, parent_session_id=None, coding_plan=None
    ):  # Added coding_plan parameter
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO session (design_goal, parent_session_id, coding_plan)  -- Updated INSERT statement
            VALUES (?, ?, ?)
            """,
            (design_goal, parent_session_id, coding_plan),
        )
        conn.commit()
        session_id = cursor.lastrowid
        self._return_connection(conn)
        logging.info(f"Session inserted with ID: {session_id}")
        return session_id

    def update_session(
        self,
        session_id,
        design_goal: str | None = None,
        coding_plan: dict | None = None,
    ):  # Make design_goal optional and denote coding_plan as dict|None
        if design_goal is None and coding_plan is None:
            logging.warning("Either design_goal or coding_plan must be provided.")
            return
        conn = self._get_connection()
        cursor = conn.cursor()
        if design_goal is not None and coding_plan is not None:
            cursor.execute(
                """
                UPDATE session SET design_goal = ?, coding_plan = ? WHERE id = ?
                """,
                (design_goal, json.dumps(coding_plan), session_id),
            )
        elif design_goal is not None:
            cursor.execute(
                """
                UPDATE session SET design_goal = ? WHERE id = ?
                """,
                (design_goal, session_id),
            )
        elif coding_plan is not None:
            cursor.execute(
                """
                UPDATE session SET coding_plan = ? WHERE id = ?
                """,
                (json.dumps(coding_plan), session_id),
            )
        conn.commit()
        self._return_connection(conn)
        logging.info(f"Session with ID {session_id} updated.")

    def get_iteration(self, iteration_id, fields=None):
        conn = self._get_connection()
        cursor = conn.cursor()
        if fields is None:
            fields = "*"
        else:
            fields = ", ".join(fields)
        cursor.execute(
            f"""
            SELECT {fields} FROM iteration WHERE id = ?
            """,
            (iteration_id,),
        )
        result = cursor.fetchone()
        self._return_connection(conn)
        if result:
            return dict(
                zip([description[0] for description in cursor.description], result)
            )
        else:
            logging.warning(f"No iteration found with ID: {iteration_id}")
            return None

    def get_iterations(self, session_id, fields=None):
        conn = self._get_connection()
        cursor = conn.cursor()
        if fields is None:
            fields = "*"
        else:
            fields = ", ".join(fields)
        cursor.execute(
            f"""
            SELECT {fields} FROM iteration WHERE session_id = ?
            """,
            (session_id,),
        )
        results = cursor.fetchall()
        self._return_connection(conn)
        if results:
            return [
                dict(
                    zip([description[0] for description in cursor.description], result)
                )
                for result in results
            ]
        else:
            logging.warning(f"No iterations found for session ID: {session_id}")
            return None

    def insert_iteration(self, session_id, code, feedback=None):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO iteration (session_id, code, feedback)
            VALUES (?, ?, ?)
            """,
            (session_id, code, feedback),
        )
        conn.commit()
        iteration_id = cursor.lastrowid
        self._return_connection(conn)
        logging.info(f"Iteration inserted with ID: {iteration_id}")
        return iteration_id

    def update_iteration(self, iteration_id, code=None, feedback=None):
        conn = self._get_connection()
        cursor = conn.cursor()
        if code is not None and feedback is not None:
            cursor.execute(
                """
                UPDATE iteration SET code = ?, feedback = ? WHERE id = ?
                """,
                (code, feedback, iteration_id),
            )
        elif code is not None:
            cursor.execute(
                """
                UPDATE iteration SET code = ? WHERE id = ?
                """,
                (code, iteration_id),
            )
        elif feedback is not None:
            cursor.execute(
                """
                UPDATE iteration SET feedback = ? WHERE id = ?
                """,
                (feedback, iteration_id),
            )
        conn.commit()
        self._return_connection(conn)
        logging.info(f"Iteration with ID {iteration_id} updated.")

    # Error API

    def get_errors(self, iteration_id, fields=None):
        conn = self._get_connection()
        cursor = conn.cursor()
        if fields is None:
            fields = "*"
        else:
            fields = ", ".join(fields)
        cursor.execute(
            f"""
            SELECT {fields} FROM error WHERE iteration_id = ?
            """,
            (iteration_id,),
        )
        results = cursor.fetchall()
        self._return_connection(conn)
        if results:
            return [
                dict(
                    zip([description[0] for description in cursor.description], result)
                )
                for result in results
            ]
        else:
            logging.warning(f"No errors found for iteration ID: {iteration_id}")
            return None

    def insert_error(self, iteration_id, error_type, error_message, error_line=None):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO error (iteration_id, error_type, error_message, error_line)
            VALUES (?, ?, ?, ?)
            """,
            (iteration_id, error_type, error_message, error_line),
        )
        conn.commit()
        error_id = cursor.lastrowid
        self._return_connection(conn)
        logging.info(f"Error inserted with ID: {error_id}")
        return error_id

    def update_error(self, error_id, error_message, error_line=None):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE error SET error_message = ?, error_line = ? WHERE id = ?
            """,
            (error_message, error_line, error_id),
        )
        conn.commit()
        self._return_connection(conn)
        logging.info(f"Error with ID {error_id} updated.")

    # Additional Method

    def get_session_history(self, session_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM session WHERE id = ?
            """,
            (session_id,),
        )
        session = cursor.fetchone()
        if session is None:
            self._return_connection(conn)
            return None

        cursor.execute(
            """
            SELECT * FROM iteration WHERE session_id = ?
            """,
            (session_id,),
        )
        iterations = cursor.fetchall()

        for iteration in iterations:
            iteration_id = iteration[0]
            cursor.execute(
                """
                SELECT * FROM error WHERE iteration_id = ?
                """,
                (iteration_id,),
            )
            errors = cursor.fetchall()
            iteration += (errors,)

        self._return_connection(conn)
        session += (iterations,)
        return session

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
    code_id_1 = code_cache.insert_iteration(
        session_id_1, 'print("Hello, World!")', "Looks good"
    )
    code_id_2 = code_cache.insert_iteration(
        session_id_1, 'print("Goodbye!")', "Looks good"
    )

    # Insert errors for the first iteration
    code_cache.insert_error(code_id_1, "syntax", "IndentationError", 2)
    code_cache.insert_error(code_id_2, "runtime", "NameError", 1)

    # Retrieve and print session history
    session_history = code_cache.get_session_history(session_id_1)
    logging.info(f"Session history for session {session_id_1}: {session_history}")

    # Clean up resources
    code_cache.close()
