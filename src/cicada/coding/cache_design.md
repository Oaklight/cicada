# Code Cache Design Document -- Conversation with Deepseek v2.5

## Finalized Database Design and API Methods

#### **Database Schema**

1. **Session Table**
   - **Columns:**

     - `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
     - `design_goal` (TEXT NOT NULL)
     - `parent_session_id` (INTEGER, FOREIGN KEY REFERENCES session(id), NULLABLE)
     - `created_at` (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)

2. **Iteration Table**
   - **Columns:**

     - `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
     - `session_id` (INTEGER NOT NULL, FOREIGN KEY REFERENCES session(id))
     - `code` (TEXT NOT NULL)
     - `feedback` (TEXT, NULLABLE)
     - `created_at` (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)

3. **Error Table**
   - **Columns:**

     - `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
     - `iteration_id` (INTEGER NOT NULL, FOREIGN KEY REFERENCES iteration(id))
     - `error_type` (TEXT CHECK(error_type IN ('syntax', 'runtime')))
     - `error_message` (TEXT)
     - `error_line` (INTEGER, NULLABLE)
     - `created_at` (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)

#### **API Methods**

1. **Session API**
   - `get_session(session_id, fields=None)`

   - `insert_session(design_goal, parent_session_id=None)`

   - `update_session(session_id, design_goal)`

2. **Iteration API**
   - `get_iteration(iteration_id, fields=None)`

   - `get_iterations(session_id, fields=None)`

   - `insert_iteration(session_id, code, feedback=None)`

   - `update_iteration(iteration_id, code=None, feedback=None)`

3. **Error API**
   - `get_errors(iteration_id, fields=None)`

   - `insert_error(iteration_id, error_type, error_message, error_line=None)`

   - `update_error(error_id, error_message, error_line=None)`

4. **Additional Method**
   - `get_session_history(session_id)` : Retrieves the session and all its iterations and errors.

#### **Key Considerations**

* **Session Tracking**: The `parent_session_id` allows tracking the evolution of design goals by linking sessions in a chain.
* **Iteration Sequencing**: Iterations are ordered by `created_at` timestamp or by their `id` within a session.
* **Error Handling**: Errors are stored in a separate table to handle multiple errors per iteration.
* **Data Validation**: Ensure that session_id and iteration_id exist before performing operations.
* **Flexibility**: API methods allow specifying fields to retrieve, and only update provided fields.

This design provides a clear, scalable, and maintainable structure for managing code generation sessions, iterations, and associated errors.

### Estimated Database Size

To estimate the size of the SQLite database for the given scenario, we need to consider the size of the data stored in each table ( `session` , `iteration` , and `error` ) and calculate the total storage requirements. Here's a step-by-step breakdown:

---

### **Assumptions:**

1. **Number of Sessions:** 40,000.
2. **Average Number of Iterations per Session:** 4.
3. **Average Number of Errors per Session:** 3.
4. **Schema Structure:**
   - `session` : Stores metadata about each session.
   - `iteration` : Stores code iterations for each session.
   - `error` : Stores error records for each iteration.

---

## **Data Size Estimation for Each Table:**

#### 1. ** `session` Table:**

* **Columns:**
  + `id`: INTEGER (4 bytes).
  + `design_goal`: TEXT (average length of 100 characters, or 100 bytes).
  + `parent_session_id`: INTEGER (4 bytes, nullable, so assume 50% nulls).
  + `created_at`: TIMESTAMP (21 bytes, including precision).
* **Average Row Size:**
  \[
  4 + 100 + (0.5 \times 4) + 21 = 127 \text{ bytes per session}.
  \]
* **Total Size for `session`:**
  \[
  40, 000 \times 127 = 5, 080, 000 \text{ bytes (5.08 MB)}.
  \]

---

#### 2. ** `iteration` Table:**

* **Columns:**
  + `id`: INTEGER (4 bytes).
  + `session_id`: INTEGER (4 bytes).
  + `code`: TEXT (average length of 500 characters, or 500 bytes).
  + `feedback`: TEXT (average length of 200 characters, or 200 bytes, nullable, so assume 50% nulls).
  + `created_at`: TIMESTAMP (21 bytes).
* **Average Row Size:**
  \[
  4 + 4 + 500 + (0.5 \times 200) + 21 = 734 \text{ bytes per iteration}.
  \]
* **Total Iterations:**
  \[
  40, 000 \times 4 = 160, 000 \text{ iterations}.
  \]
* **Total Size for `iteration`:**
  \[
  160, 000 \times 734 = 117, 440, 000 \text{ bytes (117.44 MB)}.
  \]

---

#### 3. ** `error` Table:**

* **Columns:**
  + `id`: INTEGER (4 bytes).
  + `iteration_id`: INTEGER (4 bytes).
  + `error_type`: TEXT (average length of 20 characters, or 20 bytes).
  + `error_message`: TEXT (average length of 100 characters, or 100 bytes).
  + `error_line`: INTEGER (4 bytes, nullable, so assume 50% nulls).
  + `created_at`: TIMESTAMP (21 bytes).
* **Average Row Size:**
  \[
  4 + 4 + 20 + 100 + (0.5 \times 4) + 21 = 156 \text{ bytes per error}.
  \]
* **Total Errors:**
  \[
  40, 000 \times 3 = 120, 000 \text{ errors}.
  \]
* **Total Size for `error`:**
  \[
  120, 000 \times 156 = 18, 720, 000 \text{ bytes (18.72 MB)}.
  \]

---

### **Total Database Size:**

Now, we sum up the sizes of all three tables:
\[
\text{Total Size} = 5.08 \text{ MB} + 117.44 \text{ MB} + 18.72 \text{ MB} = 141.24 \text{ MB}.
\]

---

### **Additional Considerations:**

1. **SQLite Overhead:**
   - SQLite adds some overhead for bookkeeping (e.g., indexes, metadata, etc.). This overhead is typically small (around 10-20%) compared to the size of the data.
   - Assuming an overhead of 15%, the total database size would be approximately:

     \[
     141.24 \text{ MB} \times 1.15 = 162.43 \text{ MB}.
     \]

2. **Compression:**
   - SQLite databases are stored as single files, and modern filesystems (e.g., ext4, NTFS) provide some level of compression. However, SQLite itself does not compress data directly, so the total size estimate is realistic.

3. **Dynamic Changes:**
   - If the average sizes of text fields ( `design_goal` , `code` , `feedback` , etc.) increase, the database size will grow proportionally.

---

### **Final Estimate:**

The SQLite database will occupy approximately **162 MB** of storage for 40, 000 sessions, with 4 iterations per session and 3 error records per session.
