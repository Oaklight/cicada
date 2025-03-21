import json
import logging
import os
import sqlite3
from sqlite3 import Connection

logger = logging.getLogger(__name__)


class CodeCache:
    def __init__(self, db_file="coding.db"):
        # Ensure the directory exists
        db_dir = os.path.dirname(db_file)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)

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
                is_correct INTEGER DEFAULT 0,  -- 1 for True, 0 for False
                is_runnable INTEGER DEFAULT 0, -- 1 for True, 0 for False
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
        logger.info("Database tables initialized.")

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
            logger.warning(f"No session found with ID: {session_id}")
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
        logger.info(f"Session inserted with ID: {session_id}")
        return session_id

    def update_session(
        self,
        session_id,
        design_goal: str | None = None,
        coding_plan: dict | None = None,
    ):  # Make design_goal optional and denote coding_plan as dict|None
        if design_goal is None and coding_plan is None:
            logger.warning("Either design_goal or coding_plan must be provided.")
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
        logger.info(f"Session with ID {session_id} updated.")

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
            logger.warning(f"No iteration found with ID: {iteration_id}")
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
            logger.warning(f"No iterations found for session ID: {session_id}")
            return None

    def insert_iteration(self, session_id, code, feedback=None):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO iteration (session_id, code, feedback, is_correct, is_runnable)
            VALUES (?, ?, ?, 0, 1)  -- 0 for False, 1 for True
            """,
            (session_id, code, feedback),
        )
        conn.commit()
        iteration_id = cursor.lastrowid
        self._return_connection(conn)
        logger.info(f"Iteration inserted with ID: {iteration_id}")
        return iteration_id

    def update_iteration(
        self, iteration_id, code=None, feedback=None, is_correct=None, is_runnable=None
    ):
        conn = self._get_connection()
        cursor = conn.cursor()
        set_clauses = []
        params = []
        if code is not None:
            set_clauses.append("code = ?")
            params.append(code)
        if feedback is not None:
            set_clauses.append("feedback = ?")
            params.append(feedback)
        if is_correct is not None:
            set_clauses.append("is_correct = ?")
            params.append(int(is_correct))
        if is_runnable is not None:
            set_clauses.append("is_runnable = ?")
            params.append(int(is_runnable))
        if set_clauses:
            query = f"UPDATE iteration SET {', '.join(set_clauses)} WHERE id = ?"
            params.append(iteration_id)
            cursor.execute(query, tuple(params))
            conn.commit()
        self._return_connection(conn)
        logger.info(f"Iteration with ID {iteration_id} updated.")

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
            logger.warning(f"No errors found for iteration ID: {iteration_id}")
            return None

    def insert_error(self, iteration_id, error_type, error_message, error_line=None):
        conn = self._get_connection()
        cursor = conn.cursor()
        # Set is_runnable to False if any error is present
        cursor.execute(
            """
            UPDATE iteration SET is_runnable = 0 WHERE id = ?
            """,
            (iteration_id,),
        )
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
        logger.info(f"Error inserted with ID: {error_id}")
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
        logger.info(f"Error with ID {error_id} updated.")

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

    def get_session_id(self, identifier, type_="iteration"):
        conn = self._get_connection()
        cursor = conn.cursor()

        if type_ == "iteration":
            cursor.execute(
                """
                SELECT session_id FROM iteration WHERE id = ?
                """,
                (identifier,),
            )
        elif type_ == "error":
            cursor.execute(
                """
                SELECT session_id FROM iteration WHERE id = (
                    SELECT iteration_id FROM error WHERE id = ?
                )
                """,
                (identifier,),
            )
        else:
            self._return_connection(conn)
            logger.error(f"Invalid type: {type_}")
            return None

        result = cursor.fetchone()
        self._return_connection(conn)

        if result:
            return result[0]
        else:
            logger.warning(f"No session found for {type_} ID: {identifier}")
            return None

    def close(self):
        for conn in self.connection_pool:
            if conn:
                conn.close()
        self.connection_pool.clear()
        logger.info("All database connections closed and cleaned up.")


# Usage example
if __name__ == "__main__":

    from cicada.core.utils import setup_logging

    setup_logging()

    # Create an instance of CodeCache
    code_cache = CodeCache("/tmp/cicada/coding.db")

    # Insert a new session
    session_id_1 = code_cache.insert_session("First Test Session")
    logger.info(f"Created session with ID: {session_id_1}")

    # Insert code snippets for the first session
    code_id_1 = code_cache.insert_iteration(
        session_id_1, 'print("Hello, World!")', "Looks good"
    )
    code_id_2 = code_cache.insert_iteration(
        session_id_1, 'print("Goodbye!")', "Syntax error"
    )

    # Insert errors for the second iteration
    code_cache.insert_error(code_id_2, "syntax", "IndentationError", 2)

    # After fixing errors, update iteration flags
    # Assuming errors are fixed
    code_cache.update_iteration(code_id_2, is_runnable=True)

    # Validate and set is_correct to True
    # Assuming external validation confirms correctness
    code_cache.update_iteration(code_id_1, is_correct=True)

    # Retrieve and print iterations with their flags
    iterations = code_cache.get_iterations(
        session_id_1, fields=["id", "code", "is_correct", "is_runnable"]
    )
    for iteration in iterations:
        logger.info(
            f"Iteration ID: {iteration['id']}, Code: {iteration['code']}, Correct: {bool(iteration['is_correct'])}, Runnable: {bool(iteration['is_runnable'])}"
        )

    # Clean up resources
    code_cache.close()
