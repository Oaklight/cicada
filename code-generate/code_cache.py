import sqlite3
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Database setup
conn = sqlite3.connect("code_generator.db")
cursor = conn.cursor()


# Create tables if they don't exist
def initialize_database():
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
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
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
    logging.info("Database tables initialized.")


# Insert a new session
def insert_session(description):
    cursor.execute(
        """
        INSERT INTO sessions_table (description)
        VALUES (?)
    """,
        (description,),
    )
    conn.commit()
    logging.info(f"Session inserted with ID: {cursor.lastrowid}")
    return cursor.lastrowid


# Insert code into codes_table
def insert_code(session_id, description, code):
    cursor.execute(
        """
        INSERT INTO codes_table (session_id, description, code)
        VALUES (?, ?, ?)
    """,
        (session_id, description, code),
    )
    conn.commit()
    logging.info(f"Code inserted with ID: {cursor.lastrowid}")
    return cursor.lastrowid


# Insert execution result into execution_table
def insert_execution_result(code_id, success, error_message=None, output=None):
    cursor.execute(
        """
        INSERT INTO execution_table (code_id, success, error_message, output)
        VALUES (?, ?, ?, ?)
    """,
        (code_id, success, error_message, output),
    )
    conn.commit()
    logging.info(f"Execution result inserted for code ID: {code_id}")


# Retrieve code by ID
def get_code_by_id(code_id):
    cursor.execute(
        """
        SELECT code FROM codes_table WHERE id = ?
    """,
        (code_id,),
    )
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        logging.warning(f"No code found with ID: {code_id}")
        return None


# Retrieve all codes
def get_all_codes():
    cursor.execute(
        """
        SELECT id, description, code FROM codes_table
    """
    )
    return cursor.fetchall()


# Retrieve all codes in a session, ordered by timestamp
def get_everything_by_session(session_id, order_by="DESC"):
    order_map = {"descending": "DESC", "ascending": "ASC"}
    order_by = order_map.get(order_by.lower(), "DESC")

    cursor.execute(
        f"""
        SELECT id, timestamp, description, code FROM codes_table
        WHERE session_id = ?
        ORDER BY timestamp {order_by}
    """,
        (session_id,),
    )
    return cursor.fetchall()


# Retrieve execution results by code ID
def get_execution_results_by_code_id(code_id):
    cursor.execute(
        """
        SELECT success, error_message, output FROM execution_table WHERE code_id = ?
    """,
        (code_id,),
    )
    return cursor.fetchall()


# Close the database connection
def close_connection():
    conn.close()
    logging.info("Database connection closed.")
